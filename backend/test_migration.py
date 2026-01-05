"""
Test script for user uploads migration
Run with: python backend/test_migration.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import db


async def test_migration():
    """Test the user uploads migration"""
    print("=" * 60)
    print("Testing User Uploads Migration (004)")
    print("=" * 60)
    print()

    # Initialize database (runs migrations)
    print("[1/6] Initializing database...")
    await db.initialize()
    print("  [OK] Database initialized")
    print()

    # Check migration was applied
    print("[2/6] Checking migration status...")
    migrations = await db.fetch_all(
        "SELECT version, name, applied_at FROM _migrations ORDER BY version"
    )
    for m in migrations:
        print(f"  Migration {m['version']}: {m['name']} (applied {m['applied_at']})")

    if len(migrations) < 4:
        print("  [ERROR] Migration 004 not applied!")
        return False
    print("  [OK] All migrations applied")
    print()

    # Check document table has new columns
    print("[3/6] Checking document table schema...")
    schema = await db.fetch_all("PRAGMA table_info(document)")
    column_names = [col['name'] for col in schema]

    expected_columns = ['is_user_uploaded', 'original_filename', 'upload_mime', 'source_path']
    for col in expected_columns:
        if col in column_names:
            print(f"  [OK] Column '{col}' exists")
        else:
            print(f"  [ERROR] Column '{col}' missing!")
            return False
    print()

    # Check version table has new columns
    print("[4/6] Checking version table schema...")
    schema = await db.fetch_all("PRAGMA table_info(version)")
    column_names = [col['name'] for col in schema]

    expected_columns = ['parse_warnings_json', 'page_map_json']
    for col in expected_columns:
        if col in column_names:
            print(f"  [OK] Column '{col}' exists")
        else:
            print(f"  [ERROR] Column '{col}' missing!")
            return False
    print()

    # Check pinned_document table exists
    print("[5/6] Checking pinned_document table...")
    tables = await db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pinned_document'"
    )
    if tables:
        print("  [OK] Table 'pinned_document' exists")

        # Check schema
        schema = await db.fetch_all("PRAGMA table_info(pinned_document)")
        column_names = [col['name'] for col in schema]
        expected = ['document_id', 'pinned_ts']
        for col in expected:
            if col in column_names:
                print(f"  [OK] Column '{col}' exists")
            else:
                print(f"  [ERROR] Column '{col}' missing!")
                return False
    else:
        print("  [ERROR] Table 'pinned_document' not found!")
        return False
    print()

    # Test pin/unpin functions
    print("[6/6] Testing pin/unpin functions...")

    # Create a test source first
    test_source_id = "test_source"
    await db.execute("""
        INSERT OR IGNORE INTO source (id, name)
        VALUES (?, 'Test Source')
    """, (test_source_id,))

    # Create a test document
    test_doc_id = "test_doc_123"
    await db.execute("""
        INSERT INTO document (id, source_id, title, first_seen_ts, last_seen_ts)
        VALUES (?, ?, 'Test Document', datetime('now'), datetime('now'))
    """, (test_doc_id, test_source_id))
    print(f"  Created test document: {test_doc_id}")

    # Test pinning
    result = await db.pin_document(test_doc_id)
    if result:
        print("  [OK] Document pinned successfully")
    else:
        print("  [ERROR] Failed to pin document")
        return False

    # Check if pinned
    is_pinned = await db.is_pinned(test_doc_id)
    if is_pinned:
        print("  [OK] Document is pinned (verified)")
    else:
        print("  [ERROR] Document not showing as pinned")
        return False

    # Try pinning again (should fail)
    result = await db.pin_document(test_doc_id)
    if not result:
        print("  [OK] Cannot pin already-pinned document (correct)")
    else:
        print("  [ERROR] Should not allow double-pinning")
        return False

    # Get pinned documents
    pinned = await db.get_pinned_documents()
    if len(pinned) == 1 and pinned[0]['id'] == test_doc_id:
        print(f"  [OK] Retrieved pinned documents: {len(pinned)} document(s)")
    else:
        print(f"  [ERROR] Expected 1 pinned document, got {len(pinned)}")
        return False

    # Test unpinning
    result = await db.unpin_document(test_doc_id)
    if result:
        print("  [OK] Document unpinned successfully")
    else:
        print("  [ERROR] Failed to unpin document")
        return False

    # Verify unpinned
    is_pinned = await db.is_pinned(test_doc_id)
    if not is_pinned:
        print("  [OK] Document is not pinned (verified)")
    else:
        print("  [ERROR] Document still showing as pinned")
        return False

    # Cleanup test document
    await db.execute("DELETE FROM document WHERE id = ?", (test_doc_id,))
    print(f"  Cleaned up test document")
    print()

    return True


async def main():
    """Main test runner"""
    try:
        success = await test_migration()

        print("=" * 60)
        if success:
            print("ALL TESTS PASSED!")
            print("=" * 60)
            return 0
        else:
            print("TESTS FAILED!")
            print("=" * 60)
            return 1

    except Exception as e:
        print()
        print("=" * 60)
        print(f"TEST ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Close database connection
        await db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
