import openai
import logging
import re
from typing import List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """OpenAI Embedding Service for generating vector embeddings"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.chunk_size = settings.openai_chunk_size
        self.chunk_overlap = settings.openai_chunk_overlap

    def create_chunks(self, text: str) -> List[str]:
        """Split text into chunks for embedding"""
        try:
            if not text:
                return []
            
            # Simple text splitting by paragraphs and sentences
            chunks = []
            paragraphs = text.split('\n\n')
            
            for paragraph in paragraphs:
                if len(paragraph.strip()) < self.chunk_size:
                    if paragraph.strip():
                        chunks.append(paragraph.strip())
                else:
                    # Split long paragraphs by sentences
                    sentences = re.split(r'[.!?]+', paragraph)
                    current_chunk = ""
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                            
                        if len(current_chunk) + len(sentence) < self.chunk_size:
                            current_chunk += sentence + ". "
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence + ". "
                    
                    if current_chunk:
                        chunks.append(current_chunk.strip())
            
            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
        except Exception as e:
            logger.error(f"Failed to create chunks: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=settings.openai_model,
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text of length {len(text)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts in batch"""
        try:
            if not texts:
                return []
            
            response = self.client.embeddings.create(
                model=settings.openai_model,
                input=texts
            )
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to get batch embeddings: {e}")
            raise

    def create_resume_embeddings(self, resume_text: str, skills: List[str], experience: List[str]) -> List[float]:
        """Create embeddings for resume content"""
        try:
            # Create meaningful chunks from resume
            chunks = []
            
            # Add full text chunk
            chunks.append(resume_text[:1000])  # First 1000 characters
            
            # Add skills chunk
            if skills:
                skills_text = "Skills: " + ", ".join(skills)
                chunks.append(skills_text)
            
            # Add experience chunks
            for exp in experience[:3]:  # Top 3 experiences
                chunks.append(exp[:500])  # First 500 characters of each experience
            
            # Get embeddings for all chunks
            embeddings = self.get_embeddings_batch(chunks)
            
            # Average the embeddings to get a single vector
            if embeddings:
                avg_embedding = [sum(emb[i] for emb in embeddings) / len(embeddings) 
                               for i in range(len(embeddings[0]))]
                logger.info(f"Created resume embedding with {len(avg_embedding)} dimensions")
                return avg_embedding
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to create resume embeddings: {e}")
            raise

    def create_job_embedding(self, job_description: str) -> List[float]:
        """Create embedding for job description"""
        try:
            # Clean and prepare job description
            cleaned_jd = job_description.strip()
            if len(cleaned_jd) > 2000:
                cleaned_jd = cleaned_jd[:2000]  # Limit to 2000 characters
            
            embedding = self.get_embedding(cleaned_jd)
            logger.info(f"Created job description embedding")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create job embedding: {e}")
            raise


    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            # Try to get embedding for a simple text
            test_embedding = self.get_embedding("test")
            return len(test_embedding) > 0
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False


# Global embedding service instance
embedding_service = EmbeddingService() 