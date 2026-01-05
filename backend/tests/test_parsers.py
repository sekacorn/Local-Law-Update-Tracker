"""
Parser tests
"""
import pytest
from app.parsers.normalizer import normalize_text, extract_outline, extract_snippets
from app.parsers.html_parser import parse_html, clean_text


def test_normalize_text():
    """Test text normalization"""
    text = "This  is   a    test.\n\n\nWith   multiple   spaces."
    normalized = normalize_text(text)

    assert "  " not in normalized  # No double spaces
    assert normalized.count("\n") <= 2  # Normalized line breaks


def test_extract_outline():
    """Test outline extraction"""
    text = """
    I. Introduction
    This is the introduction section.

    II. Main Content
    This is the main content.

    Section 1. Details
    More details here.
    """

    outline = extract_outline(text)

    assert "sections" in outline
    assert len(outline["sections"]) >= 2


def test_extract_snippets():
    """Test snippet extraction"""
    text = """
    This is the first paragraph with some important information.

    This is the second paragraph with more details.

    This is the third paragraph with additional context.

    This is the fourth paragraph with even more information.
    """

    snippets = extract_snippets(text, max_snippet_length=100, num_snippets=2)

    assert len(snippets) <= 2
    for snippet in snippets:
        assert len(snippet) <= 100


def test_clean_html_text():
    """Test HTML text cleaning"""
    text = "Multiple     spaces\n\n\n\nand    newlines"
    cleaned = clean_text(text)

    assert "    " not in cleaned
    assert "\n\n\n" not in cleaned


def test_parse_html():
    """Test HTML parsing"""
    html = """
    <html>
    <head><title>Test Document</title></head>
    <body>
        <h1>Main Heading</h1>
        <p>First paragraph.</p>
        <h2>Sub Heading</h2>
        <p>Second paragraph.</p>
    </body>
    </html>
    """

    result = parse_html(html)

    assert "text" in result
    assert "headings" in result
    assert result["metadata"]["title"] == "Test Document"
    assert len(result["headings"]) >= 2
