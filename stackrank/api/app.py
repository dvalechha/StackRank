"""FastAPI application entry point."""

from fastapi import FastAPI

from stackrank.api.middleware import setup_middleware
from stackrank.api.routes import health, jobs, screening

app = FastAPI(
    title="StackRank API",
    version="0.1.0",
    description="AI-powered resume screening",
)

setup_middleware(app)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(screening.router)