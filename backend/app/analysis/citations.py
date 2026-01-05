"""
Citation extraction for user-uploaded documents
Supports both PDF (page-based) and non-PDF (section-based) citations
"""
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class CitationLocation:
    """Location information for a citation"""
    # For all documents
    section: Optional[str] = None  # Section heading
    char_start: Optional[int] = None  # Character offset start
    char_end: Optional[int] = None  # Character offset end

    # For PDFs only
    page: Optional[int] = None  # Page number (1-indexed)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Citation:
    """Citation to source text in a document"""
    doc_id: str
    version_id: str
    citation_type: str  # "user_upload" or "government_doc"
    text: str  # The cited text
    location: CitationLocation
    confidence: float  # 0.0-1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "doc_id": self.doc_id,
            "version_id": self.version_id,
            "type": self.citation_type,
            "text": self.text,
            "location": self.location.to_dict(),
            "confidence": self.confidence
        }


class CitationExtractor:
    """Extract citations from uploaded documents"""

    MIN_CITATION_LENGTH = 10  # Minimum characters for a valid citation
    MAX_CITATION_LENGTH = 500  # Maximum characters for a single citation
    MIN_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for grounding

    def __init__(self):
        pass

    def extract_citations(
        self,
        text: str,
        outline: List[Dict[str, Any]],
        page_map: Optional[Dict[str, Any]],
        doc_id: str,
        version_id: str,
        is_pdf: bool = False
    ) -> Tuple[List[Citation], float]:
        """
        Extract citations from a document

        Args:
            text: Full document text
            outline: Document outline (sections)
            page_map: Page map for PDFs (page -> char positions)
            doc_id: Document ID
            version_id: Version ID
            is_pdf: Whether this is a PDF document

        Returns:
            Tuple of (citations list, overall confidence score)
        """
        citations = []

        if not text or len(text) < self.MIN_CITATION_LENGTH:
            return citations, 0.0

        # Extract citations for each section in the outline
        for section in outline:
            section_citations = self._extract_from_section(
                text=text,
                section=section,
                page_map=page_map,
                doc_id=doc_id,
                version_id=version_id,
                is_pdf=is_pdf
            )
            citations.extend(section_citations)

        # If no outline, create citations from whole document
        if not outline:
            full_doc_citation = self._create_citation(
                text=text[:self.MAX_CITATION_LENGTH],
                section_title=None,
                char_start=0,
                char_end=min(len(text), self.MAX_CITATION_LENGTH),
                page_num=None,
                doc_id=doc_id,
                version_id=version_id
            )
            citations.append(full_doc_citation)

        # Calculate overall confidence
        overall_confidence = self._calculate_confidence(
            text=text,
            outline=outline,
            page_map=page_map,
            citations=citations
        )

        return citations, overall_confidence

    def _extract_from_section(
        self,
        text: str,
        section: Dict[str, Any],
        page_map: Optional[Dict[str, Any]],
        doc_id: str,
        version_id: str,
        is_pdf: bool
    ) -> List[Citation]:
        """Extract citations from a single section"""
        citations = []

        section_title = section.get("title", "")
        start_char = section.get("start_char", 0)
        end_char = section.get("end_char", len(text))
        page_num = section.get("page")

        # Extract the section text
        section_text = text[start_char:end_char]

        if len(section_text) < self.MIN_CITATION_LENGTH:
            return citations

        # For long sections, break into smaller citation chunks
        if len(section_text) > self.MAX_CITATION_LENGTH:
            # Extract first part as citation
            citation_text = section_text[:self.MAX_CITATION_LENGTH]
            citation = self._create_citation(
                text=citation_text,
                section_title=section_title,
                char_start=start_char,
                char_end=start_char + self.MAX_CITATION_LENGTH,
                page_num=page_num,
                doc_id=doc_id,
                version_id=version_id
            )
            citations.append(citation)
        else:
            # Entire section as citation
            citation = self._create_citation(
                text=section_text,
                section_title=section_title,
                char_start=start_char,
                char_end=end_char,
                page_num=page_num,
                doc_id=doc_id,
                version_id=version_id
            )
            citations.append(citation)

        return citations

    def _create_citation(
        self,
        text: str,
        section_title: Optional[str],
        char_start: int,
        char_end: int,
        page_num: Optional[int],
        doc_id: str,
        version_id: str
    ) -> Citation:
        """Create a citation object"""
        location = CitationLocation(
            section=section_title,
            char_start=char_start,
            char_end=char_end,
            page=page_num
        )

        # Calculate confidence based on available metadata
        confidence = self._calculate_citation_confidence(
            text=text,
            section_title=section_title,
            page_num=page_num
        )

        return Citation(
            doc_id=doc_id,
            version_id=version_id,
            citation_type="user_upload",
            text=text.strip(),
            location=location,
            confidence=confidence
        )

    def _calculate_citation_confidence(
        self,
        text: str,
        section_title: Optional[str],
        page_num: Optional[int]
    ) -> float:
        """
        Calculate confidence score for a citation

        Confidence is based on:
        - Presence of section heading: +0.3
        - Presence of page number: +0.2
        - Text length adequacy: +0.5 (if >= MIN_CITATION_LENGTH)
        """
        confidence = 0.0

        # Text length check
        if len(text) >= self.MIN_CITATION_LENGTH:
            confidence += 0.5
        else:
            confidence += 0.2  # Partial credit

        # Section heading available
        if section_title and len(section_title) > 0:
            confidence += 0.3

        # Page number available (for PDFs)
        if page_num is not None:
            confidence += 0.2

        return min(confidence, 1.0)

    def _calculate_confidence(
        self,
        text: str,
        outline: List[Dict[str, Any]],
        page_map: Optional[Dict[str, Any]],
        citations: List[Citation]
    ) -> float:
        """
        Calculate overall confidence for citation extraction

        Factors:
        - Number of citations extracted
        - Coverage of document text
        - Presence of structured outline
        - Presence of page map (for PDFs)
        """
        if not text:
            return 0.0

        confidence = 0.0

        # Base confidence from text availability
        if len(text) > 0:
            confidence += 0.3

        # Outline structure adds confidence
        if outline and len(outline) > 0:
            confidence += 0.3
        else:
            confidence += 0.1  # Still some confidence without outline

        # Page map adds confidence (for PDFs)
        if page_map and len(page_map) > 0:
            confidence += 0.2

        # Citations extracted successfully
        if citations and len(citations) > 0:
            confidence += 0.2

        return min(confidence, 1.0)

    def can_cite(self, confidence: float) -> bool:
        """
        Check if citation confidence is sufficient for grounding

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            True if confidence meets threshold
        """
        return confidence >= self.MIN_CONFIDENCE_THRESHOLD

    def find_citation_spans(
        self,
        text: str,
        query: str,
        section_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find specific text spans in the document that match a query
        Useful for highlighting citations in the UI

        Args:
            text: Full document text
            query: Text to find
            section_title: Optional section to search within

        Returns:
            List of matching spans with positions
        """
        spans = []
        query_lower = query.lower()
        text_lower = text.lower()

        # Find all occurrences
        start = 0
        while True:
            pos = text_lower.find(query_lower, start)
            if pos == -1:
                break

            # Extract context around the match
            context_start = max(0, pos - 100)
            context_end = min(len(text), pos + len(query) + 100)
            context = text[context_start:context_end]

            span = {
                "text": text[pos:pos + len(query)],
                "char_start": pos,
                "char_end": pos + len(query),
                "context": context
            }

            spans.append(span)
            start = pos + len(query)

        return spans

    def extract_upload_citations(
        self,
        version_data: Dict[str, Any],
        doc_id: str,
        version_id: str
    ) -> Tuple[List[Citation], float]:
        """
        Extract citations from a user upload version

        Args:
            version_data: Version row from database
            doc_id: Document ID
            version_id: Version ID

        Returns:
            Tuple of (citations, confidence)
        """
        text = version_data.get("normalized_text", "")

        # Parse outline
        outline_json = version_data.get("outline_json")
        outline = json.loads(outline_json) if outline_json else []

        # Parse page map
        page_map_json = version_data.get("page_map_json")
        page_map = json.loads(page_map_json) if page_map_json else None

        # Check if PDF
        upload_mime = version_data.get("upload_mime", "")
        is_pdf = upload_mime.lower() == "pdf"

        # Extract citations
        return self.extract_citations(
            text=text,
            outline=outline,
            page_map=page_map,
            doc_id=doc_id,
            version_id=version_id,
            is_pdf=is_pdf
        )


# Global instance
citation_extractor = CitationExtractor()
