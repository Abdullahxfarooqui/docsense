"""
Extract and show raw text from PDF to understand structure
"""
import pypdf

pdf_path = "production data.pdf"

print("="*80)
print("RAW PDF TEXT SAMPLE")
print("="*80)

with open(pdf_path, 'rb') as f:
    pdf = pypdf.PdfReader(f)
    
    # Get first page
    page1_text = pdf.pages[0].extract_text()
    
    # Show first 3000 characters
    print("\nFIRST 3000 CHARACTERS OF PAGE 1:")
    print("-" * 80)
    print(page1_text[:3000])
    
    print("\n" + "="*80)
    
    # Search for HALINI specifically
    if "HALINI" in page1_text or "halini" in page1_text.lower():
        print("\n✓ FOUND 'HALINI' in page 1!")
        # Show context around HALINI
        pos = page1_text.upper().find("HALINI")
        if pos >= 0:
            print("\nContext around HALINI:")
            print(page1_text[max(0, pos-200):pos+200])
    else:
        print("\n✗ 'HALINI' not found in page 1")
    
    # Check if HALINI exists anywhere in the document
    print("\n" + "="*80)
    print("SEARCHING ALL PAGES FOR 'HALINI'...")
    print("-" * 80)
    
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if "HALINI" in text.upper():
            print(f"\n✓ Found on page {i+1}")
            pos = text.upper().find("HALINI")
            print(f"Context: {text[max(0, pos-150):pos+150]}")
            break
    else:
        print("✗ 'HALINI' not found in any page")
