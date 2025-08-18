#!/usr/bin/env python3

import json
import os
from pdf_generator import JSONToPDFConverter
from mapping_extractor import MappingDataExtractor, DataFormat

def main():
    print("Testing PDF generation with mapping.json...")
    
    # Create PDF generator
    generator = JSONToPDFConverter()
    
    # Generate PDF from the mapping.json file
    input_file = "sample_data/mapping.json"
    output_file = "output/mapping11.pdf"
    
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
        
        # Get sections info
        sections_info = extractor.get_sections_info(raw_data)
        print(f"Found {len(sections_info)} sections:")
        for section in sections_info:
            print(f"  - Section {section['section_id']}: {section['section_title']}")
            print(f"    Module: {section['module_label']}")
            print(f"    Section Key: {section['section_key']}")
        
        # Extract normalized data
        normalized_data = extractor.extract_from_data(raw_data)
        print(f"Normalized data structure created successfully")
        
        # Check the gap analysis report structure
        gap_report = normalized_data.get('gap_analysis_report', {})
        metadata = gap_report.get('metadata', {})
        section_analyses = gap_report.get('section_analyses', {})
        
        print(f"Metadata: {metadata}")
        print(f"Number of section analyses: {len(section_analyses)}")
        
        # Generate PDF
        print(f"Generating PDF...")
        generator.convert_file(input_file, output_file)  # Let it auto-generate title from filename
        print(f"PDF generated successfully: {output_file}")
        
        # Check file size
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"Output file size: {file_size:,} bytes")
        
        print("Check the PDF to see the enhanced formatting for mapping.json!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
