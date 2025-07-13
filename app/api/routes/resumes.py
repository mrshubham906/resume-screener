from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
import logging

from app.api.auth import get_api_key_header
from app.services.database import db_service
from app.services.vector_store import vector_store
from app.models.resume import ResumeDetailResponse, ResumeStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    resume_id: str,
    api_key: str = Depends(get_api_key_header)
):
    """Get detailed information about a specific resume"""
    
    try:
        resume = await db_service.get_resume(resume_id)
        
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )
        
        return ResumeDetailResponse(
            id=resume_id,
            filename=resume.filename,
            upload_date=resume.upload_date,
            status=resume.status,
            content=resume.content,
            metadata=resume.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resume {resume_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get resume"
        )


@router.get("/", response_model=List[ResumeDetailResponse])
async def list_resumes(
    skip: int = Query(0, ge=0, description="Number of resumes to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of resumes to return"),
    status: Optional[ResumeStatus] = Query(None, description="Filter by status"),
    api_key: str = Depends(get_api_key_header)
):
    """List all resumes with optional filtering"""
    
    try:
        if status:
            resumes = await db_service.get_resumes_by_status(status, limit)
        else:
            resumes = await db_service.get_all_resumes(skip, limit)
        
        return [
            ResumeDetailResponse(
                id=resume.id,
                filename=resume.filename,
                upload_date=resume.upload_date,
                status=resume.status,
                content=resume.content,
                metadata=resume.metadata
            )
            for resume in resumes
        ]
        
    except Exception as e:
        logger.error(f"Failed to list resumes: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list resumes"
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    api_key: str = Depends(get_api_key_header)
):
    """Delete a resume and its associated vector"""
    
    try:
        # Get resume first to check if it exists
        resume = await db_service.get_resume(resume_id)
        
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )
        
        # Delete from vector store if vector_id exists
        if resume.vector_id:
            vector_store.delete_vector(resume.vector_id)
            logger.info(f"Deleted vector {resume.vector_id} from vector store")
        
        # Delete from database
        success = await db_service.delete_resume(resume_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete resume from database"
            )
        
        logger.info(f"Successfully deleted resume {resume_id}")
        
        return {
            "message": "Resume deleted successfully",
            "resume_id": resume_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete resume {resume_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete resume"
        )
