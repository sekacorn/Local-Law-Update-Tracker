"""
Uploads API endpoints
Handle user-uploaded documents (PDF, DOCX, TXT, HTML)
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Path, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import hashlib
from datetime import datetime
from pathlib import Path as PathLib

from ..db import db
from ..config import settings
from ..parsers.document_parser import DocumentParser

router = APIRouter()

# Initialize parser
parser = DocumentParser()

# Uploads directory
UPLOADS_DIR = settings.app_data_dir / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class UploadMetadata(BaseModel):
    """Metadata for uploaded document"""
    jurisdiction: Optional[str] = Field(None, description="Federal/State/Local")
    doc_type: Optional[str] = Field(None, description="Lease/Contract/HR/Employment/Other")
    title: Optional[str] = Field(None, description="Document title")
    focus: Optional[str] = Field(None, description="home_buying/job_hr/lease/general")


class UploadResponse(BaseModel):
    """Response from upload endpoint"""
    doc_id: str
    version_id: str
    stats: Dict[str, Any]
    warnings: List[str]


class StorageStats(BaseModel):
    """Storage statistics"""
    total_uploads: int
    total_size_mb: float
    by_type: Dict[str, int]
    storage_mode: str


def _generate_doc_id(filename: str) -> str:
    """Generate unique document ID"""
    timestamp = datetime.utcnow().isoformat()
    content = f"{filename}_{timestamp}"
    hash_obj = hashlib.md5(content.encode())
    return f"upload_{hash_obj.hexdigest()[:12]}"


def _generate_version_id(doc_id: str) -> str:
    """Generate unique version ID"""
    timestamp = datetime.utcnow().isoformat()
    content = f"{doc_id}_{timestamp}"
    hash_obj = hashlib.md5(content.encode())
    return f"v_{hash_obj.hexdigest()[:12]}"


def _save_file(doc_id: str, file_bytes: bytes, filename: str) -> PathLib:
    """Save uploaded file to disk"""
    doc_dir = UPLOADS_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    file_path = doc_dir / filename
    with open(file_path, 'wb') as f:
        f.write(file_bytes)

    return file_path


def _save_normalized_text(doc_id: str, version_id: str, text: str) -> PathLib:
    """Save normalized text to disk"""
    doc_dir = UPLOADS_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    text_file = doc_dir / f"{version_id}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text)

    return text_file


def _save_metadata(doc_id: str, metadata: dict) -> PathLib:
    """Save document metadata to disk"""
    doc_dir = UPLOADS_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    meta_file = doc_dir / "metadata.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    return meta_file


@router.post("", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    metadata: str = Form("{}", description="JSON metadata for the document")
) -> UploadResponse:
    """
    Upload a new document

    Accepts: PDF, DOCX, TXT, HTML
    Max size: 50MB

    Process:
    1. Validate file (format, size)
    2. Parse document (extract text, outline, snippets)
    3. Save to database
    4. Index in FTS
    5. Return doc_id, stats, warnings
    """
    try:
        # Parse metadata
        try:
            meta = json.loads(metadata)
            upload_meta = UploadMetadata(**meta)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid metadata JSON"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metadata: {str(e)}"
            )

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Read file
        file_bytes = await file.read()
        file_size = len(file_bytes)

        # Check file size
        if file_size > parser.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size} bytes). Max size: {parser.MAX_FILE_SIZE} bytes"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        # Detect format
        try:
            format_type = parser.detect_format(file_bytes, file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file format: {str(e)}"
            )

        # Parse document
        try:
            parsed = parser.parse(file_bytes, file.filename, format_hint=format_type)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse document: {str(e)}"
            )

        # Generate IDs
        doc_id = _generate_doc_id(file.filename)
        version_id = _generate_version_id(doc_id)

        # Prepare document title
        doc_title = upload_meta.title or file.filename

        # Save files based on storage mode
        source_path = None
        if settings.storage_mode == "full":
            # Save original file
            file_path = _save_file(doc_id, file_bytes, file.filename)
            source_path = str(file_path.relative_to(settings.app_data_dir))

        # Always save normalized text
        _save_normalized_text(doc_id, version_id, parsed.text)

        # Save metadata
        file_metadata = {
            "upload_date": datetime.utcnow().isoformat(),
            "original_filename": file.filename,
            "mime_type": format_type,
            "jurisdiction": upload_meta.jurisdiction,
            "doc_type": upload_meta.doc_type,
            "focus": upload_meta.focus,
            "file_size": file_size
        }
        _save_metadata(doc_id, file_metadata)

        # Insert into database
        now = datetime.utcnow().isoformat()

        # Ensure user_uploads source exists
        await db.execute("""
            INSERT OR IGNORE INTO source (id, name, base_url, enabled, poll_interval_minutes)
            VALUES ('user_uploads', 'User Uploads', '', 1, 0)
        """)

        # Insert document
        await db.execute(
            """
            INSERT INTO document (
                id, source_id, jurisdiction, doc_type, title,
                identifiers_json, canonical_url, first_seen_ts, last_seen_ts,
                is_user_uploaded, original_filename, upload_mime, source_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                "user_uploads",
                upload_meta.jurisdiction,
                upload_meta.doc_type or format_type,
                doc_title,
                json.dumps({"filename": file.filename}),
                f"local://uploads/{doc_id}",
                now,
                now,
                1,  # is_user_uploaded
                file.filename,
                format_type,
                source_path
            )
        )

        # Prepare outline JSON
        outline_data = []
        for section in parsed.outline:
            outline_data.append({
                "level": section.level,
                "title": section.title,
                "start_char": section.start_char,
                "end_char": section.end_char,
                "page": section.page
            })

        # Insert version
        await db.execute(
            """
            INSERT INTO version (
                id, document_id, version_label, published_ts, fetched_ts,
                content_mode, normalized_text, outline_json, snippets_json,
                parse_warnings_json, page_map_json, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                doc_id,
                "uploaded",
                now,
                now,
                settings.storage_mode,
                parsed.text,
                json.dumps(outline_data) if outline_data else None,
                json.dumps(parsed.snippets) if parsed.snippets else None,
                json.dumps(parsed.warnings) if parsed.warnings else None,
                json.dumps(parsed.page_map) if parsed.page_map else None,
                parsed.confidence_score
            )
        )

        # Index in FTS
        await db.execute(
            """
            INSERT INTO version_fts (version_id, title, text)
            VALUES (?, ?, ?)
            """,
            (version_id, doc_title, parsed.text)
        )

        # Calculate stats
        stats = {
            "file_size": file_size,
            "format": format_type,
            "sections": len(parsed.outline),
            "words": len(parsed.text.split()) if parsed.text else 0,
            "confidence": parsed.confidence_score
        }

        if parsed.page_map:
            stats["pages"] = len(parsed.page_map)

        return UploadResponse(
            doc_id=doc_id,
            version_id=version_id,
            stats=stats,
            warnings=parsed.warnings
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/{doc_id}/version")
async def add_version(
    doc_id: str = Path(..., description="Document ID"),
    file: UploadFile = File(..., description="New version file")
) -> Dict[str, Any]:
    """
    Add a new version to an existing uploaded document
    """
    try:
        # Check if document exists and is user-uploaded
        doc = await db.fetch_one(
            "SELECT * FROM document WHERE id = ? AND is_user_uploaded = 1",
            (doc_id,)
        )

        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found or not a user upload"
            )

        # Read file
        file_bytes = await file.read()
        file_size = len(file_bytes)

        # Validate
        if file_size > parser.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        # Detect and parse
        format_type = parser.detect_format(file_bytes, file.filename or "")
        parsed = parser.parse(file_bytes, file.filename or "", format_hint=format_type)

        # Generate version ID
        version_id = _generate_version_id(doc_id)

        # Save normalized text
        _save_normalized_text(doc_id, version_id, parsed.text)

        # Insert version
        now = datetime.utcnow().isoformat()

        outline_data = []
        for section in parsed.outline:
            outline_data.append({
                "level": section.level,
                "title": section.title,
                "start_char": section.start_char,
                "end_char": section.end_char,
                "page": section.page
            })

        await db.execute(
            """
            INSERT INTO version (
                id, document_id, version_label, published_ts, fetched_ts,
                content_mode, normalized_text, outline_json, snippets_json,
                parse_warnings_json, page_map_json, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                doc_id,
                f"v{now}",
                now,
                now,
                settings.storage_mode,
                parsed.text,
                json.dumps(outline_data) if outline_data else None,
                json.dumps(parsed.snippets) if parsed.snippets else None,
                json.dumps(parsed.warnings) if parsed.warnings else None,
                json.dumps(parsed.page_map) if parsed.page_map else None,
                parsed.confidence_score
            )
        )

        # Update FTS
        await db.execute(
            """
            INSERT INTO version_fts (version_id, title, text)
            VALUES (?, ?, ?)
            """,
            (version_id, doc["title"], parsed.text)
        )

        # Update document last_seen_ts
        await db.execute(
            "UPDATE document SET last_seen_ts = ? WHERE id = ?",
            (now, doc_id)
        )

        return {
            "success": True,
            "version_id": version_id,
            "doc_id": doc_id,
            "confidence": parsed.confidence_score,
            "warnings": parsed.warnings
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add version: {str(e)}"
        )


@router.get("/recent")
async def get_recent_uploads(
    limit: int = Query(20, ge=1, le=100, description="Max number of results")
) -> Dict[str, Any]:
    """
    Get recently uploaded documents
    """
    try:
        uploads = await db.fetch_all(
            """
            SELECT
                d.id,
                d.title,
                d.doc_type,
                d.jurisdiction,
                d.original_filename,
                d.upload_mime,
                d.first_seen_ts,
                d.last_seen_ts,
                (SELECT COUNT(*) FROM version WHERE document_id = d.id) as version_count,
                (SELECT confidence_score FROM version WHERE document_id = d.id ORDER BY fetched_ts DESC LIMIT 1) as latest_confidence,
                (SELECT id FROM version WHERE document_id = d.id ORDER BY fetched_ts DESC LIMIT 1) as latest_version_id
            FROM document d
            WHERE d.is_user_uploaded = 1
            ORDER BY d.last_seen_ts DESC
            LIMIT ?
            """,
            (limit,)
        )

        return {
            "uploads": uploads,
            "count": len(uploads)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent uploads: {str(e)}"
        )


@router.get("/list")
async def list_uploads(
    limit: int = Query(100, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Offset for pagination")
) -> Dict[str, Any]:
    """
    Get list of all uploaded documents
    Returns document metadata sorted by upload date (newest first)
    """
    try:
        # Get all uploaded documents
        uploads = await db.fetch_all(
            """
            SELECT
                d.id,
                d.title,
                d.doc_type,
                d.jurisdiction,
                d.original_filename,
                d.upload_mime,
                d.first_seen_ts,
                COUNT(v.id) as version_count
            FROM document d
            LEFT JOIN version v ON v.document_id = d.id
            WHERE d.is_user_uploaded = 1
            GROUP BY d.id
            ORDER BY d.first_seen_ts DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )

        # Get total count
        total = await db.fetch_one(
            "SELECT COUNT(*) as count FROM document WHERE is_user_uploaded = 1"
        )

        return {
            "success": True,
            "total": total["count"] if total else 0,
            "limit": limit,
            "offset": offset,
            "documents": [dict(doc) for doc in uploads]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list uploads: {str(e)}"
        )


@router.get("/{doc_id}")
async def get_upload(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """
    Get detailed information about an uploaded document
    """
    try:
        # Get document
        doc = await db.fetch_one(
            "SELECT * FROM document WHERE id = ? AND is_user_uploaded = 1",
            (doc_id,)
        )

        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Upload not found"
            )

        # Get versions
        versions = await db.fetch_all(
            """
            SELECT
                id, version_label, published_ts, fetched_ts,
                content_mode, confidence_score,
                parse_warnings_json, page_map_json
            FROM version
            WHERE document_id = ?
            ORDER BY fetched_ts DESC
            """,
            (doc_id,)
        )

        # Parse warnings for each version
        for v in versions:
            if v.get("parse_warnings_json"):
                v["warnings"] = json.loads(v["parse_warnings_json"])
            else:
                v["warnings"] = []

        # Check if pinned
        is_pinned = await db.is_pinned(doc_id)

        return {
            "document": doc,
            "versions": versions,
            "is_pinned": is_pinned,
            "version_count": len(versions)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get upload: {str(e)}"
        )


@router.delete("/{doc_id}")
async def delete_upload(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """
    Delete an uploaded document and all its versions
    """
    try:
        # Check if document exists and is user-uploaded
        doc = await db.fetch_one(
            "SELECT * FROM document WHERE id = ? AND is_user_uploaded = 1",
            (doc_id,)
        )

        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Upload not found"
            )

        # Delete from FTS
        await db.execute(
            """
            DELETE FROM version_fts
            WHERE version_id IN (
                SELECT id FROM version WHERE document_id = ?
            )
            """,
            (doc_id,)
        )

        # Delete versions
        await db.execute(
            "DELETE FROM version WHERE document_id = ?",
            (doc_id,)
        )

        # Delete from pinned if pinned
        await db.execute(
            "DELETE FROM pinned_document WHERE document_id = ?",
            (doc_id,)
        )

        # Delete document
        await db.execute(
            "DELETE FROM document WHERE id = ?",
            (doc_id,)
        )

        # Delete files from disk
        doc_dir = UPLOADS_DIR / doc_id
        if doc_dir.exists():
            import shutil
            shutil.rmtree(doc_dir)

        return {
            "success": True,
            "message": "Document deleted",
            "doc_id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete upload: {str(e)}"
        )


@router.post("/{doc_id}/pin")
async def pin_upload(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """
    Pin an uploaded document to keep it permanently
    """
    try:
        # Check if document exists and is user-uploaded
        doc = await db.fetch_one(
            "SELECT id FROM document WHERE id = ? AND is_user_uploaded = 1",
            (doc_id,)
        )

        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Upload not found"
            )

        # Pin the document
        success = await db.pin_document(doc_id)

        if not success:
            # Check if already pinned
            is_pinned = await db.is_pinned(doc_id)
            if is_pinned:
                return {
                    "success": True,
                    "message": "Document already pinned",
                    "doc_id": doc_id
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to pin document"
                )

        return {
            "success": True,
            "message": "Document pinned",
            "doc_id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pin upload: {str(e)}"
        )


@router.delete("/{doc_id}/pin")
async def unpin_upload(
    doc_id: str = Path(..., description="Document ID")
) -> Dict[str, Any]:
    """
    Unpin an uploaded document
    """
    try:
        # Unpin the document
        success = await db.unpin_document(doc_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not pinned or not found"
            )

        return {
            "success": True,
            "message": "Document unpinned",
            "doc_id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unpin upload: {str(e)}"
        )


@router.get("/storage/stats", response_model=StorageStats)
async def get_storage_stats() -> StorageStats:
    """
    Get storage statistics for uploaded documents
    """
    try:
        # Count total uploads
        result = await db.fetch_one(
            "SELECT COUNT(*) as count FROM document WHERE is_user_uploaded = 1"
        )
        total_uploads = result["count"] if result else 0

        # Get uploads by type
        type_counts = await db.fetch_all(
            """
            SELECT upload_mime, COUNT(*) as count
            FROM document
            WHERE is_user_uploaded = 1
            GROUP BY upload_mime
            """
        )

        by_type = {row["upload_mime"]: row["count"] for row in type_counts if row["upload_mime"]}

        # Calculate total size
        total_size = 0
        if UPLOADS_DIR.exists():
            for item in UPLOADS_DIR.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size

        total_size_mb = total_size / (1024 * 1024)

        return StorageStats(
            total_uploads=total_uploads,
            total_size_mb=round(total_size_mb, 2),
            by_type=by_type,
            storage_mode=settings.storage_mode
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.delete("/storage/clear")
async def clear_all_uploads(confirm: bool = Query(..., description="Must be true to confirm")) -> Dict[str, Any]:
    """
    Clear all uploaded documents from database and storage
    WARNING: This deletes all user uploads permanently
    """
    import shutil

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm deletion by setting confirm=true"
        )

    try:
        # Get all upload IDs
        uploads = await db.fetch_all(
            "SELECT id FROM document WHERE is_user_uploaded = 1"
        )

        deleted_count = len(uploads)

        # Delete from database (cascade will delete versions, FTS entries)
        await db.execute(
            "DELETE FROM document WHERE is_user_uploaded = 1"
        )

        # Delete upload files from disk
        if UPLOADS_DIR.exists():
            shutil.rmtree(UPLOADS_DIR)
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "message": f"Deleted {deleted_count} uploaded documents",
            "deleted_count": deleted_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear uploads: {str(e)}"
        )
