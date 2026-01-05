"""
PDF parsing functionality
"""
import io
from typing import Dict, Any, List, Optional
import pdfplumber


def parse_pdf(
    pdf_bytes: bytes,
    extract_images: bool = False
) -> Dict[str, Any]:
    """
    Parse PDF document and extract text, structure, and metadata

    Args:
        pdf_bytes: PDF file as bytes
        extract_images: Whether to extract images (not implemented in MVP)

    Returns:
        Dictionary with:
            - text: Full extracted text
            - pages: List of page dictionaries
            - metadata: PDF metadata
            - outline: Document outline/headings
    """
    result = {
        "text": "",
        "pages": [],
        "metadata": {},
        "outline": []
    }

    try:
        pdf_file = io.BytesIO(pdf_bytes)

        with pdfplumber.open(pdf_file) as pdf:
            # Extract metadata
            if pdf.metadata:
                result["metadata"] = {
                    key: str(value) if value else ""
                    for key, value in pdf.metadata.items()
                }

            # Extract text from each page
            all_text = []
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                all_text.append(page_text)

                # Store page data
                result["pages"].append({
                    "page_number": page_num,
                    "text": page_text,
                    "width": page.width,
                    "height": page.height,
                    "char_count": len(page_text)
                })

            # Join all page text
            result["text"] = "\n\n".join(all_text)

            # Try to extract outline/bookmarks if available
            # pdfplumber doesn't directly support outline extraction
            # For MVP, we'll detect headings from text formatting later

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        raise

    return result


def extract_pdf_metadata(pdf_bytes: bytes) -> Dict[str, Any]:
    """Extract only metadata from PDF"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)

        with pdfplumber.open(pdf_file) as pdf:
            metadata = {}
            if pdf.metadata:
                metadata = {
                    key: str(value) if value else ""
                    for key, value in pdf.metadata.items()
                }

            metadata["page_count"] = len(pdf.pages)

            return metadata

    except Exception as e:
        print(f"Error extracting PDF metadata: {e}")
        return {}


def extract_pdf_pages(
    pdf_bytes: bytes,
    start_page: int = 1,
    end_page: Optional[int] = None
) -> str:
    """Extract text from specific page range"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        text_parts = []

        with pdfplumber.open(pdf_file) as pdf:
            end = end_page or len(pdf.pages)
            end = min(end, len(pdf.pages))

            for page_num in range(start_page - 1, end):
                if page_num < len(pdf.pages):
                    page_text = pdf.pages[page_num].extract_text() or ""
                    text_parts.append(page_text)

        return "\n\n".join(text_parts)

    except Exception as e:
        print(f"Error extracting PDF pages: {e}")
        return ""
