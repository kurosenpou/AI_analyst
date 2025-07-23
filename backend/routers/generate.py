"""
Report generation router
Handles AI-powered business report generation using OpenAI GPT-4
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid

from services.ai_generator import AIReportGenerator
from models.schemas import DataAnalysisRequest, ReportGenerationResponse
from routers.upload import get_parsed_data

router = APIRouter()

# In-memory storage for generated reports (use database in production)
reports_store = {}

@router.post("/business-report", response_model=ReportGenerationResponse)
async def generate_business_report(request: DataAnalysisRequest):
    """
    Generate a comprehensive business report from uploaded data
    Uses OpenAI GPT-4 for intelligent analysis and recommendations
    """
    
    # Get parsed data
    file_data = get_parsed_data(request.file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found")
    
    try:
        # Initialize AI generator
        ai_generator = AIReportGenerator()
        
        # Generate report based on type
        if request.report_type == "business_plan":
            report_content = await ai_generator.generate_business_plan(
                file_data["parsed_data"], 
                request.additional_context
            )
        elif request.report_type == "market_report":
            report_content = await ai_generator.generate_market_analysis(
                file_data["parsed_data"], 
                request.additional_context
            )
        elif request.report_type == "investment_summary":
            report_content = await ai_generator.generate_investment_summary(
                file_data["parsed_data"], 
                request.additional_context
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Store generated report
        report_id = str(uuid.uuid4())
        reports_store[report_id] = {
            "report_id": report_id,
            "file_id": request.file_id,
            "report_type": request.report_type,
            "content": report_content,
            "generated_at": datetime.now(),
            "metadata": {
                "source_filename": file_data["filename"],
                "data_points": len(file_data["parsed_data"]) if isinstance(file_data["parsed_data"], list) else 1,
                "additional_context": request.additional_context
            }
        }
        
        return ReportGenerationResponse(
            success=True,
            report_id=report_id,
            report_type=request.report_type,
            content=report_content,
            generated_at=datetime.now(),
            metadata=reports_store[report_id]["metadata"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/{report_id}")
async def get_report(report_id: str):
    """Retrieve a generated report by ID"""
    
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return reports_store[report_id]

@router.get("/{report_id}/download")
async def download_report(report_id: str, format: str = "markdown"):
    """Download report in specified format (markdown, pdf, docx)"""
    
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = reports_store[report_id]
    
    if format == "markdown":
        from fastapi.responses import Response
        return Response(
            content=report["content"],
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.md"}
        )
    else:
        # For now, only markdown is supported
        raise HTTPException(status_code=400, detail="Only markdown format is currently supported")

@router.post("/quick-analysis")
async def quick_data_analysis(request: DataAnalysisRequest):
    """
    Generate a quick data analysis summary
    Faster alternative to full report generation
    """
    
    file_data = get_parsed_data(request.file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found")
    
    try:
        ai_generator = AIReportGenerator()
        analysis = await ai_generator.quick_analysis(file_data["parsed_data"])
        
        return {
            "success": True,
            "analysis": analysis,
            "file_id": request.file_id,
            "analyzed_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in quick analysis: {str(e)}")

# Export reports_store for potential future use
def get_report_by_id(report_id: str):
    """Get report by ID"""
    return reports_store.get(report_id)
