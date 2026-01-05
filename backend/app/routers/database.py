"""
Database management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import shutil

from ..db import db
from ..config import settings

router = APIRouter()


class ResetConfirmation(BaseModel):
    """Database reset confirmation"""
    confirm: bool = False


@router.post("/reset")
async def reset_database(confirmation: ResetConfirmation) -> Dict[str, Any]:
    """
    Reset local database and cache
    WARNING: This deletes all downloaded documents and metadata!
    """
    if not confirmation.confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm reset by setting confirm=true"
        )

    try:
        # Get sizes before deletion
        db_size = settings.db_path.stat().st_size if settings.db_path.exists() else 0
        cache_size = 0
        if settings.cache_dir.exists():
            cache_size = sum(
                f.stat().st_size
                for f in settings.cache_dir.rglob('*')
                if f.is_file()
            )

        # Reset database
        await db.reset()

        # Clear cache directory
        if settings.cache_dir.exists():
            shutil.rmtree(settings.cache_dir)
            settings.cache_dir.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "message": "Database and cache reset successfully",
            "freed_bytes": db_size + cache_size
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset database: {str(e)}"
        )


@router.get("/status")
async def get_database_status() -> Dict[str, Any]:
    """Get database status and statistics"""
    try:
        # Get database size
        db_size = settings.db_path.stat().st_size if settings.db_path.exists() else 0

        # Get cache size
        cache_size = 0
        cache_files = 0
        if settings.cache_dir.exists():
            for f in settings.cache_dir.rglob('*'):
                if f.is_file():
                    cache_size += f.stat().st_size
                    cache_files += 1

        # Get document counts
        doc_count = await db.fetch_one("SELECT COUNT(*) as count FROM document")
        version_count = await db.fetch_one("SELECT COUNT(*) as count FROM version")
        change_count = await db.fetch_one("SELECT COUNT(*) as count FROM change_event")

        return {
            "database": {
                "path": str(settings.db_path),
                "size_bytes": db_size,
                "exists": settings.db_path.exists()
            },
            "cache": {
                "path": str(settings.cache_dir),
                "size_bytes": cache_size,
                "files": cache_files
            },
            "counts": {
                "documents": doc_count["count"] if doc_count else 0,
                "versions": version_count["count"] if version_count else 0,
                "changes": change_count["count"] if change_count else 0
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database status: {str(e)}"
        )
