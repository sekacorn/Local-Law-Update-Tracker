"""
Debug script to see the actual JSON structure from Federal Register
"""
import asyncio
import httpx
import json


async def check_json_structure():
    """Check the JSON structure from Federal Register API"""
    doc_number = "2025-23844"  # First document from our test

    url = f"https://www.federalregister.gov/api/v1/documents/{doc_number}.json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()

        print("JSON Structure:")
        print("=" * 60)
        print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
        print("=" * 60)
        print(f"\nTop-level keys: {list(data.keys())}")


if __name__ == "__main__":
    asyncio.run(check_json_structure())
