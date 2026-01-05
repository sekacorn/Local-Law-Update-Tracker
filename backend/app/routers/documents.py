"""
Documents API endpoints
"""
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

from ..db import db
from ..diff_engine import compute_smart_diff

router = APIRouter()


class PinRequest(BaseModel):
    """Pin/unpin request"""
    pin: bool


@router.get("/{doc_id}")
async def get_document(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """
    Get document metadata and version list
    """
    try:
        # Get document
        doc = await db.fetch_one(
            "SELECT * FROM document WHERE id = ?",
            (doc_id,)
        )

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get versions
        versions = await db.fetch_all(
            """
            SELECT id, version_label, published_ts, fetched_ts,
                   content_mode, content_hash
            FROM version
            WHERE document_id = ?
            ORDER BY published_ts DESC
            """,
            (doc_id,)
        )

        return {
            "document": doc,
            "versions": versions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )


@router.post("/{doc_id}/pin")
async def pin_document(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """Pin a document to keep locally"""
    # TODO: Implement pinning logic
    return {
        "success": True,
        "message": "Document pinned",
        "document_id": doc_id
    }


@router.post("/{doc_id}/unpin")
async def unpin_document(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """Unpin a document"""
    # TODO: Implement unpinning logic
    return {
        "success": True,
        "message": "Document unpinned",
        "document_id": doc_id
    }


@router.get("/versions/{version_id}")
async def get_version(
    version_id: str = Path(..., description="Version ID")
) -> Dict[str, Any]:
    """
    Get full version content including outline and text
    """
    try:
        # Get version with document info
        version = await db.fetch_one(
            """
            SELECT
                v.*,
                d.title as document_title,
                d.doc_type,
                d.jurisdiction,
                d.canonical_url,
                s.name as source_name
            FROM version v
            JOIN document d ON d.id = v.document_id
            JOIN source s ON s.id = d.source_id
            WHERE v.id = ?
            """,
            (version_id,)
        )

        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Parse JSON fields
        outline = json.loads(version.get("outline_json", "{}"))
        snippets = json.loads(version.get("snippets_json", "{}"))

        return {
            "version_id": version["id"],
            "document_id": version["document_id"],
            "document_title": version["document_title"],
            "doc_type": version["doc_type"],
            "jurisdiction": version["jurisdiction"],
            "source": version["source_name"],
            "version_label": version["version_label"],
            "published_ts": version["published_ts"],
            "fetched_ts": version["fetched_ts"],
            "content_mode": version["content_mode"],
            "canonical_url": version["canonical_url"],
            "outline": outline,
            "snippets": snippets,
            "normalized_text": version.get("normalized_text"),
            "has_full_text": bool(version.get("normalized_text"))
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get version: {str(e)}"
        )


@router.get("/versions/{version_id}/diff")
async def diff_versions(
    version_id: str = Path(..., description="New version ID"),
    against: str = Query(..., description="Old version ID to compare against")
) -> Dict[str, Any]:
    """
    Compare two versions and return detailed diff
    """
    try:
        # Get both versions
        old_version = await db.fetch_one(
            "SELECT * FROM version WHERE id = ?",
            (against,)
        )

        if not old_version:
            raise HTTPException(status_code=404, detail=f"Old version {against} not found")

        new_version = await db.fetch_one(
            "SELECT * FROM version WHERE id = ?",
            (version_id,)
        )

        if not new_version:
            raise HTTPException(status_code=404, detail=f"New version {version_id} not found")

        # Verify both versions belong to the same document
        if old_version["document_id"] != new_version["document_id"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot compare versions from different documents"
            )

        # Compute diff
        diff_result = compute_smart_diff(dict(old_version), dict(new_version))

        return {
            "success": True,
            "diff": diff_result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute diff: {str(e)}"
        )
