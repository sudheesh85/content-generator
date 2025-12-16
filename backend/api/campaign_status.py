"""
Campaign Status API Endpoints
Provides endpoints to check campaign status and retrieve campaign data.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/campaign", tags=["campaign"])

# Import campaign storage from content_management
try:
    from backend.api.content_management import campaign_storage
except ModuleNotFoundError:
    from api.content_management import campaign_storage

@router.get("/{campaign_id}/status")
async def get_campaign_status(campaign_id: str):
    """Get the current status of a campaign."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    status = campaign.get("status", "completed")
    progress = campaign.get("progress", "")
    calendar = campaign.get("calendar")
    
    # Count entries by status
    approval_pending = 0
    approved = 0
    published = 0
    total_entries = 0
    
    if calendar and hasattr(calendar, 'entries'):
        total_entries = len(calendar.entries)
        for entry in calendar.entries:
            if entry.approval_status == "pending":
                approval_pending += 1
            elif entry.approval_status == "approved":
                approved += 1
            if entry.status == "published":
                published += 1
    
    return {
        "campaign_id": campaign_id,
        "status": status,
        "progress": progress,
        "started_at": campaign.get("started_at"),
        "completed_at": campaign.get("completed_at"),
        "error": campaign.get("error") if status == "failed" else None,
        "has_strategy": bool(campaign.get("strategy")),
        "has_research": bool(campaign.get("research")),
        "has_brand_voice": bool(campaign.get("brand_voice")),
        "has_content": bool(campaign.get("content")),
        "has_calendar": bool(campaign.get("calendar")),
        "approval_pending": approval_pending,
        "approved": approved,
        "published": published,
        "total_entries": total_entries
    }

@router.get("/{campaign_id}/data")
async def get_campaign_data(campaign_id: str):
    """Get full campaign data."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    
    # Check status
    if campaign.get("status") == "running":
        raise HTTPException(status_code=202, detail="Campaign still running. Check status endpoint.")
    
    if campaign.get("status") == "failed":
        raise HTTPException(status_code=500, detail=campaign.get("error", "Campaign failed"))
    
    # Serialize the data
    try:
        strategy_dict = campaign["strategy"].model_dump() if hasattr(campaign.get("strategy"), 'model_dump') else campaign.get("strategy")
        research_dict = campaign["research"].model_dump() if hasattr(campaign.get("research"), 'model_dump') else campaign.get("research")
        brand_voice_dict = campaign["brand_voice"].model_dump() if hasattr(campaign.get("brand_voice"), 'model_dump') else campaign.get("brand_voice")
        
        content = campaign.get("content")
        content_dict = {
            "captions": [c.model_dump() if hasattr(c, 'model_dump') else c for c in content.captions] if content else [],
            "image_briefs": [i.model_dump() if hasattr(i, 'model_dump') else i for i in content.image_briefs] if content else [],
            "video_scripts": [v.model_dump() if hasattr(v, 'model_dump') else v for v in content.video_scripts] if content else [],
        }
        
        calendar_dict = campaign["calendar"].model_dump() if hasattr(campaign.get("calendar"), 'model_dump') else campaign.get("calendar")
        
        return {
            "status": "success",
            "data": {
                "campaign_id": campaign_id,
                "strategy": strategy_dict,
                "research": research_dict,
                "brand_voice": brand_voice_dict,
                "content": content_dict,
                "calendar": calendar_dict,
                "publish_result": campaign.get("publish_result")
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error serializing campaign {campaign_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error serializing campaign data: {str(e)}")

@router.get("/{campaign_id}/media")
async def get_campaign_media(campaign_id: str):
    """Get media library for a campaign."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    media_library = campaign.get("media_library", {})
    
    return {
        "campaign_id": campaign_id,
        "media": media_library
    }

@router.get("/list")
async def list_campaigns():
    """List all campaigns."""
    campaigns = []
    for campaign_id, campaign in campaign_storage.items():
        campaigns.append({
            "campaign_id": campaign_id,
            "status": campaign.get("status", "completed"),
            "created_at": campaign.get("started_at"),
            "completed_at": campaign.get("completed_at")
        })
    
    return {"campaigns": campaigns}
