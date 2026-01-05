"""
HTML parsing functionality
"""
from typing import Dict, Any, List, Optional
from selectolax.parser import HTMLParser
import re


def parse_html(
    html_content: str,
    extract_links: bool = True
) -> Dict[str, Any]:
    """
    Parse HTML document and extract text, structure, and links

    Args:
        html_content: HTML as string
        extract_links: Whether to extract links

    Returns:
        Dictionary with:
            - text: Extracted text content
            - headings: List of headings with hierarchy
            - links: List of links (if extract_links=True)
            - metadata: Metadata from HTML
    """
    result = {
        "text": "",
        "headings": [],
        "links": [],
        "metadata": {}
    }

    try:
        tree = HTMLParser(html_content)

        # Extract title
        title_node = tree.css_first("title")
        if title_node:
            result["metadata"]["title"] = title_node.text(strip=True)

        # Extract meta tags
        meta_tags = tree.css("meta")
        for meta in meta_tags:
            name = meta.attributes.get("name") or meta.attributes.get("property")
            content = meta.attributes.get("content")
            if name and content:
                result["metadata"][name] = content

        # Extract headings (h1-h6)
        for level in range(1, 7):
            headings = tree.css(f"h{level}")
            for heading in headings:
                text = heading.text(strip=True)
                if text:
                    result["headings"].append({
                        "level": level,
                        "text": text
                    })

        # Extract main text content
        # Remove script and style tags
        for tag in tree.css("script, style"):
            tag.decompose()

        # Get text from body or main content
        body = tree.css_first("body") or tree.css_first("main") or tree.root
        if body:
            result["text"] = clean_text(body.text(separator="\n"))

        # Extract links
        if extract_links:
            links = tree.css("a")
            for link in links:
                href = link.attributes.get("href")
                text = link.text(strip=True)
                if href:
                    result["links"].append({
                        "href": href,
                        "text": text
                    })

    except Exception as e:
        print(f"Error parsing HTML: {e}")
        raise

    return result


def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()


def extract_html_section(
    html_content: str,
    section_id: Optional[str] = None,
    heading_text: Optional[str] = None
) -> str:
    """
    Extract a specific section from HTML by ID or heading text
    """
    try:
        tree = HTMLParser(html_content)

        # Find by ID
        if section_id:
            section = tree.css_first(f"#{section_id}")
            if section:
                return clean_text(section.text())

        # Find by heading text
        if heading_text:
            for level in range(1, 7):
                headings = tree.css(f"h{level}")
                for heading in headings:
                    if heading_text.lower() in heading.text(strip=True).lower():
                        # Get content until next heading of same or higher level
                        # For MVP, just return the heading's parent content
                        parent = heading.parent
                        if parent:
                            return clean_text(parent.text())

        return ""

    except Exception as e:
        print(f"Error extracting HTML section: {e}")
        return ""
