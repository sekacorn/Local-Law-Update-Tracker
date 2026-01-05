"""
Search functionality using SQLite FTS5
"""
from typing import Dict, Any, List, Optional

from .db import db


async def search_documents(
    query: str,
    source_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search documents using FTS5 full-text search
    """

    # Build the FTS query
    # Use basic FTS5 match syntax
    fts_query = query

    # Build SQL with filters
    sql_parts = [
        """
        SELECT
            v.id as version_id,
            v.document_id,
            d.title,
            d.doc_type,
            d.jurisdiction,
            d.canonical_url,
            d.is_user_uploaded,
            d.original_filename,
            d.upload_mime,
            s.name as source_name,
            v.version_label,
            v.published_ts,
            v.confidence_score,
            snippet(version_fts, 2, '<mark>', '</mark>', '...', 32) as snippet,
            rank
        FROM version_fts
        JOIN version v ON v.id = version_fts.version_id
        JOIN document d ON d.id = v.document_id
        JOIN source s ON s.id = d.source_id
        WHERE version_fts MATCH ?
        """
    ]

    params = [fts_query]

    # Add filters
    if source_id:
        sql_parts.append("AND d.source_id = ?")
        params.append(source_id)

    if doc_type:
        sql_parts.append("AND d.doc_type = ?")
        params.append(doc_type)

    if jurisdiction:
        sql_parts.append("AND d.jurisdiction = ?")
        params.append(jurisdiction)

    if date_from:
        sql_parts.append("AND v.published_ts >= ?")
        params.append(date_from)

    if date_to:
        sql_parts.append("AND v.published_ts <= ?")
        params.append(date_to)

    # Order by rank (relevance)
    sql_parts.append("ORDER BY rank")

    # Add pagination
    sql_parts.append("LIMIT ? OFFSET ?")
    params.extend([limit, offset])

    sql = "\n".join(sql_parts)

    try:
        # Execute search
        results = await db.fetch_all(sql, tuple(params))

        # Get total count (without pagination)
        count_sql_parts = [
            """
            SELECT COUNT(*) as total
            FROM version_fts
            JOIN version v ON v.id = version_fts.version_id
            JOIN document d ON d.id = v.document_id
            WHERE version_fts MATCH ?
            """
        ]

        count_params = [fts_query]

        if source_id:
            count_sql_parts.append("AND d.source_id = ?")
            count_params.append(source_id)

        if doc_type:
            count_sql_parts.append("AND d.doc_type = ?")
            count_params.append(doc_type)

        if jurisdiction:
            count_sql_parts.append("AND d.jurisdiction = ?")
            count_params.append(jurisdiction)

        if date_from:
            count_sql_parts.append("AND v.published_ts >= ?")
            count_params.append(date_from)

        if date_to:
            count_sql_parts.append("AND v.published_ts <= ?")
            count_params.append(date_to)

        count_sql = "\n".join(count_sql_parts)
        count_result = await db.fetch_one(count_sql, tuple(count_params))
        total = count_result["total"] if count_result else 0

        return {
            "total": total,
            "results": results
        }

    except Exception as e:
        # If FTS search fails, return empty results
        print(f"Search error: {e}")
        return {
            "total": 0,
            "results": []
        }


async def get_recent_changes(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent change events"""
    sql = """
        SELECT
            ce.*,
            d.title,
            d.doc_type,
            s.name as source_name
        FROM change_event ce
        JOIN document d ON d.id = ce.document_id
        JOIN source s ON s.id = d.source_id
        ORDER BY ce.created_ts DESC
        LIMIT ?
    """

    return await db.fetch_all(sql, (limit,))
