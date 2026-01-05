"""
Check database contents
"""
import asyncio
from app.db import db


async def check_database():
    """Check what's in the database"""
    print("Checking database contents...")
    print("=" * 60)

    # Check documents
    docs = await db.fetch_all("SELECT * FROM document LIMIT 3")
    print(f"\nDocuments: {len(docs)}")
    for doc in docs:
        print(f"  - {doc['title'][:60]}")

    # Check versions
    versions = await db.fetch_all("SELECT id, document_id, normalized_text FROM version LIMIT 3")
    print(f"\nVersions: {len(versions)}")
    for version in versions:
        text_preview = (version['normalized_text'] or '')[:100]
        print(f"  - Version {version['id'][:8]}")
        print(f"    Text: {text_preview}...")

    # Check FTS
    fts_count = await db.fetch_one("SELECT COUNT(*) as count FROM version_fts")
    print(f"\nFTS Index entries: {fts_count['count']}")

    # Try a direct FTS query
    fts_results = await db.fetch_all("SELECT * FROM version_fts WHERE text MATCH 'pay' LIMIT 3")
    print(f"\nFTS search for 'pay': {len(fts_results)} results")

    # Check if FTS has any content
    sample_fts = await db.fetch_all("SELECT version_id, substr(text, 1, 100) as text_sample FROM version_fts LIMIT 3")
    print(f"\nFTS content samples:")
    for row in sample_fts:
        print(f"  - {row['text_sample'][:80]}")


if __name__ == "__main__":
    asyncio.run(check_database())
