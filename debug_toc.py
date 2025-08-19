#!/usr/bin/env python3

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_toc_generation():
    """Debug which TOC generation method is being called."""
    
    # Load the transformed JSON
    input_file = "sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json"
    
    try:
        from mapping_extractor import MappingDataExtractor
        
        extractor = MappingDataExtractor()
        
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Extract normalized data
        normalized_data = extractor.extract_from_data(raw_data)
        
        # Check the structure
        gap_report = normalized_data.get('gap_analysis_report', {})
        
        print("Data structure analysis:")
        print("=" * 50)
        
        # Check what's available in the gap report
        print("Gap report keys:", list(gap_report.keys()))
        
        # Check if we have modules_structure
        modules_structure = gap_report.get('modules_structure', {})
        section_analyses = gap_report.get('section_analyses', {})
        
        print(f"Has modules_structure: {bool(modules_structure)}")
        print(f"Has section_analyses: {bool(section_analyses)}")
        
        if modules_structure:
            print("\nModules structure:")
            for module_key, module_data in modules_structure.items():
                if isinstance(module_data, dict):
                    print(f"  {module_key}: {module_data.get('module_label', 'No label')}")
                    sections = module_data.get('sections', {})
                    print(f"    Sections type: {type(sections)}")
                    if isinstance(sections, list):
                        print("    Section items:")
                        for i, section in enumerate(sections[:2]):  # Show first 2
                            if isinstance(section, dict):
                                print(f"      [{i}] section_key: {section.get('section_key')}")
                                print(f"      [{i}] section_title: {section.get('section_title')}")
                    elif isinstance(sections, dict):
                        print("    Section keys:", list(sections.keys())[:3])
        
        if section_analyses:
            print("\nSection analyses:")
            for section_key, section_data in list(section_analyses.items())[:2]:  # Show first 2
                if isinstance(section_data, dict):
                    print(f"  {section_key}: {section_data.get('section_title', 'No title')}")
        
    except ImportError as e:
        print(f"Import error (expected without ReportLab): {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_toc_generation()