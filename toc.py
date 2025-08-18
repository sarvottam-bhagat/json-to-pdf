import json
import os
import sys
from mapping_extractor import MappingDataExtractor, DataFormat

def generate_toc_for_file(input_file, output_file):
    """Generate table of contents for a JSON file."""
    print(f"Generating TOC for: {input_file}")

    # Load data
    with open(input_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Extract and normalize data
    extractor = MappingDataExtractor()
    detected_format = extractor.detect_format(raw_data)
    normalized_data = extractor.extract_from_data(raw_data)

    print(f"Detected format: {detected_format}")

    # Generate TOC
    toc = []
    gap_report = normalized_data.get("gap_analysis_report", {})
    section_analyses = gap_report.get("section_analyses", {})

    # Add format information
    format_name = "Mapping JSON" if detected_format == DataFormat.MAPPING_JSON else "Test JSON"
    toc.append(f"Gap Analysis Report - {format_name}")
    toc.append("=" * 50)
    toc.append("")

    # Add metadata if available
    if "_mapping_metadata" in normalized_data:
        mapping_meta = normalized_data["_mapping_metadata"]
        toc.append("Source Information:")
        if mapping_meta.get("name"):
            toc.append(f"  Job Name: {mapping_meta['name']}")
        if mapping_meta.get("filename"):
            filenames = mapping_meta["filename"]
            if isinstance(filenames, list):
                toc.append(f"  Source Files: {', '.join(filenames)}")
            else:
                toc.append(f"  Source File: {filenames}")
        toc.append("")

    # Sort sections by section number for proper ordering
    def sort_key(item):
        section_id, section_data = item
        if isinstance(section_data, dict):
            section_num = section_data.get('section', section_id)
            # Parse section number for proper sorting (e.g., "1.1", "1.2", "1.10")
            try:
                # Split by dots and convert to integers for proper numerical sorting
                parts = [int(x) for x in str(section_num).split('.')]
                return parts
            except (ValueError, AttributeError):
                # Fallback to string sorting if parsing fails
                return [float('inf'), str(section_num)]
        return [float('inf'), section_id]

    sorted_sections = sorted(section_analyses.items(), key=sort_key)

    # Add sections in sorted order
    for section_id, section_data in sorted_sections:
        section_title = section_data.get("section_title", "")
        toc.append(f"Section {section_id}: {section_title}")

        coverage_analysis = []
        coverage_categories = section_data.get("coverage_categories", {})
        for category, details in coverage_categories.items():
            if isinstance(details, dict) and "checkpoint_count" in details:
                checkpoint_count = details["checkpoint_count"]
                category_name = category.replace('_', ' ').title()
                coverage_analysis.append(f"{category_name}: {checkpoint_count} checkpoints")

        if coverage_analysis:
            toc.append("\t\t" + "\n\t\t".join(coverage_analysis))
        toc.append("")

    # Write TOC
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(toc))

    print(f"TOC generated: {output_file}")

def main():
    # Generate TOC for both formats
    test_files = [
        ("sample_data/test.json", "output/toc_test.txt"),
        ("sample_data/mapping.json", "output/toc_mapping.txt")
    ]

    for input_file, output_file in test_files:
        if os.path.exists(input_file):
            try:
                generate_toc_for_file(input_file, output_file)
            except Exception as e:
                print(f"Error processing {input_file}: {e}")
        else:
            print(f"File not found: {input_file}")

if __name__ == "__main__":
    main()