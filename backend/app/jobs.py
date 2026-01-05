"""
Job management system for sync operations
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Represents a sync job"""

    def __init__(self, job_id: str, sources: Optional[List[str]] = None):
        self.id = job_id
        self.sources = sources or []
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.progress: Dict[str, Dict[str, Any]] = {}
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "id": self.id,
            "status": self.status.value,
            "sources": self.sources,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "error": self.error
        }


class JobManager:
    """Manages sync jobs"""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.current_job: Optional[Job] = None

    async def create_sync_job(self, sources: Optional[List[str]] = None) -> str:
        """Create a new sync job"""
        job_id = str(uuid.uuid4())
        job = Job(job_id, sources)
        self.jobs[job_id] = job

        # Start the job
        job.task = asyncio.create_task(self._run_sync_job(job))

        return job_id

    async def _run_sync_job(self, job: Job):
        """Run a sync job"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow().isoformat()
            self.current_job = job

            # Import here to avoid circular dependency
            from .connectors import get_enabled_connectors

            # Get connectors
            connectors = await get_enabled_connectors()

            # Filter by requested sources if specified
            if job.sources:
                connectors = [c for c in connectors if c.source_id in job.sources]

            # Run each connector
            for connector in connectors:
                if job.status == JobStatus.CANCELLED:
                    break

                try:
                    # Initialize progress for this source
                    job.progress[connector.source_id] = {
                        "stage": "starting",
                        "items_done": 0,
                        "items_total": 0,
                        "last_error": None
                    }

                    # Run connector sync
                    await connector.sync(
                        progress_callback=lambda stage, done, total:
                        self._update_progress(job, connector.source_id, stage, done, total)
                    )

                    # Mark as complete
                    job.progress[connector.source_id]["stage"] = "completed"

                except Exception as e:
                    # Record error but continue with other sources
                    job.progress[connector.source_id]["last_error"] = str(e)
                    job.progress[connector.source_id]["stage"] = "failed"

            # Job completed
            if job.status != JobStatus.CANCELLED:
                job.status = JobStatus.COMPLETED

            job.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow().isoformat()

        finally:
            if self.current_job and self.current_job.id == job.id:
                self.current_job = None

    def _update_progress(
        self,
        job: Job,
        source_id: str,
        stage: str,
        items_done: int,
        items_total: int
    ):
        """Update job progress"""
        if source_id in job.progress:
            job.progress[source_id].update({
                "stage": stage,
                "items_done": items_done,
                "items_total": items_total
            })

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None

    async def get_latest_job_status(self) -> Optional[Dict[str, Any]]:
        """Get status of the most recent job"""
        if not self.jobs:
            return None

        # Get most recent job
        latest_job = max(self.jobs.values(), key=lambda j: j.created_at)
        return latest_job.to_dict()

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        job = self.jobs.get(job_id)

        if not job:
            return False

        if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            return False

        # Cancel the job
        job.status = JobStatus.CANCELLED

        if job.task and not job.task.done():
            job.task.cancel()

        return True


# Global job manager instance
job_manager = JobManager()
