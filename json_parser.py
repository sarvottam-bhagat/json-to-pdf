"""
JSON Parser and Validator Module

This module provides robust JSON parsing with error handling, validation,
and support for various JSON structures including objects, arrays, and nested data.
"""

import json
import os
from typing import Any, Dict, List, Union, Tuple
from enum import Enum


class JSONDataType(Enum):
    """Enumeration of JSON data types for styling purposes."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"
    OBJECT = "object"
    ARRAY = "array"


class JSONParseError(Exception):
    """Custom exception for JSON parsing errors."""
    pass


class JSONValidator:
    """Validates and analyzes JSON data structures."""
    
    @staticmethod
    def get_data_type(value: Any) -> JSONDataType:
        """
        Determine the JSON data type of a value.
        
        Args:
            value: The value to analyze
            
        Returns:
            JSONDataType: The corresponding data type
        """
        if value is None:
            return JSONDataType.NULL
        elif isinstance(value, bool):
            return JSONDataType.BOOLEAN
        elif isinstance(value, (int, float)):
            return JSONDataType.NUMBER
        elif isinstance(value, str):
            return JSONDataType.STRING
        elif isinstance(value, dict):
            return JSONDataType.OBJECT
        elif isinstance(value, list):
            return JSONDataType.ARRAY
        else:
            return JSONDataType.STRING  # Default fallback
    
    @staticmethod
    def analyze_structure(data: Any, max_depth: int = 10) -> Dict[str, Any]:
        """
        Analyze the structure of JSON data.
        
        Args:
            data: The JSON data to analyze
            max_depth: Maximum depth to analyze (prevents infinite recursion)
            
        Returns:
            Dict containing structure analysis
        """
        def _analyze_recursive(obj: Any, depth: int = 0) -> Dict[str, Any]:
            if depth > max_depth:
                return {"type": "max_depth_reached", "depth": depth}
            
            data_type = JSONValidator.get_data_type(obj)
            analysis = {
                "type": data_type.value,
                "depth": depth
            }
            
            if data_type == JSONDataType.OBJECT:
                analysis["keys"] = list(obj.keys())
                analysis["key_count"] = len(obj)
                analysis["children"] = {
                    key: _analyze_recursive(value, depth + 1)
                    for key, value in obj.items()
                }
            elif data_type == JSONDataType.ARRAY:
                analysis["length"] = len(obj)
                if obj:  # Non-empty array
                    # Analyze first few items to understand array structure
                    sample_size = min(3, len(obj))
                    analysis["sample_items"] = [
                        _analyze_recursive(obj[i], depth + 1)
                        for i in range(sample_size)
                    ]
                    # Check if all items have the same type
                    types = set(JSONValidator.get_data_type(item).value for item in obj)
                    analysis["homogeneous"] = len(types) == 1
                    analysis["item_types"] = list(types)
            
            return analysis
        
        return _analyze_recursive(data)


class JSONParser:
    """Handles JSON parsing with comprehensive error handling."""
    
    def __init__(self):
        self.validator = JSONValidator()
    
    def parse_file(self, file_path: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Parse JSON from a file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (parsed_data, structure_analysis)
            
        Raises:
            JSONParseError: If parsing fails
        """
        if not os.path.exists(file_path):
            raise JSONParseError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise JSONParseError(f"Path is not a file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                
            if not content:
                raise JSONParseError("File is empty")
                
            return self.parse_string(content)
            
        except FileNotFoundError:
            raise JSONParseError(f"File not found: {file_path}")
        except PermissionError:
            raise JSONParseError(f"Permission denied reading file: {file_path}")
        except UnicodeDecodeError as e:
            raise JSONParseError(f"File encoding error: {e}")
        except Exception as e:
            raise JSONParseError(f"Error reading file {file_path}: {e}")
    
    def parse_string(self, json_string: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Parse JSON from a string.
        
        Args:
            json_string: JSON string to parse
            
        Returns:
            Tuple of (parsed_data, structure_analysis)
            
        Raises:
            JSONParseError: If parsing fails
        """
        if not json_string or not json_string.strip():
            raise JSONParseError("JSON string is empty")
        
        try:
            data = json.loads(json_string)
            analysis = self.validator.analyze_structure(data)
            return data, analysis
            
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Invalid JSON syntax: {e}")
        except Exception as e:
            raise JSONParseError(f"Error parsing JSON: {e}")
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate that data is JSON-serializable.
        
        Args:
            data: Data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError):
            return False


def format_value_for_display(value: Any, max_length: int = 100) -> str:
    """
    Format a value for display in the PDF.
    
    Args:
        value: The value to format
        max_length: Maximum length for string representation
        
    Returns:
        Formatted string representation
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        if len(value) > max_length:
            return f'"{value[:max_length-3]}..."'
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (dict, list)):
        # For complex types, show a summary
        if isinstance(value, dict):
            return f"Object ({len(value)} keys)"
        else:
            return f"Array ({len(value)} items)"
    else:
        return str(value)
