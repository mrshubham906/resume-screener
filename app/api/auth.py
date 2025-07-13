from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from request header"""
    api_key = credentials.credentials
    
    if api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key


def get_api_key_header(api_key: str = Depends(verify_api_key)):
    """Dependency for API key validation"""
    return api_key 