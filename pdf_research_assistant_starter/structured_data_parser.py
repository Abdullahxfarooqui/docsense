"""
Structured Data Parser Module

Handles direct parsing of Excel, CSV, and tabular PDFs without vector embeddings.
Extracts numeric data exactly as it appears in cells, preserving all values and structure.

Author: GitHub Copilot
Date: October 24, 2025
"""

import logging
import os
import io
from typing import List, Dict, Any, Optional, Tuple, BinaryIO, Union
import traceback

import pandas as pd
import pdfplumber

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StructuredDataError(Exception):
    """Custom exception for structured data parsing errors."""
    pass


def is_structured_data_file(filename: str) -> bool:
    """
    Check if a file is a structured data file (Excel, CSV, or tabular PDF).
    
    Args:
        filename: Name of the file
        
    Returns:
        bool: True if file is structured data format
    """
    ext = os.path.splitext(filename.lower())[1]
    return ext in ['.xlsx', '.xls', '.csv', '.xlsm']


def detect_tabular_pdf(pdf_file: BinaryIO) -> bool:
    """
    Detect if a PDF contains tables using pdfplumber.
    
    Args:
        pdf_file: Binary file object containing PDF data
        
    Returns:
        bool: True if PDF contains detectable tables
    """
    try:
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # Check first few pages for tables
            pages_to_check = min(3, len(pdf.pages))
            for i in range(pages_to_check):
                tables = pdf.pages[i].extract_tables()
                if tables and len(tables) > 0:
                    # Verify it's not just text formatted as table
                    for table in tables:
                        if len(table) > 2 and len(table[0]) > 1:  # At least 3 rows, 2 columns
                            logger.info(f"Detected tabular data in PDF (page {i+1})")
                            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Error detecting tabular PDF: {str(e)}")
        return False


def parse_excel_file(file_obj: BinaryIO, filename: str) -> pd.DataFrame:
    """
    Parse Excel file and return combined DataFrame from all sheets.
    
    Args:
        file_obj: Binary file object containing Excel data
        filename: Name of the file
        
    Returns:
        pd.DataFrame: Combined data from all sheets
        
    Raises:
        StructuredDataError: If Excel parsing fails
    """
    try:
        logger.info(f"Parsing Excel file: {filename}")
        file_obj.seek(0)
        
        # Read all sheets
        excel_data = pd.read_excel(file_obj, sheet_name=None, engine='openpyxl')
        
        if not excel_data:
            raise StructuredDataError(f"No sheets found in Excel file: {filename}")
        
        # Combine all sheets
        all_dataframes = []
        for sheet_name, df in excel_data.items():
            if df.empty:
                logger.warning(f"Empty sheet skipped: {sheet_name}")
                continue
            
            # Add sheet name as a column if multiple sheets
            if len(excel_data) > 1:
                df['_sheet_name'] = sheet_name
            
            all_dataframes.append(df)
        
        if not all_dataframes:
            raise StructuredDataError(f"All sheets are empty in: {filename}")
        
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"Parsed Excel file: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        
        return combined_df
        
    except StructuredDataError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse Excel file '{filename}': {str(e)}")
        raise StructuredDataError(f"Excel parsing failed: {str(e)}")


def parse_csv_file(file_obj: BinaryIO, filename: str) -> pd.DataFrame:
    """
    Parse CSV file and return DataFrame.
    
    Args:
        file_obj: Binary file object containing CSV data
        filename: Name of the file
        
    Returns:
        pd.DataFrame: Parsed CSV data
        
    Raises:
        StructuredDataError: If CSV parsing fails
    """
    try:
        logger.info(f"Parsing CSV file: {filename}")
        file_obj.seek(0)
        
        # Try different encodings and separators
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        separators = [',', ';', '\t', '|']
        
        df = None
        for encoding in encodings:
            for sep in separators:
                try:
                    file_obj.seek(0)
                    df = pd.read_csv(file_obj, encoding=encoding, sep=sep)
                    
                    # Validate we got meaningful data
                    if len(df.columns) > 1 and len(df) > 0:
                        logger.info(f"Successfully parsed CSV with encoding={encoding}, separator='{sep}'")
                        logger.info(f"CSV data: {len(df)} rows, {len(df.columns)} columns")
                        return df
                        
                except Exception as parse_error:
                    logger.debug(f"Failed with encoding={encoding}, sep='{sep}': {str(parse_error)}")
                    continue
        
        if df is None or df.empty:
            raise StructuredDataError(f"Could not parse CSV file: {filename}")
        
        return df
        
    except StructuredDataError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse CSV file '{filename}': {str(e)}")
        raise StructuredDataError(f"CSV parsing failed: {str(e)}")


def parse_tabular_pdf(file_obj: BinaryIO, filename: str) -> pd.DataFrame:
    """
    Parse tabular PDF and return combined DataFrame from all tables.
    
    Args:
        file_obj: Binary file object containing PDF data
        filename: Name of the file
        
    Returns:
        pd.DataFrame: Combined data from all tables
        
    Raises:
        StructuredDataError: If PDF table parsing fails
    """
    try:
        logger.info(f"Parsing tabular PDF: {filename}")
        file_obj.seek(0)
        pdf_bytes = file_obj.read()
        file_obj.seek(0)
        
        all_tables = []
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = None
                    
                    # Strategy 1: Default settings
                    try:
                        tables = page.extract_tables()
                        if tables:
                            logger.debug(f"Default extraction succeeded on page {page_num + 1}")
                    except Exception as e:
                        logger.debug(f"Default extraction failed on page {page_num + 1}: {type(e).__name__}")
                    
                    # Strategy 2: Text-based extraction (no lines required)
                    if not tables:
                        try:
                            tables = page.extract_tables(table_settings={
                                "vertical_strategy": "text",
                                "horizontal_strategy": "text",
                            })
                            if tables:
                                logger.debug(f"Text-based extraction succeeded on page {page_num + 1}")
                        except Exception as e:
                            logger.debug(f"Text-based extraction failed on page {page_num + 1}: {type(e).__name__}")
                    
                    # If all strategies failed, skip this page
                    if not tables:
                        logger.warning(f"All extraction strategies failed on page {page_num + 1}, skipping")
                        continue
                
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    try:
                        # Convert to DataFrame
                        # First row is usually header
                        header = table[0]
                        data = table[1:]
                        
                        df = pd.DataFrame(data, columns=header)
                        
                        # Add metadata
                        df['_page'] = page_num + 1
                        df['_table'] = table_idx + 1
                        
                        all_tables.append(df)
                        logger.debug(f"Extracted table from page {page_num + 1}: {len(df)} rows")
                    except Exception as e:
                        logger.warning(f"Failed to convert table {table_idx + 1} on page {page_num + 1} to DataFrame: {str(e)}")
                        continue
        
        except Exception as pdf_error:
            logger.error(f"Critical error during PDF table extraction: {type(pdf_error).__name__}: {str(pdf_error)}")
            logger.info(f"Falling back to text-based processing for {filename}")
            return None
        
        if not all_tables:
            logger.warning(f"No tables could be extracted from PDF: {filename}")
            logger.info(f"PDF {filename} will be processed as text-based document instead")
            return None  # Return None to trigger text-based processing
        
        combined_df = pd.concat(all_tables, ignore_index=True)
        logger.info(f"Parsed tabular PDF: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        
        return combined_df
        
    except StructuredDataError:
        raise
    except Exception as e:
        logger.error(f"Failed to parse tabular PDF '{filename}': {str(e)}")
        logger.info(f"Falling back to text-based processing for {filename}")
        return None  # Return None to trigger text-based processing


def parse_structured_file(file_obj: BinaryIO, filename: str) -> Optional[pd.DataFrame]:
    """
    Parse structured data file (Excel, CSV, or tabular PDF) and return DataFrame.
    
    Args:
        file_obj: Binary file object
        filename: Name of the file
        
    Returns:
        pd.DataFrame or None: Parsed data, or None if not a structured file
        
    Raises:
        StructuredDataError: If parsing fails
    """
    ext = os.path.splitext(filename.lower())[1]
    
    try:
        if ext in ['.xlsx', '.xls', '.xlsm']:
            return parse_excel_file(file_obj, filename)
        elif ext == '.csv':
            return parse_csv_file(file_obj, filename)
        elif ext == '.pdf':
            # Check if it's tabular
            if detect_tabular_pdf(file_obj):
                return parse_tabular_pdf(file_obj, filename)
            else:
                logger.info(f"PDF {filename} does not contain tables - will use text extraction")
                return None
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error parsing structured file '{filename}': {str(e)}")
        raise StructuredDataError(f"Failed to parse {filename}: {str(e)}")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean DataFrame while preserving all structure and NULL values.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Remove completely empty columns
    df = df.dropna(axis=1, how='all')
    
    # Clean column names
    df.columns = [str(col).strip() if col is not None else f'Column_{i}' 
                  for i, col in enumerate(df.columns)]
    
    # Replace various null representations with pd.NA for consistency
    null_values = ['', 'NA', 'N/A', 'n/a', 'null', 'NULL', 'None', 'NaN', 'nan']
    df = df.replace(null_values, pd.NA)
    
    # Strip whitespace from string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df


def identify_location_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the column that contains location/source names.
    
    Args:
        df: Input DataFrame
        
    Returns:
        str or None: Name of the location column, or None if not found
    """
    # Common location column names
    location_keywords = [
        'location', 'site', 'tank', 'well', 'station', 'field', 
        'source', 'name', 'id', 'identifier', 'facility', 'area'
    ]
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        
        # Exact match
        if col_lower in location_keywords:
            logger.info(f"Found location column (exact match): {col}")
            return col
        
        # Partial match
        for keyword in location_keywords:
            if keyword in col_lower:
                logger.info(f"Found location column (partial match): {col}")
                return col
    
    # Default to first column if it contains strings
    if len(df.columns) > 0:
        first_col = df.columns[0]
        if df[first_col].dtype == 'object':
            logger.info(f"Using first column as location: {first_col}")
            return first_col
    
    logger.warning("No location column identified")
    return None


def dataframe_to_markdown(df: pd.DataFrame, filename: str = "data") -> str:
    """
    Convert DataFrame to detailed markdown format for LLM consumption.
    
    Includes:
    - File metadata
    - Column information with data types
    - Full data table in markdown format
    - NULL value indicators
    
    Args:
        df: Input DataFrame
        filename: Source filename
        
    Returns:
        str: Markdown formatted string
    """
    markdown_parts = []
    
    # Header
    markdown_parts.append(f"# Structured Data: {filename}\n")
    markdown_parts.append(f"**Total Rows:** {len(df)}")
    markdown_parts.append(f"**Total Columns:** {len(df.columns)}\n")
    
    # CRITICAL INSTRUCTION for LLM
    markdown_parts.append("---")
    markdown_parts.append("⚠️ **EXTRACTION INSTRUCTION:**")
    markdown_parts.append("- The 'Data Table' section below contains the ACTUAL data")
    markdown_parts.append("- Column headers in the data table = parameters that exist")
    markdown_parts.append("- DO NOT create rows for parameters not in the data table")
    markdown_parts.append("- Ignore any column names mentioned outside the data table")
    markdown_parts.append("---\n")
    
    markdown_parts.append("## Data Table (EXTRACT FROM THIS)\n")
    
    # Convert to markdown table
    # Replace pd.NA with "NULL" for clarity
    df_display = df.copy()
    df_display = df_display.fillna("NULL")
    
    markdown_parts.append(df_display.to_markdown(index=False))
    
    markdown_parts.append("\n---")
    markdown_parts.append("\n## Metadata (FOR REFERENCE ONLY - DO NOT EXTRACT)\n")
    
    # Column information AFTER the data table
    markdown_parts.append("**Column Details:**\n")
    for col in df.columns:
        dtype = df[col].dtype
        null_count = df[col].isna().sum()
        total = len(df)
        
        markdown_parts.append(
            f"- **{col}**: {dtype} "
            f"({null_count} NULL values out of {total} - {null_count/total*100:.1f}%)"
        )
    
    return "\n".join(markdown_parts)


def extract_numeric_parameters(df: pd.DataFrame) -> List[str]:
    """
    Extract list of numeric parameter columns from DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List[str]: List of numeric column names
    """
    numeric_cols = []
    
    for col in df.columns:
        # Skip metadata columns
        if col.startswith('_'):
            continue
        
        # Check if column is numeric or contains numeric values
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        else:
            # Check if it contains numeric values
            try:
                pd.to_numeric(df[col], errors='coerce')
                # If at least 50% of non-null values can be converted to numbers
                numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
                total_count = df[col].notna().sum()
                if total_count > 0 and numeric_count / total_count >= 0.5:
                    numeric_cols.append(col)
            except:
                pass
    
    return numeric_cols


def get_structured_data_summary(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    """
    Get summary statistics about structured data.
    
    Args:
        df: Input DataFrame
        filename: Source filename
        
    Returns:
        Dict: Summary information
    """
    location_col = identify_location_column(df)
    numeric_cols = extract_numeric_parameters(df)
    
    summary = {
        "filename": filename,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "location_column": location_col,
        "numeric_columns": numeric_cols,
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isna().sum().to_dict(),
    }
    
    if location_col and location_col in df.columns:
        summary["unique_locations"] = df[location_col].dropna().unique().tolist()
    
    return summary
