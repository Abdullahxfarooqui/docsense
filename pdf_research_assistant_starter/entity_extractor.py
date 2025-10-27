"""
Entity-Based Data Extraction Module - V3.9.1 ENTITY FILTERING

Automatically detects REAL production entity names (TAIMUR, LPG, CONDEN, OIL) 
and extracts numeric data with units using proximity-based pattern matching.

Key Features:
- Entity filtering: Ignores metadata keywords (DATA, FIXED, SALES, DELIVERY, PUBLISHED, etc.)
- Proximity enforcement: Only captures values within 20 chars of parameter keywords
- Ticket ID protection: Ignores numbers >7 digits unless near "ticket" keyword
- Section-based extraction: Extracts parameters only from entity's own section
- All parameter types: Numeric (Pressure, Temp) + Text (Product, Status) + Alphanumeric (Ticket, Sales)

Valid Entities: TAIMUR, OIL, LPG, CONDEN, GAS, and other field/production names
Invalid Entities: DATA, FIXED, SALES, DELIVERY, PUBLISHED, STORAGE, NULL, BBL, DAPI

Author: GitHub Copilot
Date: October 27, 2025
Version: 3.9.1
"""

import re
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Intelligent entity detection and parameter extraction with proximity enforcement.
    
    V3.9.1 Changes:
    - Added entity filtering to ignore metadata/system keywords
    - Strict validation: Only TAIMUR, OIL, LPG, CONDEN, GAS, and field names
    - Blocks: DATA, FIXED, SALES, DELIVERY, PUBLISHED, STORAGE, NULL, BBL, DAPI
    - Proximity windows ([^A-Za-z0-9]{0,20}) prevent distant value capture
    - Section-based extraction (only extract from entity's own text section)
    - Ticket ID protection (ignore >7 digit numbers unless near "ticket")
    """
    
    # V3.9.1: Valid production entity names (uppercase field names)
    VALID_ENTITY_NAMES = [
        "TAIMUR", "OIL", "CONDEN", "LPG", "GAS", 
        "CONDENSATE", "PRODUCTION", "WELL"
    ]
    
    # V3.9.1: Invalid metadata/system keywords (must be blocked)
    INVALID_ENTITY_KEYWORDS = [
        "DATA", "FIXED", "SALES", "DELIVERY", "DELIVER", 
        "PUBLISHED", "PUBLISH", "STORAGE", "STORE", "NULL",
        "BBL", "BARREL", "DAPI", "API", "PSIG", "PSI",
        "DEGF", "FAHRENHEIT", "TEMP", "TEMPERATURE",
        "PRESSURE", "VOLUME", "GRAVITY", "ENERGY",
        "TICKET", "STATUS", "PRODUCT", "TYPE", "CODE",
        "SHEET", "PAGE", "TABLE", "COLUMN", "ROW", "HEADER",
        "TANK", "LOA", "LOAD", "FROM", "DATE", "TIME",
        "TOTAL", "SUM", "AVERAGE", "AVG", "COUNT"
    ]
    
    # Common entity patterns in production data
    ENTITY_PATTERNS = [
        r"\b(TAIMUR)\b",
        r"\b(OIL)\b",
        r"\b(CONDEN(?:SATE)?)\b",
        r"\b(LPG)\b",
        r"\b(GAS)\b",
        r"\b(PRODUCTION)\b",
        r"\b([A-Z]{3,})\b",  # Any 3+ uppercase letters (catches custom names)
        r"(?i)Location[:\s]+([A-Z0-9]+)",
        r"(?i)Well[:\s]+([A-Z0-9]+)",
        r"(?i)Site[:\s]+([A-Z0-9]+)",
        r"(?i)Tank[:\s]+([A-Z0-9]+)",
    ]
    
    # V3.9: Proximity-based parameter patterns (captures values within 20 chars)
    PARAMETER_PROXIMITY_PATTERNS = {
        "Pressure": r"(?i)(?:pressure|press\.|psig)[^A-Za-z0-9]{0,20}([-+]?\d*\.\d+|\d+)",
        "Temperature": r"(?i)(?:temp(?:erature)?|°F|degF|fahrenheit)[^A-Za-z0-9]{0,20}([-+]?\d*\.\d+|\d+)",
        "Volume": r"(?i)(?:volume|vol\.|bbl|barrel)[^A-Za-z0-9]{0,20}([-+]?\d*\.\d+|\d+)",
        "API Gravity": r"(?i)(?:api|gravity|dAPI)[^A-Za-z0-9]{0,20}([-+]?\d*\.\d+|\d+)",
        "Energy": r"(?i)(?:energy|btu|mmbtu)[^A-Za-z0-9]{0,20}([-+]?\d*\.\d+|\d+)",
        "Ticket": r"(?i)(?:ticket)\s*(?:number|#|no\.?)?\s*[:\s]*([A-Za-z0-9]{4,15})",
        "Sales": r"(?i)(?:sales)\s*(?:code|#|no\.?)?\s*[:\s]*(\d{2,10})",
        "Product": r"(?i)(?:product|type)\s*[:\s]*(OIL|LPG|GAS|CONDEN(?:SATE)?)",
        "Status": r"(?i)(?:status|state)\s*[:\s]*(ACTIVE|INACTIVE|ONLINE|OFFLINE|RUNNING|STOPPED)",
        "Storage": r"(?i)(?:storage|tank)\s*[:\s]*([A-Za-z0-9]{2,15})",
        "Delivery": r"(?i)(?:delivery|deliver)\s*[:\s]*([A-Za-z0-9]{2,15})",
    }
    
    # Legacy parameter patterns (fallback)
    PARAMETER_PATTERNS = {
        "Pressure": [
            r"(?i)pressure",
            r"(?i)press\.",
            r"(?i)psi",
            r"(?i)psig",
        ],
        "Temperature": [
            r"(?i)temp(?:erature)?",
            r"(?i)°F",
            r"(?i)degF",
            r"(?i)fahrenheit",
        ],
        "Volume": [
            r"(?i)volume",
            r"(?i)vol\.",
            r"(?i)bbl",
            r"(?i)barrel",
        ],
        "API Gravity": [
            r"(?i)api",
            r"(?i)gravity",
            r"(?i)dAPI",
        ],
        "Energy": [
            r"(?i)energy",
            r"(?i)btu",
            r"(?i)mmbtu",
        ],
        "Ticket": [
            r"(?i)ticket",
            r"(?i)ticket\s*#",
            r"(?i)ticket\s*number",
        ],
        "Sales": [
            r"(?i)sales",
            r"(?i)revenue",
        ],
        "Product": [
            r"(?i)product",
            r"(?i)type",
        ],
        "Status": [
            r"(?i)status",
            r"(?i)state",
        ],
        "Storage": [
            r"(?i)storage",
            r"(?i)tank",
        ],
        "Delivery": [
            r"(?i)delivery",
            r"(?i)deliver",
        ],
    }
    
    # Unit detection patterns
    UNIT_PATTERNS = {
        "psig": r"\b(psig|psi)\b",
        "degF": r"\b(°F|degF|fahrenheit)\b",
        "bbl": r"\b(bbl|barrel|barrels?)\b",
        "dAPI": r"\b(dAPI|API)\b",
        "MMBtu": r"\b(MMBtu|MMBTU|BTU)\b",
        "%": r"\b(percent|%)\b",
        "mcf": r"\b(mcf|MCF)\b",
        "ft": r"\b(ft|feet)\b",
        "gal": r"\b(gal|gallon)\b",
    }
    
    def __init__(self):
        self.global_entities = defaultdict(lambda: {
            "Pressure": None,
            "Temperature": None,
            "Volume": None,
            "API Gravity": None,
            "Energy": None,
            "Ticket": None,
            "Sales": None,
            "Product": None,
            "Status": None,
            "Storage": None,
            "Delivery": None,
            "Notes": [],
            "Sources": set(),
        })
    
    def get_section_for_entity(self, text: str, entity: str) -> str:
        """
        V3.9: Extract the text section belonging to a specific entity.
        This prevents cross-contamination where TAIMUR's values mix with LPG's values.
        
        Args:
            text: Full document text
            entity: Entity name (e.g., "TAIMUR")
            
        Returns:
            Text section for this entity only
        """
        # Pattern: Entity name followed by everything until next entity or end
        pattern = rf"{entity}.*?(?=\b(TAIMUR|OIL|CONDEN|LPG|GAS)\b|$)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        
        if match:
            section = match.group(0)
            logger.debug(f"📍 Extracted {len(section)} char section for {entity}")
            return section
        
        # Fallback: Return full text if entity not found
        logger.debug(f"⚠️ No dedicated section found for {entity}, using full text")
        return text
    
    def is_valid_entity(self, entity: str) -> bool:
        """
        V3.9.1: Validate that entity name is a real production entity, not metadata.
        
        Valid entities: TAIMUR, OIL, LPG, CONDEN, GAS, etc. (field names)
        Invalid entities: DATA, FIXED, SALES, DELIVERY, PUBLISHED, etc. (metadata keywords)
        
        Args:
            entity: Entity name to validate
            
        Returns:
            True if valid entity, False if metadata/system keyword
        """
        entity_upper = entity.upper().strip()
        
        # Block invalid metadata keywords
        if entity_upper in self.INVALID_ENTITY_KEYWORDS:
            logger.debug(f"🚫 Blocked invalid entity: {entity_upper} (metadata keyword)")
            return False
        
        # Allow known valid entities
        if entity_upper in self.VALID_ENTITY_NAMES:
            logger.debug(f"✅ Valid entity: {entity_upper}")
            return True
        
        # For unknown entities, check if it's a field name pattern
        # Valid: 3+ chars, all uppercase, not in invalid list
        if len(entity_upper) >= 3 and entity_upper.isalpha():
            logger.debug(f"✅ Valid entity (field name pattern): {entity_upper}")
            return True
        
        # Otherwise, block it
        logger.debug(f"🚫 Blocked invalid entity: {entity_upper} (doesn't match field pattern)")
        return False
    
    def is_ticket_id_not_parameter(self, value: str, context: str) -> bool:
        """
        V3.9: Protect against ticket IDs being misread as pressure/temperature.
        
        Rule: Ignore any numeric string >7 digits unless near "ticket" keyword.
        
        Args:
            value: The numeric value extracted
            context: The surrounding text
            
        Returns:
            True if this is likely a ticket ID (should be ignored), False otherwise
        """
        # If value has more than 7 digits, it's likely a ticket ID
        digits_only = re.sub(r'[^0-9]', '', value)
        if len(digits_only) > 7:
            # Check if "ticket" keyword is nearby
            context_lower = context.lower()
            if "ticket" not in context_lower:
                logger.debug(f"🛡️ Blocked {value} (>7 digits, not near 'ticket')")
                return True
        return False
    
    def detect_unit_for_parameter(self, param: str, text: str = "") -> str:
        """
        V3.9: Detect unit based on parameter type.
        
        Args:
            param: Parameter name
            text: Optional text to search for explicit units
            
        Returns:
            Unit string (psig, °F, bbl, etc.)
        """
        # Check text for explicit units first
        if text:
            for unit, pattern in self.UNIT_PATTERNS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    return unit
        
        # Infer from parameter type
        unit_map = {
            "Pressure": "psig",
            "Temperature": "°F",
            "Volume": "bbl",
            "API Gravity": "dAPI",
            "Energy": "MMBtu",
            "Ticket": "",
            "Sales": "",
            "Product": "",
            "Status": "",
            "Storage": "",
            "Delivery": "",
        }
        return unit_map.get(param, "")
    
    def detect_entity_name(self, text: str, context: str = "") -> str:
        """
        Detect entity name from text using pattern matching.
        
        Args:
            text: Text to search for entity name
            context: Additional context (filename, etc.)
            
        Returns:
            Detected entity name or "UNKNOWN"
        """
        # Try each pattern
        for pattern in self.ENTITY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return first match, normalized
                entity = matches[0].strip().upper()
                # Filter out common words that aren't entities
                if entity not in ["THE", "AND", "FOR", "WITH", "FROM"]:
                    return entity
        
        # Try to extract from context (filename)
        if context:
            # Look for meaningful names in filename
            filename_match = re.search(r"([A-Z]{3,})", context.upper())
            if filename_match:
                return filename_match.group(1)
        
        return "UNKNOWN"
    
    def detect_unit(self, text: str) -> Tuple[str, str]:
        """
        Detect measurement unit from text.
        
        Args:
            text: Text to search for units
            
        Returns:
            Tuple of (unit, note) - note is "Explicit" or "Inferred"
        """
        for unit, pattern in self.UNIT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return unit, "Explicit"
        
        # Infer from context
        text_lower = text.lower()
        if "pressure" in text_lower:
            return "psig", "Inferred from context"
        elif "temperature" in text_lower or "temp" in text_lower:
            return "degF", "Inferred from context"
        elif "volume" in text_lower or "vol" in text_lower:
            return "bbl", "Inferred from context"
        elif "api" in text_lower or "gravity" in text_lower:
            return "dAPI", "Inferred from context"
        elif "energy" in text_lower:
            return "MMBtu", "Inferred from context"
        
        return "", "Unknown"
    
    def detect_parameter(self, text: str) -> Optional[str]:
        """
        Detect which parameter a line is describing.
        
        Args:
            text: Text to analyze
            
        Returns:
            Parameter name or None
        """
        text_lower = text.lower()
        for param, patterns in self.PARAMETER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return param
        return None
    
    def extract_numbers(self, text: str) -> List[str]:
        """
        Extract all numeric values from text.
        
        Args:
            text: Text to search
            
        Returns:
            List of numeric strings
        """
        # Match integers, decimals, and scientific notation
        return re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    
    def extract_from_text(self, text: str, source: str = "Document") -> Dict[str, Any]:
        """
        V3.9.1: Extract entity-based data using proximity patterns, section isolation, and entity filtering.
        
        Key improvements:
        - Entity filtering: Only valid production entities (TAIMUR, OIL, LPG), not metadata
        - Proximity enforcement: Only captures values within 20 chars of parameter keyword
        - Section-based extraction: Extract from entity's own section only
        - Ticket ID protection: Ignores >7 digit numbers unless near "ticket"
        
        Args:
            text: Text to extract from
            source: Source identifier (filename, etc.)
            
        Returns:
            Dictionary of entities with their data
        """
        # Step 1: Detect all entities in document
        detected_entities = []
        for pattern in self.ENTITY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.strip().upper()
                
                # V3.9.1: Filter out common words and metadata keywords
                if entity in ["THE", "AND", "FOR", "WITH", "FROM"]:
                    continue
                
                # V3.9.1: Validate entity (block DATA, FIXED, SALES, DELIVERY, etc.)
                if not self.is_valid_entity(entity):
                    continue
                
                # Avoid duplicates
                if entity not in detected_entities:
                    detected_entities.append(entity)
        
        if not detected_entities:
            logger.warning(f"⚠️ No valid entities detected in text (only metadata keywords found)")
            return {}
        
        logger.info(f"🔍 Detected {len(detected_entities)} valid entities: {', '.join(detected_entities)}")
        
        # Step 2: Extract parameters for each entity using proximity patterns
        for entity in detected_entities:
            # Get the text section for this entity only
            section = self.get_section_for_entity(text, entity)
            entity_data = self.global_entities[entity]
            
            # Extract each parameter using proximity patterns
            for param, pattern in self.PARAMETER_PROXIMITY_PATTERNS.items():
                # Search in entity's section only
                matches = re.finditer(pattern, section, re.IGNORECASE)
                
                for match in matches:
                    value = match.group(1).strip()
                    
                    # V3.9.1: Block if value is just a parameter keyword itself
                    value_upper = value.upper()
                    if value_upper in ["SALES", "STORAGE", "DELIVERY", "DELIVER", "TICKET", 
                                       "PRODUCT", "STATUS", "TYPE", "CODE", "PRESSURE", 
                                       "TEMPERATURE", "VOLUME", "GRAVITY", "ENERGY"]:
                        logger.debug(f"🚫 Skipping {value} for {entity}.{param} (parameter keyword, not value)")
                        continue
                    
                    # V3.9: Ticket ID protection for numeric parameters
                    if param in ["Pressure", "Temperature", "Volume", "API Gravity", "Energy"]:
                        # Check if this looks like a ticket ID (>7 digits)
                        if self.is_ticket_id_not_parameter(value, match.group(0)):
                            logger.debug(f"🛡️ Skipping {value} for {entity}.{param} (looks like ticket ID)")
                            continue
                    
                    # Get unit for this parameter
                    unit = self.detect_unit_for_parameter(param, match.group(0))
                    
                    # Format value with unit (if applicable)
                    if unit:
                        formatted_value = f"{value} {unit}"
                    else:
                        formatted_value = value
                    
                    # Store the value
                    if entity_data[param] is None or entity_data[param] == "—":
                        entity_data[param] = formatted_value
                        entity_data["Notes"].append("Explicit")
                        entity_data["Sources"].add(source)
                        logger.debug(f"✅ {entity}.{param} = {formatted_value}")
                    else:
                        # Value already exists, only update if new value is more specific
                        existing_len = len(str(entity_data[param]))
                        new_len = len(formatted_value)
                        if new_len > existing_len:
                            logger.debug(f"🔄 Updated {entity}.{param}: {entity_data[param]} → {formatted_value}")
                            entity_data[param] = formatted_value
        
        return dict(self.global_entities)
    
    def extract_from_dataframe(self, df: pd.DataFrame, source: str = "Excel") -> Dict[str, Any]:
        """
        Extract entity-based data from pandas DataFrame.
        
        Args:
            df: DataFrame to extract from
            source: Source identifier
            
        Returns:
            Dictionary of entities with their data
        """
        # Try to identify entity column
        entity_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['location', 'entity', 'name', 'site', 'well', 'source']):
                entity_col = col
                break
        
        # If we found an entity column, process row by row
        if entity_col:
            for idx, row in df.iterrows():
                entity = str(row[entity_col]).strip().upper()
                if not entity or entity == "NAN":
                    continue
                
                entity_data = self.global_entities[entity]
                
                # Process each column
                for col in df.columns:
                    if col == entity_col:
                        continue
                    
                    value = row[col]
                    if pd.isna(value):
                        continue
                    
                    # Detect parameter from column name
                    param = self.detect_parameter(str(col))
                    if not param:
                        continue
                    
                    # Detect unit from value or column name
                    unit, note = self.detect_unit(f"{col} {value}")
                    
                    # Store value
                    if entity_data[param] is None:
                        if unit:
                            entity_data[param] = f"{value} {unit}"
                        else:
                            entity_data[param] = str(value)
                        
                        if note not in entity_data["Notes"]:
                            entity_data["Notes"].append(note)
                        
                        entity_data["Sources"].add(source)
        else:
            # No entity column - convert to text and extract
            text = df.to_string(index=False)
            self.extract_from_text(text, source)
        
        return dict(self.global_entities)
    
    def merge_entities(self, new_data: Dict[str, Any]) -> None:
        """
        Merge new entity data into global entities.
        
        Args:
            new_data: New entity data to merge
        """
        for entity, data in new_data.items():
            if entity not in self.global_entities:
                self.global_entities[entity] = data
            else:
                # Merge parameters (don't overwrite existing values)
                for key, value in data.items():
                    if key == "Notes":
                        self.global_entities[entity]["Notes"].extend(
                            [n for n in value if n not in self.global_entities[entity]["Notes"]]
                        )
                    elif key == "Sources":
                        if isinstance(value, set):
                            self.global_entities[entity]["Sources"].update(value)
                        else:
                            self.global_entities[entity]["Sources"].add(value)
                    elif value and not self.global_entities[entity].get(key):
                        self.global_entities[entity][key] = value
    
    def format_as_markdown(self) -> str:
        """
        Format extracted entities as a Markdown table (LONG FORMAT).
        Only includes parameters that actually have data - NO placeholder rows.
        
        Returns:
            Markdown table string with one row per entity-parameter pair
        """
        if not self.global_entities:
            return "No entities detected."
        
        # Parameter order for consistent output
        PARAM_ORDER = ["Pressure", "Temperature", "Volume", "API Gravity", "Energy", 
                       "Ticket", "Sales", "Product", "Status", "Storage", "Delivery"]
        
        # Header for long format
        table = "| Entity | Parameter | Value | Unit | Notes |\n"
        table += "|--------|-----------|-------|------|-------|\n"
        
        # Rows - one per parameter with data
        for entity, data in sorted(self.global_entities.items()):
            # Only create rows for parameters that exist
            for param in PARAM_ORDER:
                value = data.get(param)
                if value and value != "—":  # Only include if parameter has actual data
                    # Extract value and unit
                    value_str = str(value)
                    unit = "—"
                    
                    # Try to extract unit from value string
                    if "psig" in value_str.lower():
                        unit = "psig"
                        value_str = value_str.replace("psig", "").replace("psi", "").strip()
                    elif "°f" in value_str.lower() or "degf" in value_str.lower():
                        unit = "°F"
                        value_str = value_str.replace("°F", "").replace("degF", "").strip()
                    elif "bbl" in value_str.lower() or "barrel" in value_str.lower():
                        unit = "bbl"
                        value_str = value_str.replace("bbl", "").replace("barrel", "").strip()
                    elif "dapi" in value_str.lower() or "°api" in value_str.lower():
                        unit = "dAPI"
                        value_str = value_str.replace("dAPI", "").replace("°API", "").strip()
                    elif "mmbtu" in value_str.lower():
                        unit = "MMBtu"
                        value_str = value_str.replace("MMBtu", "").replace("MMBTU", "").strip()
                    
                    # Clean value
                    value_str = value_str.strip()
                    
                    # Notes
                    notes = "Explicit" if "Explicit" in data.get("Notes", []) else "Inferred from context"
                    
                    table += f"| {entity} | {param} | {value_str} | {unit} | {notes} |\n"
        
        # If no parameters with data found, return message
        if table.count("\n") == 2:  # Only header rows
            return f"Entity '{list(self.global_entities.keys())[0]}' detected but no parameters with data found."
        
        return table
    
    def format_as_json(self) -> List[Dict[str, Any]]:
        """
        Format extracted entities as JSON-compatible list.
        
        Returns:
            List of entity dictionaries
        """
        result = []
        for entity, data in sorted(self.global_entities.items()):
            entry = {"Location": entity}
            for key, value in data.items():
                if key not in ["Notes", "Sources"]:
                    entry[key] = value if value else None
            
            entry["Notes"] = ", ".join([n for n in data.get("Notes", []) if n != "Unknown"]) or "Valid"
            result.append(entry)
        
        return result
    
    def reset(self):
        """Reset all extracted entities."""
        self.global_entities.clear()
    
    def get_entity_count(self) -> int:
        """Get number of detected entities."""
        return len(self.global_entities)
    
    def get_entities(self) -> List[str]:
        """Get list of detected entity names."""
        return sorted(self.global_entities.keys())


# Singleton instance
_entity_extractor = None

def get_entity_extractor() -> EntityExtractor:
    """Get or create the global entity extractor instance."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor
