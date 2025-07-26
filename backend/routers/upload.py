"""
File upload router
Handles CSV and PDF file uploads with automatic parsing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import uuid
import os
from datetime import datetime
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from services.file_parser import FileParser
from models.schemas import FileUploadResponse, FileValidationResponse
from database.config import get_db_session
from database.crud import FileUploadCRUD, DataQualityAssessmentCRUD

router = APIRouter()

# Store uploaded files temporarily
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# File size limit (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

@router.post("/validate", response_model=FileValidationResponse)
async def validate_file(file: UploadFile = File(...)):
    """
    Validate file before upload
    """
    allowed_types = [".csv", ".pdf", ".xlsx", ".xls", ".txt", ".docx", ".json"]
    filename = file.filename or "unknown"
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Read file size
    content = await file.read()
    file_size = len(content)
    
    validation_errors = []
    recommendations = []
    
    # Validate file type
    if file_extension not in allowed_types:
        validation_errors.append(f"Unsupported file type: {file_extension}")
        recommendations.append(f"Please use one of: {', '.join(allowed_types)}")
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        validation_errors.append(f"File too large: {file_size / (1024*1024):.1f}MB (max: 50MB)")
        recommendations.append("Please reduce file size or split into smaller files")
    
    if file_size == 0:
        validation_errors.append("File is empty")
        recommendations.append("Please upload a file with content")
    
    return FileValidationResponse(
        is_valid=len(validation_errors) == 0,
        file_type=file_extension,
        file_size=file_size,
        supported_formats=allowed_types,
        validation_errors=validation_errors,
        recommendations=recommendations
    )

@router.post("/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db_session)):
    """
    Upload and parse files with database storage
    Returns parsed data preview and file metadata
    """
    
    # Validate file type and size
    allowed_types = [".csv", ".pdf", ".xlsx", ".xls", ".txt", ".docx", ".json"]
    filename = file.filename or "unknown"
    file_extension = os.path.splitext(filename)[1].lower()
    
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size / (1024*1024):.1f}MB (max: 50MB)"
        )
    
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        safe_filename = filename or "unknown_file"
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create database record
        file_upload = await FileUploadCRUD.create(
            db=db,
            id=file_id,
            filename=safe_filename,
            original_filename=filename,
            file_type=file_extension,
            file_size=file_size,
            file_path=file_path,
            validation_status="pending"
        )
        
        # Parse file content
        parser = FileParser()
        try:
            parsed_data = await parser.parse_file(file_path, file_extension)
            
            # Create preview of parsed data
            preview = parser.create_data_preview(parsed_data)
            
            # Update validation status
            await FileUploadCRUD.update_validation_status(
                db=db, 
                file_id=file_id, 
                status="valid"
            )
            
            # Perform data quality assessment
            try:
                quality_assessment = await parser.assess_data_quality(parsed_data)
                await DataQualityAssessmentCRUD.create(
                    db=db,
                    file_upload_id=file_id,
                    **quality_assessment
                )
            except Exception as e:
                # Log but don't fail upload if quality assessment fails
                import logging
                logging.warning(f"Data quality assessment failed for {file_id}: {e}")
            
        except Exception as parse_error:
            # Update validation status with error
            await FileUploadCRUD.update_validation_status(
                db=db,
                file_id=file_id,
                status="invalid",
                errors=[str(parse_error)]
            )
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing file: {str(parse_error)}"
            )
        
        return FileUploadResponse(
            success=True,
            file_id=file_id,
            filename=safe_filename,
            file_type=file_extension,
            message="File uploaded and parsed successfully",
            parsed_data_preview=preview
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/{file_id}/status")
async def get_file_status(file_id: str, db: AsyncSession = Depends(get_db_session)):
    """Get status and metadata of uploaded file"""
    
    file_upload = await FileUploadCRUD.get_by_id(db, file_id)
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get data quality assessment if available
    quality_assessment = await DataQualityAssessmentCRUD.get_by_file_id(db, file_id)
    
    response = {
        "file_id": file_id,
        "filename": file_upload.filename,
        "original_filename": file_upload.original_filename,
        "file_type": file_upload.file_type,
        "file_size": file_upload.file_size,
        "validation_status": file_upload.validation_status,
        "uploaded_at": file_upload.upload_time,
        "reports_count": len(file_upload.reports) if file_upload.reports else 0
    }
    
    if file_upload.validation_errors:
        response["validation_errors"] = file_upload.validation_errors
    
    if quality_assessment:
        response["data_quality"] = {
            "overall_score": quality_assessment.overall_score,
            "completeness_score": quality_assessment.completeness_score,
            "accuracy_score": quality_assessment.accuracy_score,
            "consistency_score": quality_assessment.consistency_score,
            "timeliness_score": quality_assessment.timeliness_score,
            "issues_found": quality_assessment.issues_found,
            "recommendations": quality_assessment.recommendations
        }
    
    return response

@router.delete("/{file_id}")
async def delete_file(file_id: str, db: AsyncSession = Depends(get_db_session)):
    """Delete uploaded file and its data"""
    
    file_upload = await FileUploadCRUD.get_by_id(db, file_id)
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Remove physical file
    if os.path.exists(file_upload.file_path):
        try:
            os.remove(file_upload.file_path)
        except OSError as e:
            # Log but don't fail if file removal fails
            import logging
            logging.warning(f"Failed to remove file {file_upload.file_path}: {e}")
    
    # Delete from database (cascade will handle related records)
    await db.delete(file_upload)
    await db.commit()
    
    return {"message": "File deleted successfully"}

@router.get("/")
async def list_files(limit: int = 10, db: AsyncSession = Depends(get_db_session)):
    """List recent uploaded files"""
    
    files = await FileUploadCRUD.get_recent(db, limit=limit)
    
    return {
        "files": [
            {
                "file_id": f.id,
                "filename": f.filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "validation_status": f.validation_status,
                "uploaded_at": f.upload_time,
                "reports_count": len(f.reports) if f.reports else 0
            }
            for f in files
        ]
    }

# Helper function for other modules to get file data
async def get_file_data(file_id: str, db: AsyncSession):
    """Get file upload record and parse data if needed"""
    file_upload = await FileUploadCRUD.get_by_id(db, file_id)
    if not file_upload or file_upload.validation_status != "valid":
        return None
    
    # Parse file data on demand
    try:
        parser = FileParser()
        parsed_data = await parser.parse_file(file_upload.file_path, file_upload.file_type)
        return {
            "file_upload": file_upload,
            "parsed_data": parsed_data
        }
    except Exception as e:
        import logging
        logging.error(f"Failed to parse file {file_id}: {e}")
        return None
