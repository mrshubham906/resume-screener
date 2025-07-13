from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SearchRequest(BaseModel):
    job_description: str = Field(..., min_length=10, description="Job description to search for")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top matches to return")
    min_similarity: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")


class ResumeMatch(BaseModel):
    id: str
    filename: str
    similarity_score: float
    skills: List[str] = []
    experience_years: Optional[int] = None
    summary: Optional[str] = None
    upload_date: datetime

    model_config = {}


class SearchResponse(BaseModel):
    matches: List[ResumeMatch]
    total_matches: int
    search_time: float
    query: str 