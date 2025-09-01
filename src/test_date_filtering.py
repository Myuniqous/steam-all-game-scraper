#!/usr/bin/env python3
"""
Test script to validate Steam date filtering logic
"""

import sys
import os
from datetime import datetime, timedelta
import re

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions from app.py
from app import parse_steam_date_to_comparable, is_steam_date_in_range

def test_date_parsing():
    """Test the date parsing function"""
    print("=" * 60)
    print("TESTING DATE PARSING FUNCTION")
    print("=" * 60)
    
    test_dates = [
        # Valid specific dates
        "16 Oct, 2024",
        "Oct 16, 2024", 
        "October 16, 2024",
        "1 Nov, 2024",
        "Nov 1, 2024",
        "November 1, 2024",
        
        # Valid month/year dates
        "October 2024",
        "Oct 2024",
        "November 2024",
        "Nov 2024",
        "April 2025",
        "August 2025",
        
        # Invalid/vague dates (should return None)
        "2024",
        "Q1 2024",
        "Q2 2025",
        "Unknown",
        "TBA",
        "Coming Soon",
        "",
        None
    ]
    
    for date_str in test_dates:
        result = parse_steam_date_to_comparable(date_str)
        status = "✓ PARSED" if result else "✗ REJECTED"
        print(f"{status:<12} | {str(date_str):<20} | {result}")

def test_date_filtering():
    """Test the date filtering function with specific ranges"""
    print("\n" + "=" * 60)
    print("TESTING DATE FILTERING FUNCTION")
    print("=" * 60)
    
    # Test cases for October 2024 range (1 Oct to 31 Oct)
    test_cases = [
        {
            "range": ("2024-10-01", "2024-10-31"),
            "range_name": "October 2024 (1-31 Oct)",
            "dates": [
                # Should be INCLUDED
                ("16 Oct, 2024", True, "Specific October date"),
                ("Oct 16, 2024", True, "Specific October date (alt format)"),
                ("October 16, 2024", True, "Specific October date (full month)"),
                ("1 Oct, 2024", True, "First day of October"),
                ("31 Oct, 2024", True, "Last day of October"),
                ("October 2024", True, "Month/year October"),
                ("Oct 2024", True, "Month/year October (short)"),
                
                # Should be EXCLUDED
                ("30 Apr, 2025", False, "April date (wrong month/year)"),
                ("August 2025", False, "August month/year (wrong month/year)"),
                ("1 May, 2025", False, "May date (wrong month/year)"),
                ("16 Sep, 2024", False, "September date (wrong month)"),
                ("16 Nov, 2024", False, "November date (wrong month)"),
                ("November 2024", False, "November month/year (wrong month)"),
                ("2024", False, "Vague year only"),
                ("Q1 2024", False, "Vague quarter"),
                ("Unknown", False, "Unknown date"),
            ]
        },
        {
            "range": ("2024-11-01", "2024-11-30"),
            "range_name": "November 2024 (1-30 Nov)",
            "dates": [
                # Should be INCLUDED
                ("16 Nov, 2024", True, "Specific November date"),
                ("Nov 16, 2024", True, "Specific November date (alt format)"),
                ("November 16, 2024", True, "Specific November date (full month)"),
                ("November 2024", True, "Month/year November"),
                ("Nov 2024", True, "Month/year November (short)"),
                
                # Should be EXCLUDED
                ("16 Oct, 2024", False, "October date (wrong month)"),
                ("October 2024", False, "October month/year (wrong month)"),
                ("16 Dec, 2024", False, "December date (wrong month)"),
                ("December 2024", False, "December month/year (wrong month)"),
            ]
        }
    ]
    
    for test_case in test_cases:
        start_date, end_date = test_case["range"]
        range_name = test_case["range_name"]
        
        print(f"\nTesting range: {range_name}")
        print(f"Date range: {start_date} to {end_date}")
        print("-" * 60)
        
        all_passed = True
        
        for steam_date, expected, description in test_case["dates"]:
            result = is_steam_date_in_range(steam_date, start_date, end_date)
            
            if result == expected:
                status = "✓ PASS"
            else:
                status = "✗ FAIL"
                all_passed = False
                
            expected_str = "INCLUDE" if expected else "EXCLUDE"
            result_str = "INCLUDED" if result else "EXCLUDED"
            
            print(f"{status:<8} | {steam_date:<20} | Expected: {expected_str:<8} | Got: {result_str:<8} | {description}")
        
        print(f"\nRange Summary: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

def test_edge_cases():
    """Test edge cases and problematic scenarios"""
    print("\n" + "=" * 60)
    print("TESTING EDGE CASES")
    print("=" * 60)
    
    edge_cases = [
        # Month boundary tests
        ("September 2024", "2024-09-30", "2024-10-01", False, "Sep month vs Oct range"),
        ("October 2024", "2024-09-30", "2024-10-01", True, "Oct month overlaps Oct range"),
        ("October 2024", "2024-10-15", "2024-10-25", True, "Oct month overlaps mid-Oct range"),
        ("October 2024", "2024-11-01", "2024-11-30", False, "Oct month vs Nov range"),
        
        # Year boundary tests
        ("December 2024", "2024-12-31", "2025-01-01", True, "Dec 2024 overlaps year boundary"),
        ("January 2025", "2024-12-31", "2025-01-01", True, "Jan 2025 overlaps year boundary"),
        
        # Specific date tests
        ("15 Oct, 2024", "2024-10-01", "2024-10-31", True, "Mid-October specific date"),
        ("15 Oct, 2024", "2024-10-16", "2024-10-31", False, "Specific date before range start"),
        ("15 Oct, 2024", "2024-10-01", "2024-10-14", False, "Specific date after range end"),
    ]
    
    for steam_date, start_date, end_date, expected, description in edge_cases:
        result = is_steam_date_in_range(steam_date, start_date, end_date)
        
        if result == expected:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            
        expected_str = "INCLUDE" if expected else "EXCLUDE"
        result_str = "INCLUDED" if result else "EXCLUDED"
        
        print(f"{status:<8} | {steam_date:<20} | Range: {start_date} to {end_date} | Expected: {expected_str:<8} | Got: {result_str:<8} | {description}")

def main():
    print("Steam Date Filtering Test Suite")
    print("Testing current implementation in app.py")
    
    test_date_parsing()
    test_date_filtering() 
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print("\nIf you see any FAIL results above, the date filtering logic needs to be fixed.")
    print("Focus on the specific cases that failed to understand the issue.")

if __name__ == "__main__":
    main()