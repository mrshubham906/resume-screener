import asyncio
import os
import logging
from datetime import datetime
from typing import List
from app.celery_app import celery_app
from app.services.database import db_service
from app.services.parser import ResumeParser
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.models.resume import ResumeStatus
from app.config import settings

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper function to run async code in Celery tasks"""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            # If the loop is closed, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # If there's no event loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error in async operation: {e}")
        raise


@celery_app.task(bind=True, name="process_resume")
def process_resume_task(self, resume_id: str, pdf_path: str, file_size: int):
    """Background task to process resume PDF"""
    try:
        logger.info(f"Starting resume processing for ID: {resume_id}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 4, "status": "Parsing PDF..."}
        )

        
        parser = ResumeParser()
        content, metadata = parser.parse_resume(pdf_path, file_size)
        logger.info(f"Parsed resume: {metadata}")
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 1, "total": 4, "status": "Generating embeddings..."}
        )
        
        experience_texts = [exp.description for exp in content.experience]
        embedding = embedding_service.create_resume_embeddings(
            resume_text=content.text,
            skills=content.skills,
            experience=experience_texts
        )
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 2, "total": 4, "status": "Storing in vector database..."}
        )
        
        vector_id = f"resume_{resume_id}"
        vector_metadata = {
            "resume_id": resume_id,
            "filename": os.path.basename(pdf_path),
            "skills": content.skills,
            "upload_date": datetime.now().isoformat()
        }
        
        vector_success = vector_store.add_vector(
            vector_id=vector_id,
            embedding=embedding,
            metadata=vector_metadata
        )
        
        if not vector_success:
            raise Exception("Failed to store vector in database")
        
        self.update_state(
            state="PROGRESS",
            meta={"current": 3, "total": 4, "status": "Updating database..."}
        )
        
        update_data = {
            "status": ResumeStatus.PROCESSED,
            "content": content.model_dump(),
            "metadata": metadata.model_dump(),
            "vector_id": vector_id
        }
        logger.info(f"Update data: {update_data}")
        
        db_success = run_async(db_service.update_resume(resume_id, update_data))
        
        if not db_success:
            raise Exception("Failed to update resume in database")
        
        # Clean up PDF file
        try:
            os.remove(pdf_path)
            logger.info(f"Cleaned up PDF file: {pdf_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up PDF file: {e}")
        
        logger.info(f"Successfully processed resume {resume_id}")
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "vector_id": vector_id,
            "skills_count": len(content.skills),
            "experience_count": len(content.experience)
        }
        
    except Exception as e:
        logger.error(f"Failed to process resume {resume_id}: {e}")
        
        # Update resume status to failed
        try:
            run_async(db_service.update_resume_status(
                resume_id, 
                ResumeStatus.FAILED,
                error_message=str(e)
            ))
        except Exception as update_error:
            logger.error(f"Failed to update resume status: {update_error}")
        
        # Clean up PDF file on failure
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up PDF file: {cleanup_error}")
        
        raise



@celery_app.task(name="cleanup_old_files")
def cleanup_old_files_task():
    """Background task to clean up old PDF files"""
    try:
        upload_dir = settings.upload_dir
        current_time = datetime.now()
        
        cleaned_count = 0
        for filename in os.listdir(upload_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(upload_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                # Remove files older than 24 hours
                if (current_time - file_time).total_seconds() > 86400:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old file: {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {filename}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old files")
        return {"status": "success", "cleaned_count": cleaned_count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup old files: {e}")
        raise 