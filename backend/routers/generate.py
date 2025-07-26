"""
Report generation router
Handles AI-powered business report generation using OpenAI GPT-4
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid
import asyncio
import logging
from functools import wraps
from typing import Dict, Any, Callable, List
from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_generator import AIReportGenerator
from models.schemas import DataAnalysisRequest, ReportGenerationResponse, EnhancedReportResponse, DataQualityAssessment, FileValidationResponse
from routers.upload import get_file_data
from database.config import get_db_session
from database.crud import ReportCRUD, FileUploadCRUD
import time

router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# Retry decorator for AI operations
def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry failed operations with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {current_delay} seconds...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator

# Enhanced error handling
class ReportGenerationError(Exception):
    """Custom exception for report generation errors"""
    def __init__(self, message: str, error_code: str = "GENERATION_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DataQualityError(Exception):
    """Custom exception for data quality issues"""
    def __init__(self, message: str, quality_issues: list = None):
        self.message = message
        self.quality_issues = quality_issues or []
        super().__init__(self.message)

@retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
async def _generate_report_with_retry(ai_generator: AIReportGenerator, report_type: str, data: Any, context: str) -> str:
    """Internal function to generate report with retry logic"""
    try:
        if report_type == "business_plan":
            return await ai_generator.generate_business_plan(data, context)
        elif report_type == "market_report":
            return await ai_generator.generate_market_analysis(data, context)
        elif report_type == "investment_summary":
            return await ai_generator.generate_investment_summary(data, context)
        elif report_type == "financial_analysis":
            return await ai_generator.generate_financial_analysis(data, context)
        elif report_type == "risk_assessment":
            return await ai_generator.generate_risk_assessment(data, context)
        elif report_type == "competitive_analysis":
            return await ai_generator.generate_competitive_analysis(data, context)
        elif report_type == "data_insights":
            return await ai_generator.generate_data_insights(data, context)
        else:
            raise ReportGenerationError(
                f"Unsupported report type: {report_type}",
                error_code="INVALID_REPORT_TYPE",
                details={"supported_types": ["business_plan", "market_report", "investment_summary", "financial_analysis", "risk_assessment", "competitive_analysis", "data_insights"]}
            )
    except Exception as e:
        logger.error(f"Error generating {report_type} report: {str(e)}")
        raise ReportGenerationError(
            f"Failed to generate {report_type} report: {str(e)}",
            error_code="AI_GENERATION_FAILED",
            details={"report_type": report_type, "original_error": str(e)}
        )

@router.post("/business-report", response_model=EnhancedReportResponse)
async def generate_business_report(request: DataAnalysisRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Generate a comprehensive business report from uploaded data
    Enhanced with multiple report types and quality assessment
    """
    
    start_time = time.time()
    
    # Get file data from database
    file_data = await get_file_data(request.file_id, db)
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found or invalid")
    
    try:
        # Initialize AI generator
        ai_generator = AIReportGenerator()
        
        # Assess data quality
        data_quality = _assess_data_quality(file_data["parsed_data"])
        
        # Check data quality threshold
        if data_quality.overall_score < 0.3:
            raise DataQualityError(
                "Data quality is too low for reliable report generation",
                quality_issues=data_quality.issues_found
            )
        
        # Generate report with retry mechanism
        logger.info(f"Starting {request.report_type} report generation for file {request.file_id}")
        report_content = await _generate_report_with_retry(
            ai_generator,
            request.report_type,
            file_data["parsed_data"],
            request.additional_context or ""
        )
        
        # Determine model used based on report type
        model_mapping = {
            "business_plan": ai_generator.primary_model,
            "market_report": ai_generator.secondary_model,
            "investment_summary": ai_generator.judge_model,
            "financial_analysis": ai_generator.primary_model,
            "risk_assessment": ai_generator.secondary_model,
            "competitive_analysis": ai_generator.judge_model,
            "data_insights": ai_generator.primary_model
        }
        model_used = model_mapping.get(request.report_type, ai_generator.primary_model)
        
        processing_time = time.time() - start_time
        
        # Calculate confidence metrics
        confidence_metrics = _calculate_confidence_metrics(
            file_data["parsed_data"], 
            request.report_type, 
            data_quality.overall_score
        )
        
        # Create metadata
        metadata = {
            "source_filename": file_data["file_upload"].filename,
            "data_points": len(file_data["parsed_data"]) if isinstance(file_data["parsed_data"], list) else 1,
            "additional_context": request.additional_context,
            "focus_areas": request.focus_areas,
            "file_type": file_data["file_upload"].file_type
        }
        
        # Store generated report in database
        report = await ReportCRUD.create(
            db=db,
            file_upload_id=request.file_id,
            report_type=request.report_type,
            title=f"{request.report_type.replace('_', ' ').title()} Report",
            content=report_content,
            analysis_depth=request.analysis_depth,
            focus_areas=request.focus_areas,
            additional_context=request.additional_context,
            confidence_score=confidence_metrics.get("overall_confidence", 0.0),
            data_quality_score=data_quality.overall_score,
            processing_time=processing_time,
            model_used=model_used,
            confidence_metrics=confidence_metrics,
            metadata=metadata,
            status="completed"
        )
        
        return EnhancedReportResponse(
            success=True,
            report_id=report.id,
            report_type=request.report_type,
            content=report_content,
            generated_at=report.generated_at,
            metadata=metadata,
            data_quality=data_quality,
            processing_time=processing_time,
            model_used=model_used,
            confidence_metrics=confidence_metrics
        )
        
    except DataQualityError as e:
        logger.warning(f"Data quality error for file {request.file_id}: {e.message}")
        raise HTTPException(
            status_code=422, 
            detail={
                "error": "Data quality insufficient",
                "message": e.message,
                "quality_issues": e.quality_issues,
                "recommendations": [
                    "Please check your data for completeness",
                    "Ensure data is properly formatted",
                    "Consider data cleaning before analysis"
                ]
            }
        )
    except ReportGenerationError as e:
        logger.error(f"Report generation error for file {request.file_id}: {e.message}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error generating report for file {request.file_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during report generation",
                "details": {"original_error": str(e)}
            }
        )

@router.get("/{report_id}", response_model=ReportGenerationResponse)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieve a generated report by ID"""
    
    report = await ReportCRUD.get_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportGenerationResponse(
        success=True,
        report_id=report.id,
        content=report.content,
        generated_at=report.generated_at,
        metadata=report.metadata or {}
    )

@router.get("/{report_id}/download")
async def download_report(report_id: str, format: str = "markdown", db: AsyncSession = Depends(get_db_session)):
    """Download report in specified format (markdown, pdf, docx)"""
    
    report = await ReportCRUD.get_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format == "markdown":
        from fastapi.responses import Response
        return Response(
            content=report.content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.md"}
        )
    else:
        # For now, only markdown is supported
        raise HTTPException(status_code=400, detail="Only markdown format is currently supported")

@router.post("/quick-analysis")
async def quick_data_analysis(request: DataAnalysisRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Generate a quick data analysis summary
    Faster alternative to full report generation with enhanced error handling
    """
    
    file_data = await get_file_data(request.file_id, db)
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found or invalid")
    
    try:
        # Quick data quality check
        data_quality = _assess_data_quality(file_data["parsed_data"])
        
        # Lower threshold for quick analysis
        if data_quality.overall_score < 0.2:
            raise DataQualityError(
                "Data quality is too low even for quick analysis",
                quality_issues=data_quality.issues_found
            )
        
        ai_generator = AIReportGenerator()
        logger.info(f"Starting quick analysis for file {request.file_id}")
        
        # Use retry mechanism for quick analysis too
        analysis = await retry_on_failure(max_retries=2, delay=0.5, backoff=1.5)(
            ai_generator.quick_analysis
        )(file_data["parsed_data"])
        
        return {
            "success": True,
            "analysis": analysis,
            "file_id": request.file_id,
            "analyzed_at": datetime.now(),
            "data_quality_score": data_quality.overall_score,
            "quality_warnings": data_quality.issues_found if data_quality.overall_score < 0.7 else []
        }
        
    except DataQualityError as e:
        logger.warning(f"Data quality error in quick analysis for file {request.file_id}: {e.message}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Data quality insufficient for analysis",
                "message": e.message,
                "quality_issues": e.quality_issues
            }
        )
    except Exception as e:
        logger.error(f"Error in quick analysis for file {request.file_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "QUICK_ANALYSIS_FAILED",
                "message": "Failed to perform quick analysis",
                "details": {"original_error": str(e)}
            }
        )

@router.post("/validate-file", response_model=FileValidationResponse)
async def validate_file_data(request: DataAnalysisRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Validate uploaded file data quality and structure
    Provides detailed assessment before report generation
    """
    
    file_data = await get_file_data(request.file_id, db)
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found or invalid")
    
    try:
        logger.info(f"Starting file validation for file {request.file_id}")
        
        # Perform comprehensive data quality assessment
        data_quality = _assess_data_quality(file_data["parsed_data"])
        
        # Determine validation status
        if data_quality.overall_score >= 0.8:
            validation_status = "excellent"
            can_generate_reports = True
            recommended_actions = ["Data is ready for comprehensive analysis"]
        elif data_quality.overall_score >= 0.6:
            validation_status = "good"
            can_generate_reports = True
            recommended_actions = ["Data is suitable for analysis", "Consider addressing minor quality issues for better results"]
        elif data_quality.overall_score >= 0.4:
            validation_status = "fair"
            can_generate_reports = True
            recommended_actions = ["Data can be analyzed but with limitations", "Recommend data cleaning before analysis"]
        elif data_quality.overall_score >= 0.2:
            validation_status = "poor"
            can_generate_reports = True
            recommended_actions = ["Only basic analysis recommended", "Significant data quality issues detected"]
        else:
            validation_status = "insufficient"
            can_generate_reports = False
            recommended_actions = ["Data quality too low for reliable analysis", "Please clean and reformat data"]
        
        # Analyze data structure
        data_structure_info = _analyze_data_structure(file_data["parsed_data"])
        
        return FileValidationResponse(
            file_id=request.file_id,
            validation_status=validation_status,
            can_generate_reports=can_generate_reports,
            data_quality=data_quality,
            data_structure=data_structure_info,
            recommended_actions=recommended_actions,
            supported_report_types=_get_supported_report_types(file_data["parsed_data"], data_quality.overall_score),
            validated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error validating file {request.file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "VALIDATION_FAILED",
                "message": "Failed to validate file data",
                "details": {"original_error": str(e)}
            }
        )

def _analyze_data_structure(data: Any) -> Dict[str, Any]:
    """Analyze the structure of parsed data"""
    structure_info = {
        "data_type": "unknown",
        "total_records": 0,
        "columns": [],
        "sample_data": None,
        "data_types": {},
        "has_headers": False,
        "estimated_size_mb": 0
    }
    
    try:
        if isinstance(data, list) and data:
            structure_info["data_type"] = "tabular"
            structure_info["total_records"] = len(data)
            
            if isinstance(data[0], dict):
                structure_info["columns"] = list(data[0].keys())
                structure_info["has_headers"] = True
                
                # Analyze data types
                for col in structure_info["columns"]:
                    sample_values = [row.get(col) for row in data[:10] if row.get(col) is not None]
                    if sample_values:
                        common_type = type(sample_values[0]).__name__
                        structure_info["data_types"][col] = common_type
                
                # Sample data (first 3 records)
                structure_info["sample_data"] = data[:3]
            
        elif isinstance(data, dict):
            structure_info["data_type"] = "document" if "full_text" in data else "structured"
            structure_info["total_records"] = 1
            
            if "full_text" in data:
                text_length = len(data["full_text"])
                structure_info["estimated_size_mb"] = text_length / (1024 * 1024)
                structure_info["sample_data"] = data["full_text"][:500] + "..." if text_length > 500 else data["full_text"]
            else:
                structure_info["columns"] = list(data.keys())
                structure_info["sample_data"] = {k: str(v)[:100] for k, v in data.items()}
        
        # Estimate size
        import sys
        structure_info["estimated_size_mb"] = sys.getsizeof(str(data)) / (1024 * 1024)
        
    except Exception as e:
        logger.warning(f"Error analyzing data structure: {str(e)}")
    
    return structure_info

def _get_supported_report_types(data: Any, quality_score: float) -> List[str]:
    """Determine which report types are supported based on data and quality"""
    base_types = ["data_insights"]
    
    if quality_score >= 0.4:
        base_types.extend(["business_plan", "market_report"])
    
    if quality_score >= 0.6:
        base_types.extend(["investment_summary", "risk_assessment"])
    
    if quality_score >= 0.7:
        base_types.extend(["financial_analysis", "competitive_analysis"])
    
    # Check if data is suitable for financial analysis
    if isinstance(data, list) and data:
        if any(isinstance(row, dict) and any(key.lower() in ['revenue', 'profit', 'cost', 'price', 'amount', 'value'] 
               for key in row.keys()) for row in data[:5]):
            if "financial_analysis" not in base_types and quality_score >= 0.5:
                base_types.append("financial_analysis")
    
    return base_types

def _assess_data_quality(data: any) -> DataQualityAssessment:
    """Assess the quality of parsed data"""
    
    completeness_score = 0.0
    accuracy_score = 0.0
    consistency_score = 0.0
    timeliness_score = 0.0
    issues_found = []
    recommendations = []
    
    if isinstance(data, list) and data:
        # Tabular data assessment
        total_cells = 0
        empty_cells = 0
        
        for row in data:
            if isinstance(row, dict):
                for key, value in row.items():
                    total_cells += 1
                    if value is None or value == "" or str(value).strip() == "":
                        empty_cells += 1
        
        # Completeness: percentage of non-empty cells
        completeness_score = (total_cells - empty_cells) / total_cells if total_cells > 0 else 0.0
        
        # Consistency: check for consistent data types in columns
        if data:
            columns = data[0].keys() if isinstance(data[0], dict) else []
            consistent_columns = 0
            
            for col in columns:
                values = [row.get(col) for row in data if row.get(col) is not None]
                if values:
                    first_type = type(values[0])
                    if all(type(v) == first_type for v in values):
                        consistent_columns += 1
            
            consistency_score = consistent_columns / len(columns) if columns else 0.0
        
        # Accuracy: basic validation (no obvious errors)
        accuracy_score = 0.8  # Default assumption, would need domain-specific validation
        
        # Timeliness: assume current data is timely
        timeliness_score = 0.9
        
        # Identify issues
        if completeness_score < 0.8:
            issues_found.append(f"Data has {(1-completeness_score)*100:.1f}% missing values")
            recommendations.append("Consider data cleaning to handle missing values")
        
        if consistency_score < 0.9:
            issues_found.append("Inconsistent data types detected in some columns")
            recommendations.append("Standardize data types for better analysis")
            
    elif isinstance(data, dict):
        # Document or structured data assessment
        if "full_text" in data:
            text_content = data["full_text"]
            if len(text_content.strip()) > 100:
                completeness_score = 0.9
                accuracy_score = 0.8
                consistency_score = 0.9
                timeliness_score = 0.8
            else:
                completeness_score = 0.5
                issues_found.append("Document content appears to be very short")
                recommendations.append("Verify document content is complete")
        else:
            # Structured data
            non_empty_values = sum(1 for v in data.values() if v is not None and str(v).strip() != "")
            completeness_score = non_empty_values / len(data) if data else 0.0
            accuracy_score = 0.8
            consistency_score = 0.8
            timeliness_score = 0.8
    
    else:
        # Unknown data type
        completeness_score = 0.5
        accuracy_score = 0.5
        consistency_score = 0.5
        timeliness_score = 0.5
        issues_found.append("Unknown data format detected")
        recommendations.append("Verify data format is supported")
    
    overall_score = (completeness_score + accuracy_score + consistency_score + timeliness_score) / 4
    
    return DataQualityAssessment(
        completeness_score=completeness_score,
        accuracy_score=accuracy_score,
        consistency_score=consistency_score,
        timeliness_score=timeliness_score,
        overall_score=overall_score,
        issues_found=issues_found,
        recommendations=recommendations
    )

def _calculate_confidence_metrics(data: any, report_type: str, data_quality_score: float) -> Dict[str, float]:
    """Calculate confidence metrics for the generated report"""
    
    # Base confidence based on data quality
    base_confidence = data_quality_score
    
    # Data size factor
    data_size_factor = 1.0
    if isinstance(data, list):
        if len(data) < 10:
            data_size_factor = 0.7
        elif len(data) < 50:
            data_size_factor = 0.8
        elif len(data) > 1000:
            data_size_factor = 1.0
        else:
            data_size_factor = 0.9
    
    # Report type complexity factor
    complexity_factors = {
        "business_plan": 0.8,  # Complex, requires comprehensive data
        "market_report": 0.9,  # Moderate complexity
        "investment_summary": 0.85,  # Moderate complexity
        "financial_analysis": 0.95,  # High confidence with financial data
        "risk_assessment": 0.8,  # Complex, requires domain knowledge
        "competitive_analysis": 0.75,  # Complex, requires market data
        "data_insights": 0.9  # Direct data analysis
    }
    
    complexity_factor = complexity_factors.get(report_type, 0.8)
    
    # Calculate final confidence
    overall_confidence = base_confidence * data_size_factor * complexity_factor
    
    return {
        "overall_confidence": min(overall_confidence, 1.0),
        "data_quality_confidence": base_confidence,
        "data_size_confidence": data_size_factor,
        "analysis_complexity_confidence": complexity_factor
    }

# Legacy function - reports are now stored in database
# Use ReportCRUD.get_by_id instead
