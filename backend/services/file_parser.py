"""
File parsing service
Handles CSV, PDF, and Excel file parsing with data extraction
"""

import pandas as pd
import PyPDF2
import os
from typing import Dict, Any, List, Union
import json

class FileParser:
    """Handles parsing of uploaded files into structured data"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.pdf', '.xlsx', '.xls']
    
    async def parse_file(self, file_path: str, file_extension: str) -> Union[List[Dict], Dict[str, Any]]:
        """
        Parse file based on its extension
        Returns structured data ready for AI analysis
        """
        
        if file_extension == '.csv':
            return await self._parse_csv(file_path)
        elif file_extension == '.pdf':
            return await self._parse_pdf(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            return await self._parse_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def _parse_csv(self, file_path: str) -> List[Dict]:
        """Parse CSV file into list of dictionaries"""
        try:
            df = pd.read_csv(file_path)
            
            # Clean data: remove empty rows, handle NaN values
            df = df.dropna(how='all')  # Remove completely empty rows
            df = df.fillna('')  # Fill NaN with empty string
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            
            return data
            
        except Exception as e:
            raise Exception(f"Error parsing CSV file: {str(e)}")
    
    async def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file and extract text content"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text_content = ""
                page_contents = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text_content += page_text + "\n"
                    page_contents.append({
                        "page_number": page_num + 1,
                        "content": page_text.strip()
                    })
                
                return {
                    "total_pages": len(pdf_reader.pages),
                    "full_text": text_content.strip(),
                    "pages": page_contents,
                    "metadata": {
                        "title": pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                        "author": pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                        "subject": pdf_reader.metadata.get('/Subject', '') if pdf_reader.metadata else ''
                    }
                }
                
        except Exception as e:
            raise Exception(f"Error parsing PDF file: {str(e)}")
    
    async def _parse_excel(self, file_path: str) -> List[Dict]:
        """Parse Excel file into list of dictionaries"""
        try:
            # Read all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            if len(excel_data) == 1:
                # Single sheet - return as list of records
                sheet_name = list(excel_data.keys())[0]
                df = excel_data[sheet_name]
                df = df.dropna(how='all').fillna('')
                return df.to_dict('records')
            else:
                # Multiple sheets - return structured data
                result = {}
                for sheet_name, df in excel_data.items():
                    df = df.dropna(how='all').fillna('')
                    result[sheet_name] = df.to_dict('records')
                return result
                
        except Exception as e:
            raise Exception(f"Error parsing Excel file: {str(e)}")
    
    def create_data_preview(self, parsed_data: Union[List[Dict], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a preview of parsed data for frontend display
        Limits data size to avoid overwhelming the UI
        """
        
        if isinstance(parsed_data, list):
            # CSV/Excel data
            preview = {
                "type": "tabular",
                "total_rows": len(parsed_data),
                "columns": list(parsed_data[0].keys()) if parsed_data else [],
                "sample_rows": parsed_data[:5],  # First 5 rows
                "data_types": self._analyze_data_types(parsed_data[:100])  # Analyze first 100 rows
            }
            
        elif isinstance(parsed_data, dict):
            if "full_text" in parsed_data:
                # PDF data
                preview = {
                    "type": "document",
                    "total_pages": parsed_data.get("total_pages", 0),
                    "text_preview": parsed_data["full_text"][:500] + "..." if len(parsed_data["full_text"]) > 500 else parsed_data["full_text"],
                    "metadata": parsed_data.get("metadata", {}),
                    "word_count": len(parsed_data["full_text"].split())
                }
            else:
                # Multi-sheet Excel
                preview = {
                    "type": "multi_sheet",
                    "sheets": {
                        sheet_name: {
                            "rows": len(sheet_data),
                            "columns": list(sheet_data[0].keys()) if sheet_data else [],
                            "sample": sheet_data[:3]
                        }
                        for sheet_name, sheet_data in parsed_data.items()
                    }
                }
        else:
            preview = {"type": "unknown", "data": str(parsed_data)[:200]}
        
        return preview
    
    def _analyze_data_types(self, data_sample: List[Dict]) -> Dict[str, str]:
        """Analyze data types of columns for better AI understanding"""
        if not data_sample:
            return {}
        
        columns = data_sample[0].keys()
        type_analysis = {}
        
        for col in columns:
            values = [row.get(col, '') for row in data_sample if row.get(col, '') != '']
            
            if not values:
                type_analysis[col] = "empty"
                continue
            
            # Try to determine type
            numeric_count = sum(1 for v in values if str(v).replace('.', '').replace('-', '').isdigit())
            date_count = sum(1 for v in values if self._is_date_like(str(v)))
            
            if numeric_count / len(values) > 0.8:
                type_analysis[col] = "numeric"
            elif date_count / len(values) > 0.8:
                type_analysis[col] = "date"
            else:
                type_analysis[col] = "text"
        
        return type_analysis
    
    def _is_date_like(self, value: str) -> bool:
        """Simple date detection"""
        date_indicators = ['/', '-', ' ', '年', '月', '日']
        return any(indicator in value for indicator in date_indicators) and any(c.isdigit() for c in value)
