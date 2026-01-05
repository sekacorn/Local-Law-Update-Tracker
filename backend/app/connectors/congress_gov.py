"""
Congress.gov connector
Fetches bills and legislative actions
"""
import httpx
import json
from typing import List, Optional
from datetime import datetime, timedelta

from .base import Connector, RemoteDocRef, ParsedDoc


class CongressGovConnector(Connector):
    """Connector for Congress.gov API"""

    def __init__(self):
        super().__init__()
        self.source_id = "congress_gov"
        self.source_name = "Congress.gov"
        self.base_url = "https://api.congress.gov/v3"

    def _get_api_key(self) -> Optional[str]:
        """Get API key from settings"""
        from ..settings import settings_manager

        settings = settings_manager.load()
        return settings.get("sources", {}).get("congress_gov", {}).get("api_key")

    async def list_updates(
        self,
        since_ts: Optional[str] = None
    ) -> List[RemoteDocRef]:
        """
        List bills with recent actions
        """
        api_key = self._get_api_key()

        if not api_key:
            print("Congress.gov API key not configured. Skipping.")
            return []

        updates = []

        # Default to last 30 days if no timestamp provided
        if since_ts:
            try:
                since_date = datetime.fromisoformat(since_ts.replace('Z', '+00:00'))
            except:
                since_date = datetime.utcnow() - timedelta(days=30)
        else:
            since_date = datetime.utcnow() - timedelta(days=30)

        # Format date for API (YYYY-MM-DD)
        since_str = since_date.strftime("%Y-%m-%d")

        # Get current congress number (118th Congress started Jan 2023)
        # Simple calculation: (current_year - 1789) / 2
        current_congress = (datetime.now().year - 1789) // 2 + 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Query bills from current congress
                params = {
                    "api_key": api_key,
                    "format": "json",
                    "limit": 50,
                    "offset": 0
                }

                response = await client.get(
                    f"{self.base_url}/bill/{current_congress}",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                bills = data.get("bills", [])

                for bill in bills:
                    # Get bill details
                    bill_number = bill.get("number", "")
                    bill_type = bill.get("type", "")
                    bill_title = bill.get("title", "Unknown Bill")

                    # Check if there are recent updates
                    update_date = bill.get("updateDate", bill.get("introducedDate", ""))

                    if update_date:
                        try:
                            update_dt = datetime.fromisoformat(update_date.replace('Z', '+00:00'))
                            if update_dt < since_date:
                                continue
                        except:
                            pass

                    # Get bill URL
                    bill_url = f"https://www.congress.gov/bill/{current_congress}th-congress/{bill_type.lower()}-bill/{bill_number}"

                    updates.append(RemoteDocRef(
                        source_id=self.source_id,
                        remote_id=f"{current_congress}-{bill_type}-{bill_number}",
                        doc_type="bill",
                        title=bill_title,
                        url=bill_url,
                        published_ts=update_date or datetime.utcnow().isoformat(),
                        metadata={
                            "congress": current_congress,
                            "bill_type": bill_type,
                            "bill_number": bill_number,
                            "introduced_date": bill.get("introducedDate"),
                            "update_date": update_date,
                            "api_url": bill.get("url")
                        }
                    ))

            except Exception as e:
                print(f"Error listing Congress.gov bills: {e}")

        return updates[:30]  # Limit for MVP

    async def fetch_doc(
        self,
        remote_ref: RemoteDocRef
    ) -> bytes:
        """
        Fetch bill details from API
        """
        api_key = self._get_api_key()

        if not api_key:
            raise Exception("Congress.gov API key not configured")

        # Use API URL from metadata
        api_url = remote_ref.metadata.get("api_url")

        if not api_url:
            # Construct API URL
            congress = remote_ref.metadata.get("congress")
            bill_type = remote_ref.metadata.get("bill_type")
            bill_number = remote_ref.metadata.get("bill_number")
            api_url = f"{self.base_url}/bill/{congress}/{bill_type}/{bill_number}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                params = {
                    "api_key": api_key,
                    "format": "json"
                }

                response = await client.get(api_url, params=params)
                response.raise_for_status()
                return response.content

            except Exception as e:
                print(f"Error fetching bill {remote_ref.remote_id}: {e}")
                raise

    async def parse_payload(
        self,
        raw: bytes,
        remote_ref: RemoteDocRef
    ) -> ParsedDoc:
        """
        Parse Congress.gov API response
        """
        try:
            data = json.loads(raw.decode('utf-8'))
            bill_data = data.get("bill", {})

            # Extract document fields
            doc_data = {
                "source_id": self.source_id,
                "jurisdiction": "US-FED",
                "doc_type": "bill",
                "title": bill_data.get("title", remote_ref.title),
                "identifiers_json": json.dumps({
                    "congress": remote_ref.metadata.get("congress"),
                    "bill_type": remote_ref.metadata.get("bill_type"),
                    "bill_number": remote_ref.metadata.get("bill_number")
                }),
                "canonical_url": remote_ref.url
            }

            # Extract summary and text
            summary = bill_data.get("summary", {}).get("text", "")
            actions = bill_data.get("actions", {})

            # Create outline from actions
            outline = {
                "type": "bill",
                "sections": []
            }

            # Add action items to outline
            action_items = actions.get("items", []) if isinstance(actions, dict) else []
            for action in action_items[:10]:  # Limit to first 10 actions
                outline["sections"].append({
                    "date": action.get("actionDate", ""),
                    "text": action.get("text", "")[:200]
                })

            # Create normalized text
            normalized_text = f"{bill_data.get('title', '')}\n\n"
            if summary:
                normalized_text += f"Summary:\n{summary}\n\n"

            # Add recent actions
            if action_items:
                normalized_text += "Recent Actions:\n"
                for action in action_items[:5]:
                    normalized_text += f"- {action.get('actionDate', '')}: {action.get('text', '')}\n"

            # Create version data
            version_data = {
                "version_label": "current",
                "published_ts": remote_ref.published_ts,
                "normalized_text": normalized_text,
                "outline_json": json.dumps(outline),
                "snippets_json": json.dumps({
                    "summary": summary[:500] if summary else "",
                    "title": bill_data.get("title", "")[:300]
                }),
                "content_mode": "full"
            }

            return ParsedDoc(
                document=doc_data,
                versions=[version_data]
            )

        except Exception as e:
            print(f"Error parsing bill: {e}")
            raise
