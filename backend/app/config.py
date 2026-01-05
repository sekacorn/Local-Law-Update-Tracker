"""
Configuration management for LLUT backend
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "LLUT"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    app_data_dir: Path = project_root / "app_data"
    cache_dir: Path = app_data_dir / "cache"
    db_path: Path = app_data_dir / "llut.db"
    settings_file: Path = app_data_dir / "settings.json"

    # Database
    db_url: str = ""

    # Storage mode
    storage_mode: str = "full"  # full | thin | meta

    # Cache retention (days)
    cache_retention_days: int = 30

    # API Keys (loaded from settings.json)
    congress_api_key: Optional[str] = None

    class Config:
        env_prefix = "LLUT_"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set db_url after initialization
        if not self.db_url:
            self.db_url = f"sqlite:///{self.db_path}"

        # Ensure directories exist
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
