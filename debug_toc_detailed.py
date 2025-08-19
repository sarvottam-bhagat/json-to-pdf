#!/usr/bin/env python3

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_modules_structure():
    """Debug the modules_structure in detail."""
    
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
        
        print("Detailed modules_structure analysis:")
        print("=" * 50)
        
        for module_key, module_data in modules_structure.items():
            if isinstance(module_data, dict):
                print(f"\n{module_key}: {module_data.get('module_label', 'No label')}")
                sections = module_data.get('sections', {})
                
                if isinstance(sections, dict):
                    print(f"  Sections (dict with {len(sections)} items):")
                    for section_key, section_data in sections.items():
                        print(f"    {section_key}: {type(section_data)}")
                        if isinstance(section_data, list) and section_data:
                            first_item = section_data[0]
                            if isinstance(first_item, dict):
                                print(f"      First item keys: {list(first_item.keys())[:5]}")
                                print(f"      section_title: {first_item.get('section_title', 'Not found')}")
                                print(f"      pre_ind_maps: {len(first_item.get('pre_ind_maps', []))} items")
                elif isinstance(sections, list):
                    print(f"  Sections (list with {len(sections)} items):")
                    for i, section in enumerate(sections[:2]):
                        if isinstance(section, dict):
                            print(f"    [{i}] section_key: {section.get('section_key')}")
                            print(f"    [{i}] section_title: {section.get('section_title')}")
        
        print("\n" + "=" * 50)
        print("Direct raw data check (first module):")
        # Check raw data structure
        m1_data = raw_data.get('M1', {})
        raw_sections = m1_data.get('sections', [])
        print(f"M1 sections type in raw data: {type(raw_sections)}")
        if isinstance(raw_sections, list) and raw_sections:
            first_section = raw_sections[0]
            print(f"First section keys: {list(first_section.keys()) if isinstance(first_section, dict) else 'Not dict'}")
            if isinstance(first_section, dict):
                print(f"section_key: {first_section.get('section_key')}")
                print(f"section_title: {first_section.get('section_title')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_modules_structure()