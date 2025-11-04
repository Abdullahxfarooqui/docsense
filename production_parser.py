"""
Specialized parser for database-export PDFs with repeating column headers
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def parse_database_export_text(text: str) -> Optional[pd.DataFrame]:
    """
    Parse database export format where each row contains all column headers.
    
    Example format:
    COL1 value1 COL2 value2 COL3 value3
    COL1 value4 COL2 value5 COL3 value6
    
    Args:
        text: Raw text from PDF
        
    Returns:
        DataFrame or None
    """
    try:
        # Find common column patterns in production data
        column_patterns = [
            r'(TICKET_NO)\s*(\d+)',
            r'(START_DATETIME)\s*([\d\-: ]+)',
            r'(LIQ_VOL)\s*([\d.]+)',
            r'(OIL_VOL)\s*([\d.]+)',
            r'(WATER_VOL)\s*([\d.]+)',
            r'(TICKET_VOL)\s*([\d.]+)',
            r'(BSW_VOL_FRAC)\s*([\d.]+)',
            r'(TEMP)\s*([\d.]+)',
            r'(PRESS)\s*([\d.]+)',
            r'(PRODUCT)\s*(\w+)',
            r'(ITEM_NAME)\s*([^:]+:[^:]+)',
        ]
        
        # Split text into potential rows (very long lines)
        lines = [line for line in text.split('\n') if len(line) > 100]  # Database rows are long
        
        records = []
        for line in lines[:1000]:  # Limit processing
            record = {}
            
            # Extract column-value pairs
            for pattern in column_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    col_name = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
                    col_value = matches[0][1] if isinstance(matches[0], tuple) and len(matches[0]) > 1 else matches[0]
                    
                    # Clean value
                    if col_value and col_value != 'NULL':
                        record[col_name] = col_value
            
            if len(record) >= 3:  # At least 3 fields found
                records.append(record)
        
        if records:
            df = pd.DataFrame(records)
            logger.info(f"Parsed {len(df)} records with columns: {list(df.columns)}")
            return df
            
    except Exception as e:
        logger.error(f"Error parsing database export: {e}")
    
    return None


def extract_production_metrics(text: str) -> Optional[pd.DataFrame]:
    """
    Extract production metrics from text into structured format.
    
    Args:
        text: Raw text containing production data
        
    Returns:
        DataFrame with production metrics
    """
    try:
        # Strategy 1: Find volume measurements with type context
        # Look for LIQ_VOL, OIL_VOL, WATER_VOL specifically
        liq_vol_pattern = r'LIQ_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl'
        oil_vol_pattern = r'OIL_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl'
        water_vol_pattern = r'WATER_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl'
        
        liq_volumes = [float(v) for v in re.findall(liq_vol_pattern, text, re.IGNORECASE) if float(v) > 0]
        oil_volumes = [float(v) for v in re.findall(oil_vol_pattern, text, re.IGNORECASE) if float(v) > 0]
        water_volumes = [float(v) for v in re.findall(water_vol_pattern, text, re.IGNORECASE) if float(v) > 0]
        
        # Fallback: Find all numbers followed by 'bbl' if specific patterns fail
        if not liq_volumes and not oil_volumes and not water_volumes:
            bbl_pattern = r'([\d]+\.?[\d]*)\s*bbl'
            all_bbl = [float(v) for v in re.findall(bbl_pattern, text, re.IGNORECASE) if float(v) > 0]
            liq_volumes = all_bbl  # Treat as liquid volumes
        
        # Strategy 2: Find temperature values (numbers followed by degF)
        temp_pattern = r'([\d]+\.?[\d]*)\s*degF'
        temperatures = [float(v) for v in re.findall(temp_pattern, text, re.IGNORECASE) if float(v) > 0]
        
        # Strategy 3: Find pressure values (numbers followed by psi/psig)
        press_pattern = r'([\d]+\.?[\d]*)\s*psi'
        pressures = [float(v) for v in re.findall(press_pattern, text, re.IGNORECASE) if float(v) > 0]
        
        # Strategy 4: Extract tank names
        tank_pattern = r'Storage_Delivery_Tank-C:([^:]+)'
        tanks = list(set(re.findall(tank_pattern, text, re.IGNORECASE)))
        
        # Strategy 5: Extract ticket numbers
        ticket_pattern = r'TICKET_NO\s*(\d+)'
        tickets = list(set(re.findall(ticket_pattern, text, re.IGNORECASE)))
        
        # Strategy 6: Extract products
        product_pattern = r'PRODUCT\s+(\w+)'
        products = list(set(re.findall(product_pattern, text, re.IGNORECASE)))
        
        # Create comprehensive summary with separate volume types
        if liq_volumes or oil_volumes or water_volumes or temperatures or pressures:
            summary_data = []
            
            if liq_volumes:
                summary_data.append({
                    'Metric': 'Liquid Volume (LIQ_VOL)',
                    'Count': len(liq_volumes),
                    'Total': f"{sum(liq_volumes):.2f}",
                    'Average': f"{sum(liq_volumes)/len(liq_volumes):.2f}",
                    'Min': f"{min(liq_volumes):.2f}",
                    'Max': f"{max(liq_volumes):.2f}",
                    'Unit': 'bbl'
                })
            
            if oil_volumes:
                summary_data.append({
                    'Metric': 'Oil Volume (OIL_VOL)',
                    'Count': len(oil_volumes),
                    'Total': f"{sum(oil_volumes):.2f}",
                    'Average': f"{sum(oil_volumes)/len(oil_volumes):.2f}",
                    'Min': f"{min(oil_volumes):.2f}",
                    'Max': f"{max(oil_volumes):.2f}",
                    'Unit': 'bbl'
                })
            
            if water_volumes:
                summary_data.append({
                    'Metric': 'Water Volume (WATER_VOL)',
                    'Count': len(water_volumes),
                    'Total': f"{sum(water_volumes):.2f}",
                    'Average': f"{sum(water_volumes)/len(water_volumes):.2f}",
                    'Min': f"{min(water_volumes):.2f}",
                    'Max': f"{max(water_volumes):.2f}",
                    'Unit': 'bbl'
                })
            
            if temperatures:
                summary_data.append({
                    'Metric': 'Temperature',
                    'Count': len(temperatures),
                    'Total': '-',
                    'Average': f"{sum(temperatures)/len(temperatures):.2f}",
                    'Min': f"{min(temperatures):.2f}",
                    'Max': f"{max(temperatures):.2f}",
                    'Unit': 'degF'
                })
            
            if pressures:
                summary_data.append({
                    'Metric': 'Pressure',
                    'Count': len(pressures),
                    'Total': '-',
                    'Average': f"{sum(pressures)/len(pressures):.2f}",
                    'Min': f"{min(pressures):.2f}",
                    'Max': f"{max(pressures):.2f}",
                    'Unit': 'psi'
                })
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                total_vols = len(liq_volumes) + len(oil_volumes) + len(water_volumes)
                logger.info(f"Extracted {len(df)} metrics: {len(liq_volumes)} LIQ, {len(oil_volumes)} OIL, {len(water_volumes)} WATER")
                return df
        
        # Extract ticket numbers and products
        ticket_pattern = r'(TICKET_NO|Ticket)\s*(\d+)'
        product_pattern = r'(PRODUCT|Product)\s*(\w+)'
        
        tickets = re.findall(ticket_pattern, text, re.IGNORECASE)
        products = re.findall(product_pattern, text, re.IGNORECASE)
        
        if tickets:
            data = []
            for i, (_, ticket_no) in enumerate(tickets[:100]):
                row = {'Ticket_No': ticket_no}
                
                # Find corresponding product
                if i < len(products):
                    row['Product'] = products[i][1]
                
                # Find nearby volume value
                pos = text.find(ticket_no)
                if pos > 0:
                    nearby = text[pos:pos+500]
                    vol_match = re.search(r'(\d+\.?\d*)\s*bbl', nearby, re.IGNORECASE)
                    if vol_match:
                        row['Volume'] = float(vol_match.group(1))
                        row['Unit'] = 'bbl'
                
                if len(row) > 1:
                    data.append(row)
            
            if data:
                df = pd.DataFrame(data)
                logger.info(f"Extracted {len(df)} ticket records")
                return df
        
    except Exception as e:
        logger.error(f"Error extracting production metrics: {e}")
    
    return None


def get_production_summary(text: str) -> Dict[str, Any]:
    """
    Get overall production summary from text.
    
    Args:
        text: Raw text from PDF
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        'total_tickets': 0,
        'total_volume_bbl': 0.0,
        'volume_count': 0,
        'products': set(),
        'tanks': set(),
        'avg_temp': 0.0,
        'avg_pressure': 0.0
    }
    
    try:
        # Extract volume measurements by type
        liq_vol_pattern = r'LIQ_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl'
        oil_vol_pattern = r'OIL_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl'
        water_vol_pattern = r'WATER_VOL[^\d]*([\d]+\.?[\d]*)\s*bbl'
        
        liq_volumes = [float(v) for v in re.findall(liq_vol_pattern, text, re.IGNORECASE) if float(v) > 0]
        oil_volumes = [float(v) for v in re.findall(oil_vol_pattern, text, re.IGNORECASE) if float(v) > 0]
        water_volumes = [float(v) for v in re.findall(water_vol_pattern, text, re.IGNORECASE) if float(v) > 0]
        
        # If specific patterns don't work, get all bbl measurements
        if not liq_volumes and not oil_volumes:
            bbl_pattern = r'([\d]+\.?[\d]*)\s*bbl'
            all_volumes = [float(v) for v in re.findall(bbl_pattern, text, re.IGNORECASE) if float(v) > 0]
            if all_volumes:
                summary['total_volume_bbl'] = sum(all_volumes)
                summary['volume_count'] = len(all_volumes)
        else:
            summary['liq_volume_bbl'] = sum(liq_volumes) if liq_volumes else 0
            summary['oil_volume_bbl'] = sum(oil_volumes) if oil_volumes else 0
            summary['water_volume_bbl'] = sum(water_volumes) if water_volumes else 0
            summary['total_volume_bbl'] = summary['liq_volume_bbl'] + summary['oil_volume_bbl'] + summary['water_volume_bbl']
            summary['volume_count'] = len(liq_volumes) + len(oil_volumes) + len(water_volumes)
        
        # Count unique tickets
        tickets = re.findall(r'TICKET_NO\s*(\d+)', text, re.IGNORECASE)
        unique_tickets = set(tickets)
        summary['total_tickets'] = len(unique_tickets)
        
        # Extract products
        products = re.findall(r'PRODUCT[_\s]+(\w+)', text, re.IGNORECASE)
        summary['products'] = set([p for p in products if p not in ['TEXT', 'XFER', 'ITEM', 'ID']])
        
        # Extract tank names
        tanks = re.findall(r'Storage_Delivery_Tank-C:([A-Za-z\s]+)', text, re.IGNORECASE)
        summary['tanks'] = set([t.strip() for t in tanks if len(t.strip()) > 2])
        
        # Temperature average
        temps = [float(v) for v in re.findall(r'([\d]+\.?[\d]*)\s*degF', text, re.IGNORECASE) if float(v) > 0]
        if temps:
            summary['avg_temp'] = sum(temps) / len(temps)
        
        # Pressure average
        pressures = [float(v) for v in re.findall(r'([\d]+\.?[\d]*)\s*psi', text, re.IGNORECASE) if float(v) > 0]
        if pressures:
            summary['avg_pressure'] = sum(pressures) / len(pressures)
        
    except Exception as e:
        logger.error(f"Error creating summary: {e}")
    
    return summary
