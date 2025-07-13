from .upload import router as upload_router
from .search import router as search_router
from .resumes import router as resumes_router

__all__ = ["upload_router", "search_router", "resumes_router"] 