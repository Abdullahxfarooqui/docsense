"""Test what's actually being extracted from the PDF"""
import pypdf
import re

pdf = pypdf.PdfReader('production data.pdf')

print(f"Total pages: {len(pdf.pages)}\n")

for page_num in range(min(2, len(pdf.pages))):  # Check first 2 pages
    print(f"\n{'='*60}")
    print(f"PAGE {page_num + 1}")
    print('='*60)
    
    text = pdf.pages[page_num].extract_text()
    
    print(f"\nTotal length: {len(text)} chars")
    
    # Look for numbers
    numbers = re.findall(r'\d+\.?\d*', text)
    print(f"Numbers found: {len(numbers)}")
    print(f"Sample numbers: {numbers[:30]}")
    
    # Look for common production terms
    keywords = ['production', 'volume', 'oil', 'gas', 'water', 'bbl', 'mcf', 'ton']
    for keyword in keywords:
        count = text.lower().count(keyword)
        if count > 0:
            print(f"'{keyword}' appears: {count} times")
    
    # Show first 2000 chars
    print(f"\nFirst 2000 characters:")
    print(text[:2000])
    
    # Show lines with numbers
    print(f"\nLines containing numbers (first 20):")
    lines_with_nums = [line for line in text.split('\n') if re.search(r'\d', line)][:20]
    for i, line in enumerate(lines_with_nums, 1):
        print(f"{i}. {line[:100]}")
