"""
Source connectors for LLUT
"""
from typing import List
from .base import Connector
from .federal_register import FederalRegisterConnector
from .congress_gov import CongressGovConnector
from .govinfo import GovInfoConnector
from .scotus import ScotusConnector
from .user_uploads import UserUploadsConnector


async def get_enabled_connectors() -> List[Connector]:
    """Get list of enabled connectors based on settings"""
    from ..settings import settings_manager

    settings = settings_manager.load()
    sources = settings.get("sources", {})

    connectors = []

    # Federal Register
    if sources.get("federal_register", {}).get("enabled", True):
        connectors.append(FederalRegisterConnector())

    # Congress.gov
    if sources.get("congress_gov", {}).get("enabled", True):
        connectors.append(CongressGovConnector())

    # GovInfo
    if sources.get("govinfo", {}).get("enabled", True):
        connectors.append(GovInfoConnector())

    # Supreme Court
    if sources.get("scotus", {}).get("enabled", True):
        connectors.append(ScotusConnector())

    # User Uploads
    if sources.get("user_uploads", {}).get("enabled", True):
        uploads_dir = sources.get("user_uploads", {}).get("directory", "user_uploads")
        connectors.append(UserUploadsConnector(uploads_dir=uploads_dir))

    return connectors
