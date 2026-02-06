"""
Unit tests for citation extraction, verification, and confidence scoring
Tests the Trust Engine implementation
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.analysis.citations import CitationExtractor, Citation, CitationLocation


class TestCitationVerification:
    """Test citation span verification with exact and fuzzy matching"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = CitationExtractor()
        self.sample_text = """LEASE AGREEMENT

SECTION 1. PARTIES
This lease agreement is entered into between Landlord and Tenant.

SECTION 2. PREMISES
The premises are located at 123 Main Street.

SECTION 3. TERM
The lease term is 12 months beginning January 1, 2026.

SECTION 4. RENT
Tenant shall pay $1,500 per month. Rent is due on the 1st of each month.
A late fee of $50 applies after the 5th.

SECTION 5. TERMINATION
Either party may terminate with 30 days notice."""

    def test_exact_match_at_claimed_position(self):
        """Test exact match at the claimed position"""
        quote = "This lease agreement is entered into between Landlord and Tenant."
        start = self.sample_text.find(quote)
        end = start + len(quote)

        verified, match_method, actual_start, actual_end = self.extractor.verify_citation_span(
            quote_text=quote,
            full_text=self.sample_text,
            claimed_start=start,
            claimed_end=end
        )

        assert verified is True
        assert match_method == "exact"
        assert actual_start == start
        assert actual_end == end

    def test_exact_match_at_different_position(self):
        """Test exact match when claimed position is wrong but text exists"""
        quote = "Tenant shall pay $1,500 per month."
        wrong_start = 0
        wrong_end = len(quote)

        verified, match_method, actual_start, actual_end = self.extractor.verify_citation_span(
            quote_text=quote,
            full_text=self.sample_text,
            claimed_start=wrong_start,
            claimed_end=wrong_end
        )

        assert verified is True
        assert match_method == "exact"
        # Should find the actual position
        assert actual_start == self.sample_text.find(quote)

    def test_fuzzy_match(self):
        """Test fuzzy matching with minor differences"""
        # Original text with slight variation
        quote = "The lease term is twelve months beginning January 1, 2026."
        original = "The lease term is 12 months beginning January 1, 2026."
        start = self.sample_text.find(original)
        end = start + len(original)

        verified, match_method, actual_start, actual_end = self.extractor.verify_citation_span(
            quote_text=quote,
            full_text=self.sample_text,
            claimed_start=start,
            claimed_end=end
        )

        # Should match fuzzily since similarity is high
        assert match_method in ["exact", "fuzzy"]
        if match_method == "fuzzy":
            assert verified is True

    def test_no_match_found(self):
        """Test when citation cannot be verified"""
        quote = "This text does not exist in the document at all."

        verified, match_method, actual_start, actual_end = self.extractor.verify_citation_span(
            quote_text=quote,
            full_text=self.sample_text,
            claimed_start=0,
            claimed_end=len(quote)
        )

        assert verified is False
        assert match_method == "none"

    def test_case_insensitive_exact_match(self):
        """Test that exact matching is case-insensitive"""
        quote = "TENANT SHALL PAY $1,500 PER MONTH."

        verified, match_method, actual_start, actual_end = self.extractor.verify_citation_span(
            quote_text=quote,
            full_text=self.sample_text,
            claimed_start=0,
            claimed_end=len(quote)
        )

        assert verified is True
        assert match_method == "exact"


class TestConfidenceScoring:
    """Test deterministic confidence scoring with reasons"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = CitationExtractor()

    def test_high_confidence_verified_exact_txt(self):
        """Test high confidence for verified exact match in TXT"""
        confidence, reasons = self.extractor._calculate_citation_confidence(
            text="This is a valid citation with adequate length for testing purposes.",
            section_title="Section 1. Introduction",
            page_num=None,
            verified=True,
            match_method="exact",
            mime_type="text/plain"
        )

        assert confidence >= 0.7  # Should be high
        assert "Citation verified in source text" in reasons
        assert "Exact match found at claimed position" in reasons
        assert any("High parser reliability" in r for r in reasons)
        assert any("Section heading available" in r for r in reasons)

    def test_low_confidence_unverified(self):
        """Test low confidence for unverified citation"""
        confidence, reasons = self.extractor._calculate_citation_confidence(
            text="Short text",
            section_title=None,
            page_num=None,
            verified=False,
            match_method="none",
            mime_type="unknown"
        )

        assert confidence < 0.5  # Should be low
        assert "WARNING: Citation could not be verified in source text" in reasons
        assert "WARNING: No match found for citation" in reasons

    def test_medium_confidence_fuzzy_pdf(self):
        """Test medium confidence for fuzzy match in PDF"""
        confidence, reasons = self.extractor._calculate_citation_confidence(
            text="This is a citation of adequate length for testing.",
            section_title="Introduction",
            page_num=1,
            verified=True,
            match_method="fuzzy",
            mime_type="application/pdf"
        )

        # Should be moderate due to fuzzy match and PDF
        assert 0.4 <= confidence <= 0.8
        assert any("Fuzzy match found" in r for r in reasons)
        assert any("Good parser reliability" in r or "Moderate parser reliability" in r for r in reasons)
        assert any("Page number available" in r for r in reasons)

    def test_confidence_reasons_deterministic(self):
        """Test that confidence scoring is deterministic"""
        # Same inputs should give same results
        conf1, reasons1 = self.extractor._calculate_citation_confidence(
            text="Test citation text here",
            section_title="Test Section",
            page_num=5,
            verified=True,
            match_method="exact",
            mime_type="text/html"
        )

        conf2, reasons2 = self.extractor._calculate_citation_confidence(
            text="Test citation text here",
            section_title="Test Section",
            page_num=5,
            verified=True,
            match_method="exact",
            mime_type="text/html"
        )

        assert conf1 == conf2
        assert reasons1 == reasons2

    def test_all_factors_contribute(self):
        """Test that all confidence factors contribute"""
        # Test with all positive factors
        conf_all, reasons_all = self.extractor._calculate_citation_confidence(
            text="This is a sufficiently long citation text.",
            section_title="Important Section",
            page_num=10,
            verified=True,
            match_method="exact",
            mime_type="text/plain"
        )

        # Test with minimal factors
        conf_min, reasons_min = self.extractor._calculate_citation_confidence(
            text="Short",
            section_title=None,
            page_num=None,
            verified=False,
            match_method="none",
            mime_type="unknown"
        )

        assert conf_all > conf_min
        assert len(reasons_all) > len(reasons_min)


class TestCitationExtraction:
    """Test full citation extraction with verification"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = CitationExtractor()

    def test_extract_citations_from_txt(self):
        """Test citation extraction from plain text"""
        text = """EMPLOYMENT AGREEMENT

1. Position
Employee shall serve as Software Engineer.

2. Compensation
Annual salary of $100,000.

3. Benefits
Health insurance and 401k provided."""

        outline = [
            {"title": "1. Position", "start_char": 21, "end_char": 64},
            {"title": "2. Compensation", "start_char": 66, "end_char": 98},
            {"title": "3. Benefits", "start_char": 100, "end_char": 145}
        ]

        citations, confidence = self.extractor.extract_citations(
            text=text,
            outline=outline,
            page_map=None,
            doc_id="test_doc",
            version_id="test_version",
            is_pdf=False,
            mime_type="text/plain"
        )

        assert len(citations) == 3
        assert confidence > 0.5

        # Check first citation
        assert citations[0].verified is True
        assert citations[0].match_method == "exact"
        assert len(citations[0].confidence_reasons) > 0
        assert citations[0].location.section == "1. Position"

    def test_extract_citations_from_html(self):
        """Test citation extraction from HTML"""
        text = """Terms of Service

Section 1: Acceptance
By using our service, you agree to these terms.

Section 2: Privacy
We collect and use your data as described in our privacy policy."""

        outline = [
            {"title": "Section 1: Acceptance", "start_char": 18, "end_char": 73},
            {"title": "Section 2: Privacy", "start_char": 75, "end_char": 145}
        ]

        citations, confidence = self.extractor.extract_citations(
            text=text,
            outline=outline,
            page_map=None,
            doc_id="test_doc",
            version_id="test_version",
            is_pdf=False,
            mime_type="text/html"
        )

        assert len(citations) == 2
        # HTML should have high parser weight
        assert confidence >= 0.5

        for citation in citations:
            assert citation.verified is True
            assert citation.doc_id == "test_doc"
            assert citation.version_id == "test_version"

    def test_overall_confidence_with_verified_citations(self):
        """Test overall confidence calculation"""
        text = "Test document with content."
        outline = [{"title": "Section 1", "start_char": 0, "end_char": 27}]

        citations, confidence = self.extractor.extract_citations(
            text=text,
            outline=outline,
            page_map=None,
            doc_id="doc1",
            version_id="v1",
            is_pdf=False,
            mime_type="text/plain"
        )

        # Should have high confidence with verified citation in TXT
        assert confidence > 0.6
        assert len(citations) == 1
        assert citations[0].verified is True


class TestCitationDataclass:
    """Test Citation dataclass functionality"""

    def test_citation_to_dict(self):
        """Test Citation.to_dict() includes all fields"""
        location = CitationLocation(
            section="Test Section",
            char_start=100,
            char_end=200,
            page=5
        )

        citation = Citation(
            doc_id="doc123",
            version_id="v456",
            citation_type="user_upload",
            text="This is a test citation.",
            location=location,
            confidence=0.85,
            verified=True,
            match_method="exact",
            confidence_reasons=["Verified", "Exact match"]
        )

        result = citation.to_dict()

        assert result["doc_id"] == "doc123"
        assert result["version_id"] == "v456"
        assert result["verified"] is True
        assert result["match_method"] == "exact"
        assert result["confidence"] == 0.85
        assert result["confidence_reasons"] == ["Verified", "Exact match"]
        assert result["quote_text"] == "This is a test citation."
        assert result["location"]["section"] == "Test Section"
        assert result["location"]["page"] == 5


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
