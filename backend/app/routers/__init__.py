"""
API Routers
"""
from fastapi import APIRouter

from .settings import router as settings_router
from .database import router as db_router
from .sync import router as sync_router
from .search import router as search_router
from .documents import router as docs_router
from .summary import router as summary_router
from .uploads import router as uploads_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(db_router, prefix="/db", tags=["database"])
api_router.include_router(sync_router, prefix="/sync", tags=["sync"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(docs_router, prefix="/docs", tags=["documents"])
api_router.include_router(summary_router, prefix="/summary", tags=["summary"])
api_router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
