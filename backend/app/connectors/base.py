"""
Base connector class
All source connectors must inherit from this
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RemoteDocRef:
    """Reference to a remote document"""
    source_id: str
    remote_id: str  # External ID from the source
    doc_type: str
    title: str
    url: str
    published_ts: str
    metadata: Dict[str, Any]


@dataclass
class ParsedDoc:
    """Parsed document with versions"""
    document: Dict[str, Any]  # Document table fields
    versions: List[Dict[str, Any]]  # Version table fields


class Connector(ABC):
    """Base class for source connectors"""

    def __init__(self):
        self.source_id: str = ""
        self.source_name: str = ""
        self.base_url: str = ""

    @abstractmethod
    async def list_updates(
        self,
        since_ts: Optional[str] = None
    ) -> List[RemoteDocRef]:
        """
        List available updates since the given timestamp
        Returns list of remote document references
        """
        pass

    @abstractmethod
    async def fetch_doc(
        self,
        remote_ref: RemoteDocRef
    ) -> bytes:
        """
        Fetch raw document content (PDF, HTML, JSON, etc.)
        Returns raw bytes
        """
        pass

    @abstractmethod
    async def parse_payload(
        self,
        raw: bytes,
        remote_ref: RemoteDocRef
    ) -> ParsedDoc:
        """
        Parse raw payload into structured document
        Returns ParsedDoc with document and version data
        """
        pass

    def get_canonical_url(self, remote_ref: RemoteDocRef) -> str:
        """Get canonical URL for a document"""
        return remote_ref.url

    async def sync(
        self,
        progress_callback: Optional[Callable] = None
    ):
        """
        Run sync process for this connector
        Fetches updates and stores them in database
        """
        from ..db import db
        import uuid
        import json
        import hashlib

        try:
            # Get last sync time
            source_row = await db.fetch_one(
                "SELECT last_sync_ts FROM source WHERE id = ?",
                (self.source_id,)
            )

            since_ts = source_row["last_sync_ts"] if source_row else None

            # Update progress
            if progress_callback:
                progress_callback("listing", 0, 0)

            # List updates
            updates = await self.list_updates(since_ts)

            total = len(updates)
            if progress_callback:
                progress_callback("fetching", 0, total)

            # Process each update
            for idx, remote_ref in enumerate(updates):
                try:
                    # Check if document already exists
                    existing_doc = await db.fetch_one(
                        """
                        SELECT id FROM document
                        WHERE source_id = ? AND identifiers_json LIKE ?
                        """,
                        (self.source_id, f'%"{remote_ref.remote_id}"%')
                    )

                    # Fetch document content
                    raw_content = await self.fetch_doc(remote_ref)

                    # Parse document
                    parsed = await self.parse_payload(raw_content, remote_ref)

                    # Store or update document
                    if existing_doc:
                        doc_id = existing_doc["id"]
                    else:
                        doc_id = str(uuid.uuid4())
                        await db.execute(
                            """
                            INSERT INTO document (
                                id, source_id, jurisdiction, doc_type,
                                title, identifiers_json, canonical_url,
                                first_seen_ts, last_seen_ts,
                                is_user_uploaded, original_filename, upload_mime, source_path
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                doc_id,
                                parsed.document["source_id"],
                                parsed.document.get("jurisdiction"),
                                parsed.document.get("doc_type"),
                                parsed.document.get("title"),
                                parsed.document.get("identifiers_json"),
                                parsed.document.get("canonical_url"),
                                datetime.utcnow().isoformat(),
                                datetime.utcnow().isoformat(),
                                parsed.document.get("is_user_uploaded", False),
                                parsed.document.get("original_filename"),
                                parsed.document.get("upload_mime"),
                                parsed.document.get("source_path")
                            )
                        )

                    # Store versions
                    for version_data in parsed.versions:
                        version_id = str(uuid.uuid4())

                        # Calculate content hash
                        content_hash = hashlib.sha256(
                            (version_data.get("normalized_text") or "").encode()
                        ).hexdigest()

                        await db.execute(
                            """
                            INSERT INTO version (
                                id, document_id, version_label, published_ts,
                                fetched_ts, content_mode, content_hash,
                                normalized_text, outline_json, snippets_json,
                                parse_warnings_json, page_map_json, confidence_score
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                version_id,
                                doc_id,
                                version_data.get("version_label", "default"),
                                version_data.get("published_ts"),
                                datetime.utcnow().isoformat(),
                                version_data.get("content_mode", "full"),
                                content_hash,
                                version_data.get("normalized_text"),
                                version_data.get("outline_json"),
                                version_data.get("snippets_json"),
                                version_data.get("parse_warnings_json"),
                                version_data.get("page_map_json"),
                                version_data.get("confidence_score", 1.0)
                            )
                        )

                        # Create change event
                        change_id = str(uuid.uuid4())
                        await db.execute(
                            """
                            INSERT INTO change_event (
                                id, document_id, new_version_id,
                                change_type, summary, created_ts
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                change_id,
                                doc_id,
                                version_id,
                                "new_version" if existing_doc else "new_doc",
                                f"Added {version_data.get('version_label', 'version')}",
                                datetime.utcnow().isoformat()
                            )
                        )

                except Exception as e:
                    print(f"Error processing {remote_ref.remote_id}: {e}")
                    continue

                # Update progress
                if progress_callback:
                    progress_callback("fetching", idx + 1, total)

            # Update last sync time
            await db.execute(
                "UPDATE source SET last_sync_ts = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), self.source_id)
            )

            if progress_callback:
                progress_callback("completed", total, total)

        except Exception as e:
            if progress_callback:
                progress_callback("failed", 0, 0)
            raise e
