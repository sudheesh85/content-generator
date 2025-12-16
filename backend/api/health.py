"""
Health check endpoint to verify backend is running.
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "content-generator-api"
    }

