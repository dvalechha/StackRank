"""In-memory storage for Phase 2."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from stackrank.api.models.responses import CandidateResult


@dataclass
class Job:
    """Job data model."""

    job_id: str
    title: str
    created_at: datetime
    status: str = "active"
    jd_file_path: Optional[str] = None
    screening_runs: int = 0


@dataclass
class ScreeningRun:
    """Screening run data model."""

    run_id: str
    job_id: str
    job_title: str
    run_timestamp: datetime
    model: str
    provider: str
    total_candidates_evaluated: int
    candidates: list[CandidateResult]


# In-memory stores (Phase 2 only)
jobs_store: dict[str, Job] = {}
runs_store: dict[str, ScreeningRun] = {}