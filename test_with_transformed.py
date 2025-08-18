#!/usr/bin/env python3

import json
import os
from pdf_generator import JSONToPDFConverter
from mapping_extractor import MappingDataExtractor, DataFormat

def main():
    print("Testing PDF generation with transformed JSON format...")
    
    # Create PDF generator
    generator = JSONToPDFConverter()
    
    # Generate PDF from the transformed JSON file
    input_file = "sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json"
    output_file = "output/transformed_mapping7.pdf"
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    try:
        # Test the mapping extractor first
        extractor = MappingDataExtractor()
        print(f"Testing mapping extractor...")
        
        # Load and analyze the file
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        detected_format = extractor.detect_format(raw_data)
        print(f"Detected format: {detected_format}")
        
        # Verify it's detected as transformed mapping
        if detected_format != DataFormat.TRANSFORMED_MAPPING:
            print(f"WARNING: Expected TRANSFORMED_MAPPING, got {detected_format}")
        else:
            print("✓ Format correctly detected as TRANSFORMED_MAPPING")
        
        # Get sections info
        sections_info = extractor.get_sections_info(raw_data)
        print(f"Found {len(sections_info)} sections:")
        for section in sections_info:
            print(f"  - Section {section['section_id']}: {section['section_title']}")
            print(f"    Module: {section['module_label']}")
            print(f"    Section Key: {section['section_key']}")
            print(f"    Format: {section['format']}")
        
        # Extract normalized data
        normalized_data = extractor.extract_from_data(raw_data)
        print(f"Normalized data structure created successfully")
        
        # Check the gap analysis report structure
        gap_report = normalized_data.get('gap_analysis_report', {})
        metadata = gap_report.get('metadata', {})
        section_analyses = gap_report.get('section_analyses', {})
        modules_structure = gap_report.get('modules_structure', {})
        
        print(f"Metadata: {metadata}")
        print(f"Number of section analyses: {len(section_analyses)}")
        print(f"Number of modules: {len(modules_structure)}")
        
        # Check synthetic metadata
        mapping_metadata = normalized_data.get('_mapping_metadata', {})
        print(f"Synthetic metadata: {mapping_metadata}")
        
        # Generate PDF
        print(f"Generating PDF...")
        generator.convert_file(input_file, output_file)  # Let it auto-generate title from filename
        print(f"PDF generated successfully: {output_file}")
        
        # Check file size
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"Output file size: {file_size:,} bytes")
        
        print("✓ Check the PDF to see the enhanced formatting for transformed JSON!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_both_formats():
    """Test both original mapping.json and transformed format for comparison."""
    print("\n" + "="*60)
    print("COMPARING BOTH FORMATS")
    print("="*60)
    
    extractor = MappingDataExtractor()
    
    # Test files
    files = [
        ("sample_data/First Sample Job Test 2_transformed_2025-08-18T09-39-44-682Z.json", "Transformed JSON")
    ]
    
    for file_path, file_type in files:
        if not os.path.exists(file_path):
            print(f"❌ {file_type}: File not found - {file_path}")
            continue
            
        print(f"\n--- {file_type} ---")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Test detection
            detected_format = extractor.detect_format(data)
            print(f"Detected format: {detected_format}")
            
            # Test extraction
            normalized_data = extractor.extract_from_data(data)
            gap_report = normalized_data.get('gap_analysis_report', {})
            metadata = gap_report.get('metadata', {})
            
            print(f"Sections analyzed: {metadata.get('sections_analyzed', 'N/A')}")
            print(f"Total checkpoints: {metadata.get('total_checkpoints', 'N/A')}")
            print(f"Coverage percentage: {metadata.get('overall_coverage_percentage', 'N/A')}%")
            
            # Check modules structure
            modules_structure = gap_report.get('modules_structure', {})
            print(f"Modules found: {list(modules_structure.keys())}")
            
        except Exception as e:
            print(f"❌ Error processing {file_type}: {e}")

if __name__ == "__main__":
    main()
    test_both_formats()