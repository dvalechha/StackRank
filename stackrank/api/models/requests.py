"""Pydantic request models for the API."""

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    """Request model for creating a new job."""

    title: str = Field(..., description="Job title, e.g., 'Senior Engineer'")