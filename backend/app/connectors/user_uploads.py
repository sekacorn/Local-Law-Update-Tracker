"""
User Uploads connector
Watches a directory for user-uploaded documents (PDF, DOCX, TXT, HTML)
"""
import json
import hashlib
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .base import Connector, RemoteDocRef, ParsedDoc
from ..parsers.document_parser import DocumentParser


class UserUploadsConnector(Connector):
    """Connector for user-uploaded documents"""

    def __init__(self, uploads_dir: str = None):
        super().__init__()
        self.source_id = "user_uploads"
        self.source_name = "User Uploads"
        self.base_url = ""  # Not applicable for local files

        # Default uploads directory if not specified
        if uploads_dir is None:
            uploads_dir = str(Path.cwd() / "user_uploads")

        self.uploads_dir = Path(uploads_dir)
        self.parser = DocumentParser()

    async def list_updates(
        self,
        since_ts: Optional[str] = None
    ) -> List[RemoteDocRef]:
        """
        Scan uploads directory for new/modified files

        Args:
            since_ts: ISO timestamp - only return files modified after this time

        Returns:
            List of RemoteDocRef for each valid document file
        """
        updates = []

        # Ensure uploads directory exists
        if not self.uploads_dir.exists():
            self.uploads_dir.mkdir(parents=True, exist_ok=True)
            return []

        # Parse since_ts if provided
        since_datetime = None
        if since_ts:
            try:
                since_datetime = datetime.fromisoformat(since_ts.replace('Z', '+00:00'))
            except Exception:
                since_datetime = None

        # Walk through uploads directory
        for file_path in self.uploads_dir.rglob('*'):
            # Skip directories
            if not file_path.is_file():
                continue

            # Check file extension
            ext = file_path.suffix.lower().lstrip('.')
            if ext not in self.parser.SUPPORTED_FORMATS:
                continue

            # Check modification time
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if since_datetime and mod_time <= since_datetime:
                continue

            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.parser.MAX_FILE_SIZE:
                print(f"[WARN] File too large, skipping: {file_path.name} ({file_size} bytes)")
                continue

            if file_size == 0:
                print(f"[WARN] Empty file, skipping: {file_path.name}")
                continue

            # Create remote reference
            # Use file path hash as remote_id for uniqueness
            relative_path = file_path.relative_to(self.uploads_dir)
            remote_id = hashlib.md5(str(relative_path).encode()).hexdigest()

            updates.append(RemoteDocRef(
                source_id=self.source_id,
                remote_id=remote_id,
                doc_type=ext,  # pdf, docx, txt, html
                title=file_path.stem,  # Filename without extension
                url=str(file_path.absolute()),  # Local file path
                published_ts=mod_time.isoformat(),
                metadata={
                    "filename": file_path.name,
                    "relative_path": str(relative_path),
                    "absolute_path": str(file_path.absolute()),
                    "file_size": file_size,
                    "modified_ts": mod_time.isoformat(),
                    "extension": ext
                }
            ))

        return updates

    async def fetch_doc(
        self,
        remote_ref: RemoteDocRef
    ) -> bytes:
        """
        Read document file from disk

        Args:
            remote_ref: Reference to the local file

        Returns:
            Raw file bytes
        """
        file_path = Path(remote_ref.metadata["absolute_path"])

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")

    async def parse_payload(
        self,
        raw: bytes,
        remote_ref: RemoteDocRef
    ) -> ParsedDoc:
        """
        Parse uploaded document using DocumentParser

        Args:
            raw: Raw file bytes
            remote_ref: Reference to the file

        Returns:
            ParsedDoc with document and version data
        """
        filename = remote_ref.metadata["filename"]
        file_ext = remote_ref.metadata["extension"]

        try:
            # Parse document using DocumentParser
            parsed = self.parser.parse(raw, filename, format_hint=file_ext)

            # Create document data
            doc_data = {
                "source_id": self.source_id,
                "jurisdiction": None,  # User uploads don't have jurisdiction
                "doc_type": file_ext,
                "title": remote_ref.title,
                "identifiers_json": json.dumps({
                    "remote_id": remote_ref.remote_id,
                    "filename": filename,
                    "path": remote_ref.metadata["relative_path"]
                }),
                "canonical_url": remote_ref.metadata["absolute_path"],
                # User upload specific fields (from migration 004)
                "is_user_uploaded": True,
                "original_filename": filename,
                "upload_mime": parsed.metadata.get('format', file_ext),
                "source_path": remote_ref.metadata["relative_path"]
            }

            # Prepare outline JSON
            outline_data = []
            for section in parsed.outline:
                outline_data.append({
                    "level": section.level,
                    "title": section.title,
                    "start_char": section.start_char,
                    "end_char": section.end_char,
                    "page": section.page
                })

            # Create version data
            version_data = {
                "version_label": "uploaded",
                "published_ts": remote_ref.published_ts,
                "normalized_text": parsed.text,
                "outline_json": json.dumps(outline_data) if outline_data else None,
                "snippets_json": json.dumps(parsed.snippets) if parsed.snippets else None,
                "content_mode": "full",
                "raw_path": None,  # Could cache raw file if needed
                # New fields from migration 004
                "parse_warnings_json": json.dumps(parsed.warnings) if parsed.warnings else None,
                "page_map_json": json.dumps(parsed.page_map) if parsed.page_map else None,
                "confidence_score": parsed.confidence_score
            }

            return ParsedDoc(
                document=doc_data,
                versions=[version_data]
            )

        except Exception as e:
            # If parsing fails, create a minimal document entry with error info
            print(f"[ERROR] Failed to parse {filename}: {e}")

            doc_data = {
                "source_id": self.source_id,
                "jurisdiction": None,
                "doc_type": file_ext,
                "title": f"{remote_ref.title} (parse failed)",
                "identifiers_json": json.dumps({
                    "remote_id": remote_ref.remote_id,
                    "filename": filename
                }),
                "canonical_url": remote_ref.metadata["absolute_path"],
                "is_user_uploaded": True,
                "original_filename": filename,
                "upload_mime": file_ext,
                "source_path": remote_ref.metadata["relative_path"]
            }

            version_data = {
                "version_label": "uploaded",
                "published_ts": remote_ref.published_ts,
                "normalized_text": f"[Parse Error: {str(e)}]",
                "outline_json": None,
                "snippets_json": None,
                "content_mode": "thin",
                "raw_path": None,
                "parse_warnings_json": json.dumps([f"Parse failed: {str(e)}"]),
                "page_map_json": None,
                "confidence_score": 0.0
            }

            return ParsedDoc(
                document=doc_data,
                versions=[version_data]
            )

    def get_canonical_url(self, remote_ref: RemoteDocRef) -> str:
        """Get canonical URL (file path) for a document"""
        return remote_ref.metadata["absolute_path"]
