"""
Plain-language summary API endpoints
"""
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from ..db import db
from ..summary_engine import generate_summary, explain_section
from ..analysis.citations import citation_extractor

router = APIRouter()


class SummarizeRequest(BaseModel):
    """Request for document summary"""
    version_id: str
    focus: str = "general"  # general, home_buying, job_hr, lease, contractor, privacy
    max_length: str = "medium"  # short, medium, long


class ExplainRequest(BaseModel):
    """Request for section explanation"""
    version_id: str
    selection: str  # Text selection or heading to explain
    question: Optional[str] = None  # Optional specific question


@router.post("/summarize")
async def summarize_document(request: SummarizeRequest) -> Dict[str, Any]:
    """
    Generate a plain-language summary of a document
    Helps non-lawyers understand complex legal text

    Features:
    - Plain-language explanations
    - Risk and liability warnings
    - Questions to ask a professional
    - Citations to source text (with grounding)

    For user uploads, citations include:
    - Page numbers (for PDFs)
    - Section headings (for all documents)
    - Character positions for precise references
    """
    try:
        # Get version with document info
        version = await db.fetch_one(
            """
            SELECT
                v.*,
                d.id as doc_id,
                d.title,
                d.doc_type,
                d.is_user_uploaded,
                d.upload_mime
            FROM version v
            JOIN document d ON d.id = v.document_id
            WHERE v.id = ?
            """,
            (request.version_id,)
        )

        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        # Check if we have text to summarize
        text = version.get("normalized_text") or version.get("snippets_json", "")

        if not text or len(text) < 10:
            raise HTTPException(
                status_code=400,
                detail="Document does not have sufficient text for summarization. "
                       "Try fetching the full version first."
            )

        # For user uploads, extract citations with verification and check grounding confidence
        citations = []
        citation_confidence = 1.0  # Default for government docs
        confidence_reasons = []

        if version.get("is_user_uploaded"):
            citations, citation_confidence = citation_extractor.extract_upload_citations(
                version_data=dict(version),
                doc_id=version["doc_id"],
                version_id=request.version_id
            )

            # Persist citations to database
            if citations:
                import uuid
                citation_dicts = []
                for citation in citations:
                    citation_id = str(uuid.uuid4())
                    citation_dicts.append({
                        "id": citation_id,
                        "document_id": citation.doc_id,
                        "version_id": citation.version_id,
                        "quote_text": citation.text,
                        "start_char": citation.location.char_start,
                        "end_char": citation.location.char_end,
                        "verified": citation.verified,
                        "match_method": citation.match_method,
                        "confidence": citation.confidence,
                        "heading": citation.location.section,
                        "page_number": citation.location.page
                    })

                # Save citations to database
                saved_count = await db.save_citations_batch(citation_dicts)
                print(f"Saved {saved_count} citation spans to database for version {request.version_id}")

            # Collect confidence reasons from citations
            if citations:
                # Aggregate unique reasons from all citations
                all_reasons = set()
                for citation in citations:
                    all_reasons.update(citation.confidence_reasons)
                confidence_reasons = list(all_reasons)

            # Check if we can reliably cite this document
            if not citation_extractor.can_cite(citation_confidence):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "insufficient_support",
                        "message": "Cannot generate summary with sufficient citation confidence. "
                                   "The document structure may be too complex or poorly formatted.",
                        "confidence": citation_confidence,
                        "threshold": citation_extractor.MIN_CONFIDENCE_THRESHOLD,
                        "reasons": confidence_reasons
                    }
                )

        # Generate summary
        summary = generate_summary(
            text=text,
            title=version["title"],
            doc_type=version["doc_type"],
            focus=request.focus,
            max_length=request.max_length
        )

        # Add citation information to summary with verification details
        summary["citations"] = [c.to_dict() for c in citations]
        summary["citation_confidence"] = citation_confidence
        summary["grounding"] = {
            "can_cite": citation_extractor.can_cite(citation_confidence),
            "confidence": citation_confidence,
            "confidence_reasons": confidence_reasons,
            "citation_count": len(citations),
            "verified_count": sum(1 for c in citations if c.verified),
            "exact_matches": sum(1 for c in citations if c.match_method == "exact"),
            "fuzzy_matches": sum(1 for c in citations if c.match_method == "fuzzy")
        }

        # Load upload settings for user uploads
        upload_settings = None
        if version.get("is_user_uploaded"):
            try:
                import json
                from pathlib import Path
                from ..config import settings as app_settings

                doc_id = version["doc_id"]
                meta_file = app_settings.app_data_dir / "uploads" / doc_id / "metadata.json"
                if meta_file.exists():
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    upload_settings = {
                        "doc_type": metadata.get("doc_type"),
                        "focus": metadata.get("focus"),
                        "jurisdiction": metadata.get("jurisdiction"),
                        "upload_date": metadata.get("upload_date")
                    }
            except Exception as e:
                # Log but don't fail the request
                print(f"Warning: Could not load upload settings: {e}")

        return {
            "success": True,
            "version_id": request.version_id,
            "document_title": version["title"],
            "doc_id": version["doc_id"],
            "focus": request.focus,
            "is_user_upload": bool(version.get("is_user_uploaded")),
            "upload_settings": upload_settings,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/explain")
async def explain_text(request: ExplainRequest) -> Dict[str, Any]:
    """
    Explain a specific section of text in plain language
    Useful for understanding specific clauses or passages

    Features:
    - Plain-language explanations
    - Legal term definitions
    - Citations to context (with grounding for uploads)
    - NOT legal advice disclaimer
    """
    try:
        # Get version with document info
        version = await db.fetch_one(
            """
            SELECT
                v.*,
                d.id as doc_id,
                d.is_user_uploaded,
                d.upload_mime
            FROM version v
            JOIN document d ON d.id = v.document_id
            WHERE v.id = ?
            """,
            (request.version_id,)
        )

        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        text = version.get("normalized_text")

        if not text:
            raise HTTPException(
                status_code=400,
                detail="Document does not have full text available. "
                       "Try fetching the full version first."
            )

        # For user uploads, check citation confidence
        citation_confidence = 1.0

        if version.get("is_user_uploaded"):
            # Find the selection in the text and create citation
            citation_spans = citation_extractor.find_citation_spans(
                text=text,
                query=request.selection
            )

            if not citation_spans:
                raise HTTPException(
                    status_code=400,
                    detail="Selected text not found in document. "
                           "Please ensure you copied the exact text."
                )

            # Calculate confidence for this specific citation
            # Use stored confidence or calculate new one
            stored_confidence = version.get("confidence_score", 0.8)
            citation_confidence = stored_confidence

            if not citation_extractor.can_cite(citation_confidence):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "insufficient_support",
                        "message": "Cannot provide grounded explanation with sufficient confidence. "
                                   "The document structure may be unclear.",
                        "confidence": citation_confidence,
                        "threshold": citation_extractor.MIN_CONFIDENCE_THRESHOLD
                    }
                )

        # Generate explanation
        explanation = explain_section(
            text=text,
            selection=request.selection,
            question=request.question
        )

        if "error" in explanation:
            raise HTTPException(status_code=400, detail=explanation["error"])

        # Add grounding information for uploads
        if version.get("is_user_uploaded"):
            explanation["grounding"] = {
                "can_cite": citation_extractor.can_cite(citation_confidence),
                "confidence": citation_confidence
            }

        return {
            "success": True,
            "version_id": request.version_id,
            "doc_id": version["doc_id"],
            "is_user_upload": bool(version.get("is_user_uploaded")),
            "explanation": explanation
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to explain text: {str(e)}"
        )
