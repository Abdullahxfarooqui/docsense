"""
Table and Chart Formatter for DocSense

Formats LLM responses into structured tables and visualizations.
"""

import re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def extract_numerical_data(text: str) -> Optional[pd.DataFrame]:
    """
    Extract numerical data from text and convert to DataFrame.
    
    Args:
        text: Text containing data
        
    Returns:
        DataFrame if data found, None otherwise
    """
    try:
        # Try to find table-like structures
        lines = text.strip().split('\n')
        
        # Look for lines with multiple numbers or delimiters
        data_rows = []
        header = None
        
        for line in lines:
            # Check if line has table delimiters (|, tabs, multiple spaces)
            if '|' in line or '\t' in line or re.search(r'\s{2,}', line):
                # Split by delimiters
                if '|' in line:
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                elif '\t' in line:
                    cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
                else:
                    cells = [cell.strip() for cell in re.split(r'\s{2,}', line) if cell.strip()]
                
                # Skip separator lines (---, ===)
                if all(re.match(r'^[-=_]+$', cell) for cell in cells if cell):
                    continue
                
                # First valid row could be header
                if header is None and cells:
                    header = cells
                else:
                    data_rows.append(cells)
        
        if data_rows and header:
            # Create DataFrame
            max_cols = max(len(header), max(len(row) for row in data_rows))
            
            # Pad rows to same length
            header = header + [''] * (max_cols - len(header))
            data_rows = [row + [''] * (max_cols - len(row)) for row in data_rows]
            
            df = pd.DataFrame(data_rows, columns=header[:max_cols])
            return df
        
        # Alternative: Look for key-value pairs with numbers
        pattern = r'([A-Za-z\s]+):\s*([\d,.-]+)'
        matches = re.findall(pattern, text)
        
        if matches and len(matches) > 2:
            df = pd.DataFrame(matches, columns=['Metric', 'Value'])
            return df
            
    except Exception as e:
        logger.error(f"Error extracting numerical data: {e}")
    
    return None


def format_as_table(text: str) -> str:
    """
    Format text response as a markdown table if it contains structured data.
    
    Args:
        text: Response text
        
    Returns:
        Formatted markdown table or original text
    """
    df = extract_numerical_data(text)
    
    if df is not None and not df.empty:
        # Convert to markdown table
        return df.to_markdown(index=False)
    
    return text


def detect_chart_type(df: pd.DataFrame) -> str:
    """
    Detect appropriate chart type for the data.
    
    Args:
        df: DataFrame
        
    Returns:
        Chart type ('bar', 'line', 'pie', 'scatter', 'table')
    """
    if len(df) == 0:
        return 'table'
    
    # Count numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    if len(numeric_cols) == 0:
        # Try to convert columns to numeric
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''))
                numeric_cols = df.select_dtypes(include=['number']).columns
            except:
                pass
    
    if len(numeric_cols) == 0:
        return 'table'
    
    # If single numeric column, use bar chart
    if len(numeric_cols) == 1:
        return 'bar'
    
    # If 2+ numeric columns, use line chart
    if len(numeric_cols) >= 2:
        return 'line'
    
    return 'table'


def create_chart(df: pd.DataFrame, chart_type: str = 'auto', title: str = "Data Visualization") -> Optional[go.Figure]:
    """
    Create an interactive chart from DataFrame.
    
    Args:
        df: DataFrame with data
        chart_type: Type of chart ('auto', 'bar', 'line', 'pie', 'scatter')
        title: Chart title
        
    Returns:
        Plotly figure or None
    """
    try:
        if df is None or df.empty:
            return None
        
        # Auto-detect chart type
        if chart_type == 'auto':
            chart_type = detect_chart_type(df)
        
        # Convert string numbers to numeric
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''))
                except:
                    pass
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if len(numeric_cols) == 0:
            return None
        
        # Create chart based on type
        if chart_type == 'bar':
            x_col = text_cols[0] if text_cols else df.columns[0]
            y_col = numeric_cols[0] if numeric_cols else df.columns[1]
            
            fig = px.bar(df, x=x_col, y=y_col, title=title)
            
        elif chart_type == 'line':
            x_col = text_cols[0] if text_cols else df.columns[0]
            y_cols = numeric_cols[:3]  # Max 3 lines
            
            fig = go.Figure()
            for y_col in y_cols:
                fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], 
                                        mode='lines+markers', name=y_col))
            fig.update_layout(title=title, xaxis_title=x_col)
            
        elif chart_type == 'pie':
            label_col = text_cols[0] if text_cols else df.columns[0]
            value_col = numeric_cols[0] if numeric_cols else df.columns[1]
            
            fig = px.pie(df, values=value_col, names=label_col, title=title)
            
        elif chart_type == 'scatter':
            x_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]
            y_col = numeric_cols[1] if len(numeric_cols) > 1 else df.columns[1]
            
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
            
        else:
            return None
        
        fig.update_layout(height=400)
        return fig
        
    except Exception as e:
        logger.error(f"Error creating chart: {e}")
        return None


def display_response_with_visuals(response: str, show_charts: bool = True):
    """
    Display response with automatic table formatting and chart generation.
    
    Args:
        response: LLM response text
        show_charts: Whether to show charts
    """
    # Extract and display tables
    df = extract_numerical_data(response)
    
    if df is not None and not df.empty:
        st.markdown("### 📊 Data Table")
        st.dataframe(df, use_container_width=True)
        
        if show_charts:
            # Create and display chart
            chart = create_chart(df, chart_type='auto', title="Extracted Data Visualization")
            if chart:
                st.markdown("### 📈 Visualization")
                st.plotly_chart(chart, use_container_width=True)
    
    # Display text response
    st.markdown("### 💬 Analysis")
    st.markdown(response)


def parse_table_from_response(response: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Parse table data from LLM response and return cleaned text.
    
    Args:
        response: LLM response
        
    Returns:
        Tuple of (DataFrame or None, cleaned text)
    """
    df = extract_numerical_data(response)
    
    # Remove table portion from text if found
    cleaned_text = response
    
    return df, cleaned_text
