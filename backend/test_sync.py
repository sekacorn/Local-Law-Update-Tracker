"""
Test script to verify connectors are working
"""
import asyncio
from datetime import datetime, timedelta
from app.connectors.federal_register import FederalRegisterConnector


async def test_federal_register():
    """Test Federal Register connector"""
    print("Testing Federal Register Connector...")
    print("=" * 60)

    connector = FederalRegisterConnector()

    # Try fetching from last 90 days instead of 30
    since = (datetime.utcnow() - timedelta(days=90)).isoformat()

    print(f"Fetching Executive Orders since: {since}")

    try:
        updates = await connector.list_updates(since_ts=since)

        print(f"\nFound {len(updates)} documents")
        print("-" * 60)

        # Show first 5
        for i, doc in enumerate(updates[:5], 1):
            print(f"\n{i}. {doc.title[:100]}")
            print(f"   ID: {doc.remote_id}")
            print(f"   Published: {doc.published_ts}")
            print(f"   URL: {doc.url}")

            # Try fetching one document
            if i == 1:
                print(f"\n   Fetching full document...")
                try:
                    raw_data = await connector.fetch_doc(doc)
                    print(f"   [OK] Successfully fetched {len(raw_data)} bytes")

                    # Try parsing
                    parsed = await connector.parse_payload(raw_data, doc)
                    print(f"   [OK] Successfully parsed document")
                    print(f"   Title: {parsed.document['title'][:100]}")
                    print(f"   Versions: {len(parsed.versions)}")

                except Exception as e:
                    print(f"   [ERROR] Error: {e}")

        print("\n" + "=" * 60)
        print(f"Test completed successfully! Found {len(updates)} documents.")

    except Exception as e:
        print(f"\n[ERROR] Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_federal_register())
