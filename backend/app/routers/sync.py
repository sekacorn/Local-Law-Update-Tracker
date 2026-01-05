"""
Sync API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from ..jobs import job_manager

router = APIRouter()


class SyncRequest(BaseModel):
    """Sync request"""
    sources: Optional[List[str]] = None  # Specific sources or all if None


@router.post("/run")
async def run_sync(request: SyncRequest) -> Dict[str, Any]:
    """
    Start a sync job to retrieve new data from sources
    """
    try:
        job_id = await job_manager.create_sync_job(request.sources)

        return {
            "success": True,
            "job_id": job_id,
            "message": "Sync job started"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start sync: {str(e)}"
        )


@router.get("/status")
async def get_sync_status(job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get sync job status
    If job_id is None, returns status of the most recent job
    """
    try:
        if job_id:
            status = await job_manager.get_job_status(job_id)
        else:
            status = await job_manager.get_latest_job_status()

        if not status:
            return {
                "status": "none",
                "message": "No sync jobs found"
            }

        return status

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/cancel")
async def cancel_sync(job_id: str) -> Dict[str, Any]:
    """Cancel a running sync job"""
    try:
        success = await job_manager.cancel_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail="Job not found or already completed")

        return {
            "success": True,
            "message": "Sync job cancelled"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel sync: {str(e)}"
        )
