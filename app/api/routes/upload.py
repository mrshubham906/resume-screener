import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import aiofiles
import logging

from app.api.auth import get_api_key_header
from app.services.database import db_service
from app.tasks.processing import process_resume_task
from app.models.resume import ResumeResponse, ResumeStatus
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/resume", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key_header)
):
    """Upload a PDF resume for processing"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Validate file size
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.max_file_size} bytes"
        )
    
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.upload_dir, unique_filename)
        # Ensure the upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
        logger.info(f"File path: {file_path}")
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create resume record in database
        resume_data = {
            "filename": file.filename,
            "upload_date": datetime.now(),
            "status": ResumeStatus.PROCESSING,
            "file_size": len(content)
        }
        
        resume_id = await db_service.create_resume(resume_data)
        
        # Queue background task for processing
        task = process_resume_task.delay(resume_id, file_path, len(content))

        
        logger.info(f"Queued resume processing task {task.id} for resume {resume_id}")
        
        return ResumeResponse(
            id=resume_id,
            filename=file.filename,
            status=ResumeStatus.PROCESSING,
            message="Resume uploaded successfully and queued for processing",
            upload_date=resume_data["upload_date"]
        )
        
    except Exception as e:
        logger.error(f"Failed to upload resume: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload resume"
        )


@router.get("/status/{resume_id}")
async def get_upload_status(
    resume_id: str,
    api_key: str = Depends(get_api_key_header)
):
    """Get the processing status of a resume"""
    
    try:
        resume = await db_service.get_resume(resume_id)
        
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )
        
        return {
            "id": resume_id,
            "filename": resume.filename,
            "status": resume.status,
            "upload_date": resume.upload_date,
            "processing_time": resume.metadata.processing_time if resume.metadata else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get upload status"
        ) 