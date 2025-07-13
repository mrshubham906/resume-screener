from celery import Celery
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "resume_screener",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.processing"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_always_eager=False,  # Set to True for testing
)

# Optional: Configure task routing
celery_app.conf.task_routes = {
    "app.tasks.processing.*": {"queue": "resume_processing"},
}


@celery_app.on_after_configure.connect
def setup_worker_connections(sender, **kwargs):
    """Setup worker connections when worker starts"""
    logger.info("Setting up worker connections...")
    
    # Import here to avoid circular imports
    from app.services.embedding import embedding_service
    from app.services.vector_store import vector_store
    
    try:
        # Test other services (database will connect when needed)
        if embedding_service.test_connection():
            logger.info("OpenAI connection verified in worker")
        else:
            logger.warning("OpenAI connection failed in worker")
        
        if vector_store.test_connection():
            logger.info("Vector store connection verified in worker")
        else:
            logger.warning("Vector store connection failed in worker")
            
        logger.info("Worker connections setup completed")
            
    except Exception as e:
        logger.error(f"Failed to setup worker connections: {e}")


if __name__ == "__main__":
    celery_app.start() 