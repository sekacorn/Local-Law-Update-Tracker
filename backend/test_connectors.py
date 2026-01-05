"""
Test all connectors with demo API keys
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.connectors.congress_gov import CongressGovConnector
from app.connectors.govinfo import GovInfoConnector
from app.connectors.scotus import ScotusConnector
from app.connectors.federal_register import FederalRegisterConnector


async def test_congress_gov():
    """Test Congress.gov connector"""
    print("\n" + "="*60)
    print("TESTING CONGRESS.GOV CONNECTOR")
    print("="*60)

    connector = CongressGovConnector()

    try:
        print("Listing recent bills...")
        updates = await connector.list_updates()
        print(f"[OK] Found {len(updates)} bills")

        if updates:
            print(f"\nFirst bill: {updates[0].title[:80]}...")
            print(f"URL: {updates[0].url}")
            print(f"Remote ID: {updates[0].remote_id}")

            # Try fetching the first bill
            print("\nFetching full bill data...")
            raw_data = await connector.fetch_doc(updates[0])
            print(f"[OK] Downloaded {len(raw_data)} bytes")

            # Try parsing
            print("Parsing bill data...")
            parsed = await connector.parse_payload(raw_data, updates[0])
            print(f"[OK] Parsed successfully")
            print(f"Title: {parsed.document['title'][:100]}")
            print(f"Versions: {len(parsed.versions)}")

            return True
        else:
            print("[WARN]  No bills found (may need valid API key)")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def test_govinfo():
    """Test GovInfo connector"""
    print("\n" + "="*60)
    print("TESTING GOVINFO CONNECTOR")
    print("="*60)

    connector = GovInfoConnector()

    try:
        print("Listing recent publications...")
        updates = await connector.list_updates()
        print(f"[OK] Found {len(updates)} documents")

        if updates:
            print(f"\nFirst document: {updates[0].title[:80]}...")
            print(f"Type: {updates[0].doc_type}")
            print(f"URL: {updates[0].url}")

            # Try fetching the first document
            print("\nFetching document summary...")
            raw_data = await connector.fetch_doc(updates[0])
            print(f"[OK] Downloaded {len(raw_data)} bytes")

            # Try parsing
            print("Parsing document data...")
            parsed = await connector.parse_payload(raw_data, updates[0])
            print(f"[OK] Parsed successfully")
            print(f"Title: {parsed.document['title'][:100]}")

            return True
        else:
            print("[WARN]  No documents found")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scotus():
    """Test SCOTUS connector"""
    print("\n" + "="*60)
    print("TESTING SCOTUS CONNECTOR")
    print("="*60)

    connector = ScotusConnector()

    try:
        print("Scraping Supreme Court opinions...")
        updates = await connector.list_updates()
        print(f"[OK] Found {len(updates)} opinions")

        if updates:
            print(f"\nFirst opinion: {updates[0].title[:80]}...")
            print(f"Case number: {updates[0].metadata.get('case_number')}")
            print(f"PDF URL: {updates[0].url}")

            # Note: Not fetching PDF to avoid large downloads
            print("\n[WARN]  Skipping PDF download to save bandwidth")
            print("(PDF fetching and parsing is implemented)")

            return True
        else:
            print("[WARN]  No opinions found")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_federal_register():
    """Test Federal Register connector (already working)"""
    print("\n" + "="*60)
    print("TESTING FEDERAL REGISTER CONNECTOR (Already Working)")
    print("="*60)

    connector = FederalRegisterConnector()

    try:
        print("Listing recent Executive Orders...")
        updates = await connector.list_updates()
        print(f"[OK] Found {len(updates)} documents")

        if updates:
            print(f"\nFirst document: {updates[0].title[:80]}...")
            print(f"Type: {updates[0].doc_type}")

            return True
        else:
            print("[WARN]  No documents found")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def main():
    """Run all connector tests"""
    print("\nCONNECTOR TEST SUITE")
    print("Testing all data source connectors...")

    results = {}

    # Test each connector
    results['federal_register'] = await test_federal_register()
    results['congress_gov'] = await test_congress_gov()
    results['govinfo'] = await test_govinfo()
    results['scotus'] = await test_scotus()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for connector, passed in results.items():
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{connector:20s} : {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\nAll connectors working!")
    elif passed > 0:
        print(f"\n{total - passed} connector(s) need attention")
    else:
        print("\nAll connectors failed - check API keys and network")


if __name__ == "__main__":
    asyncio.run(main())
