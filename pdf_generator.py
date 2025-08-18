"""
PDF Generation Engine

This module contains the core PDF generation logic using ReportLab,
including document structure, page layout, content rendering, and
proper formatting for nested JSON structures.
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import PageBreak, KeepTogether, HRFlowable
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF
from datetime import datetime
from typing import Any, List, Dict, Union
import os
import re

from json_parser import JSONParser, JSONDataType, JSONValidator, format_value_for_display
from pdf_styles import PDFStyleManager, PDFStyleConfig, ColorScheme
from mapping_extractor import MappingDataExtractor, DataFormat


class PDFGenerationError(Exception):
    """Custom exception for PDF generation errors."""
    pass


class JSONToPDFConverter:
    """Main class for converting JSON data to PDF documents."""
    
    def __init__(self, color_scheme: ColorScheme = ColorScheme.DEFAULT, exclude_keys: List[str] = None):
        """
        Initialize the converter with specified styling.

        Args:
            color_scheme: Color scheme to use for the PDF
            exclude_keys: Optional list of JSON keys to skip when rendering
        """
        self.style_manager = PDFStyleManager(color_scheme)
        self.parser = JSONParser()
        self.validator = JSONValidator()
        self.mapping_extractor = MappingDataExtractor()
        # Keys to exclude from rendering (case-insensitive)
        default_excluded = {"checkpoint_details", "_mapping_metadata", "_extracted_sections_info", "combined_supporting_evidence"}
        self.excluded_keys = set(k.lower() for k in (exclude_keys or [])) or default_excluded
        # Keys that should never be treated as headers even if they contain header-like words
        self.non_header_keys = {
            'sections_analyzed',
            'total_checkpoints',
            'overall_coverage_percentage',
            'total_input_chunks_analyzed',
            'status'
        }
        # Table of contents tracking
        self.toc_entries = []
        
    def convert_file(self, input_file: str, output_file: str, title: str = None) -> None:
        """
        Convert a JSON file to PDF.

        Args:
            input_file: Path to input JSON file
            output_file: Path to output PDF file
            title: Optional title for the document

        Raises:
            PDFGenerationError: If conversion fails
        """
        try:
            # First parse the raw data
            raw_data, analysis = self.parser.parse_file(input_file)

            # Extract and normalize data using mapping extractor
            normalized_data = self.mapping_extractor.extract_from_data(raw_data)

            # Re-analyze the normalized data structure
            normalized_analysis = self.validator.analyze_structure(normalized_data)

            if title is None:
                # Create a more descriptive title based on detected format
                detected_format = self.mapping_extractor.get_detected_format()
                # Clean up filename: remove extension and shorten if too long
                filename = os.path.basename(input_file)
                clean_name = os.path.splitext(filename)[0]  # Remove extension
                if len(clean_name) > 50:  # Shorten very long names
                    clean_name = clean_name[:47] + "..."
                
                if detected_format in [DataFormat.MAPPING_JSON, DataFormat.TRANSFORMED_MAPPING]:
                    title = f"Gap Analysis Report: {clean_name}"
                else:
                    title = f"JSON Document: {clean_name}"

            self._generate_pdf(normalized_data, normalized_analysis, output_file, title, input_file)

        except Exception as e:
            raise PDFGenerationError(f"Failed to convert file {input_file}: {e}")
    
    def convert_data(self, data: Any, output_file: str, title: str = "JSON Document") -> None:
        """
        Convert JSON data to PDF.

        Args:
            data: JSON data to convert
            output_file: Path to output PDF file
            title: Title for the document

        Raises:
            PDFGenerationError: If conversion fails
        """
        try:
            if not self.parser.validate_data(data):
                raise PDFGenerationError("Data is not JSON-serializable")

            # Extract and normalize data using mapping extractor
            normalized_data = self.mapping_extractor.extract_from_data(data)

            # Re-analyze the normalized data structure
            normalized_analysis = self.validator.analyze_structure(normalized_data)

            # Update title based on detected format if it's the default
            if title == "JSON Document":
                detected_format = self.mapping_extractor.get_detected_format()
                if detected_format in [DataFormat.MAPPING_JSON, DataFormat.TRANSFORMED_MAPPING]:
                    title = "Gap Analysis Report"

            self._generate_pdf(normalized_data, normalized_analysis, output_file, title)

        except Exception as e:
            raise PDFGenerationError(f"Failed to convert data: {e}")
    
    def _generate_pdf(self, data: Any, analysis: Dict, output_file: str,
                     title: str, source_file: str = None) -> None:
        """
        Generate the actual PDF document.

        Args:
            data: Parsed JSON data
            analysis: Structure analysis
            output_file: Output file path
            title: Document title
            source_file: Source file path (optional)
        """
        try:
            # Validate output directory
            output_dir = os.path.dirname(os.path.abspath(output_file))
            if not os.path.exists(output_dir):
                raise PDFGenerationError(f"Output directory does not exist: {output_dir}")

            if not os.access(output_dir, os.W_OK):
                raise PDFGenerationError(f"No write permission for directory: {output_dir}")

            # Check if file already exists and is writable
            if os.path.exists(output_file) and not os.access(output_file, os.W_OK):
                raise PDFGenerationError(f"Cannot write to existing file: {output_file}")

            # Create document
            try:
                doc = SimpleDocTemplate(
                    output_file,
                    pagesize=A4,
                    topMargin=PDFStyleConfig.MARGIN_TOP,
                    bottomMargin=PDFStyleConfig.MARGIN_BOTTOM,
                    leftMargin=PDFStyleConfig.MARGIN_LEFT,
                    rightMargin=PDFStyleConfig.MARGIN_RIGHT
                )
            except Exception as e:
                raise PDFGenerationError(f"Failed to create PDF document template: {e}")

            # Build content
            story = []

            try:
                # Add title
                story.append(Paragraph(title, self.style_manager.get_style('title')))
                story.append(Spacer(1, 20))

                # First pass: collect TOC entries by rendering content
                self.toc_entries = []
                content = self._render_json_content(data, 0, data)

                # Add Table of Contents if we have entries
                if self.toc_entries:
                    toc = self._create_table_of_contents()
                    story.extend(toc)
                    story.append(PageBreak())

                # Add JSON content
                story.extend(content)

            except Exception as e:
                raise PDFGenerationError(f"Failed to build PDF content: {e}")

            # Build PDF
            try:
                doc.build(story)
            except Exception as e:
                # Clean up partial file if it exists
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except:
                        pass  # Ignore cleanup errors
                raise PDFGenerationError(f"Failed to write PDF file: {e}")

            # Verify the file was created successfully
            if not os.path.exists(output_file):
                raise PDFGenerationError("PDF file was not created successfully")

            if os.path.getsize(output_file) == 0:
                raise PDFGenerationError("Generated PDF file is empty")

        except PDFGenerationError:
            raise  # Re-raise our custom errors
        except Exception as e:
            raise PDFGenerationError(f"Unexpected error during PDF generation: {e}")
    
    # _create_metadata method removed - metadata table no longer displayed per manager's request

    def _create_table_of_contents(self) -> List:
        """Create a table of contents with clickable links."""
        toc_content = []

        # TOC Title
        toc_title_style = ParagraphStyle(
            'TOCTitle',
            parent=self.style_manager.styles['heading'],
            fontSize=18,
            textColor=self.style_manager.get_color('primary'),
            spaceBefore=0,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        toc_content.append(Paragraph("Table of Contents", toc_title_style))

        # TOC Entries
        for entry in self.toc_entries:
            level = entry.get('level', 0)
            title = entry.get('title', '')
            anchor = entry.get('anchor', '')

            # Create indentation based on level
            left_indent = level * 20

            # TOC entry style
            toc_entry_style = ParagraphStyle(
                f'TOCEntry{level}',
                parent=self.style_manager.styles['normal'],
                fontSize=12 if level == 0 else 10,
                textColor=self.style_manager.get_color('primary') if level == 0 else self.style_manager.get_color('secondary'),
                leftIndent=left_indent,
                spaceBefore=6 if level == 0 else 3,
                spaceAfter=3,
                fontName='Helvetica-Bold' if level == 0 else 'Helvetica'
            )

            # Create clickable link to the corresponding anchor
            if anchor:
                # Use ReportLab's internal link format with href
                link_text = f'<a href="#{anchor}" color="{toc_entry_style.textColor}">{title}</a>'
            else:
                link_text = title

            toc_content.append(Paragraph(link_text, toc_entry_style))

        toc_content.append(Spacer(1, 20))
        return toc_content

    def _create_anchor(self, text: str) -> str:
        """Create a URL-safe anchor from text."""
        # Remove HTML tags and special characters, replace spaces with underscores
        clean_text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        clean_text = re.sub(r'[^\w\s-]', '', clean_text)  # Remove special chars except spaces and hyphens
        clean_text = re.sub(r'\s+', '_', clean_text.strip())  # Replace spaces with underscores
        # Add a prefix to ensure uniqueness and avoid conflicts
        return f"toc_{clean_text.lower()}"

    def _should_include_in_toc(self, key: str, level: int) -> bool:
        """Determine if a section should be included in the table of contents."""
        key_lower = key.lower()

        # Only include very specific main sections at level 0
        if level == 0:
            main_sections = ['gap_analysis_report', 'metadata']
            return key_lower in main_sections

        # For level 1, only include specific subsections
        if level == 1:
            level1_sections = ['metadata']
            return key_lower in level1_sections

        return False

    def _extract_section_toc_entries(self, section_analyses: Dict, base_level: int, data: Dict = None) -> None:
        """Extract TOC entries from section_analyses structure."""
        # Add module information if available from mapping.json
        if data and '_extracted_sections_info' in data:
            sections_info = data['_extracted_sections_info']
            # Group sections by module
            modules = {}
            for section_info in sections_info:
                module_label = section_info.get('module_label', 'Unknown Module')
                if module_label not in modules:
                    modules[module_label] = []
                modules[module_label].append(section_info)

            # Add module headers if we have multiple modules
            if len(modules) > 1:
                for module_label, module_sections in modules.items():
                    module_anchor = self._create_anchor(f"module_{module_label}")
                    self.toc_entries.append({
                        'title': f"Module: {module_label}",
                        'anchor': module_anchor,
                        'level': 0  # Module level
                    })

        # Sort sections by section number for proper ordering in TOC
        def sort_key(item):
            section_key, section_data = item
            if isinstance(section_data, dict):
                section_num = section_data.get('section', section_key)
                # Parse section number for proper sorting (e.g., "1.1", "1.2", "1.10")
                try:
                    # Split by dots and convert to integers for proper numerical sorting
                    parts = [int(x) for x in str(section_num).split('.')]
                    return parts
                except (ValueError, AttributeError):
                    # Fallback to string sorting if parsing fails
                    return [float('inf'), str(section_num)]
            return [float('inf'), section_key]

        sorted_sections = sorted(section_analyses.items(), key=sort_key)

        for section_key, section_data in sorted_sections:
            if isinstance(section_data, dict):
                # Extract section number and title
                section_num = section_data.get('section', section_key)
                section_title = section_data.get('section_title', '')

                if section_title:
                    # Create section header entry
                    section_header = f"Section {section_num}: {section_title}"
                    section_anchor = self._create_anchor(f"section_{section_num}_{section_title}")

                    self.toc_entries.append({
                        'title': section_header,
                        'anchor': section_anchor,
                        'level': 0  # Main section level
                    })

                    # Coverage categories removed from TOC as per manager's request


    
    def _render_json_content(self, data: Any, level: int, full_data: Any = None) -> List:
        """
        Render JSON content recursively with intelligent document formatting.

        Args:
            data: JSON data to render
            level: Current nesting level
            full_data: Full data context for TOC generation

        Returns:
            List of flowable elements
        """
        content = []
        data_type = self.validator.get_data_type(data)

        # Use data as full_data if not provided (for root level)
        if full_data is None:
            full_data = data

        if data_type == JSONDataType.OBJECT:
            content.extend(self._render_object_as_document(data, level, full_data))
        elif data_type == JSONDataType.ARRAY:
            content.extend(self._render_array_as_document(data, level))
        else:
            content.extend(self._render_primitive(data, level))

        return content
    
    def _render_object(self, obj: Dict, level: int) -> List:
        """Render a JSON object."""
        content = []

        if level > 0:  # Don't show header for root object
            header_text = f"Object ({len(obj)} keys)"
            content.append(Paragraph(header_text, self.style_manager.get_style('object_header')))
            # Add visual separator for nested objects
            content.append(self._create_separator(level))

        for i, (key, value) in enumerate(obj.items()):
            # Create key-value pair with enhanced formatting
            key_para = Paragraph(f"<b>{key}:</b>", self.style_manager.get_style('key'))
            content.append(key_para)

            # Add indentation for nested content
            if self.validator.get_data_type(value) in [JSONDataType.OBJECT, JSONDataType.ARRAY]:
                nested_content = self._render_json_content(value, level + 1)
                # Apply indentation
                for item in nested_content:
                    if hasattr(item, 'style'):
                        item.style.leftIndent = self.style_manager.calculate_indent(level + 1)
                content.extend(nested_content)
            else:
                value_content = self._render_primitive(value, level + 1)
                for item in value_content:
                    if hasattr(item, 'style'):
                        item.style.leftIndent = self.style_manager.calculate_indent(level + 1)
                content.extend(value_content)

            # Add spacing between items, but not after the last one
            if i < len(obj) - 1:
                content.append(Spacer(1, 6))

        return content
    
    def _render_array(self, arr: List, level: int) -> List:
        """Render a JSON array."""
        content = []

        header_text = f"Array ({len(arr)} items)"
        content.append(Paragraph(header_text, self.style_manager.get_style('array_header')))
        # Add visual separator for arrays
        content.append(self._create_separator(level))

        for i, item in enumerate(arr):
            # Add index with enhanced formatting
            index_para = Paragraph(f"<b>[{i}]:</b>", self.style_manager.get_style('key'))
            content.append(index_para)

            # Add item content
            if self.validator.get_data_type(item) in [JSONDataType.OBJECT, JSONDataType.ARRAY]:
                nested_content = self._render_json_content(item, level + 1)
                # Apply indentation
                for nested_item in nested_content:
                    if hasattr(nested_item, 'style'):
                        nested_item.style.leftIndent = self.style_manager.calculate_indent(level + 1)
                content.extend(nested_content)
            else:
                value_content = self._render_primitive(item, level + 1)
                for value_item in value_content:
                    if hasattr(value_item, 'style'):
                        value_item.style.leftIndent = self.style_manager.calculate_indent(level + 1)
                content.extend(value_content)

            # Add spacing between items, but not after the last one
            if i < len(arr) - 1:
                content.append(Spacer(1, 6))

        return content
    
    def _render_primitive(self, value: Any, level: int) -> List:
        """Render a primitive JSON value."""
        content = []
        data_type = self.validator.get_data_type(value)
        
        # Format the value
        formatted_value = format_value_for_display(value)
        
        # Choose appropriate style
        style_map = {
            JSONDataType.STRING: 'string_value',
            JSONDataType.NUMBER: 'number_value',
            JSONDataType.BOOLEAN: 'boolean_value',
            JSONDataType.NULL: 'null_value'
        }
        
        style_name = style_map.get(data_type, 'normal')
        para = Paragraph(formatted_value, self.style_manager.get_style(style_name))
        content.append(para)

        return content

    def _create_separator(self, level: int) -> HRFlowable:
        """Create a visual separator line."""
        # Adjust line width based on nesting level
        width_factor = max(0.3, 1.0 - (level * 0.1))
        line_width = 0.5 * width_factor

        return HRFlowable(
            width="100%",
            thickness=line_width,
            color=self.style_manager.get_color('border'),
            spaceBefore=2,
            spaceAfter=4
        )

    def _render_object_as_document(self, obj: Dict, level: int, full_data: Any = None) -> List:
        """Render JSON object as a document with intelligent formatting."""
        content = []
        section_counter = 1

        # Check if we have modules_structure (new format) to prioritize it over section_analyses
        has_modules_structure = 'modules_structure' in obj and isinstance(obj['modules_structure'], dict)

        for key, value in self._ordered_items(obj):
            # Skip excluded keys entirely
            if key.lower() in self.excluded_keys:
                continue

            # Special handling for modules structure (new hierarchical format)
            if key == 'modules_structure' and isinstance(value, dict):
                self._extract_modules_toc_entries(value, level + 1, full_data)
                # Render modules structure with proper hierarchy
                content.extend(self._render_modules_structure(key, value, level))
                continue

            # Special handling for section analyses structure (legacy format)
            # Skip if we have modules_structure to avoid duplication
            elif key == 'section_analyses' and isinstance(value, dict) and not has_modules_structure:
                self._extract_section_toc_entries(value, level + 1, full_data)
                # Render section analyses with special handling for individual sections
                content.extend(self._render_section_analyses(key, value, level))
                continue

            # Skip section_analyses if we have modules_structure (to avoid duplication)
            elif key == 'section_analyses' and has_modules_structure:
                continue

            # Add TOC entry for sections that should be included (only for main sections)
            elif level <= 1 and self._should_include_in_toc(key, level):
                header_text = self._format_key(key)
                anchor = self._create_anchor(f"{level}_{header_text}")
                self.toc_entries.append({
                    'title': header_text,
                    'anchor': anchor,
                    'level': level
                })

                # Add a header with anchor for this section
                section_header_style = ParagraphStyle(
                    f'TOCSection{level}',
                    parent=self.style_manager.styles['heading'],
                    textColor=self.style_manager.get_color('primary'),
                    spaceBefore=12,
                    spaceAfter=8,
                    fontSize=16,
                    fontName='Helvetica-Bold'
                )
                header_with_anchor = f'<a name="{anchor}"/>{header_text}'
                content.append(Paragraph(header_with_anchor, section_header_style))

            # Special handling for important analysis fields
            if key in ['combined_gap_analysis', 'strategic_recommendations']:
                # Render the content directly without redundant header for gap analysis
                if isinstance(value, str) and value.strip():
                    if key == 'combined_gap_analysis':
                        # No header for gap analysis - content already has title
                        content.extend(self._render_as_paragraph("", value, level))
                    else:
                        # Keep header for other fields like strategic_recommendations
                        field_title = key.replace('_', ' ').title()
                        field_header_style = ParagraphStyle(
                            f'ImportantField{level}',
                            parent=self.style_manager.styles['subheading'],
                            textColor=self.style_manager.get_color('primary'),
                            spaceBefore=12,
                            spaceAfter=6,
                            fontSize=16,
                            fontName='Helvetica-Bold'
                        )
                        content.append(Paragraph(field_title, field_header_style))
                        content.extend(self._render_as_paragraph("", value, level))
                else:
                    content.extend(self._render_as_field("", value, level))

            # Determine if this should be a header, subheader, or content
            elif self._is_title_key(key):
                content.extend(self._render_as_title(key, value, level))
            elif self._is_main_section(key, value):
                content.extend(self._render_as_numbered_section(key, value, section_counter, level))
                section_counter += 1
            elif self._is_header_key(key):
                content.extend(self._render_as_header(key, value, level))
            elif isinstance(value, str) and self._is_markdown_content(value):
                # Prefer markdown rendering over generic list handling
                content.extend(self._render_as_paragraph(key, value, level))
            elif self._is_list_content(value):
                content.extend(self._render_as_list(key, value, level))
            elif isinstance(value, dict):
                content.extend(self._render_as_section(key, value, level))
            elif isinstance(value, str) and len(value) > 100:
                # Long text without markdown
                content.extend(self._render_as_paragraph(key, value, level))
            else:
                content.extend(self._render_as_field(key, value, level))

        return content

    def _render_section_analyses(self, key: str, section_analyses: Dict, level: int) -> List:
        """Render section analyses with proper anchors for TOC navigation."""
        content = []

        # Add section analyses header
        header_text = self._format_key(key)
        header_style = ParagraphStyle(
            f'SectionAnalysesHeader{level}',
            parent=self.style_manager.styles['heading'],
            textColor=self.style_manager.get_color('primary'),
            spaceBefore=12,
            spaceAfter=8
        )
        content.append(Paragraph(header_text, header_style))

        # Sort sections by section number for proper ordering
        def sort_key(item):
            section_key, section_data = item
            if isinstance(section_data, dict):
                section_num = section_data.get('section', section_key)
                # Parse section number for proper sorting (e.g., "1.1", "1.2", "1.10")
                try:
                    # Split by dots and convert to integers for proper numerical sorting
                    parts = [int(x) for x in str(section_num).split('.')]
                    return parts
                except (ValueError, AttributeError):
                    # Fallback to string sorting if parsing fails
                    return [float('inf'), str(section_num)]
            return [float('inf'), section_key]

        sorted_sections = sorted(section_analyses.items(), key=sort_key)

        # Render each individual section in sorted order
        for section_key, section_data in sorted_sections:
            if isinstance(section_data, dict):
                # Extract section number and title
                section_num = section_data.get('section', section_key)
                section_title = section_data.get('section_title', '')

                if section_title:
                    # Create section header with anchor
                    section_header = f"Section {section_num}: {section_title}"
                    section_anchor = self._create_anchor(f"section_{section_num}_{section_title}")

                    # Create section header style
                    section_header_style = ParagraphStyle(
                        f'IndividualSectionHeader{level}',
                        parent=self.style_manager.styles['heading'],
                        textColor=self.style_manager.get_color('secondary'),
                        spaceBefore=16,
                        spaceAfter=8,
                        fontSize=14,
                        fontName='Helvetica-Bold'
                    )

                    # Add section header with anchor
                    section_with_anchor = f'<a name="{section_anchor}"/>{section_header}'
                    content.append(Paragraph(section_with_anchor, section_header_style))

                    # Render section content with special handling for coverage categories
                    content.extend(self._render_section_content_with_anchors(section_data, section_num, level + 1))

                    # Add spacing between sections
                    content.append(Spacer(1, 12))
                else:
                    # Fallback for sections without titles
                    content.extend(self._render_as_section(section_key, section_data, level + 1))
            else:
                # Fallback for non-dict section data
                content.extend(self._render_as_field(section_key, section_data, level + 1))

        return content

    def _render_section_content_with_anchors(self, section_data: Dict, section_num: str, level: int) -> List:
        """Render section content with anchors for coverage categories."""
        content = []

        for key, value in self._ordered_items(section_data):
            # Skip excluded keys
            if key.lower() in self.excluded_keys:
                continue

            # Special handling for coverage_categories
            if key == 'coverage_categories' and isinstance(value, dict):
                # Add coverage categories header
                coverage_header = "Coverage Analysis"
                coverage_header_style = ParagraphStyle(
                    f'CoverageHeader{level}',
                    parent=self.style_manager.styles['subheading'],
                    textColor=self.style_manager.get_color('accent'),
                    spaceBefore=10,
                    spaceAfter=6,
                    fontSize=12,
                    fontName='Helvetica-Bold'
                )
                content.append(Paragraph(coverage_header, coverage_header_style))

                # Render each coverage category with anchor
                for category_key, category_data in value.items():
                    if isinstance(category_data, dict) and 'checkpoint_count' in category_data:
                        checkpoint_count = category_data['checkpoint_count']
                        category_name = category_key.replace('_', ' ').title()
                        category_title = f"{category_name}: {checkpoint_count} checkpoints"
                        category_anchor = self._create_anchor(f"coverage_{section_num}_{category_key}")

                        # Create category style
                        category_style = ParagraphStyle(
                            f'CoverageCategory{level}',
                            parent=self.style_manager.styles['normal'],
                            textColor=self.style_manager.get_color('secondary'),
                            spaceBefore=6,
                            spaceAfter=4,
                            leftIndent=20,
                            fontSize=14,
                            fontName='Helvetica-Bold'
                        )

                        # Add category with anchor
                        category_with_anchor = f'<a name="{category_anchor}"/>{category_title}'
                        content.append(Paragraph(category_with_anchor, category_style))

                        # Render category content if there's more than just checkpoint_count
                        if len(category_data) > 1:
                            content.extend(self._render_object_as_document(category_data, level + 1))
                    else:
                        # Fallback for categories without checkpoint_count
                        content.extend(self._render_as_field(category_key, category_data, level + 1))
            else:
                # Regular content rendering
                if self._is_header_key(key):
                    content.extend(self._render_as_header(key, value, level))
                elif isinstance(value, dict):
                    content.extend(self._render_as_section(key, value, level))
                elif isinstance(value, str) and self._is_markdown_content(value):
                    content.extend(self._render_as_paragraph(key, value, level))
                elif self._is_list_content(value):
                    content.extend(self._render_as_list(key, value, level))
                elif isinstance(value, str) and len(value) > 100:
                    content.extend(self._render_as_paragraph(key, value, level))
                else:
                    content.extend(self._render_as_field(key, value, level))

        return content

    def _render_modules_structure(self, key: str, modules_structure: Dict, level: int) -> List:
        """Render modules structure with proper hierarchy: Module -> Section -> Coverage Analysis."""
        content = []

        # Add modules structure header
        header_text = "Module Analysis"
        header_style = ParagraphStyle(
            f'ModulesHeader{level}',
            parent=self.style_manager.styles['heading'],
            textColor=self.style_manager.get_color('primary'),
            spaceBefore=12,
            spaceAfter=8,
            fontSize=16,
            fontName='Helvetica-Bold'
        )
        content.append(Paragraph(header_text, header_style))

        # Sort modules by numerical order (M1, M2, M3, etc.)
        def module_sort_key(item):
            module_key = item[0]
            # Extract number from module key (e.g., "M1" -> 1, "M3" -> 3)
            try:
                if module_key.startswith('M'):
                    return int(module_key[1:])
                else:
                    return float('inf')  # Put non-standard keys at the end
            except (ValueError, IndexError):
                return float('inf')

        sorted_modules = sorted(modules_structure.items(), key=module_sort_key)

        for module_key, module_data in sorted_modules:
            if not isinstance(module_data, dict):
                continue

            module_label = module_data.get('module_label', module_key)
            sections = module_data.get('sections', {})

            # Add module header
            module_header = f"{module_label}"
            module_anchor = self._create_anchor(f"module_{module_key}")
            module_style = ParagraphStyle(
                f'ModuleHeader{level}',
                parent=self.style_manager.styles['heading'],
                textColor=self.style_manager.get_color('primary'),
                spaceBefore=16,
                spaceAfter=8,
                fontSize=14,
                fontName='Helvetica-Bold'
            )
            module_with_anchor = f'<a name="{module_anchor}"/>{module_header}'
            content.append(Paragraph(module_with_anchor, module_style))

            # Render sections within this module
            content.extend(self._render_module_sections(sections, module_key, level + 1))

        return content

    def _render_module_sections(self, sections: Dict, module_key: str, level: int) -> List:
        """Render sections within a module."""
        content = []

        # Sort sections by section key for consistent ordering
        sorted_sections = sorted(sections.items(), key=lambda x: self._parse_section_number(x[0]))

        for section_key, section_items in sorted_sections:
            if not isinstance(section_items, list):
                continue

            # Add section header
            section_header = f"Section {section_key}"
            section_anchor = self._create_anchor(f"section_{module_key}_{section_key}")
            section_style = ParagraphStyle(
                f'SectionHeader{level}',
                parent=self.style_manager.styles['subheading'],
                textColor=self.style_manager.get_color('secondary'),
                spaceBefore=12,
                spaceAfter=6,
                fontSize=12,
                fontName='Helvetica-Bold'
            )
            section_with_anchor = f'<a name="{section_anchor}"/>{section_header}'
            content.append(Paragraph(section_with_anchor, section_style))

            # Render each item in this section
            for item in section_items:
                if isinstance(item, dict):
                    section_id = item.get('section_id', '')
                    section_title = item.get('section_title', '')
                    gap_data = item.get('gap_data', {})

                    # Add subsection header
                    subsection_title = f"{section_id}: {section_title}" if section_title else section_id
                    subsection_anchor = self._create_anchor(f"subsection_{module_key}_{section_key}_{section_id}")
                    subsection_style = ParagraphStyle(
                        f'SubsectionHeader{level}',
                        parent=self.style_manager.styles['normal'],
                        textColor=self.style_manager.get_color('text'),
                        spaceBefore=8,
                        spaceAfter=4,
                        leftIndent=20,
                        fontName='Helvetica-Bold'
                    )
                    subsection_with_anchor = f'<a name="{subsection_anchor}"/>{subsection_title}'
                    content.append(Paragraph(subsection_with_anchor, subsection_style))

                    # Render coverage analysis for this subsection
                    if gap_data:
                        content.extend(self._render_subsection_coverage(gap_data, section_id, level + 1))

        return content

    def _render_subsection_coverage(self, gap_data: Dict, section_id: str, level: int) -> List:
        """Render coverage analysis for a subsection."""
        content = []

        # Add coverage analysis header
        coverage_header = "Coverage Analysis"
        coverage_style = ParagraphStyle(
            f'CoverageHeader{level}',
            parent=self.style_manager.styles['normal'],
            textColor=self.style_manager.get_color('accent'),
            spaceBefore=6,
            spaceAfter=4,
            leftIndent=20,
            fontSize=10,
            fontName='Helvetica-Bold'
        )
        content.append(Paragraph(coverage_header, coverage_style))

        # Render coverage categories if available
        coverage_categories = gap_data.get('coverage_categories', {})
        if coverage_categories:
            for category_key, category_data in coverage_categories.items():
                if isinstance(category_data, dict) and 'checkpoint_count' in category_data:
                    checkpoint_count = category_data['checkpoint_count']
                    category_name = category_key.replace('_', ' ').title()
                    category_title = f"{category_name}: {checkpoint_count} checkpoints"
                    category_anchor = self._create_anchor(f"coverage_{section_id}_{category_key}")

                    category_style = ParagraphStyle(
                        f'CoverageCategory{level}',
                        parent=self.style_manager.styles['normal'],
                        textColor=self.style_manager.get_color('secondary'),
                        spaceBefore=4,
                        spaceAfter=2,
                        leftIndent=30,
                        fontSize=12
                    )

                    category_with_anchor = f'<a name="{category_anchor}"/>{category_title}'
                    content.append(Paragraph(category_with_anchor, category_style))

                    # Render the content within this coverage category
                    content.extend(self._render_coverage_category_content(category_data, level + 1))

        # Render key gap analysis fields with special formatting
        priority_fields = ['combined_gap_analysis', 'strategic_recommendations']

        for field_key in priority_fields:
            if field_key in gap_data and isinstance(gap_data[field_key], str) and gap_data[field_key].strip():
                # Render content directly without redundant header for gap analysis
                if field_key == 'combined_gap_analysis':
                    # No header for gap analysis - content already has title
                    content.extend(self._render_as_paragraph("", gap_data[field_key], level + 1))
                else:
                    # Keep header for other fields like strategic_recommendations
                    field_title = field_key.replace('_', ' ').title()
                    field_header_style = ParagraphStyle(
                        f'FieldHeader{level}',
                        parent=self.style_manager.styles['normal'],
                        textColor=self.style_manager.get_color('primary'),
                        spaceBefore=8,
                        spaceAfter=4,
                        leftIndent=30,
                        fontSize=14,
                        fontName='Helvetica-Bold'
                    )
                    content.append(Paragraph(field_title, field_header_style))
                    content.extend(self._render_as_paragraph("", gap_data[field_key], level + 1))

        # Render other gap analysis content (summary, etc.)
        for key, value in gap_data.items():
            if (key not in ['coverage_categories'] + priority_fields and
                not key.lower() in self.excluded_keys):
                if isinstance(value, dict):
                    content.extend(self._render_as_section(key, value, level))
                elif isinstance(value, str) and len(value) > 50:
                    content.extend(self._render_as_paragraph(key, value, level))
                else:
                    content.extend(self._render_as_field(key, value, level))

        return content

    def _render_coverage_category_content(self, category_data: Dict, level: int) -> List:
        """Render the content within a coverage category (excellent_coverage, good_coverage, etc.)."""
        content = []

        # Priority fields that should be prominently displayed
        priority_fields = ['combined_gap_analysis']

        for field_key in priority_fields:
            if field_key in category_data and isinstance(category_data[field_key], str):
                field_value = category_data[field_key].strip()
                if field_value and field_value != "No checkpoints in this category":
                    # Render content directly without redundant header for gap analysis
                    if field_key == 'combined_gap_analysis':
                        # No header for gap analysis - content already has title
                        if self._is_markdown_content(field_value):
                            # Use markdown rendering for properly formatted content
                            markdown_content = self._render_markdown_content("", field_value, level + 1)
                            # Adjust indentation for markdown content
                            for item in markdown_content:
                                if hasattr(item, 'style') and hasattr(item.style, 'leftIndent'):
                                    item.style.leftIndent += 40  # Add extra indentation
                            content.extend(markdown_content)
                        else:
                            # Fallback to simple paragraph for non-markdown content
                            field_content_style = ParagraphStyle(
                                f'CategoryFieldContent{level}',
                                parent=self.style_manager.styles['normal'],
                                textColor=self.style_manager.get_color('text'),
                                spaceBefore=2,
                                spaceAfter=4,
                                leftIndent=50,
                                fontSize=8,
                                leading=10
                            )
                            content.append(Paragraph(field_value, field_content_style))
                    else:
                        # Keep header for other fields
                        field_title = field_key.replace('_', ' ').title()
                        field_header_style = ParagraphStyle(
                            f'CategoryFieldHeader{level}',
                            parent=self.style_manager.styles['normal'],
                            textColor=self.style_manager.get_color('primary'),
                            spaceBefore=6,
                            spaceAfter=3,
                            leftIndent=40,
                            fontSize=12,
                            fontName='Helvetica-Bold'
                        )
                        content.append(Paragraph(field_title, field_header_style))

                        # Render the content with proper markdown formatting
                        if self._is_markdown_content(field_value):
                            # Use markdown rendering for properly formatted content
                            markdown_content = self._render_markdown_content("", field_value, level + 1)
                            # Adjust indentation for markdown content
                            for item in markdown_content:
                                if hasattr(item, 'style') and hasattr(item.style, 'leftIndent'):
                                    item.style.leftIndent += 40  # Add extra indentation
                            content.extend(markdown_content)
                        else:
                            # Fallback to simple paragraph for non-markdown content
                            field_content_style = ParagraphStyle(
                                f'CategoryFieldContent{level}',
                                parent=self.style_manager.styles['normal'],
                                textColor=self.style_manager.get_color('text'),
                                spaceBefore=2,
                                spaceAfter=4,
                                leftIndent=50,
                                fontSize=8,
                                leading=10
                            )
                            content.append(Paragraph(field_value, field_content_style))

        # Render other fields in the category (excluding checkpoint_count and priority fields)
        for key, value in category_data.items():
            if (key not in ['checkpoint_count'] + priority_fields and
                not key.lower() in self.excluded_keys):
                if isinstance(value, str) and len(value) > 20 and value.strip():
                    # Render as a field with content
                    field_title = key.replace('_', ' ').title()
                    field_header_style = ParagraphStyle(
                        f'CategoryOtherFieldHeader{level}',
                        parent=self.style_manager.styles['normal'],
                        textColor=self.style_manager.get_color('secondary'),
                        spaceBefore=4,
                        spaceAfter=2,
                        leftIndent=40,
                        fontSize=8,
                        fontName='Helvetica-Bold'
                    )
                    content.append(Paragraph(field_title, field_header_style))

                    # Use markdown rendering if applicable
                    if isinstance(value, str) and self._is_markdown_content(value):
                        markdown_content = self._render_markdown_content("", value, level + 1)
                        # Adjust indentation for markdown content
                        for item in markdown_content:
                            if hasattr(item, 'style') and hasattr(item.style, 'leftIndent'):
                                item.style.leftIndent += 40
                        content.extend(markdown_content)
                    else:
                        field_content_style = ParagraphStyle(
                            f'CategoryOtherFieldContent{level}',
                            parent=self.style_manager.styles['normal'],
                            textColor=self.style_manager.get_color('text'),
                            spaceBefore=1,
                            spaceAfter=3,
                            leftIndent=50,
                            fontSize=8,
                            leading=9
                        )
                        content.append(Paragraph(str(value), field_content_style))

        return content

    def _extract_modules_toc_entries(self, modules_structure: Dict, level: int, full_data: Any = None):
        """Extract TOC entries from modules structure."""
        # Sort modules by numerical order (M1, M2, M3, etc.)
        def module_sort_key(item):
            module_key = item[0]
            # Extract number from module key (e.g., "M1" -> 1, "M3" -> 3)
            try:
                if module_key.startswith('M'):
                    return int(module_key[1:])
                else:
                    return float('inf')  # Put non-standard keys at the end
            except (ValueError, IndexError):
                return float('inf')

        sorted_modules = sorted(modules_structure.items(), key=module_sort_key)

        for module_key, module_data in sorted_modules:
            if not isinstance(module_data, dict):
                continue

            module_label = module_data.get('module_label', module_key)
            sections = module_data.get('sections', {})

            # Add module to TOC
            module_anchor = self._create_anchor(f"module_{module_key}")
            self.toc_entries.append({
                'title': module_label,
                'anchor': module_anchor,
                'level': 0
            })

            # Sort sections by section key for consistent ordering
            sorted_sections = sorted(sections.items(), key=lambda x: self._parse_section_number(x[0]))

            for section_key, section_items in sorted_sections:
                if not isinstance(section_items, list):
                    continue

                # Add section to TOC
                section_title = f"Section {section_key}"
                section_anchor = self._create_anchor(f"section_{module_key}_{section_key}")
                self.toc_entries.append({
                    'title': section_title,
                    'anchor': section_anchor,
                    'level': 1
                })

                # Add coverage analysis entries for each subsection
                for item in section_items:
                    if isinstance(item, dict):
                        section_id = item.get('section_id', '')
                        section_title_text = item.get('section_title', '')
                        gap_data = item.get('gap_data', {})

                        # Add subsection to TOC
                        subsection_title = f"{section_id}: {section_title_text}" if section_title_text else section_id
                        subsection_anchor = self._create_anchor(f"subsection_{module_key}_{section_key}_{section_id}")
                        self.toc_entries.append({
                            'title': subsection_title,
                            'anchor': subsection_anchor,
                            'level': 2
                        })

                        # Coverage categories removed from TOC as per manager's request

    def _parse_section_number(self, section_key: str) -> tuple:
        """Parse section number for proper sorting (e.g., '1.4.1' -> (1, 4, 1))."""
        try:
            parts = section_key.split('.')
            return tuple(int(part) for part in parts)
        except (ValueError, AttributeError):
            return (float('inf'),)  # Put non-numeric sections at the end

    def _render_array_as_document(self, arr: List, level: int) -> List:
        """Render JSON array as a document with intelligent formatting."""
        content = []

        # If this array is essentially a block of markdown lines, render via markdown
        try:
            if arr and all(isinstance(item, str) for item in arr):
                if any(self._is_markdown_content(item) or item.strip().startswith(('##', '###', '- ', '  - ')) for item in arr):
                    markdown_text = '\n'.join(arr)
                    content.extend(self._render_markdown_content("", markdown_text, level))
                    return content
        except Exception:
            pass

        # Check if this is a list of similar objects (like bullet points)
        if self._is_bullet_list(arr):
            content.extend(self._render_as_bullet_list(arr, level))
        elif self._is_numbered_list(arr):
            content.extend(self._render_as_numbered_list(arr, level))
        else:
            # Render as sections
            for i, item in enumerate(arr):
                if isinstance(item, dict):
                    content.extend(self._render_as_section(f"Item {i+1}", item, level))
                else:
                    content.extend(self._render_primitive(item, level))
                content.append(Spacer(1, 6))

        return content

    def _is_title_key(self, key: str) -> bool:
        """Check if a key should be rendered as a title."""
        title_indicators = ['title', 'name', 'heading', 'header', 'subject']
        return any(indicator in key.lower() for indicator in title_indicators)

    def _is_header_key(self, key: str) -> bool:
        """Check if a key should be rendered as a header.

        Avoid false positives like 'sections_analyzed' by using word boundaries
        and explicit exceptions.
        """
        key_l = key.lower()
        if key_l in self.non_header_keys:
            return False
        # Normalize separators and split into words
        import re
        words = re.findall(r"[a-zA-Z]+", key_l)
        header_words = {'section', 'sections', 'chapter', 'summary', 'overview', 'description'}
        return any(word in header_words for word in words)

    def _is_main_section(self, key: str, value: Any) -> bool:
        """Check if a key-value pair should be rendered as a main numbered section."""
        # Main sections are typically complex objects with multiple sub-items
        if isinstance(value, dict) and len(value) > 1:
            return True
        # Or arrays with multiple items that aren't simple strings
        if isinstance(value, list) and len(value) > 2:
            return True
        return False

    def _format_key(self, key: str) -> str:
        """Format a key for display by replacing underscores and capitalizing."""
        return key.replace('_', ' ').title()

    def _ordered_items(self, obj: Dict) -> List:
        """Return items ordered with preferences: Gap Analysis before Supporting Evidence.

        All other keys keep their relative order.
        """
        original_index = {k: i for i, k in enumerate(obj.keys())}

        def priority(key: str) -> int:
            lower_key = key.lower()
            if 'gap' in lower_key and 'analysis' in lower_key:
                return 0
            if 'supporting' in lower_key and 'evidence' in lower_key:
                return 1
            return 2

        return sorted(obj.items(), key=lambda kv: (priority(kv[0]), original_index[kv[0]]))

    def _is_list_content(self, value: Any) -> bool:
        """Check if value should be rendered as a list.

        Markdown-like strings are handled elsewhere to preserve headings and
        nested bullet hierarchy.
        """
        if isinstance(value, list):
            return True
        if isinstance(value, str):
            if self._is_markdown_content(value):
                return False
            stripped = value.lstrip()
            # Treat square bullets as list markers too
            bullet_starts = ('- ', '• ', '▪ ', '▫ ')
            if any(stripped.startswith(bs) for bs in bullet_starts):
                return True
            return any(b in value for b in ('\n- ', '\n• ', '\n▪ ', '\n▫ '))
        return False

    def _is_bullet_list(self, arr: List) -> bool:
        """Check if array should be rendered as bullet points."""
        if len(arr) == 0:
            return False
        # If most items are strings or simple objects, treat as bullet list
        simple_items = sum(1 for item in arr if isinstance(item, (str, int, float, bool)) or
                          (isinstance(item, dict) and len(item) <= 3))
        return simple_items / len(arr) > 0.7

    def _is_numbered_list(self, arr: List) -> bool:
        """Check if array should be rendered as numbered list."""
        # Look for numbered patterns in the data
        if isinstance(arr[0], dict):
            first_keys = list(arr[0].keys())
            return any('number' in key.lower() or 'step' in key.lower() or 'point' in key.lower()
                      for key in first_keys)
        return False

    def _render_as_title(self, key: str, value: Any, level: int) -> List:
        """Render as document title."""
        content = []
        title_text = str(value) if not isinstance(value, dict) else key

        # Create title style
        title_style = ParagraphStyle(
            'DocumentTitle',
            parent=self.style_manager.styles['title'],
            fontSize=20,
            textColor=self.style_manager.get_color('primary'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        content.append(Paragraph(title_text, title_style))
        content.append(Spacer(1, 10))

        # If value is a dict, render its contents
        if isinstance(value, dict):
            content.extend(self._render_object_as_document(value, level + 1))

        return content

    def _render_as_header(self, key: str, value: Any, level: int) -> List:
        """Render as section header."""
        content = []

        # Clean up the key for display
        header_text = key.replace('_', ' ').title()

        # Create anchor for TOC linking
        anchor = self._create_anchor(f"header_{level}_{header_text}")

        # Add to TOC if this should be included
        if self._should_include_in_toc(key, level):
            self.toc_entries.append({
                'title': header_text,
                'anchor': anchor,
                'level': level
            })

        # Choose header style based on level
        if level == 0:
            style_name = 'heading'
            color = self.style_manager.get_color('primary')
        elif level == 1:
            style_name = 'subheading'
            color = self.style_manager.get_color('secondary')
        else:
            style_name = 'subheading'
            color = self.style_manager.get_color('accent')

        header_style = ParagraphStyle(
            f'Header{level}',
            parent=self.style_manager.styles[style_name],
            textColor=color,
            spaceBefore=12,
            spaceAfter=8
        )

        # Add paragraph with anchor for TOC navigation
        if self._should_include_in_toc(key, level):
            header_with_anchor = f'<a name="{anchor}"/>{header_text}'
            content.append(Paragraph(header_with_anchor, header_style))
        else:
            content.append(Paragraph(header_text, header_style))

        # Render the value content
        if isinstance(value, str):
            content.extend(self._render_as_paragraph("", value, level + 1))
        elif isinstance(value, dict):
            content.extend(self._render_object_as_document(value, level + 1))
        elif isinstance(value, list):
            content.extend(self._render_array_as_document(value, level + 1))

        return content

    def _render_as_numbered_section(self, key: str, value: Any, section_number: int, level: int) -> List:
        """Render as a numbered section (e.g., '1. Section Name')."""
        content = []

        # Create numbered header
        header_text = f"{section_number}. {self._format_key(key)}"

        # Create anchor for TOC linking
        anchor = self._create_anchor(f"numbered_{section_number}_{header_text}")

        # Add to TOC if this is a main section
        if self._should_include_in_toc(key, level):
            self.toc_entries.append({
                'title': header_text,
                'anchor': anchor,
                'level': level
            })

        # Choose header style based on level
        if level == 0:
            style_name = 'heading'
            color = self.style_manager.get_color('primary')
        else:
            style_name = 'subheading'
            color = self.style_manager.get_color('secondary')

        header_style = ParagraphStyle(
            f'NumberedHeader{level}',
            parent=self.style_manager.styles[style_name],
            textColor=color,
            spaceBefore=12,
            spaceAfter=8
        )

        # Add paragraph with anchor for TOC navigation
        if self._should_include_in_toc(key, level):
            header_with_anchor = f'<a name="{anchor}"/>{header_text}'
            content.append(Paragraph(header_with_anchor, header_style))
        else:
            content.append(Paragraph(header_text, header_style))

        # Render the content
        if isinstance(value, dict):
            content.extend(self._render_object_as_document(value, level + 1))
        elif isinstance(value, list):
            content.extend(self._render_array_as_document(value, level + 1))
        elif isinstance(value, str):
            content.extend(self._render_as_paragraph("", value, level + 1))

        return content

    def _render_as_section(self, key: str, value: Dict, level: int) -> List:
        """Render as a document section."""
        content = []

        # Section header
        section_text = key.replace('_', ' ').title()

        # Create anchor for TOC linking
        anchor = self._create_anchor(f"section_{level}_{section_text}")

        # Add to TOC if this should be included
        if self._should_include_in_toc(key, level):
            self.toc_entries.append({
                'title': section_text,
                'anchor': anchor,
                'level': level
            })

        header_style = ParagraphStyle(
            f'Section{level}',
            parent=self.style_manager.styles['heading'] if level < 2 else self.style_manager.styles['subheading'],
            textColor=self.style_manager.get_color('secondary'),
            spaceBefore=10,
            spaceAfter=6,
            fontSize=14 if level < 2 else 12
        )

        # Add paragraph with anchor for TOC navigation
        if self._should_include_in_toc(key, level):
            section_with_anchor = f'<a name="{anchor}"/>{section_text}'
            content.append(Paragraph(section_with_anchor, header_style))
        else:
            content.append(Paragraph(section_text, header_style))
        content.extend(self._render_object_as_document(value, level + 1))
        content.append(Spacer(1, 8))

        return content

    def _render_as_list(self, key: str, value: Any, level: int) -> List:
        """Render as a formatted list."""
        content = []

        # Add list header if key is meaningful
        if key and not key.isdigit():
            list_header = key.replace('_', ' ').title()
            header_style = ParagraphStyle(
                'ListHeader',
                parent=self.style_manager.styles['subheading'],
                textColor=self.style_manager.get_color('secondary'),
                spaceBefore=8,
                spaceAfter=4
            )
            content.append(Paragraph(list_header, header_style))

        if isinstance(value, list):
            if value and all(isinstance(item, str) for item in value) and any(self._is_markdown_content(item) for item in value):
                markdown_text = '\n'.join(value)
                content.extend(self._render_markdown_content("", markdown_text, level))
            else:
                content.extend(self._render_as_bullet_list(value, level))
        elif isinstance(value, str):
            if self._is_markdown_content(value):
                content.extend(self._render_markdown_content("", value, level))
            else:
                # Split string into bullet points
                lines = [line.strip() for line in value.split('\n') if line.strip()]
                content.extend(self._render_as_bullet_list(lines, level))

        return content

    def _render_as_bullet_list(self, items: List, level: int) -> List:
        """Render as bullet points with variety."""
        content = []

        # Different bullet symbols for different levels
        # Use only widely supported glyphs to avoid fallback squares in some viewers
        bullet_symbols = ['•', '-', '-', '-', '-']
        bullet_symbol = bullet_symbols[level % len(bullet_symbols)]
        # Make dot bullets larger and dashes normal sized
        if bullet_symbol == '•':
            bullet_font_size = 14  # larger main bullet
        else:  # '-'
            bullet_font_size = 12  # dash bullets at normal size

        for item in items:
            bullet_style = ParagraphStyle(
                'BulletPoint',
                parent=self.style_manager.styles['normal'],
                leftIndent=8 + (level * 10),
                bulletIndent=0,  # No gap between bullet and text
                spaceBefore=2,
                spaceAfter=2,
                bulletFontName='Helvetica',
                bulletFontSize=bullet_font_size,
                bulletText=bullet_symbol,
                bulletColor=self.style_manager.get_color('primary'),
                fontSize=10,
                leading=12
            )

            if isinstance(item, dict):
                # For dict items, render as bullet with title and content
                for k, v in item.items():
                    # Main bullet point with bold title
                    title = f"<b>{self._format_key(k)}:</b>"

                    if isinstance(v, str) and len(v) > 100:
                        # Long text - title on one line, content indented below
                        content.append(Paragraph(title, bullet_style))
                        content_style = ParagraphStyle(
                            'BulletContent',
                            parent=self.style_manager.styles['normal'],
                            leftIndent=18 + (level * 12),  # Tighter indentation
                            spaceBefore=1,
                            spaceAfter=2
                        )
                        content.append(Paragraph(str(v), content_style))
                    elif isinstance(v, list):
                        # Sub-list - render title then nested bullets
                        content.append(Paragraph(title, bullet_style))
                        content.extend(self._render_as_bullet_list(v, level + 1))
                    else:
                        # Short content - inline
                        text = f"{title} {str(v)}"
                        content.append(Paragraph(text, bullet_style))
                    break
            else:
                text = str(item)
                content.append(Paragraph(text, bullet_style))

        return content

    def _render_as_numbered_list(self, items: List, level: int) -> List:
        """Render as numbered list."""
        content = []

        for i, item in enumerate(items, 1):
            number_style = ParagraphStyle(
                'NumberedPoint',
                parent=self.style_manager.styles['normal'],
                leftIndent=25 + (level * 15),
                spaceBefore=3,
                spaceAfter=3
            )

            if isinstance(item, dict):
                # For dict items, use the first key-value as the numbered text
                for k, v in item.items():
                    text = f"<b>{i}. {k.replace('_', ' ').title()}:</b> {str(v)}"
                    content.append(Paragraph(text, number_style))
                    break
            else:
                text = f"{i}. {str(item)}"
                content.append(Paragraph(text, number_style))

        return content

    def _render_as_paragraph(self, key: str, value: str, level: int) -> List:
        """Render as formatted paragraph with markdown support."""
        content = []

        # Check if this looks like markdown content
        if self._is_markdown_content(value):
            return self._render_markdown_content(key, value, level)

        # Add paragraph header if key is meaningful
        if key and not key.isdigit():
            para_header = key.replace('_', ' ').title()
            header_style = ParagraphStyle(
                'ParagraphHeader',
                parent=self.style_manager.styles['subheading'],
                textColor=self.style_manager.get_color('accent'),
                spaceBefore=6,
                spaceAfter=3
            )
            content.append(Paragraph(para_header, header_style))

        # Format the paragraph text
        para_style = ParagraphStyle(
            'DocumentParagraph',
            parent=self.style_manager.styles['normal'],
            spaceBefore=3,
            spaceAfter=6,
            leftIndent=level * 10,
            alignment=TA_JUSTIFY
        )

        content.append(Paragraph(value, para_style))

        return content

    def _render_as_field(self, key: str, value: Any, level: int) -> List:
        """Render as a simple field."""
        content = []

        field_style = ParagraphStyle(
            'DocumentField',
            parent=self.style_manager.styles['normal'],
            spaceBefore=2,
            spaceAfter=2,
            leftIndent=level * 10
        )

        # Format key-value pair
        clean_key = key.replace('_', ' ').title()
        text = f"<b>{clean_key}:</b> {str(value)}"
        content.append(Paragraph(text, field_style))

        return content

    def _is_markdown_content(self, text: str) -> bool:
        """Check if text contains markdown formatting."""
        markdown_indicators = [
            '##',  # Headers
            '###',  # Subheaders
            '####',  # Sub-subheaders
            '**',  # Bold text
            '- ',  # Bullet points
            '> ',  # Blockquotes
            '  - ',  # Sub-bullets
        ]
        return any(indicator in text for indicator in markdown_indicators)

    def _render_markdown_content(self, key: str, value: str, level: int) -> List:
        """Render markdown-formatted content."""
        content = []

        # Add section header if key is meaningful
        if key and not key.isdigit():
            section_header = key.replace('_', ' ').title()
            header_style = ParagraphStyle(
                'MarkdownSectionHeader',
                parent=self.style_manager.styles['heading'],
                textColor=self.style_manager.get_color('primary'),
                spaceBefore=12,
                spaceAfter=8,
                fontSize=16,
                fontName='Helvetica-Bold'
            )
            content.append(Paragraph(section_header, header_style))

        # Split content into lines and process
        lines = value.split('\n')
        current_block = []
        in_blockquote = False

        for line in lines:
            line = line.rstrip()

            # Handle empty lines
            if not line:
                if current_block:
                    content.extend(self._process_markdown_block(current_block, level, in_blockquote))
                    current_block = []
                    in_blockquote = False
                continue

            # Check if starting/continuing blockquote
            if line.startswith('> '):
                if not in_blockquote:
                    if current_block:
                        content.extend(self._process_markdown_block(current_block, level, False))
                        current_block = []
                    in_blockquote = True
                current_block.append(line)
            else:
                if in_blockquote:
                    content.extend(self._process_markdown_block(current_block, level, True))
                    current_block = []
                    in_blockquote = False
                current_block.append(line)

        # Process remaining block
        if current_block:
            content.extend(self._process_markdown_block(current_block, level, in_blockquote))

        return content

    def _process_markdown_block(self, lines: List[str], level: int, is_blockquote: bool) -> List:
        """Process a block of markdown lines."""
        content = []

        if is_blockquote:
            # Handle blockquote
            blockquote_text = '\n'.join(line[2:] if line.startswith('> ') else line for line in lines)
            blockquote_style = ParagraphStyle(
                'Blockquote',
                parent=self.style_manager.styles['normal'],
                leftIndent=20,
                rightIndent=20,
                spaceBefore=8,
                spaceAfter=8,
                borderWidth=1,
                borderColor=self.style_manager.get_color('accent'),
                borderPadding=8,
                backColor=colors.HexColor('#f8f9fa'),
                fontName='Helvetica-Oblique',
                fontSize=10
            )
            content.append(Paragraph(self._format_text(blockquote_text), blockquote_style))
        else:
            # Process regular content
            i = 0
            while i < len(lines):
                line = lines[i]
                # Detect GitHub-style table blocks starting with a pipe row
                if line.strip().startswith('|') and line.strip().endswith('|'):
                    table_lines = [line]
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                        table_lines.append(lines[i])
                        i += 1
                    try:
                        table_flowable = self._render_markdown_table(table_lines)
                        content.append(table_flowable)
                        content.append(Spacer(1, 6))
                        continue
                    except Exception:
                        # Fallback to paragraph rendering if parsing fails
                        pass

                # Non-table processing
                if line.startswith('## '):
                    # Main header
                    header_text = line[3:].strip()

                    # Create anchor and add to TOC if it should be included
                    anchor = self._create_anchor(header_text)
                    if self._should_include_in_toc(header_text, level):
                        self.toc_entries.append({
                            'title': header_text,
                            'anchor': anchor,
                            'level': level
                        })

                    header_style = ParagraphStyle(
                        'MarkdownH2',
                        parent=self.style_manager.styles['heading'],
                        textColor=self.style_manager.get_color('primary'),
                        spaceBefore=12,
                        spaceAfter=6,
                        fontSize=14,
                        fontName='Helvetica-Bold'
                    )

                    # Add anchor to the paragraph
                    header_with_anchor = f'<a name="{anchor}"/>{self._format_text(header_text)}'
                    content.append(Paragraph(header_with_anchor, header_style))

                elif line.startswith('### '):
                    # Subheader
                    subheader_text = line[4:].strip()

                    # Create anchor and add to TOC if it should be included
                    anchor = self._create_anchor(subheader_text)
                    if self._should_include_in_toc(subheader_text, level + 1):
                        self.toc_entries.append({
                            'title': subheader_text,
                            'anchor': anchor,
                            'level': level + 1
                        })

                    subheader_style = ParagraphStyle(
                        'MarkdownH3',
                        parent=self.style_manager.styles['subheading'],
                        textColor=self.style_manager.get_color('secondary'),
                        spaceBefore=10,
                        spaceAfter=4,
                        fontSize=12,
                        fontName='Helvetica-Bold'
                    )

                    # Add anchor to the paragraph
                    subheader_with_anchor = f'<a name="{anchor}"/>{self._format_text(subheader_text)}'
                    content.append(Paragraph(subheader_with_anchor, subheader_style))

                elif line.startswith('#### '):
                    # Sub-subheader (H4)
                    h4_text = line[5:].strip()

                    # Create anchor and add to TOC if it should be included
                    anchor = self._create_anchor(h4_text)
                    if self._should_include_in_toc(h4_text, level + 2):
                        self.toc_entries.append({
                            'title': h4_text,
                            'anchor': anchor,
                            'level': level + 2
                        })

                    h4_style = ParagraphStyle(
                        'MarkdownH4',
                        parent=self.style_manager.styles['normal'],
                        textColor=self.style_manager.get_color('secondary'),
                        spaceBefore=8,
                        spaceAfter=3,
                        fontSize=11,
                        fontName='Helvetica-Bold'
                    )

                    # Add anchor to the paragraph
                    h4_with_anchor = f'<a name="{anchor}"/>{self._format_text(h4_text)}'
                    content.append(Paragraph(h4_with_anchor, h4_style))

                elif line.startswith('- '):
                    # Main bullet point
                    bullet_text = line[2:].strip()
                    bullet_style = ParagraphStyle(
                        'MarkdownBullet',
                        parent=self.style_manager.styles['normal'],
                        leftIndent=8,
                        spaceBefore=2,
                        spaceAfter=2,
                        bulletIndent=0,  # No gap between bullet and text
                        bulletFontName='Helvetica',
                        bulletFontSize=14,
                        bulletText='•',  # Round bullet for main points (larger)
                        fontSize=10,
                        leading=12
                    )
                    content.append(Paragraph(self._format_text(bullet_text), bullet_style))

                elif line.startswith('  - '):
                    # Sub-bullet point
                    sub_bullet_text = line[4:].strip()
                    sub_bullet_style = ParagraphStyle(
                        'MarkdownSubBullet',
                        parent=self.style_manager.styles['normal'],
                        leftIndent=18,
                        spaceBefore=1,
                        spaceAfter=1,
                        bulletIndent=0,  # No gap between bullet and text
                        bulletFontName='Helvetica',
                        bulletFontSize=12,
                        bulletText='-',  # Use dash for sub-bullets to avoid square glyphs
                        fontSize=9,
                        leading=11
                    )
                    content.append(Paragraph(self._format_text(sub_bullet_text), sub_bullet_style))

                elif line.strip():
                    # Regular paragraph
                    para_style = ParagraphStyle(
                        'MarkdownParagraph',
                        parent=self.style_manager.styles['normal'],
                        spaceBefore=4,
                        spaceAfter=4,
                        alignment=TA_JUSTIFY
                    )
                    content.append(Paragraph(self._format_text(line), para_style))

                i += 1

        return content

    def _render_markdown_table(self, table_lines: List[str]) -> Table:
        """Render a GitHub-style markdown table into a ReportLab Table."""
        # Clean and split rows
        def split_row(row: str) -> List[str]:
            parts = [cell.strip() for cell in row.strip().strip('|').split('|')]
            return parts

        if len(table_lines) < 2:
            raise ValueError('Invalid markdown table')

        header_cells = split_row(table_lines[0])
        # Skip the separator line (second line)
        data_rows = [split_row(r) for r in table_lines[2:]] if len(table_lines) >= 2 else []

        # Convert to Paragraphs
        header_style = ParagraphStyle(
            'MDTableHeader',
            parent=self.style_manager.styles['normal'],
            fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
            textColor=self.style_manager.get_color('primary'),
            spaceBefore=2,
            spaceAfter=2
        )
        cell_style = ParagraphStyle(
            'MDTableCell',
            parent=self.style_manager.styles['normal'],
            spaceBefore=2,
            spaceAfter=2
        )

        data = [[Paragraph(self._format_text(c), header_style) for c in header_cells]]
        for row in data_rows:
            # Pad/trim row to header width
            if len(row) < len(header_cells):
                row = row + [''] * (len(header_cells) - len(row))
            elif len(row) > len(header_cells):
                row = row[:len(header_cells)]
            data.append([Paragraph(self._format_text(c), cell_style) for c in row])

        # Column widths: if two columns, make first narrow
        if len(header_cells) == 2:
            col_widths = [1.6*inch, None]
        else:
            col_widths = [None] * len(header_cells)

        table = Table(data, colWidths=col_widths)
        border_color = self.style_manager.get_color('border')
        bg_header = self.style_manager.get_color('background')
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('BACKGROUND', (0, 0), (-1, 0), bg_header),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return table

    def _format_text(self, text: str) -> str:
        """Format text with bold and italic markup."""
        # Handle bold text
        import re
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        return text
