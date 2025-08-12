#!/usr/bin/env python3
"""
JSON to PDF Converter - Command Line Interface

A command-line tool for converting JSON data into visually appealing PDF documents
with professional styling and formatting.

Usage:
    python json_to_pdf.py input.json output.pdf
    python json_to_pdf.py --json '{"key": "value"}' output.pdf
"""

import argparse
import sys
import os
import json
from typing import Optional

from pdf_generator import JSONToPDFConverter, PDFGenerationError
from pdf_styles import ColorScheme, get_available_color_schemes
from json_parser import JSONParseError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert JSON data to visually appealing PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json report.pdf
  %(prog)s --json '{"name": "John", "age": 30}' output.pdf
  %(prog)s data.json report.pdf --title "My Report" --color-scheme blue
  %(prog)s data.json report.pdf --color-scheme dark --title "Dark Theme Report"

Available color schemes: """ + ", ".join(get_available_color_schemes())
    )
    
    # JSON string input (alternative to file)
    parser.add_argument(
        '--json',
        type=str,
        help='JSON string to convert (alternative to input file)'
    )

    # Input file (positional, optional)
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Path to input JSON file'
    )

    # Output file
    parser.add_argument(
        'output_file',
        help='Path to output PDF file'
    )
    
    # Styling options
    parser.add_argument(
        '--title',
        type=str,
        help='Title for the PDF document'
    )
    
    parser.add_argument(
        '--color-scheme',
        choices=get_available_color_schemes(),
        default='default',
        help='Color scheme for the PDF (default: default)'
    )
    
    # Additional options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='JSON to PDF Converter 1.0.0'
    )
    
    return parser


def validate_arguments(args) -> None:
    """Validate command line arguments."""
    # Check that either input_file or --json is provided
    if not args.input_file and not args.json:
        raise ValueError("Either input_file or --json must be provided")

    if args.input_file and args.json:
        raise ValueError("Cannot specify both input_file and --json")

    # Check input file exists if provided
    if args.input_file and not os.path.exists(args.input_file):
        raise FileNotFoundError(f"Input file not found: {args.input_file}")

    # Check if output directory exists
    output_dir = os.path.dirname(os.path.abspath(args.output_file))
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    # Check if output file has .pdf extension
    if not args.output_file.lower().endswith('.pdf'):
        print("Warning: Output file doesn't have .pdf extension", file=sys.stderr)


def main():
    """Main entry point for the CLI application."""
    parser = create_parser()
    
    try:
        args = parser.parse_args()
        
        # Validate arguments
        validate_arguments(args)
        
        if args.verbose:
            print(f"Input: {args.input_file or 'JSON string'}")
            print(f"Output: {args.output_file}")
            print(f"Color scheme: {args.color_scheme}")
            if args.title:
                print(f"Title: {args.title}")
        
        # Create converter with specified color scheme
        color_scheme = ColorScheme(args.color_scheme)
        converter = JSONToPDFConverter(color_scheme)
        
        # Convert based on input type
        if args.input_file:
            # Convert from file
            title = args.title or f"JSON Document: {os.path.basename(args.input_file)}"
            
            if args.verbose:
                print(f"Converting file: {args.input_file}")
            
            converter.convert_file(args.input_file, args.output_file, title)
            
        else:
            # Convert from JSON string
            try:
                data = json.loads(args.json)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON string: {e}", file=sys.stderr)
                sys.exit(1)
            
            title = args.title or "JSON Document"
            
            if args.verbose:
                print("Converting JSON string")
            
            converter.convert_data(data, args.output_file, title)
        
        print(f"Successfully created PDF: {args.output_file}")
        
        if args.verbose:
            file_size = os.path.getsize(args.output_file)
            print(f"Output file size: {file_size:,} bytes")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except JSONParseError as e:
        print(f"JSON Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except PDFGenerationError as e:
        print(f"PDF Generation Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
