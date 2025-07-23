"""
File upload router
Handles CSV and PDF file uploads with automatic parsing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uuid
import os
from datetime import datetime
import aiofiles

from services.file_parser import FileParser
from models.schemas import FileUploadResponse

router = APIRouter()

# Store uploaded files temporarily
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory storage for parsed data (use database in production)
parsed_data_store = {}

@router.post("/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and parse CSV or PDF files
    Returns parsed data preview and file metadata
    """
    
    # Validate file type
    allowed_types = [".csv", ".pdf", ".xlsx", ".xls"]
    filename = file.filename or "unknown"
    file_extension = os.path.splitext(filename)[1].lower()
    
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        safe_filename = filename or "unknown_file"
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Parse file content
        parser = FileParser()
        parsed_data = await parser.parse_file(file_path, file_extension)
        
        # Store parsed data
        parsed_data_store[file_id] = {
            "filename": safe_filename,
            "file_path": file_path,
            "file_type": file_extension,
            "parsed_data": parsed_data,
            "uploaded_at": datetime.now(),
            "status": "parsed"
        }
        
        # Create preview of parsed data
        preview = parser.create_data_preview(parsed_data)
        
        return FileUploadResponse(
            success=True,
            file_id=file_id,
            filename=safe_filename,
            file_type=file_extension,
            message="File uploaded and parsed successfully",
            parsed_data_preview=preview
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/{file_id}/status")
async def get_file_status(file_id: str):
    """Get status and metadata of uploaded file"""
    
    if file_id not in parsed_data_store:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = parsed_data_store[file_id]
    return {
        "file_id": file_id,
        "filename": file_info["filename"],
        "file_type": file_info["file_type"],
        "status": file_info["status"],
        "uploaded_at": file_info["uploaded_at"],
        "data_rows": len(file_info["parsed_data"]) if isinstance(file_info["parsed_data"], list) else 1
    }

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete uploaded file and its data"""
    
    if file_id not in parsed_data_store:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Remove file from storage
    file_info = parsed_data_store[file_id]
    if os.path.exists(file_info["file_path"]):
        os.remove(file_info["file_path"])
    
    # Remove from memory store
    del parsed_data_store[file_id]
    
    return {"message": "File deleted successfully"}

# Export parsed_data_store for use in other modules
def get_parsed_data(file_id: str):
    """Get parsed data by file ID"""
    return parsed_data_store.get(file_id)
