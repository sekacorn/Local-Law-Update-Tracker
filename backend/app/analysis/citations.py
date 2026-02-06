"""
Citation extraction for user-uploaded documents
Supports both PDF (page-based) and non-PDF (section-based) citations
Includes verification, fuzzy matching, and deterministic confidence scoring
"""
import json
import re
from dataclasses import dataclass, asdict, field
from difflib import SequenceMatcher
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
    """Citation to source text in a document with verification"""
    doc_id: str
    version_id: str
    citation_type: str  # "user_upload" or "government_doc"
    text: str  # The cited text (quote_text)
    location: CitationLocation
    confidence: float  # 0.0-1.0
    verified: bool = False  # True if citation was verified in source text
    match_method: str = "exact"  # "exact" or "fuzzy"
    confidence_reasons: List[str] = field(default_factory=list)  # Explainable reasons for confidence score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "doc_id": self.doc_id,
            "version_id": self.version_id,
            "type": self.citation_type,
            "text": self.text,
            "quote_text": self.text,  # Alias for clarity
            "location": self.location.to_dict(),
            "confidence": self.confidence,
            "verified": self.verified,
            "match_method": self.match_method,
            "confidence_reasons": self.confidence_reasons
        }


class CitationExtractor:
    """Extract citations from uploaded documents with verification and fuzzy matching"""

    MIN_CITATION_LENGTH = 10  # Minimum characters for a valid citation
    MAX_CITATION_LENGTH = 500  # Maximum characters for a single citation
    MIN_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for grounding
    FUZZY_MATCH_THRESHOLD = 0.85  # Minimum similarity ratio for fuzzy matches (0.0-1.0)

    # Parser reliability weights for confidence scoring
    PARSER_WEIGHTS = {
        "text/plain": 1.0,  # TXT is most reliable
        "text/html": 0.95,  # HTML is very reliable after cleaning
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 0.9,  # DOCX is good
        "application/pdf": 0.75,  # PDF can have extraction issues
        "unknown": 0.5  # Unknown format
    }

    def __init__(self):
        pass

    def verify_citation_span(
        self,
        quote_text: str,
        full_text: str,
        claimed_start: int,
        claimed_end: int
    ) -> Tuple[bool, str, int, int]:
        """
        Verify that a citation span actually exists in the text

        Args:
            quote_text: The quoted text to verify
            full_text: The full document text
            claimed_start: Claimed start position
            claimed_end: Claimed end position

        Returns:
            Tuple of (verified, match_method, actual_start, actual_end)
        """
        # Try exact match at claimed position first
        if claimed_start >= 0 and claimed_end <= len(full_text):
            actual_text = full_text[claimed_start:claimed_end]
            if actual_text == quote_text:
                return True, "exact", claimed_start, claimed_end

        # Try exact match anywhere in the document
        quote_lower = quote_text.lower().strip()
        text_lower = full_text.lower()

        exact_pos = text_lower.find(quote_lower)
        if exact_pos != -1:
            return True, "exact", exact_pos, exact_pos + len(quote_text)

        # Fallback to fuzzy matching
        return self._fuzzy_match_span(quote_text, full_text, claimed_start, claimed_end)

    def _fuzzy_match_span(
        self,
        quote_text: str,
        full_text: str,
        claimed_start: int,
        claimed_end: int
    ) -> Tuple[bool, str, int, int]:
        """
        Attempt fuzzy matching to find the citation span

        Uses sliding window approach to find best match
        """
        quote_len = len(quote_text)
        best_ratio = 0.0
        best_start = claimed_start
        best_end = claimed_end

        # Search window around claimed position (±200 chars)
        search_start = max(0, claimed_start - 200)
        search_end = min(len(full_text), claimed_end + 200)

        # Sliding window search
        for i in range(search_start, search_end - quote_len + 1):
            window = full_text[i:i + quote_len]
            ratio = SequenceMatcher(None, quote_text.lower(), window.lower()).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_start = i
                best_end = i + quote_len

        # Check if fuzzy match meets threshold
        if best_ratio >= self.FUZZY_MATCH_THRESHOLD:
            return True, "fuzzy", best_start, best_end

        # No match found
        return False, "none", claimed_start, claimed_end

    def extract_citations(
        self,
        text: str,
        outline: List[Dict[str, Any]],
        page_map: Optional[Dict[str, Any]],
        doc_id: str,
        version_id: str,
        is_pdf: bool = False,
        mime_type: str = "unknown"
    ) -> Tuple[List[Citation], float]:
        """
        Extract citations from a document with verification

        Args:
            text: Full document text
            outline: Document outline (sections)
            page_map: Page map for PDFs (page -> char positions)
            doc_id: Document ID
            version_id: Version ID
            is_pdf: Whether this is a PDF document
            mime_type: Document MIME type for parser reliability scoring

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
                is_pdf=is_pdf,
                mime_type=mime_type
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
                version_id=version_id,
                full_text=text,
                mime_type=mime_type
            )
            citations.append(full_doc_citation)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            text=text,
            outline=outline,
            page_map=page_map,
            citations=citations,
            mime_type=mime_type
        )

        return citations, overall_confidence

    def _extract_from_section(
        self,
        text: str,
        section: Dict[str, Any],
        page_map: Optional[Dict[str, Any]],
        doc_id: str,
        version_id: str,
        is_pdf: bool,
        mime_type: str = "unknown"
    ) -> List[Citation]:
        """Extract citations from a single section with verification"""
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
                version_id=version_id,
                full_text=text,
                mime_type=mime_type
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
                version_id=version_id,
                full_text=text,
                mime_type=mime_type
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
        version_id: str,
        full_text: str = "",
        mime_type: str = "unknown"
    ) -> Citation:
        """Create a citation object with verification"""
        # Verify the citation span if we have full text
        verified = False
        match_method = "exact"
        actual_start = char_start
        actual_end = char_end

        if full_text:
            verified, match_method, actual_start, actual_end = self.verify_citation_span(
                quote_text=text.strip(),
                full_text=full_text,
                claimed_start=char_start,
                claimed_end=char_end
            )

        location = CitationLocation(
            section=section_title,
            char_start=actual_start,
            char_end=actual_end,
            page=page_num
        )

        # Calculate confidence with explainable reasons
        confidence, reasons = self._calculate_citation_confidence(
            text=text,
            section_title=section_title,
            page_num=page_num,
            verified=verified,
            match_method=match_method,
            mime_type=mime_type
        )

        return Citation(
            doc_id=doc_id,
            version_id=version_id,
            citation_type="user_upload",
            text=text.strip(),
            location=location,
            confidence=confidence,
            verified=verified,
            match_method=match_method,
            confidence_reasons=reasons
        )

    def _calculate_citation_confidence(
        self,
        text: str,
        section_title: Optional[str],
        page_num: Optional[int],
        verified: bool = False,
        match_method: str = "exact",
        mime_type: str = "unknown"
    ) -> Tuple[float, List[str]]:
        """
        Calculate deterministic confidence score for a citation with explainable reasons

        Factors:
        a) Citation verification (verified=True): +0.4, verified=False: -0.3
        b) Match method (exact): +0.2, fuzzy: +0.1, none: -0.2
        c) Parser reliability (based on MIME type): 0.5-1.0 weight
        d) Structure metadata (section heading, page number): +0.1 each
        e) Text length adequacy: +0.1

        Returns:
            Tuple of (confidence_score, reasons_list)
        """
        confidence = 0.0
        reasons = []

        # Factor a) Verification status (most important)
        if verified:
            confidence += 0.4
            reasons.append("Citation verified in source text")
        else:
            confidence -= 0.3
            reasons.append("WARNING: Citation could not be verified in source text")

        # Factor b) Match method
        if match_method == "exact":
            confidence += 0.2
            reasons.append("Exact match found at claimed position")
        elif match_method == "fuzzy":
            confidence += 0.1
            reasons.append(f"Fuzzy match found (similarity >= {self.FUZZY_MATCH_THRESHOLD})")
        else:
            confidence -= 0.2
            reasons.append("WARNING: No match found for citation")

        # Factor c) Parser reliability
        parser_weight = self.PARSER_WEIGHTS.get(mime_type, self.PARSER_WEIGHTS["unknown"])
        confidence = confidence * parser_weight

        if parser_weight >= 0.9:
            reasons.append(f"High parser reliability ({mime_type})")
        elif parser_weight >= 0.75:
            reasons.append(f"Good parser reliability ({mime_type})")
        else:
            reasons.append(f"Moderate parser reliability ({mime_type})")

        # Factor d) Structural metadata
        if section_title and len(section_title) > 0:
            confidence += 0.1
            reasons.append(f"Section heading available: '{section_title}'")

        if page_num is not None:
            confidence += 0.1
            reasons.append(f"Page number available: {page_num}")

        # Factor e) Text length
        if len(text) >= self.MIN_CITATION_LENGTH:
            confidence += 0.1
            reasons.append(f"Adequate citation length ({len(text)} chars)")
        else:
            reasons.append(f"WARNING: Short citation ({len(text)} chars)")

        # Normalize to [0.0, 1.0]
        confidence = max(0.0, min(confidence, 1.0))

        return confidence, reasons

    def _calculate_overall_confidence(
        self,
        text: str,
        outline: List[Dict[str, Any]],
        page_map: Optional[Dict[str, Any]],
        citations: List[Citation],
        mime_type: str = "unknown"
    ) -> float:
        """
        Calculate overall confidence for citation extraction based on citation quality

        Uses average of individual citation confidences weighted by verification status
        """
        if not citations:
            return 0.0

        # Calculate weighted average of citation confidences
        total_weight = 0.0
        weighted_sum = 0.0

        for citation in citations:
            # Verified citations get more weight
            weight = 1.5 if citation.verified else 1.0
            weighted_sum += citation.confidence * weight
            total_weight += weight

        avg_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Apply parser reliability weight
        parser_weight = self.PARSER_WEIGHTS.get(mime_type, self.PARSER_WEIGHTS["unknown"])
        overall = avg_confidence * parser_weight

        # Bonus for having multiple verified citations (up to +0.1)
        verified_count = sum(1 for c in citations if c.verified)
        verification_bonus = min(0.1, verified_count * 0.02)
        overall += verification_bonus

        return min(overall, 1.0)

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

        # Get MIME type for parser reliability scoring
        upload_mime = version_data.get("upload_mime", "unknown")
        is_pdf = upload_mime.lower() == "application/pdf" or upload_mime.lower() == "pdf"

        # Extract citations with verification
        return self.extract_citations(
            text=text,
            outline=outline,
            page_map=page_map,
            doc_id=doc_id,
            version_id=version_id,
            is_pdf=is_pdf,
            mime_type=upload_mime
        )


# Global instance
citation_extractor = CitationExtractor()
