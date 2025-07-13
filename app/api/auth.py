from fastapi import HTTPException, Depends, Header
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key from request header"""
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
    
    return x_api_key


def get_api_key_header(api_key: str = Depends(verify_api_key)):
    """Dependency for API key validation"""
    return api_key 