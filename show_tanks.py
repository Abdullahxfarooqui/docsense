import logging
logging.basicConfig(level=logging.WARNING)
import pypdf
from tank_analyzer import extract_tank_deliveries

pdf = pypdf.PdfReader(open('production data.pdf', 'rb'))
text = ''.join([p.extract_text() for p in pdf.pages])
df = extract_tank_deliveries(text)

print(f'Found {len(df)} deliveries from {df["Tank"].nunique()} tanks\n')
print('Tank Summary:')
for tank in sorted(df['Tank'].unique()):
    tank_data = df[df['Tank'] == tank]
    total_vol = tank_data['Liquid_Volume_bbl'].sum()
    print(f'  {tank}: {len(tank_data)} deliveries, {total_vol:.2f} bbl')
