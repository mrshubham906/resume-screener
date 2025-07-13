from pinecone import Pinecone
import logging
from typing import List, Tuple, Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Vector Store Service supporting Pinecone"""
    
    def __init__(self):
        self.pinecone_index = None
        self.pinecone_client = None
        
        if settings.pinecone_api_key:
            self._init_pinecone()

    def _init_pinecone(self):
        """Initialize Pinecone vector database"""
        try:
            # Initialize Pinecone client with new API
            self.pinecone_client = Pinecone(
                api_key=settings.pinecone_api_key
            )
            
            # Check if index exists, create if not
            if settings.pinecone_index_name not in self.pinecone_client.list_indexes().names():
                self.pinecone_client.create_index(
                    name=settings.pinecone_index_name,
                    dimension=settings.pinecone_dimension,
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index: {settings.pinecone_index_name}")
            
            self.pinecone_index = self.pinecone_client.Index(settings.pinecone_index_name)
            logger.info("Pinecone initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise


    def add_vector(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Add a vector to the store"""
        try:
            if metadata is None:
                metadata = {}
            
            self.pinecone_index.upsert(
                vectors=[(vector_id, embedding, metadata)]
            )
            logger.info(f"Added vector {vector_id} to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to Pinecone: {e}")
            return False


       

    def search_similar(self, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors"""
        try:
            results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            matches = []
            for match in results.matches:
                if match.score >= min_similarity:
                    matches.append((
                        match.id,
                        match.score,
                        match.metadata or {}
                    ))
            
            logger.info(f"Found {len(matches)} matches in Pinecone")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            return []

        


    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the store"""
        try:
            self.pinecone_index.delete(ids=[vector_id])
            logger.info(f"Deleted vector {vector_id} from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Pinecone: {e}")
            return False




    def get_vector_count(self) -> int:
        """Get total number of vectors in the store"""
        try:
            stats = self.pinecone_index.describe_index_stats()
            return stats.total_vector_count
        except Exception as e:
            logger.error(f"Failed to get vector count: {e}")
            return 0

    def test_connection(self) -> bool:
        """Test connection to vector store"""
        try:
            return self.pinecone_index is not None
        except Exception as e:
            logger.error(f"Vector store connection test failed: {e}")
            return False


# Global vector store service instance
vector_store = VectorStoreService() 