"""Middleware configuration for the API."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from stackrank.api.models.responses import ErrorResponse


def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the FastAPI app."""

    # CORS middleware - allow all origins for Phase 2
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="InternalServerError",
                detail=str(exc),
            ).model_dump(),
        )