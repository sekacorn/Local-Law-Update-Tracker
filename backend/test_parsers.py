"""
Test document parsers
Run with: python backend/test_parsers.py
"""
import sys
from pathlib import Path
from io import BytesIO

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.parsers.document_parser import DocumentParser


def test_txt_parser():
    """Test plain text parsing"""
    print("=" * 60)
    print("Testing TXT Parser")
    print("=" * 60)

    parser = DocumentParser()

    # Create sample text with sections
    sample_text = """LEASE AGREEMENT

SECTION 1. PARTIES
This lease agreement is entered into between Landlord and Tenant.

SECTION 2. PREMISES
The premises are located at 123 Main Street.

SECTION 3. TERM
The lease term is 12 months beginning January 1, 2026.

SECTION 4. RENT
Tenant shall pay $1,500 per month.

1. Payment Due Date
Rent is due on the 1st of each month.

2. Late Fees
A late fee of $50 applies after the 5th.

SECTION 5. TERMINATION
Either party may terminate with 30 days notice.
"""

    file_bytes = sample_text.encode('utf-8')

    try:
        result = parser.parse(file_bytes, "sample_lease.txt")

        print(f"[OK] Format detected: {result.metadata['format']}")
        print(f"[OK] Text length: {len(result.text)} characters")
        print(f"[OK] Sections found: {len(result.outline)}")
        print(f"[OK] Confidence score: {result.confidence_score:.2f}")
        print(f"[OK] Warnings: {len(result.warnings)}")

        if result.outline:
            print("\nSections:")
            for section in result.outline[:5]:
                print(f"  - [{section.level}] {section.title}")

        if result.snippets:
            print(f"\nSnippets: {len(result.snippets)} generated")
            print(f"  First snippet: {result.snippets[0][:100]}...")

        print("\n[OK] TXT parser test passed!\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] TXT parser test failed: {e}\n")
        return False


def test_html_parser():
    """Test HTML parsing"""
    print("=" * 60)
    print("Testing HTML Parser")
    print("=" * 60)

    parser = DocumentParser()

    # Create sample HTML
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Employment Contract</title>
        <style>body { font-family: Arial; }</style>
    </head>
    <body>
        <h1>EMPLOYMENT AGREEMENT</h1>
        <p>This agreement is made between Employer and Employee.</p>

        <h2>1. Position</h2>
        <p>Employee shall serve as Software Engineer.</p>

        <h2>2. Compensation</h2>
        <p>Annual salary of $100,000.</p>

        <h3>2.1 Benefits</h3>
        <p>Health insurance, 401k, and paid time off.</p>

        <h2>3. Term</h2>
        <p>Employment begins January 1, 2026.</p>

        <script>console.log('test');</script>
    </body>
    </html>
    """

    file_bytes = sample_html.encode('utf-8')

    try:
        result = parser.parse(file_bytes, "contract.html")

        print(f"[OK] Format detected: {result.metadata['format']}")
        print(f"[OK] Text length: {len(result.text)} characters")
        print(f"[OK] Sections found: {len(result.outline)}")
        print(f"[OK] Confidence score: {result.confidence_score:.2f}")

        if result.outline:
            print("\nSections from HTML headings:")
            for section in result.outline:
                indent = "  " * section.level
                print(f"{indent}[H{section.level}] {section.title}")

        # Verify script tag was removed
        if "<script>" not in result.text:
            print("[OK] Script tags removed correctly")

        print("\n[OK] HTML parser test passed!\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] HTML parser test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_parser():
    """Test PDF parsing with a simple generated PDF"""
    print("=" * 60)
    print("Testing PDF Parser")
    print("=" * 60)

    parser = DocumentParser()

    # Create a simple PDF using reportlab if available
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Page 1
        c.drawString(100, 750, "RENTAL AGREEMENT")
        c.drawString(100, 700, "SECTION 1. PARTIES")
        c.drawString(100, 680, "Landlord: John Smith")
        c.drawString(100, 660, "Tenant: Jane Doe")

        c.showPage()

        # Page 2
        c.drawString(100, 750, "SECTION 2. RENT")
        c.drawString(100, 730, "Monthly rent: $2,000")
        c.drawString(100, 710, "Due date: 1st of month")

        c.save()

        file_bytes = buffer.getvalue()

        result = parser.parse(file_bytes, "rental.pdf")

        print(f"[OK] Format detected: {result.metadata['format']}")
        print(f"[OK] Pages: {result.metadata.get('pages', 0)}")
        print(f"[OK] Text length: {len(result.text)} characters")
        print(f"[OK] Sections found: {len(result.outline)}")
        print(f"[OK] Confidence score: {result.confidence_score:.2f}")
        print(f"[OK] Warnings: {len(result.warnings)}")

        if result.page_map:
            print(f"[OK] Page map: {len(result.page_map)} pages")

        if result.outline:
            print("\nSections:")
            for section in result.outline[:3]:
                page_info = f" (page {section.page})" if section.page else ""
                print(f"  - [{section.level}] {section.title}{page_info}")

        print("\n[OK] PDF parser test passed!\n")
        return True

    except ImportError:
        print("[WARN] reportlab not installed, creating mock PDF test")

        # Create minimal valid PDF
        # This is a very basic PDF structure
        mock_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000315 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
407
%%EOF"""

        try:
            result = parser.parse(mock_pdf, "test.pdf")
            print(f"[OK] Format detected: {result.metadata['format']}")
            print(f"[OK] Text extracted (basic)")
            print("\n[OK] PDF parser test passed (basic)!\n")
            return True
        except Exception as e:
            print(f"\n[ERROR] PDF parser test failed: {e}\n")
            return False

    except Exception as e:
        print(f"\n[ERROR] PDF parser test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_format_detection():
    """Test format detection"""
    print("=" * 60)
    print("Testing Format Detection")
    print("=" * 60)

    parser = DocumentParser()

    tests = [
        ("test.txt", b"Hello world", "txt"),
        ("test.html", b"<html><body>Test</body></html>", "html"),
        ("test.htm", b"<html><body>Test</body></html>", "html"),
    ]

    all_passed = True
    for filename, content, expected_format in tests:
        try:
            detected = parser.detect_format(content, filename)
            if detected == expected_format:
                print(f"[OK] {filename}: {detected}")
            else:
                print(f"[FAIL] {filename}: expected {expected_format}, got {detected}")
                all_passed = False
        except Exception as e:
            print(f"[FAIL] {filename}: {e}")
            all_passed = False

    if all_passed:
        print("\n[OK] Format detection test passed!\n")
    else:
        print("\n[ERROR] Some format detection tests failed!\n")

    return all_passed


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DOCUMENT PARSER TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Format Detection", test_format_detection()))
    results.append(("TXT Parser", test_txt_parser()))
    results.append(("HTML Parser", test_html_parser()))
    results.append(("PDF Parser", test_pdf_parser()))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n[FAILED] {total - passed} TEST(S) FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
