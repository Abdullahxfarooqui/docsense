"""
Test tank analyzer on the production PDF
"""
import logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

import pypdf
from tank_analyzer import extract_tank_deliveries, format_tank_data_for_llm

pdf_path = "production data.pdf"

print("="*80)
print("TESTING TANK ANALYZER")
print("="*80)

# Read full PDF
with open(pdf_path, 'rb') as f:
    pdf = pypdf.PdfReader(f)
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text() + "\n"

print(f"\nExtracted {len(full_text)} characters from PDF")

# Extract tank deliveries
tank_df = extract_tank_deliveries(full_text)

if tank_df is not None and not tank_df.empty:
    print(f"\n✓ SUCCESS: Found {len(tank_df)} tank deliveries")
    print(f"✓ Unique tanks: {tank_df['Tank'].nunique()}")
    print(f"\nTank names found:")
    for tank in tank_df['Tank'].unique():
        count = len(tank_df[tank_df['Tank'] == tank])
        print(f"  - {tank}: {count} deliveries")
    
    print("\n" + "="*80)
    print("SAMPLE DATA (first 5 rows):")
    print("="*80)
    print(tank_df.head().to_string())
    
    print("\n" + "="*80)
    print("FORMATTED OUTPUT FOR LLM:")
    print("="*80)
    formatted = format_tank_data_for_llm(tank_df)
    print(formatted[:2000])  # First 2000 chars
    
else:
    print("\n✗ FAILED: No tank deliveries found")
    print("\nChecking for tank patterns in text...")
    
    import re
    tank_pattern = r'Storage_Delivery_Tank-[A-Z]:([A-Z\s]+)'
    matches = re.findall(tank_pattern, full_text[:10000], re.IGNORECASE)
    
    if matches:
        print(f"Found {len(matches)} tank patterns in first 10000 chars:")
        for match in set(matches[:10]):
            print(f"  - {match.strip()}")
    else:
        print("No tank patterns found")

print("\n" + "="*80)
