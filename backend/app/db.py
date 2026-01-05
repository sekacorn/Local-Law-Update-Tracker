"""
Database management for LLUT
SQLite with FTS5 full-text search
"""
import sqlite3
import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from .config import settings


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> aiosqlite.Connection:
        """Get or create database connection"""
        if self._conn is None:
            self._conn = await aiosqlite.connect(
                str(self.db_path),
                isolation_level=None  # Autocommit mode
            )
            # Enable foreign keys
            await self._conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            await self._conn.execute("PRAGMA journal_mode = WAL")

        return self._conn

    async def close(self):
        """Close database connection"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        conn = await self.connect()
        try:
            await conn.execute("BEGIN")
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query"""
        conn = await self.connect()
        return await conn.execute(query, params)

    async def execute_many(self, query: str, params_list: List[tuple]) -> aiosqlite.Cursor:
        """Execute a query with multiple parameter sets"""
        conn = await self.connect()
        return await conn.executemany(query, params_list)

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one row as dict"""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dicts"""
        conn = await self.connect()
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def initialize(self):
        """Initialize database schema"""
        # Run migrations
        await self.run_migrations()

    async def run_migrations(self):
        """Run database migrations"""
        conn = await self.connect()

        # Create migrations table if it doesn't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)

        # Get current version
        cursor = await conn.execute(
            "SELECT MAX(version) as version FROM _migrations"
        )
        row = await cursor.fetchone()
        current_version = row[0] if row[0] is not None else 0

        # Apply migrations
        migrations = self._get_migrations()
        for version, name, sql in migrations:
            if version > current_version:
                print(f"Applying migration {version}: {name}")
                await conn.executescript(sql)
                await conn.execute(
                    "INSERT INTO _migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (version, name, datetime.utcnow().isoformat())
                )
                await conn.commit()

    def _get_migrations(self) -> List[tuple]:
        """Get list of migrations (version, name, sql)"""
        return [
            (1, "initial_schema", self._migration_001_initial_schema()),
            (2, "fts_index", self._migration_002_fts_index()),
            (3, "fix_fts_index", self._migration_003_fix_fts_index()),
            (4, "user_uploads", self._migration_004_user_uploads()),
        ]

    def _migration_001_initial_schema(self) -> str:
        """Migration 001: Create initial schema"""
        return """
        -- Source table
        CREATE TABLE IF NOT EXISTS source (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            base_url TEXT,
            auth_type TEXT DEFAULT 'none',
            enabled INTEGER DEFAULT 1,
            poll_interval_minutes INTEGER DEFAULT 1440,
            last_sync_ts TEXT
        );

        -- Document table
        CREATE TABLE IF NOT EXISTS document (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            jurisdiction TEXT,
            doc_type TEXT,
            title TEXT,
            identifiers_json TEXT,
            canonical_url TEXT,
            first_seen_ts TEXT NOT NULL,
            last_seen_ts TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES source(id)
        );

        -- Version table
        CREATE TABLE IF NOT EXISTS version (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            version_label TEXT,
            published_ts TEXT,
            fetched_ts TEXT NOT NULL,
            content_mode TEXT DEFAULT 'full',
            content_hash TEXT,
            raw_path TEXT,
            normalized_text TEXT,
            outline_json TEXT,
            snippets_json TEXT,
            FOREIGN KEY (document_id) REFERENCES document(id)
        );

        -- Change event table
        CREATE TABLE IF NOT EXISTS change_event (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            old_version_id TEXT,
            new_version_id TEXT,
            change_type TEXT NOT NULL,
            summary TEXT,
            created_ts TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES document(id),
            FOREIGN KEY (old_version_id) REFERENCES version(id),
            FOREIGN KEY (new_version_id) REFERENCES version(id)
        );

        -- Citation span table
        CREATE TABLE IF NOT EXISTS citation_span (
            id TEXT PRIMARY KEY,
            version_id TEXT NOT NULL,
            heading TEXT,
            page_number INTEGER,
            start_char INTEGER,
            end_char INTEGER,
            FOREIGN KEY (version_id) REFERENCES version(id)
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_document_source ON document(source_id);
        CREATE INDEX IF NOT EXISTS idx_document_type ON document(doc_type);
        CREATE INDEX IF NOT EXISTS idx_version_document ON version(document_id);
        CREATE INDEX IF NOT EXISTS idx_version_published ON version(published_ts);
        CREATE INDEX IF NOT EXISTS idx_change_event_document ON change_event(document_id);
        CREATE INDEX IF NOT EXISTS idx_change_event_created ON change_event(created_ts);

        -- Insert default sources
        INSERT OR IGNORE INTO source (id, name, base_url, enabled, poll_interval_minutes)
        VALUES
            ('congress_gov', 'Congress.gov', 'https://api.congress.gov/v3', 1, 1440),
            ('govinfo', 'GovInfo', 'https://api.govinfo.gov', 1, 1440),
            ('federal_register', 'Federal Register', 'https://www.federalregister.gov/api/v1', 1, 1440),
            ('scotus', 'Supreme Court', 'https://www.supremecourt.gov', 1, 1440);
        """

    def _migration_002_fts_index(self) -> str:
        """Migration 002: Create FTS5 full-text search index"""
        return """
        -- Create FTS5 virtual table for full-text search
        CREATE VIRTUAL TABLE IF NOT EXISTS version_fts USING fts5(
            version_id UNINDEXED,
            title,
            text,
            content='version',
            content_rowid='rowid'
        );

        -- Triggers to keep FTS in sync with version table
        CREATE TRIGGER IF NOT EXISTS version_fts_insert AFTER INSERT ON version BEGIN
            INSERT INTO version_fts(rowid, version_id, title, text)
            SELECT
                NEW.rowid,
                NEW.id,
                (SELECT title FROM document WHERE id = NEW.document_id),
                COALESCE(NEW.normalized_text, NEW.snippets_json, '');
        END;

        CREATE TRIGGER IF NOT EXISTS version_fts_update AFTER UPDATE ON version BEGIN
            UPDATE version_fts
            SET title = (SELECT title FROM document WHERE id = NEW.document_id),
                text = COALESCE(NEW.normalized_text, NEW.snippets_json, '')
            WHERE rowid = NEW.rowid;
        END;

        CREATE TRIGGER IF NOT EXISTS version_fts_delete AFTER DELETE ON version BEGIN
            DELETE FROM version_fts WHERE rowid = OLD.rowid;
        END;
        """

    def _migration_003_fix_fts_index(self) -> str:
        """Migration 003: Fix FTS5 index to use simpler schema"""
        return """
        -- Drop old FTS table and triggers
        DROP TRIGGER IF EXISTS version_fts_insert;
        DROP TRIGGER IF EXISTS version_fts_update;
        DROP TRIGGER IF EXISTS version_fts_delete;
        DROP TABLE IF EXISTS version_fts;

        -- Create simpler FTS5 virtual table (self-contained)
        CREATE VIRTUAL TABLE version_fts USING fts5(
            version_id,
            title,
            text
        );

        -- Populate FTS from existing data
        INSERT INTO version_fts(version_id, title, text)
        SELECT
            v.id,
            d.title,
            COALESCE(v.normalized_text, v.snippets_json, '')
        FROM version v
        JOIN document d ON d.id = v.document_id;

        -- Triggers to keep FTS in sync
        CREATE TRIGGER version_fts_insert AFTER INSERT ON version BEGIN
            INSERT INTO version_fts(version_id, title, text)
            SELECT
                NEW.id,
                (SELECT title FROM document WHERE id = NEW.document_id),
                COALESCE(NEW.normalized_text, NEW.snippets_json, '');
        END;

        CREATE TRIGGER version_fts_update AFTER UPDATE ON version BEGIN
            UPDATE version_fts
            SET title = (SELECT title FROM document WHERE id = NEW.document_id),
                text = COALESCE(NEW.normalized_text, NEW.snippets_json, '')
            WHERE version_id = NEW.id;
        END;

        CREATE TRIGGER version_fts_delete AFTER DELETE ON version BEGIN
            DELETE FROM version_fts WHERE version_id = OLD.id;
        END;
        """

    def _migration_004_user_uploads(self) -> str:
        """Migration 004: Add user uploads support"""
        return """
        -- Add user upload fields to document table
        ALTER TABLE document ADD COLUMN is_user_uploaded INTEGER DEFAULT 0;
        ALTER TABLE document ADD COLUMN original_filename TEXT;
        ALTER TABLE document ADD COLUMN upload_mime TEXT;
        ALTER TABLE document ADD COLUMN source_path TEXT;

        -- Add version metadata fields
        ALTER TABLE version ADD COLUMN parse_warnings_json TEXT;
        ALTER TABLE version ADD COLUMN page_map_json TEXT;
        ALTER TABLE version ADD COLUMN confidence_score REAL DEFAULT 1.0;

        -- Create pinned_document table
        CREATE TABLE IF NOT EXISTS pinned_document (
            document_id TEXT PRIMARY KEY,
            pinned_ts TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES document(id) ON DELETE CASCADE
        );

        -- Create index for faster pinned document lookups
        CREATE INDEX IF NOT EXISTS idx_pinned_document_ts ON pinned_document(pinned_ts DESC);

        -- Create index for user uploads
        CREATE INDEX IF NOT EXISTS idx_document_user_uploaded ON document(is_user_uploaded) WHERE is_user_uploaded = 1;

        -- Create index for upload mime types
        CREATE INDEX IF NOT EXISTS idx_document_upload_mime ON document(upload_mime) WHERE upload_mime IS NOT NULL;
        """

    # User Uploads Helper Methods

    async def pin_document(self, doc_id: str) -> bool:
        """
        Pin a document for persistent storage

        Args:
            doc_id: Document ID to pin

        Returns:
            True if pinned successfully, False if already pinned or doesn't exist
        """
        try:
            # Check if document exists
            doc = await self.fetch_one(
                "SELECT id FROM document WHERE id = ?",
                (doc_id,)
            )
            if not doc:
                return False

            # Check if already pinned
            existing = await self.fetch_one(
                "SELECT document_id FROM pinned_document WHERE document_id = ?",
                (doc_id,)
            )
            if existing:
                return False

            # Pin the document
            await self.execute(
                "INSERT INTO pinned_document (document_id, pinned_ts) VALUES (?, ?)",
                (doc_id, datetime.utcnow().isoformat())
            )
            return True
        except Exception as e:
            print(f"Error pinning document {doc_id}: {e}")
            return False

    async def unpin_document(self, doc_id: str) -> bool:
        """
        Unpin a document

        Args:
            doc_id: Document ID to unpin

        Returns:
            True if unpinned successfully, False if not pinned
        """
        try:
            cursor = await self.execute(
                "DELETE FROM pinned_document WHERE document_id = ?",
                (doc_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error unpinning document {doc_id}: {e}")
            return False

    async def get_pinned_documents(self) -> List[Dict[str, Any]]:
        """
        Get all pinned documents

        Returns:
            List of pinned documents with metadata
        """
        return await self.fetch_all("""
            SELECT
                d.id,
                d.source_id,
                d.jurisdiction,
                d.doc_type,
                d.title,
                d.is_user_uploaded,
                d.original_filename,
                p.pinned_ts
            FROM pinned_document p
            JOIN document d ON d.id = p.document_id
            ORDER BY p.pinned_ts DESC
        """)

    async def is_pinned(self, doc_id: str) -> bool:
        """
        Check if a document is pinned

        Args:
            doc_id: Document ID to check

        Returns:
            True if pinned, False otherwise
        """
        result = await self.fetch_one(
            "SELECT 1 FROM pinned_document WHERE document_id = ?",
            (doc_id,)
        )
        return result is not None

    async def reset(self):
        """Reset database - delete all data and recreate schema"""
        if self._conn:
            await self.close()

        # Delete database file
        if self.db_path.exists():
            self.db_path.unlink()

        # Delete WAL files
        wal_file = Path(str(self.db_path) + "-wal")
        shm_file = Path(str(self.db_path) + "-shm")
        if wal_file.exists():
            wal_file.unlink()
        if shm_file.exists():
            shm_file.unlink()

        # Reinitialize
        await self.initialize()


# Global database instance
db = Database()
