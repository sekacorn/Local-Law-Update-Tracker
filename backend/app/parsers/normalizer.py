"""
Text normalization and structure extraction
"""
import re
from typing import Dict, Any, List, Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for storage and search
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Normalize line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    # Trim
    text = text.strip()

    return text


def extract_outline(text: str) -> Dict[str, Any]:
    """
    Extract document outline/structure from text
    Detects headings based on common patterns
    """
    outline = {
        "sections": []
    }

    lines = text.split('\n')
    current_section = None

    # Patterns for detecting headings
    heading_patterns = [
        # Roman numerals
        r'^(I{1,3}V?|IV|VI{0,3}|IX|XI{0,2})\.\s+(.+)$',
        # Numbered sections
        r'^(\d+)\.\s+(.+)$',
        # Section/Article
        r'^(Section|Article|Part)\s+(\d+|[A-Z])[:\.]?\s+(.+)$',
        # ALL CAPS headings (at least 3 words)
        r'^([A-Z\s]{10,})$',
        # Lettered sections
        r'^([A-Z])\.\s+(.+)$'
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check heading patterns
        is_heading = False
        heading_text = None

        for pattern in heading_patterns:
            match = re.match(pattern, line)
            if match:
                is_heading = True
                heading_text = line
                break

        # Also detect short lines (likely headings)
        if len(line) < 80 and line.isupper() and len(line.split()) >= 2:
            is_heading = True
            heading_text = line

        if is_heading and heading_text:
            section = {
                "heading": heading_text,
                "level": 1,  # Default level
                "start_pos": text.find(line)
            }
            outline["sections"].append(section)
            current_section = section

    return outline


def extract_snippets(
    text: str,
    max_snippet_length: int = 500,
    num_snippets: int = 5
) -> List[str]:
    """
    Extract key snippets from text for thin cache mode
    """
    snippets = []

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Take first few paragraphs
    for para in paragraphs[:num_snippets]:
        if len(para) > max_snippet_length:
            # Truncate at sentence boundary
            truncated = para[:max_snippet_length]
            last_period = truncated.rfind('.')
            if last_period > max_snippet_length * 0.5:
                truncated = truncated[:last_period + 1]
            snippets.append(truncated)
        else:
            snippets.append(para)

    return snippets


def detect_key_clauses(text: str) -> List[Dict[str, Any]]:
    """
    Detect key legal clauses (liability, termination, etc.)
    Returns list of clause positions and types
    """
    clauses = []

    # Keywords for different clause types
    clause_keywords = {
        "liability": [
            "liability", "liable", "damages", "indemnify", "indemnification"
        ],
        "termination": [
            "termination", "terminate", "cancellation", "cancel"
        ],
        "warranty": [
            "warranty", "warrants", "guarantee", "guarantees"
        ],
        "confidentiality": [
            "confidential", "confidentiality", "proprietary"
        ],
        "dispute": [
            "dispute", "arbitration", "litigation", "jurisdiction"
        ]
    }

    # Search for clauses
    for clause_type, keywords in clause_keywords.items():
        for keyword in keywords:
            # Case-insensitive search
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                # Find sentence containing the keyword
                start = max(0, text.rfind('.', 0, match.start()) + 1)
                end = text.find('.', match.end())
                if end == -1:
                    end = len(text)

                sentence = text[start:end].strip()

                clauses.append({
                    "type": clause_type,
                    "keyword": keyword,
                    "position": match.start(),
                    "text": sentence
                })

    return clauses
