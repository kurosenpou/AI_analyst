"""
Pydantic models for request/response data validation
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    file_id: str
    filename: str
    file_type: str
    message: str
    parsed_data_preview: Optional[Dict[str, Any]] = None

class DataAnalysisRequest(BaseModel):
    """Request model for data analysis"""
    file_id: str
    report_type: str = "business_plan"  # business_plan, market_report, investment_summary
    additional_context: Optional[str] = None

class ReportGenerationResponse(BaseModel):
    """Response model for report generation"""
    success: bool
    report_id: str
    report_type: str
    content: str
    generated_at: datetime
    metadata: Dict[str, Any]

class BusinessInsight(BaseModel):
    """Model for individual business insights"""
    category: str
    title: str
    description: str
    importance: str  # high, medium, low
    actionable_items: List[str]

class BusinessReport(BaseModel):
    """Complete business report model"""
    report_id: str
    title: str
    executive_summary: str
    insights: List[BusinessInsight]
    recommendations: List[str]
    financial_highlights: Dict[str, Any]
    generated_at: datetime
    source_data_summary: str
