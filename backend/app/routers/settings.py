"""
Settings API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from ..settings import settings_manager

router = APIRouter()


class SettingsUpdate(BaseModel):
    """Settings update request"""
    settings: Dict[str, Any]


@router.get("")
async def get_settings() -> Dict[str, Any]:
    """Get current settings"""
    return settings_manager.load()


@router.post("")
async def update_settings(update: SettingsUpdate) -> Dict[str, Any]:
    """Update settings"""
    success = settings_manager.update(update.settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")

    return {
        "success": True,
        "settings": settings_manager.load()
    }


@router.post("/reset")
async def reset_settings() -> Dict[str, Any]:
    """Reset settings to defaults"""
    success = settings_manager.reset()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset settings")

    return {
        "success": True,
        "settings": settings_manager.load()
    }
