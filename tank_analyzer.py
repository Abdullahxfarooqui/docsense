"""
Tank Data Analyzer - Extract and organize tank-specific deliveries
"""

import re
import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def extract_tank_deliveries(text: str) -> pd.DataFrame:
    """
    Extract all tank deliveries with associated volumes.
    
    Args:
        text: Full PDF text
        
    Returns:
        DataFrame with tank name, ticket, volume, product for each delivery
    """
    records = []
    
    # Pattern to find tank delivery blocks
    # Actual format: "TANK Storage_Del ivery_Ta nk-C:MARI DEEP"
    # Match "TANK" then optional text then "-X:" then tank name
    tank_pattern = r'TANK\s+Storage[^\-]+\-([A-Z]):\s*([A-Z][A-Za-z\s]+?)(?:\d{2}:|\s{2,})'
    
    # Find all tank names
    tank_matches = list(re.finditer(tank_pattern, text, re.IGNORECASE))
    logger.info(f"Found {len(tank_matches)} tank pattern matches")
    
    for match in tank_matches:
        tank_type = match.group(1)  # C, O, etc.
        tank_name = match.group(2).strip()
        pos = match.start()
        
        # Get surrounding context (next 1000 chars after tank name)
        context = text[pos:pos+1000]
        
        # Extract ticket number
        ticket_match = re.search(r'TICKET_NO\s+(\d+)', context, re.IGNORECASE)
        ticket = ticket_match.group(1) if ticket_match else None
        
        # Extract product type
        product_match = re.search(r'PRODUCT\s+(\w+)', context, re.IGNORECASE)
        product = product_match.group(1) if product_match else None
        
        # Extract volumes - try multiple patterns
        liq_vol = None
        oil_vol = None
        water_vol = None
        
        # Look for LIQ_VOL
        liq_match = re.search(r'LIQ_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl', context, re.IGNORECASE)
        if liq_match:
            liq_vol = float(liq_match.group(1))
        
        # Look for OIL_VOL
        oil_match = re.search(r'OIL_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl', context, re.IGNORECASE)
        if oil_match:
            oil_vol = float(oil_match.group(1))
        
        # Look for WATER_VOL
        water_match = re.search(r'WATER_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl', context, re.IGNORECASE)
        if water_match:
            water_vol = float(water_match.group(1))
        
        # Fallback: look for any non-NULL volume near the end of context
        if not (liq_vol or oil_vol or water_vol):
            # Find all "number bbl" patterns that aren't NULL
            vol_matches = re.findall(r'(?:NULL|^|\s)([\d]+\.?[\d]*)\s*bbl', context, re.IGNORECASE)
            if vol_matches:
                # Take the last non-zero value (likely the actual volume)
                volumes = [float(v) for v in vol_matches if float(v) > 0]
                if volumes:
                    liq_vol = volumes[-1]  # Use last volume found
        
        # Extract date
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', context)
        date = date_match.group(1) if date_match else None
        
        # Only add if we have at least a volume
        if liq_vol or oil_vol or water_vol:
            records.append({
                'Tank': tank_name,
                'Ticket': ticket,
                'Date': date,
                'Product': product,
                'Liquid_Volume_bbl': liq_vol,
                'Oil_Volume_bbl': oil_vol,
                'Water_Volume_bbl': water_vol
            })
    
    logger.info(f"Created {len(records)} records with volume data")
    
    if records:
        df = pd.DataFrame(records)
        logger.info(f"Extracted {len(df)} tank deliveries from {df['Tank'].nunique()} tanks")
        return df
    
    return pd.DataFrame()


def get_tank_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for all tanks.
    
    Args:
        df: DataFrame from extract_tank_deliveries
        
    Returns:
        Dictionary with tank-level summaries
    """
    if df.empty:
        return {}
    
    summary = {}
    
    for tank in df['Tank'].unique():
        tank_data = df[df['Tank'] == tank]
        
        # Calculate totals (handling None values)
        liq_total = tank_data['Liquid_Volume_bbl'].dropna().sum()
        oil_total = tank_data['Oil_Volume_bbl'].dropna().sum()
        water_total = tank_data['Water_Volume_bbl'].dropna().sum()
        
        summary[tank] = {
            'delivery_count': len(tank_data),
            'liquid_volume_bbl': liq_total,
            'oil_volume_bbl': oil_total,
            'water_volume_bbl': water_total,
            'products': list(tank_data['Product'].dropna().unique())
        }
    
    return summary


def format_tank_data_for_llm(df: pd.DataFrame, tank_name: str = None) -> str:
    """
    Format tank data as clear text for LLM context.
    
    Args:
        df: DataFrame from extract_tank_deliveries
        tank_name: Optional - filter to specific tank
        
    Returns:
        Formatted string with tank delivery information
    """
    if df.empty:
        return "No tank delivery data available."
    
    if tank_name:
        df = df[df['Tank'].str.contains(tank_name, case=False, na=False)]
        if df.empty:
            return f"No data found for tank: {tank_name}"
    
    output = []
    output.append("TANK DELIVERY DATA")
    output.append("=" * 80)
    
    for tank in df['Tank'].unique():
        tank_data = df[df['Tank'] == tank]
        output.append(f"\nTank: {tank}")
        output.append("-" * 80)
        output.append(f"Total Deliveries: {len(tank_data)}")
        
        # Summary stats
        liq_total = tank_data['Liquid_Volume_bbl'].dropna().sum()
        oil_total = tank_data['Oil_Volume_bbl'].dropna().sum()
        water_total = tank_data['Water_Volume_bbl'].dropna().sum()
        
        if liq_total > 0:
            output.append(f"Total Liquid Volume: {liq_total:.2f} bbl")
        if oil_total > 0:
            output.append(f"Total Oil Volume: {oil_total:.2f} bbl")
        if water_total > 0:
            output.append(f"Total Water Volume: {water_total:.2f} bbl")
        
        # Individual deliveries
        output.append("\nDeliveries:")
        for idx, row in tank_data.iterrows():
            delivery_info = []
            if row['Ticket']:
                delivery_info.append(f"Ticket #{row['Ticket']}")
            if row['Date']:
                delivery_info.append(f"Date: {row['Date']}")
            if row['Product']:
                delivery_info.append(f"Product: {row['Product']}")
            
            volumes = []
            if pd.notna(row['Liquid_Volume_bbl']):
                volumes.append(f"Liquid: {row['Liquid_Volume_bbl']:.2f} bbl")
            if pd.notna(row['Oil_Volume_bbl']):
                volumes.append(f"Oil: {row['Oil_Volume_bbl']:.2f} bbl")
            if pd.notna(row['Water_Volume_bbl']):
                volumes.append(f"Water: {row['Water_Volume_bbl']:.2f} bbl")
            
            output.append(f"  - {' | '.join(delivery_info)} | {' | '.join(volumes)}")
        
        output.append("")
    
    return "\n".join(output)
