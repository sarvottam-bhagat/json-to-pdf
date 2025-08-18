#!/usr/bin/env python3

import json
import os
from pdf_generator import JSONToPDFConverter
from mapping_extractor import MappingDataExtractor, DataFormat

def main():
    print("Testing PDF generation with test.json...")

    # Create PDF generator
    generator = JSONToPDFConverter()

    # Generate PDF from the test.json file
    input_file = "sample_data/test.json"
    output_file = "output/test_json_enhanced.pdf"

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    try:
        # Test the format detection
        extractor = MappingDataExtractor()
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        detected_format = extractor.detect_format(raw_data)
        print(f"Detected format: {detected_format}")

        # Generate PDF with enhanced features
        generator.convert_file(input_file, output_file, title="Gap Analysis Report - Test JSON")
        print(f"PDF generated successfully: {output_file}")

        # Check file size
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"Output file size: {file_size:,} bytes")

        print("Check the PDF to see the enhanced formatting with backward compatibility!")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
