"""
Test Script for V3.6 Structured Data Parsing

This script tests the new structured data parsing functionality.
"""

import pandas as pd
import io

# Create test data
test_data = {
    'Tank': ['TAIMUR', 'LPG', 'CONDEN', 'OIL'],
    'Pressure': [None, 327.07, 0, 412.5],
    'Temperature': [301.911, None, 285.4, 310.2],
    'Volume': [1500, 2300, None, 1800],
    'dAPI': [42.3, 38.1, None, 40.5]
}

df = pd.DataFrame(test_data)

# Save to Excel
excel_path = 'test_production_data.xlsx'
df.to_excel(excel_path, index=False)
print(f"✅ Created test Excel file: {excel_path}")

# Save to CSV
csv_path = 'test_production_data.csv'
df.to_csv(csv_path, index=False)
print(f"✅ Created test CSV file: {csv_path}")

# Display data
print("\n📊 Test Data:")
print(df.to_markdown(index=False))

print("\n📝 Test Instructions:")
print("1. Upload the test file(s) to DocSense")
print("2. Try query: 'Extract all data at each location'")
print("3. Verify output uses actual names (TAIMUR, LPG, CONDEN, OIL)")
print("4. Verify NULL values appear with correct notes")
print("5. Verify exact numeric values (327.07, not 327.1)")
