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
    report_type: str = "business_plan"  # business_plan, market_report, investment_summary, financial_analysis, risk_assessment, competitive_analysis, data_insights
    additional_context: Optional[str] = None
    analysis_depth: str = "standard"  # quick, standard, comprehensive
    focus_areas: Optional[List[str]] = None  # Specific areas to focus on

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
    report_type: str
    analysis_depth: str
    confidence_score: Optional[float] = None
    data_quality_score: Optional[float] = None

class FileValidationResponse(BaseModel):
    """Response model for file validation"""
    is_valid: bool
    file_type: str
    file_size: int
    supported_formats: List[str]
    validation_errors: List[str]
    recommendations: List[str]

class DataQualityAssessment(BaseModel):
    """Model for data quality assessment"""
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    timeliness_score: float
    overall_score: float
    issues_found: List[str]
    recommendations: List[str]

class EnhancedReportResponse(BaseModel):
    """Enhanced response model for report generation"""
    success: bool
    report_id: str
    report_type: str
    content: str
    generated_at: datetime
    metadata: Dict[str, Any]
    data_quality: Optional[DataQualityAssessment] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    confidence_metrics: Optional[Dict[str, float]] = None
