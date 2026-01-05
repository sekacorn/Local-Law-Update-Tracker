"""
Database tests
"""
import pytest
import aiosqlite
from pathlib import Path
import tempfile
import os

from app.db import Database


@pytest.fixture
async def temp_db():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        await db.initialize()
        yield db
        await db.close()


@pytest.mark.asyncio
async def test_db_initialization(temp_db):
    """Test database initialization"""
    # Check that tables exist
    tables = await temp_db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = [t["name"] for t in tables]

    assert "source" in table_names
    assert "document" in table_names
    assert "version" in table_names
    assert "change_event" in table_names
    assert "citation_span" in table_names


@pytest.mark.asyncio
async def test_migrations(temp_db):
    """Test migrations are applied"""
    migrations = await temp_db.fetch_all(
        "SELECT * FROM _migrations ORDER BY version"
    )

    assert len(migrations) >= 2
    assert migrations[0]["version"] == 1
    assert migrations[1]["version"] == 2


@pytest.mark.asyncio
async def test_insert_document(temp_db):
    """Test inserting a document"""
    import uuid
    from datetime import datetime

    doc_id = str(uuid.uuid4())

    await temp_db.execute(
        """
        INSERT INTO document (
            id, source_id, jurisdiction, doc_type,
            title, identifiers_json, canonical_url,
            first_seen_ts, last_seen_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            "federal_register",
            "US-FED",
            "executive_order",
            "Test Executive Order",
            '{"document_number": "2024-001"}',
            "https://example.com/eo/2024-001",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        )
    )

    # Verify insertion
    doc = await temp_db.fetch_one(
        "SELECT * FROM document WHERE id = ?",
        (doc_id,)
    )

    assert doc is not None
    assert doc["title"] == "Test Executive Order"
    assert doc["source_id"] == "federal_register"


@pytest.mark.asyncio
async def test_fts_search(temp_db):
    """Test full-text search"""
    import uuid
    from datetime import datetime

    # Insert a document with version
    doc_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    await temp_db.execute(
        """
        INSERT INTO document (
            id, source_id, jurisdiction, doc_type,
            title, identifiers_json, canonical_url,
            first_seen_ts, last_seen_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            "federal_register",
            "US-FED",
            "executive_order",
            "Climate Change Executive Order",
            '{"document_number": "2024-002"}',
            "https://example.com/eo/2024-002",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        )
    )

    await temp_db.execute(
        """
        INSERT INTO version (
            id, document_id, version_label, published_ts,
            fetched_ts, content_mode, normalized_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_id,
            doc_id,
            "published",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            "full",
            "This executive order addresses climate change and environmental protection."
        )
    )

    # Search for "climate"
    results = await temp_db.fetch_all(
        """
        SELECT v.id, d.title
        FROM version_fts
        JOIN version v ON v.id = version_fts.version_id
        JOIN document d ON d.id = v.document_id
        WHERE version_fts MATCH ?
        """,
        ("climate",)
    )

    assert len(results) > 0
    assert "Climate" in results[0]["title"]
