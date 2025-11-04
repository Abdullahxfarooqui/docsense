"""
Quick test to see what tank names and products are in the PDF
"""
import pypdf
import re

pdf_path = "production data.pdf"

print("="*60)
print("EXTRACTING TANK NAMES AND PRODUCTS FROM PDF")
print("="*60)

# Read PDF
with open(pdf_path, 'rb') as f:
    pdf = pypdf.PdfReader(f)
    all_text = ""
    for page in pdf.pages[:2]:  # Check first 2 pages
        all_text += page.extract_text()

# Find tank patterns
print("\n1. TANK NAMES (searching for 'tank' patterns):")
print("-" * 60)
tank_patterns = [
    r'Storage[_\s]+Delivery[_\s]+Tank[_\s]*-[_\s]*C:([^\s:]+)',
    r'tank[_\s]*-[_\s]*C:([^\s:]+)',
    r'Tank[:\s]+([A-Z][A-Z\s]+)',
]

for pattern in tank_patterns:
    matches = re.findall(pattern, all_text, re.IGNORECASE)
    if matches:
        print(f"Pattern: {pattern}")
        print(f"Found: {set(matches[:20])}")
        print()

# Find product types
print("\n2. PRODUCT TYPES:")
print("-" * 60)
product_patterns = [
    r'PRODUCT[_\s]+(\w+)',
    r'Product[:\s]+(\w+)',
]

for pattern in product_patterns:
    matches = re.findall(pattern, all_text, re.IGNORECASE)
    if matches:
        print(f"Pattern: {pattern}")
        unique_products = [m for m in set(matches) if m not in ['TEXT', 'XFER', 'ITEM', 'ID', 'NULL']]
        print(f"Found: {unique_products[:10]}")
        print()

# Find location/item names
print("\n3. ITEM NAMES:")
print("-" * 60)
item_pattern = r'ITEM_NAME[_\s]+([^\n:]+)'
matches = re.findall(item_pattern, all_text, re.IGNORECASE)
if matches:
    print(f"Found {len(matches)} items:")
    for item in list(set(matches))[:10]:
        print(f"  - {item.strip()}")

# Find volumes with context
print("\n4. SAMPLE VOLUMES WITH CONTEXT:")
print("-" * 60)
# Get a chunk with volumes
vol_pattern = r'.{0,100}(\d+\.?\d*)\s*bbl.{0,100}'
matches = re.findall(vol_pattern, all_text, re.IGNORECASE)
if matches:
    print(f"Found {len(matches)} volume measurements")
    print("\nFirst 3 examples:")
    for match in list(set(matches))[:3]:
        print(f"  {match}")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
