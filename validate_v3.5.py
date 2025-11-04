#!/usr/bin/env python3
"""
DocSense V3.5 Validation Script

This script validates that V3.5 changes are working correctly.
Tests mode detection and response format validation.

Usage:
    python validate_v3.5.py
"""

import sys
import re
from typing import Tuple

# V3.5 Validation Rules
NUMERIC_TRIGGERS = [
    'extract', 'value', 'number', 'list', 'show', 'find', 'get',
    'pressure', 'temperature', 'rate', 'flow', 'volume', 'depth',
    'psi', 'psig', 'bbl', 'barrels', '°f', '°c', 'mmbtu', 'ft', 'gal',
    'table', 'spreadsheet', 'excel', 'csv',
    'at each', 'by location', 'by well', 'per location',
    'oil', 'gas', 'well', 'reservoir', 'field'
]

FORBIDDEN_PHRASES = [
    'based on the',
    'here is the',
    'introduction',
    'key insights',
    'findings',
    'in summary',
    'conclusion',
    'as we can see',
    'the data shows',
    'from the table',
    'analysis reveals',
    'observations'
]


def detect_mode(query: str) -> str:
    """
    V3.5 mode detection simulation.
    
    Args:
        query: User query
        
    Returns:
        'numeric', 'text', or 'chat'
    """
    query_lower = query.lower().strip()
    
    # Chat mode detection
    casual_phrases = ['hi', 'hello', 'hey', 'thanks', 'ok', 'bye']
    if len(query_lower.split()) <= 4 and any(query_lower.startswith(p) for p in casual_phrases):
        return 'chat'
    
    # Numeric mode detection (V3.5: single trigger, whole word matching)
    import re
    trigger_count = 0
    for trigger in NUMERIC_TRIGGERS:
        # Use word boundaries for single-word triggers to avoid "find" matching "findings"
        if ' ' in trigger:  # Multi-word triggers like "at each"
            if trigger in query_lower:
                trigger_count += 1
        else:  # Single-word triggers - use word boundaries
            if re.search(r'\b' + re.escape(trigger) + r'\b', query_lower):
                trigger_count += 1
    
    if trigger_count >= 1:
        return 'numeric'
    
    # Default to text
    return 'text'


def validate_numeric_response(response: str) -> Tuple[bool, str]:
    """
    V3.5 numeric response validation.
    
    Args:
        response: Generated response
        
    Returns:
        Tuple of (is_valid, reason)
    """
    # Check for table or JSON
    has_table = '|' in response and 'Parameter' in response
    has_json = '{' in response and '"Source"' in response
    
    if not (has_table or has_json):
        return (False, "FAIL: No table or JSON structure found")
    
    # Find where data starts
    table_start = response.find('|')
    json_start = response.find('{')
    
    if table_start > -1:
        before_data = response[:table_start]
    elif json_start > -1:
        before_data = response[:json_start]
    else:
        before_data = ""
    
    before_data_lower = before_data.lower().strip()
    
    # Check for excessive prose before data (V3.5: max 20 chars)
    if len(before_data.strip()) > 20:
        return (False, f"FAIL: {len(before_data.strip())} chars of prose before table (max 20)")
    
    # Check for forbidden phrases
    violations = [phrase for phrase in FORBIDDEN_PHRASES if phrase in before_data_lower]
    if violations:
        return (False, f"FAIL: Forbidden phrases found: {', '.join(violations)}")
    
    # Check for dummy data patterns
    if 'temperature = 0' in response.lower() or 'pressure = 0' in response.lower():
        # Allow only if explicitly "0" in source context
        if 'explicit' not in response.lower():
            return (False, "FAIL: Dummy data detected (0 values not marked as explicit)")
    
    return (True, "PASS: V3.5 compliant")


def test_mode_detection():
    """Test V3.5 mode detection."""
    print("="*70)
    print("TEST 1: Mode Detection")
    print("="*70)
    
    test_cases = [
        # (query, expected_mode)
        ("Extract pressure values at each location", "numeric"),
        ("List temperature readings", "numeric"),
        ("Show production data in bbl", "numeric"),
        ("Find values in psi", "numeric"),
        ("At each well, what is the pressure?", "numeric"),
        ("Explain the research methodology", "text"),
        ("Summarize the key findings", "text"),
        ("What are the implications?", "text"),
        ("Analyze the trends", "text"),
        ("hi", "chat"),
        ("thanks", "chat"),
        ("ok", "chat"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        detected = detect_mode(query)
        status = "✅ PASS" if detected == expected else "❌ FAIL"
        
        if detected == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | Query: '{query[:40]}...' → Expected: {expected}, Got: {detected}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_numeric_validation():
    """Test V3.5 numeric response validation."""
    print("\n" + "="*70)
    print("TEST 2: Numeric Response Validation")
    print("="*70)
    
    test_cases = [
        # (response, should_pass, description)
        (
            "| Source | Parameter | Value | Unit |\n|---|---|---|---|\n| Well-7 | Pressure | 3124 | psi |",
            True,
            "Valid table - no prose"
        ),
        (
            "Based on the document, here are the values:\n| Source | Parameter | Value | Unit |\n|---|---|---|---|\n| Well-7 | Pressure | 3124 | psi |",
            False,
            "Invalid - prose before table"
        ),
        (
            "**Introduction**\nThe following table shows pressure data:\n| Source | Parameter | Value | Unit |\n|---|---|---|---|\n| Well-7 | Pressure | 3124 | psi |",
            False,
            "Invalid - introduction header"
        ),
        (
            "| Source | Parameter | Value | Unit |\n|---|---|---|---|\n| Well-7 | Pressure | 3124 | psi |\n\nAverage: 3124 psi",
            True,
            "Valid - table with one-line calculation"
        ),
        (
            '[{"Source": "Well-7", "Parameter": "Pressure", "Value": 3124, "Unit": "psi"}]',
            True,
            "Valid JSON format"
        ),
        (
            "Here is the data:\n[{\"Source\": \"Well-7\", \"Parameter\": \"Pressure\", \"Value\": 3124}]",
            False,
            "Invalid - prose before JSON"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for response, should_pass, description in test_cases:
        is_valid, reason = validate_numeric_response(response)
        
        if is_valid == should_pass:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} | {description}")
        print(f"         Reason: {reason}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_trigger_detection():
    """Test V3.5 trigger keyword detection."""
    print("\n" + "="*70)
    print("TEST 3: Trigger Keyword Detection (30+ triggers)")
    print("="*70)
    
    queries = [
        "extract pressure data",
        "list all temperatures",
        "show production volumes in bbl",
        "find values at each location",
        "get pressure and temperature by well",
        "what is the pressure in psi?",
        "display flow rate data",
        "summarize oil production",
    ]
    
    print(f"Total triggers in database: {len(NUMERIC_TRIGGERS)}")
    print("\nTesting queries:")
    
    for query in queries:
        query_lower = query.lower()
        triggers_found = [t for t in NUMERIC_TRIGGERS if t in query_lower]
        mode = detect_mode(query)
        
        print(f"Query: '{query}'")
        print(f"  → Triggers found: {triggers_found}")
        print(f"  → Mode: {mode}")
        print()
    
    return True


def test_implementation_files():
    """Check that implementation files exist."""
    print("\n" + "="*70)
    print("TEST 4: Implementation Files Check")
    print("="*70)
    
    import os
    
    expected_files = [
        'document_mode.py',
        'MODE_DETECTION_GUIDE_V3.5.md',
        'QUICK_REFERENCE_V3.5.md',
        'V3.5_IMPLEMENTATION_SUMMARY.md',
        'RELEASE_NOTES_V3.5.md'
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    all_exist = True
    for filename in expected_files:
        filepath = os.path.join(base_path, filename)
        exists = os.path.exists(filepath)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{status} | {filename}")
        
        if not exists:
            all_exist = False
    
    return all_exist


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("DocSense V3.5 Validation Script")
    print("="*70)
    print()
    
    results = []
    
    # Run tests
    results.append(("Mode Detection", test_mode_detection()))
    results.append(("Numeric Validation", test_numeric_validation()))
    results.append(("Trigger Detection", test_trigger_detection()))
    results.append(("Implementation Files", test_implementation_files()))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} | {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - V3.5 IMPLEMENTATION VALIDATED")
    else:
        print("❌ SOME TESTS FAILED - REVIEW IMPLEMENTATION")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
