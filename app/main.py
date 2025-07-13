import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis
import asyncio

from app.config import settings
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.api.routes import upload_router, search_router, resumes_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Resume Screener API...")
    
    try:
        # Connect to MongoDB
        await db_service.connect()
        logger.info("Connected to MongoDB")
        
        # Test OpenAI connection
        if embedding_service.test_connection():
            logger.info("Connected to OpenAI")
        else:
            logger.warning("OpenAI connection failed")
        
        # Test vector store connection
        if vector_store.test_connection():
            logger.info("Connected to vector store")
        else:
            logger.warning("Vector store connection failed")
        
        # Test Redis connection
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        logger.info("Resume Screener API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Screener API...")
    
    try:
        await db_service.disconnect()
        logger.info("Disconnected from MongoDB")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Resume Screener API",
    description="A powerful microservice for parsing resumes and finding the best matches using AI embeddings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)
app.include_router(search_router)
app.include_router(resumes_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Resume Screener API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "dependencies": {}
    }
    
    try:
        # Check MongoDB
        await db_service.client.admin.command('ping')
        health_status["dependencies"]["mongodb"] = "connected"
    except Exception as e:
        health_status["dependencies"]["mongodb"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    try:
        # Check Redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["dependencies"]["redis"] = "connected"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    try:
        # Check OpenAI
        if embedding_service.test_connection():
            health_status["dependencies"]["openai"] = "connected"
        else:
            health_status["dependencies"]["openai"] = "error: connection failed"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["dependencies"]["openai"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    try:
        # Check vector store
        if vector_store.test_connection():
            health_status["dependencies"]["vector_store"] = "connected"
        else:
            health_status["dependencies"]["vector_store"] = "error: connection failed"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["dependencies"]["vector_store"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 