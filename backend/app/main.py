"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.api import (
    sessions_router,
    steps_router,
    actions_router,
    recommendations_router,
    llm_router,
    export_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-based Instructional Design Decision Support System",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions_router, prefix=settings.API_V1_PREFIX)
app.include_router(steps_router, prefix=settings.API_V1_PREFIX)
app.include_router(actions_router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendations_router, prefix=settings.API_V1_PREFIX)
app.include_router(llm_router, prefix=settings.API_V1_PREFIX)
app.include_router(export_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "sessions": f"{settings.API_V1_PREFIX}/sessions",
            "steps": f"{settings.API_V1_PREFIX}/steps",
            "actions": f"{settings.API_V1_PREFIX}/actions",
            "recommendations": f"{settings.API_V1_PREFIX}/recommendations",
            "llm": f"{settings.API_V1_PREFIX}/llm",
            "export": f"{settings.API_V1_PREFIX}/export",
        },
    }
