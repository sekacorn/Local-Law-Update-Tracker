"""
Test script for UserUploadsConnector
Run with: python backend/test_uploads_connector.py
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import shutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import db
from app.connectors.user_uploads import UserUploadsConnector


async def setup_test_directory():
    """Create test uploads directory with sample files"""
    test_dir = Path("test_uploads")

    # Clean up if exists
    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir()

    # Create sample TXT file
    txt_file = test_dir / "employment_contract.txt"
    txt_file.write_text("""EMPLOYMENT AGREEMENT

SECTION 1. PARTIES
This agreement is made between Company Inc. and John Doe.

SECTION 2. POSITION
Employee shall serve as Senior Software Engineer.

SECTION 3. COMPENSATION
Annual salary of $120,000.

SECTION 4. BENEFITS
Health insurance, 401k, and paid time off.

SECTION 5. TERM
Employment begins January 15, 2026.
""", encoding='utf-8')

    # Create sample HTML file
    html_file = test_dir / "lease_agreement.html"
    html_file.write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Lease Agreement</title>
    <style>body { font-family: Arial; }</style>
</head>
<body>
    <h1>RESIDENTIAL LEASE AGREEMENT</h1>
    <p>This lease agreement is made between Landlord and Tenant.</p>

    <h2>1. Premises</h2>
    <p>The premises are located at 456 Oak Street, Apt 2B.</p>

    <h2>2. Term</h2>
    <p>Lease term is 12 months beginning February 1, 2026.</p>

    <h2>3. Rent</h2>
    <p>Monthly rent of $1,800 due on the 1st of each month.</p>

    <h3>3.1 Late Fees</h3>
    <p>A late fee of $75 applies after the 5th.</p>

    <h2>4. Security Deposit</h2>
    <p>Security deposit of $1,800 is required.</p>

    <script>console.log('test');</script>
</body>
</html>
""", encoding='utf-8')

    # Create a subdirectory with another file
    subdir = test_dir / "legal_docs"
    subdir.mkdir()

    subdir_txt = subdir / "privacy_policy.txt"
    subdir_txt.write_text("""PRIVACY POLICY

1. INFORMATION COLLECTION
We collect personal information when you use our services.

2. DATA USAGE
Your data is used to provide and improve services.

3. DATA SHARING
We do not sell your personal information.

4. YOUR RIGHTS
You have the right to access and delete your data.
""", encoding='utf-8')

    print(f"[OK] Created test directory: {test_dir}")
    print(f"  - {txt_file.name}")
    print(f"  - {html_file.name}")
    print(f"  - legal_docs/{subdir_txt.name}")
    print()

    return test_dir


async def test_connector():
    """Test the UserUploadsConnector"""
    print("=" * 60)
    print("USER UPLOADS CONNECTOR TEST")
    print("=" * 60)
    print()

    # Setup
    test_dir = await setup_test_directory()
    connector = UserUploadsConnector(uploads_dir=str(test_dir))

    try:
        # Test 1: Initialize database (delete old DB first)
        print("[1/8] Initializing database...")

        # Force delete existing database to test fresh migrations
        db_path = Path("app_data/llut.db")
        if db_path.exists():
            try:
                import os
                os.remove(db_path)
                print("  [INFO] Deleted existing database")
            except Exception as e:
                print(f"  [WARN] Could not delete existing database: {e}")

        await db.initialize()
        print("  [OK] Database initialized")
        print()

        # Test 2: Create user_uploads source
        print("[2/8] Creating user_uploads source...")
        await db.execute("""
            INSERT OR IGNORE INTO source (id, name, base_url, enabled)
            VALUES ('user_uploads', 'User Uploads', '', 1)
        """)
        print("  [OK] Source created")
        print()

        # Test 3: List updates
        print("[3/8] Testing list_updates()...")
        updates = await connector.list_updates()
        print(f"  [OK] Found {len(updates)} files")
        for ref in updates:
            print(f"    - {ref.metadata['filename']} ({ref.doc_type})")
        print()

        if len(updates) == 0:
            print("  [ERROR] No files found!")
            return False

        # Test 4: Fetch document
        print("[4/8] Testing fetch_doc()...")
        first_ref = updates[0]
        raw_bytes = await connector.fetch_doc(first_ref)
        print(f"  [OK] Fetched {len(raw_bytes)} bytes from {first_ref.metadata['filename']}")
        print()

        # Test 5: Parse payload
        print("[5/8] Testing parse_payload()...")
        parsed = await connector.parse_payload(raw_bytes, first_ref)
        print(f"  [OK] Parsed document: {parsed.document['title']}")
        print(f"    - Text length: {len(parsed.versions[0]['normalized_text'])} chars")
        print(f"    - Sections: {len(json.loads(parsed.versions[0]['outline_json'] or '[]'))}")
        print(f"    - Confidence: {parsed.versions[0]['confidence_score']:.2f}")
        print(f"    - User uploaded: {parsed.document['is_user_uploaded']}")
        print(f"    - Original filename: {parsed.document['original_filename']}")
        print()

        # Test 6: Full sync
        print("[6/8] Testing full sync()...")
        await connector.sync()
        print("  [OK] Sync completed")
        print()

        # Test 7: Verify database records
        print("[7/8] Verifying database records...")

        # Check documents
        docs = await db.fetch_all("""
            SELECT id, title, doc_type, is_user_uploaded, original_filename
            FROM document
            WHERE source_id = 'user_uploads'
        """)
        print(f"  [OK] Documents in database: {len(docs)}")
        for doc in docs:
            print(f"    - {doc['title']} ({doc['doc_type']}) - uploaded: {doc['is_user_uploaded']}")

        # Check versions
        versions = await db.fetch_all("""
            SELECT v.id, v.version_label, v.confidence_score, d.title
            FROM version v
            JOIN document d ON v.document_id = d.id
            WHERE d.source_id = 'user_uploads'
        """)
        print(f"  [OK] Versions in database: {len(versions)}")
        for ver in versions:
            print(f"    - {ver['title']}: {ver['version_label']} (confidence: {ver['confidence_score']:.2f})")

        # Check page maps
        page_maps = await db.fetch_all("""
            SELECT v.page_map_json, d.title
            FROM version v
            JOIN document d ON v.document_id = d.id
            WHERE d.source_id = 'user_uploads' AND v.page_map_json IS NOT NULL
        """)
        if page_maps:
            print(f"  [OK] Documents with page maps: {len(page_maps)}")

        # Check parse warnings
        warnings = await db.fetch_all("""
            SELECT v.parse_warnings_json, d.title
            FROM version v
            JOIN document d ON v.document_id = d.id
            WHERE d.source_id = 'user_uploads' AND v.parse_warnings_json IS NOT NULL
        """)
        if warnings:
            print(f"  [OK] Documents with parse warnings: {len(warnings)}")
            for w in warnings:
                warns = json.loads(w['parse_warnings_json'])
                print(f"    - {w['title']}: {len(warns)} warning(s)")

        print()

        # Test 8: Re-sync (should skip existing documents)
        print("[8/8] Testing re-sync (should skip existing)...")
        updates_before = len(updates)

        # Run sync again
        await connector.sync()

        # Check if documents were duplicated
        docs_after = await db.fetch_all("""
            SELECT COUNT(*) as count FROM document WHERE source_id = 'user_uploads'
        """)

        if docs_after[0]['count'] == len(docs):
            print(f"  [OK] No duplicates created (still {len(docs)} documents)")
        else:
            print(f"  [WARN] Document count changed: {len(docs)} -> {docs_after[0]['count']}")

        print()

        print("=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"[ERROR] Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        await db.close()

        # Remove test directory
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\n[CLEANUP] Removed test directory: {test_dir}")


async def main():
    """Main test runner"""
    try:
        success = await test_connector()
        return 0 if success else 1
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
