"""
Test endpoints for debugging.
"""
from fastapi import APIRouter
import asyncio

router = APIRouter(prefix="/api/test", tags=["test"])

@router.get("/ping")
async def ping():
    """Simple ping endpoint to test connectivity."""
    return {"status": "ok", "message": "Backend is responding"}

@router.get("/slow")
async def slow_test():
    """Test endpoint that takes 5 seconds to respond."""
    await asyncio.sleep(5)
    return {"status": "ok", "message": "Slow request completed"}

@router.post("/echo")
async def echo(data: dict):
    """Echo back the received data."""
    return {"status": "ok", "received": data}

