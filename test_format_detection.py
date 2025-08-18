#!/usr/bin/env python3

import json
import os
import sys

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mapping_extractor import MappingDataExtractor, DataFormat

def test_format_detection():
    """Test format detection for both original and transformed JSON formats."""
    print("Testing format detection...")
    
    extractor = MappingDataExtractor()
    
    # Test files
    test_cases = [
        ("sample_data/mapping.json", DataFormat.MAPPING_JSON, "Original Mapping JSON"),
        ("sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json", DataFormat.TRANSFORMED_MAPPING, "Transformed JSON")
    ]
    
    for file_path, expected_format, description in test_cases:
        print(f"\n--- Testing {description} ---")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Test detection
            detected_format = extractor.detect_format(data)
            print(f"File: {os.path.basename(file_path)}")
            print(f"Expected format: {expected_format}")
            print(f"Detected format: {detected_format}")
            
            if detected_format == expected_format:
                print("✅ Format detection PASSED")
            else:
                print("❌ Format detection FAILED")
                continue
            
            # Test data structure
            print(f"Top-level keys: {list(data.keys())}")
            
            # Test extraction
            print("Testing data extraction...")
            normalized_data = extractor.extract_from_data(data)
            
            # Check structure
            gap_report = normalized_data.get('gap_analysis_report', {})
            metadata = gap_report.get('metadata', {})
            section_analyses = gap_report.get('section_analyses', {})
            modules_structure = gap_report.get('modules_structure', {})
            
            print(f"✅ Extraction successful:")
            print(f"   - Sections analyzed: {metadata.get('sections_analyzed', 'N/A')}")
            print(f"   - Total checkpoints: {metadata.get('total_checkpoints', 'N/A')}")
            print(f"   - Section analyses: {len(section_analyses)}")
            print(f"   - Modules: {len(modules_structure)}")
            
            # Check synthetic metadata for transformed format
            if detected_format == DataFormat.TRANSFORMED_MAPPING:
                mapping_metadata = normalized_data.get('_mapping_metadata', {})
                print(f"   - Synthetic metadata: {mapping_metadata.get('name', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error processing {description}: {e}")
            import traceback
            traceback.print_exc()

def test_transformed_structure():
    """Test the internal structure of transformed JSON."""
    print("\n" + "="*60)
    print("TESTING TRANSFORMED JSON STRUCTURE")
    print("="*60)
    
    file_path = "sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json"
    
    if not os.path.exists(file_path):
        print(f"❌ Transformed file not found: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"File structure analysis:")
    print(f"  - Top-level keys: {list(data.keys())}")
    
    # Check module structure
    for module_key, module_data in data.items():
        if module_key.startswith('M'):
            print(f"\nModule {module_key}:")
            print(f"  - Label: {module_data.get('label', 'N/A')}")
            print(f"  - Sections count: {len(module_data.get('sections', []))}")
            
            # Show first section structure
            sections = module_data.get('sections', [])
            if sections:
                section = sections[0]
                print(f"  - Sample section:")
                print(f"    - Section key: {section.get('section_key', 'N/A')}")
                print(f"    - Section title: {section.get('section_title', 'N/A')}")
                print(f"    - Pre-IND maps: {len(section.get('pre_ind_maps', []))}")

if __name__ == "__main__":
    test_format_detection()
    test_transformed_structure()