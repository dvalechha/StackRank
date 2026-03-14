"""Resume screening endpoints."""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from stackrank.api.models.responses import (
    CandidateResult,
    DimensionScore,
    Recommendation,
    ScreeningRunListResponse,
    ScreeningRunResponse,
)
from stackrank.api.storage import ScreeningRun, jobs_store, runs_store

router = APIRouter(prefix="/jobs", tags=["screening"])

# Valid file extensions for resumes
VALID_EXTENSIONS = {".pdf", ".docx"}


def is_valid_resume(filename: str) -> bool:
    """Check if file has a valid resume extension."""
    return Path(filename).suffix.lower() in VALID_EXTENSIONS


@router.post("/{job_id}/screen", response_model=ScreeningRunResponse)
async def screen_resumes(
    job_id: str,
    resumes: list[UploadFile] = File(...),
    top_n: int | None = Form(None),
) -> ScreeningRunResponse:
    """Upload resumes and run screening against the job's JD."""
    import os
    import tempfile
    import shutil

    # Validate job exists
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Validate JD file exists
    if not job.jd_file_path or not os.path.exists(job.jd_file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job description file not found",
        )

    # Validate resumes
    valid_resumes = [r for r in resumes if is_valid_resume(r.filename)]
    if not valid_resumes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid resume files uploaded. Allowed: .pdf, .docx",
        )

    # Create temp directory for processing
    temp_dir = tempfile.mkdtemp()

    try:
        # Import Phase 1 modules
        from stackrank.config_loader import load_config
        from stackrank.jd_parser import parse_jd
        from stackrank.resume_parser import parse_resume
        from stackrank.scorer import score_candidate

        # Load config once at startup
        config = load_config()

        # Parse JD
        jd_text = parse_jd(job.jd_file_path)

        # Process each resume
        results: list[dict] = []

        for resume_file in valid_resumes:
            # Save resume to temp
            resume_temp_path = os.path.join(temp_dir, resume_file.filename)
            with open(resume_temp_path, "wb") as f:
                content = await resume_file.read()
                f.write(content)

            try:
                # Parse resume
                candidate = parse_resume(resume_temp_path)

                # Score candidate
                score_result = score_candidate(jd_text, candidate, config)

                results.append(
                    {
                        "file_name": resume_file.filename,
                        "candidate": candidate,
                        "score_result": score_result,
                    }
                )
            finally:
                # Clean up individual resume temp file
                if os.path.exists(resume_temp_path):
                    os.remove(resume_temp_path)

        # Sort by total score descending
        results.sort(key=lambda x: x["score_result"]["total_score"], reverse=True)

        # Apply top_n limit
        if top_n:
            results = results[:top_n]

        # Build response
        candidates = []
        for rank, result in enumerate(results, start=1):
            score_result = result["score_result"]
            candidate = result["candidate"]

            # Build dimensions dict
            dimensions = {}
            for dim_name, dim_data in score_result["dimensions"].items():
                dimensions[dim_name] = DimensionScore(
                    score=dim_data["score"],
                    rationale=dim_data["rationale"],
                )

            # Determine recommendation
            total_score = score_result["total_score"]
            if total_score >= 85:
                recommendation = Recommendation.STRONG_YES
            elif total_score >= 70:
                recommendation = Recommendation.YES
            elif total_score >= 50:
                recommendation = Recommendation.MAYBE
            else:
                recommendation = Recommendation.NO

            candidates.append(
                CandidateResult(
                    rank=rank,
                    candidate_name=candidate.get("name", "Unknown"),
                    file_name=result["file_name"],
                    total_score=total_score,
                    recommendation=recommendation,
                    summary=score_result["summary"],
                    dimensions=dimensions,
                )
            )

        # Create screening run
        run_id = str(uuid.uuid4())
        run = ScreeningRun(
            run_id=run_id,
            job_id=job_id,
            job_title=job.title,
            run_timestamp=datetime.utcnow(),
            model=config.get("model", "gpt-4o"),
            provider=config.get("provider", "openai_internal"),
            total_candidates_evaluated=len(valid_resumes),
            candidates=candidates,
        )

        runs_store[run_id] = run

        # Update job's screening runs count
        job.screening_runs += 1

        return ScreeningRunResponse(
            run_id=run.run_id,
            job_id=run.job_id,
            job_title=run.job_title,
            run_timestamp=run.run_timestamp,
            model=run.model,
            provider=run.provider,
            total_candidates_evaluated=run.total_candidates_evaluated,
            candidates=run.candidates,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI provider error: {str(e)}",
        )
    finally:
        # Always clean up temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/{job_id}/runs", response_model=ScreeningRunListResponse)
async def list_runs(job_id: str) -> ScreeningRunListResponse:
    """List all screening runs for a job."""
    # Validate job exists
    if job_id not in jobs_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    runs = [
        ScreeningRunResponse(
            run_id=run.run_id,
            job_id=run.job_id,
            job_title=run.job_title,
            run_timestamp=run.run_timestamp,
            model=run.model,
            provider=run.provider,
            total_candidates_evaluated=run.total_candidates_evaluated,
            candidates=run.candidates,
        )
        for run in runs_store.values()
        if run.job_id == job_id
    ]

    return ScreeningRunListResponse(runs=runs)


@router.get("/{job_id}/runs/{run_id}", response_model=ScreeningRunResponse)
async def get_run(job_id: str, run_id: str) -> ScreeningRunResponse:
    """Retrieve full results of a past screening run."""
    # Validate job exists
    if job_id not in jobs_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    run = runs_store.get(run_id)
    if not run or run.job_id != job_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found for job {job_id}",
        )

    return ScreeningRunResponse(
        run_id=run.run_id,
        job_id=run.job_id,
        job_title=run.job_title,
        run_timestamp=run.run_timestamp,
        model=run.model,
        provider=run.provider,
        total_candidates_evaluated=run.total_candidates_evaluated,
        candidates=run.candidates,
    )