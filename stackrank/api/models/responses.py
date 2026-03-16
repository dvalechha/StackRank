"""Pydantic response models for the API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    """Candidate recommendation enum."""

    STRONG_YES = "STRONG_YES"
    YES = "YES"
    MAYBE = "MAYBE"
    NO = "NO"


class DimensionScore(BaseModel):
    """Score for a single evaluation dimension."""

    score: int = Field(..., description="Score for this dimension (0-25)")
    rationale: str = Field(..., description="Explanation for the score")


class CandidateResult(BaseModel):
    """Result for a single candidate."""

    rank: int = Field(..., description="Rank position")
    candidate_name: str = Field(..., description="Extracted candidate name")
    file_name: str = Field(..., description="Original file name")
    total_score: int = Field(..., description="Total score (0-100)")
    recommendation: Recommendation = Field(..., description="Recommendation")
    summary: str = Field(..., description="Overall summary")
    dimensions: dict[str, DimensionScore] = Field(
        ..., description="Scores for each evaluation dimension"
    )


class JobResponse(BaseModel):
    """Response model for a single job."""

    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Job status (active/completed)")
    screening_runs: int = Field(default=0, description="Number of screening runs")


class JobListResponse(BaseModel):
    """Response model for listing jobs."""

    jobs: list[JobResponse] = Field(..., description="List of jobs")


class ScreeningRunResponse(BaseModel):
    """Response model for a screening run."""

    run_id: str = Field(..., description="Unique run identifier")
    job_id: str = Field(..., description="Associated job ID")
    job_title: str = Field(..., description="Job title")
    run_timestamp: datetime = Field(..., description="Run timestamp")
    model: str = Field(..., description="AI model used")
    provider: str = Field(..., description="AI provider used")
    total_candidates_evaluated: int = Field(
        ..., description="Total candidates evaluated"
    )
    candidates: list[CandidateResult] = Field(
        ..., description="Ranked candidate results"
    )


class ScreeningRunListResponse(BaseModel):
    """Response model for listing screening runs."""

    runs: list[ScreeningRunResponse] = Field(..., description="List of screening runs")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")