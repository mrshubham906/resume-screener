from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from bson import ObjectId
from app.config import settings
from app.models.resume import Resume, ResumeStatus

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection_name = "resumes"
        self._connected = False

    async def connect(self):
        """Connect to MongoDB"""
        try:
            if self._connected and self.client is not None and self.database is not None:
                logger.info("Database already connected")
                return
            
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            self.database = self.client[settings.mongodb_database]
            
            # Test connection
            await self.client.admin.command('ping')
            self._connected = True
            logger.info("Connected to MongoDB")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            self._connected = False
            self.client = None
            self.database = None
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None
            self._connected = False
            logger.info("Disconnected from MongoDB")

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected and self.client is not None and self.database is not None

    async def _ensure_connection(self):
        """Ensure database is connected"""
        if not self._connected or self.client is None or self.database is None:
            await self.connect()

    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            collection = self.database[self.collection_name]
            
            # Create indexes
            await collection.create_index("filename")
            await collection.create_index("status")
            await collection.create_index("upload_date")
            await collection.create_index("vector_id")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def create_resume(self, resume_data: Dict[str, Any]) -> str:
        """Create a new resume document"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            result = await collection.insert_one(resume_data)
            logger.info(f"Created resume with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create resume: {e}")
            raise

    async def get_resume(self, resume_id: str) -> Optional[Resume]:
        """Get a resume by ID"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            
            # Convert string ID to ObjectId
            try:
                object_id = ObjectId(resume_id)
            except Exception:
                logger.error(f"Invalid ObjectId format: {resume_id}")
                return None
            
            document = await collection.find_one({"_id": object_id})
            
            if document:
                # Convert MongoDB ObjectId to string
                document["_id"] = str(document["_id"])
                return Resume(**document)
            return None
        except Exception as e:
            logger.error(f"Failed to get resume {resume_id}: {e}")
            raise

    async def update_resume(self, resume_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a resume document"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            
            # Convert string ID to ObjectId
            try:
                object_id = ObjectId(resume_id)
            except Exception:
                logger.error(f"Invalid ObjectId format: {resume_id}")
                return False
            
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated resume {resume_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update resume {resume_id}: {e}")
            raise

    async def update_resume_status(self, resume_id: str, status: ResumeStatus, **kwargs) -> bool:
        """Update resume status and optional fields"""
        update_data = {"status": status}
        update_data.update(kwargs)
        return await self.update_resume(resume_id, update_data)

    async def get_resumes_by_status(self, status: ResumeStatus, limit: int = 100) -> List[Resume]:
        """Get resumes by status"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            cursor = collection.find({"status": status}).limit(limit)
            
            resumes = []
            async for document in cursor:
                document["_id"] = str(document["_id"])
                resumes.append(Resume(**document))
            
            return resumes
        except Exception as e:
            logger.error(f"Failed to get resumes by status {status}: {e}")
            raise

    async def get_all_resumes(self, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get all resumes with pagination"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            cursor = collection.find().skip(skip).limit(limit).sort("upload_date", -1)
            
            resumes = []
            async for document in cursor:
                document["_id"] = str(document["_id"])
                resumes.append(Resume(**document))
            
            return resumes
        except Exception as e:
            logger.error(f"Failed to get resumes: {e}")
            raise

    async def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume document"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            
            # Convert string ID to ObjectId
            try:
                object_id = ObjectId(resume_id)
            except Exception:
                logger.error(f"Invalid ObjectId format: {resume_id}")
                return False
            
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted resume {resume_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            raise

    async def get_resume_count(self) -> int:
        """Get total number of resumes"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            return await collection.count_documents({})
        except Exception as e:
            logger.error(f"Failed to get resume count: {e}")
            raise

    async def search_resumes_by_text(self, search_text: str, limit: int = 10) -> List[Resume]:
        """Search resumes by text content"""
        try:
            await self._ensure_connection()
            collection = self.database[self.collection_name]
            
            # Create text search query
            query = {
                "$text": {"$search": search_text}
            }
            
            cursor = collection.find(query).limit(limit).sort("upload_date", -1)
            
            resumes = []
            async for document in cursor:
                document["_id"] = str(document["_id"])
                resumes.append(Resume(**document))
            
            return resumes
        except Exception as e:
            logger.error(f"Failed to search resumes: {e}")
            raise


# Global database service instance
db_service = DatabaseService() 