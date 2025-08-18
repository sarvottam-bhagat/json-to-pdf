#!/usr/bin/env python3

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mapping_extractor import MappingDataExtractor, DataFormat

def test_toc_structure():
    """Test just the TOC entries generation without full PDF."""
    
    print("Testing TOC entries generation...")
    
    extractor = MappingDataExtractor()
    file_path = "sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Extract normalized data
    normalized_data = extractor.extract_from_data(raw_data)
    
    # Simulate TOC generation logic from pdf_generator.py
    toc_entries = []
    gap_report = normalized_data.get('gap_analysis_report', {})
    modules_structure = gap_report.get('modules_structure', {})
    
    print("Simulated PDF TOC entries would be:")
    print("=" * 50)
    
    # Sort modules by numerical order (M1, M2, M3, etc.)
    def module_sort_key(item):
        module_key = item[0]
        try:
            if module_key.startswith('M'):
                return int(module_key[1:])
            else:
                return float('inf')
        except (ValueError, IndexError):
            return float('inf')

    sorted_modules = sorted(modules_structure.items(), key=module_sort_key)
    
    for module_key, module_data in sorted_modules:
        module_label = module_data.get('module_label', module_key)
        print(f"Level 0: {module_label}")
        
        sections = module_data.get('sections', {})
        sorted_sections = sorted(sections.items(), key=lambda x: x[0])
        
        for section_key, section_items in sorted_sections:
            print(f"Level 1:     Section {section_key}")
            
            for item in section_items:
                section_id = item.get('section_id', section_key)
                section_title = item.get('section_title', '')
                print(f"Level 2:         {section_id}: {section_title}")

if __name__ == "__main__":
    test_toc_structure()