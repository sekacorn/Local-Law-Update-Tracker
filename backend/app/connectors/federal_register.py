"""
Federal Register connector
Fetches Executive Orders and other presidential documents
"""
import httpx
import json
from typing import List, Optional
from datetime import datetime, timedelta

from .base import Connector, RemoteDocRef, ParsedDoc


class FederalRegisterConnector(Connector):
    """Connector for FederalRegister.gov API"""

    def __init__(self):
        super().__init__()
        self.source_id = "federal_register"
        self.source_name = "Federal Register"
        self.base_url = "https://www.federalregister.gov/api/v1"

    async def list_updates(
        self,
        since_ts: Optional[str] = None
    ) -> List[RemoteDocRef]:
        """
        List Executive Orders and presidential documents
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

        # Format date for API
        since_str = since_date.strftime("%Y-%m-%d")

        # Query parameters for Executive Orders
        params = {
            "conditions[type][]": "PRESDOCU",
            "conditions[presidential_document_type][]": "executive_order",
            "conditions[publication_date][gte]": since_str,
            "per_page": 100,
            "page": 1
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                try:
                    response = await client.get(
                        f"{self.base_url}/documents.json",
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()

                    results = data.get("results", [])
                    if not results:
                        break

                    for doc in results:
                        updates.append(RemoteDocRef(
                            source_id=self.source_id,
                            remote_id=doc.get("document_number", ""),
                            doc_type="executive_order",
                            title=doc.get("title", ""),
                            url=doc.get("html_url", ""),
                            published_ts=doc.get("publication_date", ""),
                            metadata={
                                "executive_order_number": doc.get("executive_order_number"),
                                "signing_date": doc.get("signing_date"),
                                "president": doc.get("president", {}).get("identifier"),
                                "abstract": doc.get("abstract"),
                                "pdf_url": doc.get("pdf_url"),
                                "json_url": doc.get("json_url")
                            }
                        ))

                    # Check if there are more pages
                    if len(results) < params["per_page"]:
                        break

                    params["page"] += 1

                except Exception as e:
                    print(f"Error listing Federal Register documents: {e}")
                    break

        # Limit to 10 for MVP testing
        return updates[:10]

    async def fetch_doc(
        self,
        remote_ref: RemoteDocRef
    ) -> bytes:
        """
        Fetch document content as HTML
        """
        # Use the JSON URL for structured content
        json_url = remote_ref.metadata.get("json_url")

        if not json_url:
            # Fallback to constructing URL
            json_url = f"{self.base_url}/documents/{remote_ref.remote_id}.json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(json_url)
                response.raise_for_status()
                return response.content

            except Exception as e:
                print(f"Error fetching document {remote_ref.remote_id}: {e}")
                raise

    async def parse_payload(
        self,
        raw: bytes,
        remote_ref: RemoteDocRef
    ) -> ParsedDoc:
        """
        Parse Federal Register JSON response
        """
        try:
            data = json.loads(raw.decode('utf-8'))

            # Handle both single document and wrapped responses
            if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
                data = data["results"][0]
            elif "document" in data:
                data = data["document"]

            # Extract document fields
            doc_data = {
                "source_id": self.source_id,
                "jurisdiction": "US-FED",
                "doc_type": "executive_order",
                "title": data.get("title", remote_ref.title),
                "identifiers_json": json.dumps({
                    "document_number": data.get("document_number", remote_ref.remote_id),
                    "executive_order_number": data.get("executive_order_number")
                }),
                "canonical_url": data.get("html_url", remote_ref.url)
            }

            # Extract full text
            full_text_xml = data.get("full_text_xml_url", "")
            body_html = data.get("body_html_url", "")
            raw_text = data.get("raw_text_url", "")

            # For now, use the abstract and body as normalized text
            # In production, you'd fetch and parse the full text
            abstract = data.get('abstract') or ""
            body = data.get('body') or ""

            normalized_text = f"{data.get('title', '')}\n\n"
            if abstract:
                normalized_text += f"Abstract: {abstract}\n\n"
            if body:
                normalized_text += body

            # Create outline from headings (if available)
            outline = {
                "type": "executive_order",
                "sections": []
            }

            # Create version data
            version_data = {
                "version_label": "published",
                "published_ts": data.get("publication_date", "") or data.get("signing_date", ""),
                "normalized_text": normalized_text,
                "outline_json": json.dumps(outline),
                "snippets_json": json.dumps({
                    "abstract": (data.get("abstract") or "")[:500],
                    "executive_order_number": data.get("executive_order_number", ""),
                    "citation": data.get("citation", "")
                }),
                "content_mode": "full"
            }

            return ParsedDoc(
                document=doc_data,
                versions=[version_data]
            )

        except Exception as e:
            print(f"Error parsing document: {e}")
            raise
