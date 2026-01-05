"""
Diff engine for comparing document versions
"""
import difflib
import json
from typing import Dict, Any, List, Optional


def compute_text_diff(
    old_text: str,
    new_text: str,
    context_lines: int = 3
) -> Dict[str, Any]:
    """
    Compute diff between two text versions
    Returns unified diff format
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    # Generate unified diff
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm='',
        n=context_lines
    ))

    # Parse diff into structured format
    changes = []
    current_chunk = None

    for line in diff:
        if line.startswith('---') or line.startswith('+++'):
            continue
        elif line.startswith('@@'):
            # New chunk
            if current_chunk:
                changes.append(current_chunk)
            current_chunk = {
                "header": line,
                "additions": [],
                "deletions": [],
                "context": []
            }
        elif current_chunk:
            if line.startswith('+'):
                current_chunk["additions"].append(line[1:])
            elif line.startswith('-'):
                current_chunk["deletions"].append(line[1:])
            else:
                current_chunk["context"].append(line[1:] if line.startswith(' ') else line)

    if current_chunk:
        changes.append(current_chunk)

    # Compute statistics
    total_additions = sum(len(c["additions"]) for c in changes)
    total_deletions = sum(len(c["deletions"]) for c in changes)

    return {
        "changes": changes,
        "statistics": {
            "chunks": len(changes),
            "additions": total_additions,
            "deletions": total_deletions,
            "total_changes": total_additions + total_deletions
        },
        "raw_diff": diff
    }


def compute_section_diff(
    old_outline: str,
    new_outline: str
) -> Dict[str, Any]:
    """
    Compare document outlines/sections
    Useful for structured legal documents
    """
    try:
        old_struct = json.loads(old_outline) if isinstance(old_outline, str) else old_outline
        new_struct = json.loads(new_outline) if isinstance(new_outline, str) else new_outline
    except:
        return {"error": "Invalid outline JSON"}

    # Extract sections from both
    old_sections = _extract_sections(old_struct)
    new_sections = _extract_sections(new_struct)

    # Find added, removed, and common sections
    old_set = set(old_sections)
    new_set = set(new_sections)

    added = list(new_set - old_set)
    removed = list(old_set - new_set)
    common = list(old_set & new_set)

    return {
        "added_sections": added,
        "removed_sections": removed,
        "unchanged_sections": common,
        "statistics": {
            "sections_added": len(added),
            "sections_removed": len(removed),
            "sections_unchanged": len(common)
        }
    }


def _extract_sections(outline: Dict[str, Any]) -> List[str]:
    """Extract section names from outline structure"""
    sections = []

    if isinstance(outline, dict):
        # Handle different outline structures
        if "sections" in outline:
            for section in outline.get("sections", []):
                if isinstance(section, dict):
                    sections.append(section.get("title", section.get("heading", "")))
                elif isinstance(section, str):
                    sections.append(section)
        if "heading" in outline:
            sections.append(outline["heading"])

    return [s for s in sections if s]


def compute_smart_diff(
    old_version: Dict[str, Any],
    new_version: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute comprehensive diff between two versions
    Includes text diff, section diff, and metadata changes
    """
    result = {
        "version_comparison": {
            "old": {
                "id": old_version.get("id"),
                "label": old_version.get("version_label"),
                "published": old_version.get("published_ts")
            },
            "new": {
                "id": new_version.get("id"),
                "label": new_version.get("version_label"),
                "published": new_version.get("published_ts")
            }
        }
    }

    # Text diff
    old_text = old_version.get("normalized_text", "")
    new_text = new_version.get("normalized_text", "")

    if old_text and new_text:
        result["text_diff"] = compute_text_diff(old_text, new_text)
    else:
        result["text_diff"] = {"error": "Text not available for comparison"}

    # Section/outline diff
    old_outline = old_version.get("outline_json", "{}")
    new_outline = new_version.get("outline_json", "{}")

    result["section_diff"] = compute_section_diff(old_outline, new_outline)

    # Content hash comparison
    result["content_changed"] = (
        old_version.get("content_hash") != new_version.get("content_hash")
    )

    # Summary
    text_stats = result["text_diff"].get("statistics", {})
    section_stats = result["section_diff"].get("statistics", {})

    result["summary"] = {
        "has_text_changes": text_stats.get("total_changes", 0) > 0,
        "has_section_changes": (
            section_stats.get("sections_added", 0) > 0 or
            section_stats.get("sections_removed", 0) > 0
        ),
        "total_text_changes": text_stats.get("total_changes", 0),
        "total_section_changes": (
            section_stats.get("sections_added", 0) +
            section_stats.get("sections_removed", 0)
        )
    }

    return result
