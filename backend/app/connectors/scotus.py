"""
Supreme Court connector
Fetches Supreme Court opinions
"""
import httpx
import json
from typing import List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from .base import Connector, RemoteDocRef, ParsedDoc


class ScotusConnector(Connector):
    """Connector for SupremeCourt.gov opinions"""

    def __init__(self):
        super().__init__()
        self.source_id = "scotus"
        self.source_name = "Supreme Court"
        self.base_url = "https://www.supremecourt.gov"

    async def list_updates(
        self,
        since_ts: Optional[str] = None
    ) -> List[RemoteDocRef]:
        """
        List Supreme Court opinions
        Scrapes the opinions page for recent decisions
        """
        updates = []

        # Default to last 90 days if no timestamp provided
        if since_ts:
            try:
                since_date = datetime.fromisoformat(since_ts.replace('Z', '+00:00'))
            except:
                since_date = datetime.utcnow() - timedelta(days=90)
        else:
            since_date = datetime.utcnow() - timedelta(days=90)

        # Scrape opinions page
        # Note: The Supreme Court website structure may change
        # This is a simplified example that would need adjustment for production
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                # Get the opinions page (current term)
                response = await client.get(
                    f"{self.base_url}/opinions/slipopinion/{datetime.now().year % 100}"
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find opinion links (this is simplified - actual scraping logic would depend on site structure)
                # The Supreme Court website typically lists opinions in tables or lists
                # For MVP, we'll simulate finding a few opinions

                # Look for PDF links (typical pattern)
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')

                    # Check if it's an opinion PDF
                    if 'opinions' in href.lower() and '.pdf' in href.lower():
                        # Extract case information from link text
                        link_text = link.get_text(strip=True)

                        if not link_text or len(link_text) < 3:
                            continue

                        # Construct full URL
                        if not href.startswith('http'):
                            href = self.base_url + (href if href.startswith('/') else '/' + href)

                        # Extract case number from filename if possible
                        # Example: 22-1234.pdf -> case number 22-1234
                        case_number = href.split('/')[-1].replace('.pdf', '')

                        updates.append(RemoteDocRef(
                            source_id=self.source_id,
                            remote_id=case_number,
                            doc_type="opinion",
                            title=link_text[:200],  # Truncate long titles
                            url=href,
                            published_ts=datetime.utcnow().isoformat(),  # Would need actual date from page
                            metadata={
                                "case_number": case_number,
                                "pdf_url": href,
                                "term": datetime.now().year
                            }
                        ))

            except Exception as e:
                print(f"Error listing SCOTUS opinions: {e}")

        # Limit to reasonable number for MVP
        return updates[:20]

    async def fetch_doc(
        self,
        remote_ref: RemoteDocRef
    ) -> bytes:
        """
        Fetch opinion PDF
        """
        pdf_url = remote_ref.metadata.get("pdf_url", remote_ref.url)

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            try:
                response = await client.get(pdf_url)
                response.raise_for_status()
                return response.content

            except Exception as e:
                print(f"Error fetching PDF {remote_ref.remote_id}: {e}")
                raise

    async def parse_payload(
        self,
        raw: bytes,
        remote_ref: RemoteDocRef
    ) -> ParsedDoc:
        """
        Parse Supreme Court opinion PDF
        For MVP: extract basic metadata without full PDF parsing
        """
        try:
            # For MVP: Store PDF reference and basic metadata
            # Full PDF parsing with pdfplumber can be added later

            doc_data = {
                "source_id": self.source_id,
                "jurisdiction": "US-FED",
                "doc_type": "opinion",
                "title": remote_ref.title,
                "identifiers_json": json.dumps({
                    "case_number": remote_ref.metadata.get("case_number")
                }),
                "canonical_url": remote_ref.url
            }

            # Create outline placeholder
            outline = {
                "type": "opinion",
                "case_number": remote_ref.metadata.get("case_number"),
                "sections": [
                    "Opinion",
                    "Syllabus",
                    "Decision"
                ]
            }

            # For now, use metadata as snippet
            # In production, would extract text from PDF
            snippet_text = f"Supreme Court opinion in case {remote_ref.metadata.get('case_number')}. {remote_ref.title}"

            version_data = {
                "version_label": "slip_opinion",
                "published_ts": remote_ref.published_ts,
                "normalized_text": snippet_text,  # Would be full extracted text in production
                "outline_json": json.dumps(outline),
                "snippets_json": json.dumps({
                    "title": remote_ref.title[:500]
                }),
                "content_mode": "thin",  # Using thin mode since we're not parsing full PDF yet
                "raw_path": None  # Could save PDF to cache_dir if needed
            }

            return ParsedDoc(
                document=doc_data,
                versions=[version_data]
            )

        except Exception as e:
            print(f"Error parsing opinion: {e}")
            raise
