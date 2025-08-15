# JSON to PDF Converter

A Python application that converts JSON data into visually appealing PDF documents with professional styling and formatting.

## Features

- **Professional PDF Generation**: Convert JSON files or data to beautifully formatted PDFs
- **Complex Structure Support**: Handle nested objects, arrays, and mixed data types
- **Multiple Color Schemes**: Choose from 6 built-in color schemes (default, blue, green, purple, orange, dark)
- **Visual Hierarchy**: Color-coded data types, proper indentation, and visual separators
- **Command-line Interface**: Easy-to-use CLI with comprehensive options
- **Python API**: Programmatic access for integration into other applications
- **Robust Error Handling**: Comprehensive error handling with meaningful messages
- **Modular Design**: Well-documented, extensible codebase

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage
```bash
# Convert a JSON file to PDF
python json_to_pdf.py sample_data/simple.json output/simple.pdf

# Convert with custom title and color scheme
python json_to_pdf.py sample_data/complex.json output/report.pdf --title "Company Data" --color-scheme blue

# Run test with sample test.json file
python test_with_testjson.py
```

### Using JSON String Input
```python
# For JSON string input, use the Python API
from pdf_generator import JSONToPDFConverter
from pdf_styles import ColorScheme

converter = JSONToPDFConverter(ColorScheme.GREEN)
data = {"name": "John", "age": 30, "skills": ["Python", "JavaScript"]}
converter.convert_data(data, "output.pdf", "User Profile")
```

## Command Line Interface

### Syntax
```bash
python json_to_pdf.py [OPTIONS] input_file output_file
```

### Options
- `--title TITLE`: Custom title for the PDF document
- `--color-scheme SCHEME`: Color scheme (default, blue, green, purple, orange, dark)
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message
- `--version`: Show version information

### Examples
```bash
# Basic conversion
python json_to_pdf.py data.json report.pdf

# With custom styling
python json_to_pdf.py data.json report.pdf --title "Sales Report" --color-scheme blue

# Verbose output
python json_to_pdf.py data.json report.pdf --verbose

# Different color schemes
python json_to_pdf.py data.json dark_report.pdf --color-scheme dark
python json_to_pdf.py data.json green_report.pdf --color-scheme green
```

## Python API

### Basic Usage
```python
from pdf_generator import JSONToPDFConverter
from pdf_styles import ColorScheme

# Create converter with default styling
converter = JSONToPDFConverter()

# Convert file to PDF
converter.convert_file('input.json', 'output.pdf', 'My Document')

# Convert data directly
data = {"key": "value", "numbers": [1, 2, 3]}
converter.convert_data(data, 'output.pdf', 'My Data')
```

### Advanced Usage
```python
from pdf_generator import JSONToPDFConverter
from pdf_styles import ColorScheme

# Use custom color scheme
converter = JSONToPDFConverter(ColorScheme.PURPLE)

# Handle complex nested data
complex_data = {
    "company": {
        "name": "Tech Corp",
        "employees": [
            {"name": "Alice", "role": "Developer"},
            {"name": "Bob", "role": "Designer"}
        ]
    }
}

converter.convert_data(complex_data, 'company_data.pdf', 'Company Information')
```

## Color Schemes

The application supports 6 built-in color schemes:

- **default**: Professional blue and gray tones
- **blue**: Various shades of blue with high contrast
- **green**: Nature-inspired green palette
- **purple**: Modern purple and violet tones
- **orange**: Warm orange and amber colors
- **dark**: Dark theme with light text (great for presentations)