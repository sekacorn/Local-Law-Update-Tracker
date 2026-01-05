"""
LLUT FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import sys
from pathlib import Path

from .config import settings
from .db import db
from .settings import settings_manager
from .routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Database: {settings.db_path}")
    print(f"Storage mode: {settings.storage_mode}")

    # Initialize database
    await db.initialize()
    print("Database initialized")

    # Load settings
    user_settings = settings_manager.load()
    print(f"Settings loaded: {len(user_settings)} keys")

    yield

    # Shutdown
    print("Shutting down...")
    await db.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Local Law Update Tracker - API",
    lifespan=lifespan
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    Returns status of backend services
    """
    try:
        # Check database connection
        await db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": settings.app_version,
        "database": db_status,
        "storage_mode": settings.storage_mode
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Include API routes
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
