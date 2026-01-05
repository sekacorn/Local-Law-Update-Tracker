"""
User settings management
Handles reading/writing settings.json
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .config import settings as app_config


class SettingsManager:
    """Manages user settings stored in settings.json"""

    def __init__(self):
        self.settings_file = app_config.settings_file
        self._cache: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """Load settings from file"""
        if self._cache is not None:
            return self._cache

        if not self.settings_file.exists():
            # Create default settings
            default_settings = self._get_default_settings()
            self.save(default_settings)
            return default_settings

        try:
            with open(self.settings_file, 'r') as f:
                self._cache = json.load(f)
                return self._cache
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self._get_default_settings()

    def save(self, settings_data: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            settings_data["last_updated"] = datetime.utcnow().isoformat()

            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)

            self._cache = settings_data
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        settings_data = self.load()
        return settings_data.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        settings_data = self.load()
        settings_data[key] = value
        return self.save(settings_data)

    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple settings"""
        settings_data = self.load()
        settings_data.update(updates)
        return self.save(settings_data)

    def reset(self) -> bool:
        """Reset to default settings"""
        default_settings = self._get_default_settings()
        return self.save(default_settings)

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings structure"""
        return {
            "version": "1.0",
            "storage_mode": "full",
            "cache_retention_days": 30,
            "sources": {
                "congress_gov": {
                    "enabled": True,
                    "api_key": "",
                    "poll_interval_minutes": 1440
                },
                "govinfo": {
                    "enabled": True,
                    "api_key": "",
                    "poll_interval_minutes": 1440
                },
                "federal_register": {
                    "enabled": True,
                    "api_key": "",
                    "poll_interval_minutes": 1440
                },
                "scotus": {
                    "enabled": True,
                    "api_key": "",
                    "poll_interval_minutes": 1440
                }
            },
            "ui": {
                "theme": "light",
                "default_view": "dashboard"
            },
            "search": {
                "results_per_page": 20,
                "snippet_length": 200
            },
            "last_updated": datetime.utcnow().isoformat()
        }


# Global settings manager instance
settings_manager = SettingsManager()
