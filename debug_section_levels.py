#!/usr/bin/env python3

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_section_levels():
    """Debug both main sections and subsections."""
    
    # Load the transformed JSON
    input_file = "sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json"
    
    try:
        from mapping_extractor import MappingDataExtractor
        
        extractor = MappingDataExtractor()
        
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Extract normalized data
        normalized_data = extractor.extract_from_data(raw_data)
        
        # Check the modules_structure in detail
        gap_report = normalized_data.get('gap_analysis_report', {})
        modules_structure = gap_report.get('modules_structure', {})
        
        print("Section levels analysis:")
        print("=" * 50)
        
        # Check M1 specifically
        m1_data = modules_structure.get('M1', {})
        if m1_data:
            print(f"M1: {m1_data.get('module_label', 'No label')}")
            sections = m1_data.get('sections', {})
            
            if isinstance(sections, dict):
                for section_key, section_items in sections.items():
                    print(f"\n  Section {section_key} ({type(section_items)}):")
                    if isinstance(section_items, list):
                        for i, item in enumerate(section_items):
                            if isinstance(item, dict):
                                section_id = item.get('section_id', 'No ID')
                                section_title = item.get('section_title', 'No title')
                                print(f"    [{i}] ID: {section_id}")
                                print(f"    [{i}] Title: {section_title}")
                                print(f"    [{i}] Has gap_data: {bool(item.get('gap_data'))}")
        
        # Also check the raw extracted sections (before processing)
        print("\n" + "=" * 50)
        print("Raw extracted sections:")
        sections_info = normalized_data.get('_extracted_sections_info', [])
        m1_sections = [s for s in sections_info if s.get('module_key') == 'M1']
        
        for section in m1_sections[:4]:  # Show first 4
            print(f"  ID: {section.get('section_id')}")
            print(f"  Title: {section.get('section_title')}")
            print(f"  Section Key: {section.get('section_key')}")
            print(f"  Has gap data: {bool(section.get('gap_analysis_data'))}")
            print("  ---")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_section_levels()