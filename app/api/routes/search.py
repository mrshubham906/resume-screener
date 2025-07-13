import time
from typing import List
from fastapi import APIRouter, HTTPException, Depends
import logging

from app.api.auth import get_api_key_header
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.database import db_service
from app.models.search import SearchRequest, SearchResponse, ResumeMatch
from app.models.resume import ResumeStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
async def search_resumes(
    search_request: SearchRequest,
    api_key: str = Depends(get_api_key_header)
):
    """Search for resumes matching a job description"""
    
    start_time = time.time()
    
    try:
        # Generate embedding for job description
        job_embedding = embedding_service.create_job_embedding(search_request.job_description)
        
        # Search for similar vectors
        vector_matches = vector_store.search_similar(
            query_embedding=job_embedding,
            top_k=search_request.top_k,
            min_similarity=search_request.min_similarity
        )
        
        # Get resume details for matches
        resume_matches = []
        for vector_id, similarity_score, metadata in vector_matches:
            resume_id = metadata.get("resume_id")
            if resume_id:
                resume = await db_service.get_resume(resume_id)
                if resume and resume.status == ResumeStatus.PROCESSED:
                    # Calculate experience years
                    experience_years = len(resume.content.experience) if resume.content else 0
                    
                    resume_matches.append(ResumeMatch(
                        id=resume_id,
                        filename=resume.filename,
                        similarity_score=similarity_score,
                        skills=resume.content.skills if resume.content else [],
                        experience_years=experience_years,
                        summary=resume.content.summary if resume.content else None,
                        upload_date=resume.upload_date
                    ))
        
        # Sort by similarity score (highest first)
        resume_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        search_time = time.time() - start_time
        
        logger.info(f"Search completed in {search_time:.2f}s, found {len(resume_matches)} matches")
        
        return SearchResponse(
            matches=resume_matches,
            total_matches=len(resume_matches),
            search_time=search_time,
            query=search_request.job_description
        )
        
    except Exception as e:
        logger.error(f"Failed to search resumes: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search resumes"
        )
