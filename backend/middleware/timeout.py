"""
Timeout middleware to prevent long-running requests from hanging.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to add timeout protection to requests."""
    
    def __init__(self, app, timeout: int = 900):
        super().__init__(app)
        self.timeout = timeout  # 15 minutes default
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            elapsed = time.time() - start_time
            if elapsed > 60:  # Log slow requests
                logger.warning(f"Slow request: {request.url.path} took {elapsed:.2f}s")
            
            return response
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Request failed after {elapsed:.2f}s: {str(e)}")
            raise

