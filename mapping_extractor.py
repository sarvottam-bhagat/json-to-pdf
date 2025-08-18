"""
Mapping JSON Data Extractor Module

This module provides functionality to extract gap analysis data from the complex
mapping.json structure and convert it to a format compatible with existing PDF
generation logic that was designed for test.json.
"""

import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DataFormat(Enum):
    """Enumeration of supported data formats."""
    TEST_JSON = "test_json"
    MAPPING_JSON = "mapping_json"
    UNKNOWN = "unknown"


@dataclass
class ExtractedSection:
    """Represents an extracted section with its metadata."""
    section_id: str
    section_title: str
    module_key: str
    module_label: str
    section_key: str
    gap_analysis_data: Dict[str, Any]
    strategic_recommendations: Optional[str] = None


class MappingDataExtractor:
    """Extracts and normalizes data from mapping.json files."""
    
    def __init__(self):
        self.detected_format = DataFormat.UNKNOWN
        
    def detect_format(self, data: Dict[str, Any]) -> DataFormat:
        """
        Detect whether the data is in test.json or mapping.json format.
        
        Args:
            data: The JSON data to analyze
            
        Returns:
            DataFormat: The detected format
        """
        if "gap_analysis_report" in data:
            return DataFormat.TEST_JSON
        elif "result" in data and "job_id" in data:
            return DataFormat.MAPPING_JSON
        else:
            return DataFormat.UNKNOWN
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract data from a JSON file and normalize it.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dict containing normalized gap analysis data
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        
        return self.extract_from_data(data)
    
    def extract_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize data from either format.
        
        Args:
            data: The JSON data to process
            
        Returns:
            Dict containing normalized gap analysis data in test.json format
            
        Raises:
            ValueError: If data format is not supported
        """
        self.detected_format = self.detect_format(data)
        
        if self.detected_format == DataFormat.TEST_JSON:
            return self._extract_from_test_format(data)
        elif self.detected_format == DataFormat.MAPPING_JSON:
            return self._extract_from_mapping_format(data)
        else:
            raise ValueError("Unsupported data format. Expected test.json or mapping.json structure.")
    
    def _extract_from_test_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from test.json format (pass-through).
        
        Args:
            data: Test format JSON data
            
        Returns:
            Dict: The same data (no transformation needed)
        """
        return data
    
    def _extract_from_mapping_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from mapping.json format and convert to test.json structure.
        
        Args:
            data: Mapping format JSON data
            
        Returns:
            Dict: Data converted to test.json format
        """
        # Extract job metadata
        job_metadata = {
            "job_id": data.get("job_id"),
            "user_id": data.get("user_id"),
            "status": data.get("status"),
            "filename": data.get("filename"),
            "name": data.get("name"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at")
        }
        
        # Extract all sections from all modules
        extracted_sections = self._extract_all_sections(data.get("result", {}))
        
        # Convert to test.json format
        normalized_data = self._convert_to_test_format(extracted_sections, job_metadata)
        
        return normalized_data
    
    def _extract_all_sections(self, result_data: Dict[str, Any]) -> List[ExtractedSection]:
        """
        Extract all sections from the result data.
        
        Args:
            result_data: The result portion of mapping.json
            
        Returns:
            List of ExtractedSection objects
        """
        sections = []
        
        for module_key, module_data in result_data.items():
            if not isinstance(module_data, dict):
                continue
                
            module_label = module_data.get("label", module_key)
            module_sections = module_data.get("sections", [])
            
            for section in module_sections:
                if not isinstance(section, dict):
                    continue
                    
                section_key = section.get("section_key", "")
                section_title = section.get("section_title", "")
                pre_ind_maps = section.get("pre_ind_maps", [])
                
                for pre_ind_map in pre_ind_maps:
                    if not isinstance(pre_ind_map, dict):
                        continue
                        
                    gap_result = pre_ind_map.get("result", {})
                    if gap_result:
                        # Create section ID from pre_ind_section or use section_key
                        section_id = gap_result.get("section", section_key)
                        
                        extracted_section = ExtractedSection(
                            section_id=section_id,
                            section_title=gap_result.get("section_title", section_title),
                            module_key=module_key,
                            module_label=module_label,
                            section_key=section_key,
                            gap_analysis_data=gap_result,
                            strategic_recommendations=gap_result.get("strategic_recommendations")
                        )
                        sections.append(extracted_section)
        
        return sections
    
    def _convert_to_test_format(self, sections: List[ExtractedSection],
                               job_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert extracted sections to test.json format while preserving module structure.

        Args:
            sections: List of extracted sections
            job_metadata: Job metadata from mapping.json

        Returns:
            Dict in test.json format with module structure preserved
        """
        # Calculate aggregate metadata
        total_checkpoints = 0
        total_covered = 0
        total_chunks = 0

        section_analyses = {}
        modules_structure = {}

        # Group sections by module and organize hierarchically
        for section in sections:
            gap_data = section.gap_analysis_data
            summary = gap_data.get("summary", {})

            # Add to aggregates
            total_checkpoints += summary.get("total_checkpoints", 0)
            total_covered += summary.get("covered_checkpoints", 0)
            total_chunks += summary.get("total_input_chunks_analyzed", 0)

            # Create unique section key for section_analyses
            unique_section_key = f"{section.section_key}_{section.section_id}"
            section_analyses[unique_section_key] = gap_data

            # Organize by module structure using module_key as the key
            module_key = section.module_key
            module_label = section.module_label
            if module_key not in modules_structure:
                modules_structure[module_key] = {
                    "module_label": module_label,
                    "sections": {}
                }

            # Group by section_key within module
            section_key = section.section_key
            if section_key not in modules_structure[module_key]["sections"]:
                modules_structure[module_key]["sections"][section_key] = []

            modules_structure[module_key]["sections"][section_key].append({
                "section_id": section.section_id,
                "section_title": section.section_title,
                "unique_key": unique_section_key,
                "gap_data": gap_data
            })
        
        # Calculate overall coverage percentage
        overall_coverage = (total_covered / total_checkpoints * 100) if total_checkpoints > 0 else 0
        
        # Build test.json format structure with module hierarchy
        normalized_data = {
            "gap_analysis_report": {
                "metadata": {
                    "sections_analyzed": len(sections),
                    "total_checkpoints": total_checkpoints,
                    "overall_coverage_percentage": round(overall_coverage, 1),
                    "total_input_chunks_analyzed": total_chunks,
                    "status": "complete"
                },
                "section_analyses": section_analyses,
                "modules_structure": modules_structure
            },
            # Add mapping-specific metadata for reference
            "_mapping_metadata": job_metadata,
            "_extracted_sections_info": [
                {
                    "section_id": s.section_id,
                    "module_key": s.module_key,
                    "module_label": s.module_label,
                    "section_key": s.section_key,
                    "has_strategic_recommendations": s.strategic_recommendations is not None
                }
                for s in sections
            ]
        }
        
        return normalized_data
    
    def get_detected_format(self) -> DataFormat:
        """Get the detected data format."""
        return self.detected_format
    
    def get_sections_info(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get information about all sections in the data.
        
        Args:
            data: The JSON data to analyze
            
        Returns:
            List of section information dictionaries
        """
        format_type = self.detect_format(data)
        
        if format_type == DataFormat.TEST_JSON:
            sections_info = []
            section_analyses = data.get("gap_analysis_report", {}).get("section_analyses", {})
            for section_id, section_data in section_analyses.items():
                sections_info.append({
                    "section_id": section_id,
                    "section_title": section_data.get("section_title", ""),
                    "module_label": "N/A",
                    "section_key": section_id,
                    "format": "test_json"
                })
            return sections_info
            
        elif format_type == DataFormat.MAPPING_JSON:
            sections = self._extract_all_sections(data.get("result", {}))
            return [
                {
                    "section_id": s.section_id,
                    "section_title": s.section_title,
                    "module_label": s.module_label,
                    "section_key": s.section_key,
                    "format": "mapping_json"
                }
                for s in sections
            ]
        
        return []
