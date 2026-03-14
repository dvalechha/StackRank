"""Job management endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from stackrank.api.models.requests import CreateJobRequest
from stackrank.api.models.responses import ErrorResponse, JobListResponse, JobResponse
from stackrank.api.storage import Job, jobs_store, runs_store

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    title: str,
    jd_file: UploadFile,
) -> JobResponse:
    """Create a new job by uploading a JD file."""
    import tempfile
    import shutil
    import os

    # Save uploaded JD file to temp location
    temp_dir = tempfile.mkdtemp()
    jd_temp_path = os.path.join(temp_dir, jd_file.filename)

    try:
        with open(jd_temp_path, "wb") as f:
            content = await jd_file.read()
            f.write(content)

        # Create job
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            title=title,
            created_at=datetime.utcnow(),
            status="active",
            jd_file_path=jd_temp_path,
        )
        jobs_store[job_id] = job

        return JobResponse(
            job_id=job.job_id,
            title=job.title,
            created_at=job.created_at,
            status=job.status,
            screening_runs=job.screening_runs,
        )
    except Exception as e:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


@router.get("", response_model=JobListResponse)
async def list_jobs() -> JobListResponse:
    """List all jobs."""
    jobs = [
        JobResponse(
            job_id=job.job_id,
            title=job.title,
            created_at=job.created_at,
            status=job.status,
            screening_runs=job.screening_runs,
        )
        for job in jobs_store.values()
    ]
    return JobListResponse(jobs=jobs)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Get a single job's details."""
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return JobResponse(
        job_id=job.job_id,
        title=job.title,
        created_at=job.created_at,
        status=job.status,
        screening_runs=job.screening_runs,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str) -> None:
    """Delete a job and all associated screening runs."""
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Clean up JD file
    if job.jd_file_path:
        import os
        temp_dir = os.path.dirname(job.jd_file_path)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Delete associated runs
    runs_to_delete = [run_id for run_id, run in runs_store.items() if run.job_id == job_id]
    for run_id in runs_to_delete:
        del runs_store[run_id]

    # Delete job
    del jobs_store[job_id]