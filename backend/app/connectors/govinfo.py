"""
GovInfo connector
Fetches GPO published documents
"""
import httpx
import json
from typing import List, Optional
from datetime import datetime, timedelta

from .base import Connector, RemoteDocRef, ParsedDoc


class GovInfoConnector(Connector):
    """Connector for GovInfo (GPO) API"""

    def __init__(self):
        super().__init__()
        self.source_id = "govinfo"
        self.source_name = "GovInfo"
        self.base_url = "https://api.govinfo.gov"

    def _get_api_key(self) -> Optional[str]:
        """Get API key from settings"""
        from ..settings import settings_manager

        settings = settings_manager.load()
        return settings.get("sources", {}).get("govinfo", {}).get("api_key")

    async def list_updates(
        self,
        since_ts: Optional[str] = None
    ) -> List[RemoteDocRef]:
        """
        List recent publications from GovInfo
        Focuses on collections relevant to legal updates
        """
        api_key = self._get_api_key()

        # GovInfo API can work without an API key for basic access
        # but with rate limits. API key is recommended.
        if not api_key:
            print("Warning: GovInfo API key not configured. Using public access with rate limits.")

        updates = []

        # Default to last 30 days if no timestamp provided
        if since_ts:
            try:
                since_date = datetime.fromisoformat(since_ts.replace('Z', '+00:00'))
            except:
                since_date = datetime.utcnow() - timedelta(days=30)
        else:
            since_date = datetime.utcnow() - timedelta(days=30)

        # Format dates for API
        start_date = since_date.strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

        # Collections to query (focusing on legal documents)
        collections = [
            "CFR",      # Code of Federal Regulations
            "FR",       # Federal Register
            "BILLS",    # Congressional Bills
            "STATUTE",  # US Statutes at Large
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for collection in collections:
                try:
                    # Build request URL
                    url = f"{self.base_url}/collections/{collection}/{start_date}"

                    params = {
                        "offset": 0,
                        "pageSize": 20
                    }

                    if api_key:
                        params["api_key"] = api_key

                    response = await client.get(url, params=params)

                    # Skip if collection not available or rate limited
                    if response.status_code == 404:
                        continue
                    if response.status_code == 429:
                        print(f"Rate limited on collection {collection}")
                        continue

                    response.raise_for_status()
                    data = response.json()

                    # Parse packages
                    packages = data.get("packages", [])

                    for package in packages:
                        package_id = package.get("packageId", "")
                        title = package.get("title", "Untitled Document")
                        doc_class = package.get("docClass", collection)

                        # Get package date
                        date_issued = package.get("dateIssued", datetime.utcnow().isoformat())

                        # Build URL
                        doc_url = f"https://www.govinfo.gov/app/details/{package_id}"

                        updates.append(RemoteDocRef(
                            source_id=self.source_id,
                            remote_id=package_id,
                            doc_type=doc_class.lower(),
                            title=title,
                            url=doc_url,
                            published_ts=date_issued,
                            metadata={
                                "package_id": package_id,
                                "collection": collection,
                                "doc_class": doc_class,
                                "date_issued": date_issued,
                                "granule_count": package.get("granuleCount", 0)
                            }
                        ))

                except Exception as e:
                    print(f"Error querying GovInfo collection {collection}: {e}")
                    continue

        return updates[:50]  # Limit for MVP

    async def fetch_doc(
        self,
        remote_ref: RemoteDocRef
    ) -> bytes:
        """
        Fetch package summary from GovInfo API
        """
        api_key = self._get_api_key()
        package_id = remote_ref.metadata.get("package_id", remote_ref.remote_id)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get package summary
                url = f"{self.base_url}/packages/{package_id}/summary"

                params = {}
                if api_key:
                    params["api_key"] = api_key

                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.content

            except Exception as e:
                print(f"Error fetching package {package_id}: {e}")
                raise

    async def parse_payload(
        self,
        raw: bytes,
        remote_ref: RemoteDocRef
    ) -> ParsedDoc:
        """
        Parse GovInfo package summary
        """
        try:
            data = json.loads(raw.decode('utf-8'))

            # Extract document fields
            doc_data = {
                "source_id": self.source_id,
                "jurisdiction": "US-FED",
                "doc_type": remote_ref.metadata.get("doc_class", "govinfo_doc").lower(),
                "title": data.get("title", remote_ref.title),
                "identifiers_json": json.dumps({
                    "package_id": remote_ref.metadata.get("package_id"),
                    "collection": remote_ref.metadata.get("collection")
                }),
                "canonical_url": remote_ref.url
            }

            # Extract content
            summary = data.get("summary", "")
            abstract = data.get("abstract", "")

            # Create outline
            outline = {
                "type": remote_ref.metadata.get("doc_class", "document"),
                "collection": remote_ref.metadata.get("collection"),
                "sections": []
            }

            # Check for granules (sections/parts)
            granules = data.get("granules", [])
            if granules:
                for granule in granules[:20]:  # Limit to first 20
                    outline["sections"].append({
                        "title": granule.get("title", ""),
                        "granule_id": granule.get("granuleId", "")
                    })

            # Create normalized text
            normalized_text = f"{data.get('title', '')}\n\n"

            if abstract:
                normalized_text += f"Abstract:\n{abstract}\n\n"

            if summary:
                normalized_text += f"Summary:\n{summary}\n\n"

            # Add document details
            if data.get("dateIssued"):
                normalized_text += f"Date Issued: {data.get('dateIssued')}\n"

            if data.get("congress"):
                normalized_text += f"Congress: {data.get('congress')}\n"

            # Create version data
            version_data = {
                "version_label": "published",
                "published_ts": remote_ref.metadata.get("date_issued", remote_ref.published_ts),
                "normalized_text": normalized_text,
                "outline_json": json.dumps(outline),
                "snippets_json": json.dumps({
                    "abstract": abstract[:500] if abstract else "",
                    "summary": summary[:500] if summary else ""
                }),
                "content_mode": "full"
            }

            return ParsedDoc(
                document=doc_data,
                versions=[version_data]
            )

        except Exception as e:
            print(f"Error parsing GovInfo package: {e}")
            raise
