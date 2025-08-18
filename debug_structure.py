#!/usr/bin/env python3

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mapping_extractor import MappingDataExtractor, DataFormat

def debug_structure():
    """Debug the structure of transformed JSON to understand modules_structure."""
    
    extractor = MappingDataExtractor()
    file_path = "sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Extract normalized data
    normalized_data = extractor.extract_from_data(raw_data)
    gap_report = normalized_data.get('gap_analysis_report', {})
    modules_structure = gap_report.get('modules_structure', {})
    
    print("MODULES STRUCTURE:")
    print("=" * 50)
    
    for module_key, module_data in modules_structure.items():
        print(f"\n{module_key}:")
        print(f"  Label: {module_data.get('module_label', 'N/A')}")
        
        sections = module_data.get('sections', {})
        print(f"  Sections ({len(sections)}):")
        
        for section_key, section_items in sections.items():
            print(f"    Section {section_key}:")
            for i, item in enumerate(section_items):
                section_id = item.get('section_id', 'N/A')
                section_title = item.get('section_title', 'N/A')
                print(f"      [{i}] {section_id}: {section_title}")

if __name__ == "__main__":
    debug_structure()