"""
PDF Styling and Layout System

This module defines professional styling, typography, color schemes, and layout
configurations for generating visually appealing PDF documents from JSON data.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import Dict, Any
from enum import Enum


class ColorScheme(Enum):
    """Available color schemes for PDF generation."""
    DEFAULT = "default"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    ORANGE = "orange"
    DARK = "dark"


class PDFStyleConfig:
    """Configuration class for PDF styling and layout."""
    
    # Page layout
    PAGE_SIZE = 'A4'
    MARGIN_TOP = 1 * inch
    MARGIN_BOTTOM = 1 * inch
    MARGIN_LEFT = 0.75 * inch
    MARGIN_RIGHT = 0.75 * inch
    
    # Typography
    FONT_FAMILY_NORMAL = 'Helvetica'
    FONT_FAMILY_BOLD = 'Helvetica-Bold'
    FONT_FAMILY_MONO = 'Courier'
    
    # Font sizes
    FONT_SIZE_TITLE = 24
    FONT_SIZE_HEADING = 18
    FONT_SIZE_SUBHEADING = 14
    FONT_SIZE_NORMAL = 11
    FONT_SIZE_SMALL = 9
    FONT_SIZE_MONO = 10
    
    # Spacing
    SPACE_BEFORE_TITLE = 0
    SPACE_AFTER_TITLE = 20
    SPACE_BEFORE_HEADING = 16
    SPACE_AFTER_HEADING = 8
    SPACE_BEFORE_SUBHEADING = 12
    SPACE_AFTER_SUBHEADING = 6
    SPACE_BEFORE_PARAGRAPH = 6
    SPACE_AFTER_PARAGRAPH = 6
    
    # Indentation
    INDENT_BASE = 20
    INDENT_MULTIPLIER = 1.5
    
    # Colors for different data types
    COLOR_SCHEMES = {
        ColorScheme.DEFAULT: {
            'primary': colors.HexColor('#2C3E50'),
            'secondary': colors.HexColor('#34495E'),
            'accent': colors.HexColor('#3498DB'),
            'string': colors.HexColor('#27AE60'),
            'number': colors.HexColor('#E74C3C'),
            'boolean': colors.HexColor('#9B59B6'),
            'null': colors.HexColor('#95A5A6'),
            'key': colors.HexColor('#2C3E50'),
            'background': colors.HexColor('#F8F9FA'),
            'border': colors.HexColor('#DEE2E6')
        },
        ColorScheme.BLUE: {
            'primary': colors.HexColor('#1E3A8A'),
            'secondary': colors.HexColor('#3B82F6'),
            'accent': colors.HexColor('#60A5FA'),
            'string': colors.HexColor('#059669'),
            'number': colors.HexColor('#DC2626'),
            'boolean': colors.HexColor('#7C3AED'),
            'null': colors.HexColor('#6B7280'),
            'key': colors.HexColor('#1E3A8A'),
            'background': colors.HexColor('#EFF6FF'),
            'border': colors.HexColor('#DBEAFE')
        },
        ColorScheme.GREEN: {
            'primary': colors.HexColor('#14532D'),
            'secondary': colors.HexColor('#16A34A'),
            'accent': colors.HexColor('#4ADE80'),
            'string': colors.HexColor('#059669'),
            'number': colors.HexColor('#DC2626'),
            'boolean': colors.HexColor('#7C3AED'),
            'null': colors.HexColor('#6B7280'),
            'key': colors.HexColor('#14532D'),
            'background': colors.HexColor('#F0FDF4'),
            'border': colors.HexColor('#DCFCE7')
        },
        ColorScheme.PURPLE: {
            'primary': colors.HexColor('#581C87'),
            'secondary': colors.HexColor('#9333EA'),
            'accent': colors.HexColor('#C084FC'),
            'string': colors.HexColor('#059669'),
            'number': colors.HexColor('#DC2626'),
            'boolean': colors.HexColor('#7C3AED'),
            'null': colors.HexColor('#6B7280'),
            'key': colors.HexColor('#581C87'),
            'background': colors.HexColor('#FAF5FF'),
            'border': colors.HexColor('#E9D5FF')
        },
        ColorScheme.ORANGE: {
            'primary': colors.HexColor('#9A3412'),
            'secondary': colors.HexColor('#EA580C'),
            'accent': colors.HexColor('#FB923C'),
            'string': colors.HexColor('#059669'),
            'number': colors.HexColor('#DC2626'),
            'boolean': colors.HexColor('#7C3AED'),
            'null': colors.HexColor('#6B7280'),
            'key': colors.HexColor('#9A3412'),
            'background': colors.HexColor('#FFF7ED'),
            'border': colors.HexColor('#FED7AA')
        },
        ColorScheme.DARK: {
            'primary': colors.HexColor('#F8FAFC'),
            'secondary': colors.HexColor('#E2E8F0'),
            'accent': colors.HexColor('#64748B'),
            'string': colors.HexColor('#10B981'),
            'number': colors.HexColor('#F59E0B'),
            'boolean': colors.HexColor('#8B5CF6'),
            'null': colors.HexColor('#6B7280'),
            'key': colors.HexColor('#F8FAFC'),
            'background': colors.HexColor('#1E293B'),
            'border': colors.HexColor('#334155')
        }
    }


class PDFStyleManager:
    """Manages PDF styles and provides style objects for different elements."""
    
    def __init__(self, color_scheme: ColorScheme = ColorScheme.DEFAULT):
        self.color_scheme = color_scheme
        self.colors = PDFStyleConfig.COLOR_SCHEMES[color_scheme]
        self.styles = self._create_styles()
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create and return all paragraph styles."""
        base_styles = getSampleStyleSheet()
        
        styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Title'],
                fontSize=PDFStyleConfig.FONT_SIZE_TITLE,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['primary'],
                spaceAfter=PDFStyleConfig.SPACE_AFTER_TITLE,
                spaceBefore=PDFStyleConfig.SPACE_BEFORE_TITLE,
                alignment=TA_CENTER
            ),
            
            'heading': ParagraphStyle(
                'CustomHeading',
                parent=base_styles['Heading1'],
                fontSize=PDFStyleConfig.FONT_SIZE_HEADING,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['primary'],
                spaceAfter=PDFStyleConfig.SPACE_AFTER_HEADING,
                spaceBefore=PDFStyleConfig.SPACE_BEFORE_HEADING,
                borderWidth=0,
                borderPadding=0
            ),
            
            'subheading': ParagraphStyle(
                'CustomSubheading',
                parent=base_styles['Heading2'],
                fontSize=PDFStyleConfig.FONT_SIZE_SUBHEADING,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['secondary'],
                spaceAfter=PDFStyleConfig.SPACE_AFTER_SUBHEADING,
                spaceBefore=PDFStyleConfig.SPACE_BEFORE_SUBHEADING
            ),
            
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_NORMAL,
                textColor=self.colors['primary'],
                spaceAfter=PDFStyleConfig.SPACE_AFTER_PARAGRAPH,
                spaceBefore=PDFStyleConfig.SPACE_BEFORE_PARAGRAPH
            ),
            
            'key': ParagraphStyle(
                'JSONKey',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['key'],
                spaceAfter=2,
                spaceBefore=2
            ),
            
            'string_value': ParagraphStyle(
                'JSONStringValue',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_NORMAL,
                textColor=self.colors['string'],
                spaceAfter=2,
                spaceBefore=2
            ),
            
            'number_value': ParagraphStyle(
                'JSONNumberValue',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_MONO,
                textColor=self.colors['number'],
                spaceAfter=2,
                spaceBefore=2
            ),
            
            'boolean_value': ParagraphStyle(
                'JSONBooleanValue',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['boolean'],
                spaceAfter=2,
                spaceBefore=2
            ),
            
            'null_value': ParagraphStyle(
                'JSONNullValue',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_NORMAL,
                textColor=self.colors['null'],
                spaceAfter=2,
                spaceBefore=2
            ),
            
            'array_header': ParagraphStyle(
                'ArrayHeader',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['accent'],
                spaceAfter=4,
                spaceBefore=4
            ),
            
            'object_header': ParagraphStyle(
                'ObjectHeader',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_NORMAL,
                fontName=PDFStyleConfig.FONT_FAMILY_BOLD,
                textColor=self.colors['accent'],
                spaceAfter=4,
                spaceBefore=4
            ),
            
            'metadata': ParagraphStyle(
                'Metadata',
                parent=base_styles['Normal'],
                fontSize=PDFStyleConfig.FONT_SIZE_SMALL,
                fontName=PDFStyleConfig.FONT_FAMILY_NORMAL,
                textColor=self.colors['secondary'],
                spaceAfter=12,
                spaceBefore=6,
                alignment=TA_RIGHT
            )
        }
        
        return styles
    
    def get_style(self, style_name: str) -> ParagraphStyle:
        """Get a specific style by name."""
        return self.styles.get(style_name, self.styles['normal'])
    
    def get_color(self, color_name: str) -> colors.Color:
        """Get a specific color by name."""
        return self.colors.get(color_name, self.colors['primary'])
    
    def calculate_indent(self, level: int) -> float:
        """Calculate indentation for a given nesting level."""
        return PDFStyleConfig.INDENT_BASE * (PDFStyleConfig.INDENT_MULTIPLIER ** level)


def get_available_color_schemes() -> list:
    """Return list of available color scheme names."""
    return [scheme.value for scheme in ColorScheme]
