from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResumeStatus(str, Enum):
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Experience(BaseModel):
    company: str
    position: str
    duration: str
    description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Education(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    gpa: Optional[float] = None


class ResumeContent(BaseModel):
    text: str
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []
    contact_info: Dict[str, str] = {}
    summary: Optional[str] = None


class ResumeMetadata(BaseModel):
    file_size: int
    pages: int
    processing_time: Optional[float] = None
    extracted_at: Optional[datetime] = None


class Resume(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    filename: str
    upload_date: datetime
    status: ResumeStatus = ResumeStatus.PROCESSING
    content: Optional[ResumeContent] = None
    metadata: Optional[ResumeMetadata] = None
    vector_id: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }


class ResumeCreate(BaseModel):
    filename: str
    file_size: int


class ResumeResponse(BaseModel):
    id: str
    filename: str
    status: ResumeStatus
    message: str
    upload_date: Optional[datetime] = None

    model_config = {}


class ResumeDetailResponse(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    status: ResumeStatus
    content: Optional[ResumeContent] = None
    metadata: Optional[ResumeMetadata] = None

    model_config = {} 