"""
Search API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

from ..search import search_documents

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., description="Search query"),
    source: Optional[str] = Query(None, description="Filter by source ID"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    date_from: Optional[str] = Query(None, description="Filter by date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter by date (ISO format)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Result offset for pagination")
) -> Dict[str, Any]:
    """
    Search documents using full-text search
    Returns ranked results with citations
    """
    try:
        results = await search_documents(
            query=q,
            source_id=source,
            doc_type=doc_type,
            jurisdiction=jurisdiction,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "query": q,
            "total": results["total"],
            "results": results["results"],
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
