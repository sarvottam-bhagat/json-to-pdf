#!/usr/bin/env python3

import json
from pdf_generator import JSONToPDFConverter

def main():
    print("Testing PDF generation with test.json...")
    
    # Create PDF generator
    generator = JSONToPDFConverter()
    
    # Generate PDF from the test.json file
    input_file = "sample_data/test.json"
    output_file = "output/test_json_output7.pdf"
    
    try:
        generator.convert_file(input_file, output_file, title="Gap Analysis Report")
        print(f"PDF generated successfully: {output_file}")
        print("Check the PDF to see the numbered section formatting!")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == "__main__":
    main()
