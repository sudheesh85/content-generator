"""
Content Management API Endpoints
Handles content editing, regeneration, approval, and publishing.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/content", tags=["content"])

# In-memory storage for campaigns (in production, use database)
campaign_storage: Dict[str, Any] = {}

class EditCaptionRequest(BaseModel):
    campaign_id: str
    entry_id: str
    new_caption: str

class RegenerateAssetRequest(BaseModel):
    campaign_id: str
    asset_type: str  # "image" or "video"
    asset_id: str
    keep_caption: bool = True

class ApproveEntryRequest(BaseModel):
    campaign_id: str
    entry_id: str
    approved_by: str

class RejectEntryRequest(BaseModel):
    campaign_id: str
    entry_id: str
    reason: str

class PublishEntryRequest(BaseModel):
    campaign_id: str
    entry_id: str

@router.post("/edit-caption")
async def edit_caption(request: EditCaptionRequest):
    """Edit a caption for a calendar entry."""
    if request.campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[request.campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    # Find and update entry
    for entry in calendar.entries:
        if str(id(entry)) == request.entry_id:
            # Update caption in content bundle
            content = campaign.get("content")
            if content:
                for caption_set in content.captions:
                    if caption_set.channel.lower() == entry.channel.lower():
                        try:
                            idx = int(entry.caption_ref)
                            if 0 <= idx < len(caption_set.captions):
                                caption_set.captions[idx] = request.new_caption
                                return {"status": "success", "message": "Caption updated"}
                        except (ValueError, IndexError):
                            pass
            
            raise HTTPException(status_code=404, detail="Caption not found")
    
    raise HTTPException(status_code=404, detail="Entry not found")

@router.post("/regenerate-asset")
async def regenerate_asset(request: RegenerateAssetRequest):
    """Regenerate a specific asset (image or video) while keeping caption if requested."""
    if request.campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[request.campaign_id]
    content = campaign.get("content")
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    try:
        from backend.services.media_generation import MediaGenerationService
        from backend.services.media_storage import MediaStorageService
        
        media_service = MediaGenerationService()
        storage_service = MediaStorageService()
        
        if request.asset_type == "image":
            # Find image brief
            for image_brief in content.image_briefs:
                if image_brief.media_id == request.asset_id:
                    # Regenerate image
                    result = await media_service.generate_image_from_brief(
                        image_brief.model_dump()
                    )
                    
                    # Update image brief
                    image_brief.generated_image_path = result["local_path"]
                    image_brief.generated_image_url = result.get("url")
                    
                    return {
                        "status": "success",
                        "message": "Image regenerated",
                        "image_path": result["local_path"],
                        "image_url": result.get("url")
                    }
        
        elif request.asset_type == "video":
            # Find video script
            for video_script in content.video_scripts:
                if video_script.media_id == request.asset_id:
                    # Regenerate video
                    result = await media_service.generate_video(
                        script=video_script.script_content,
                        scene_instructions=video_script.scene_instructions
                    )
                    
                    # Update video script
                    video_script.generated_video_path = result["local_path"]
                    
                    return {
                        "status": "success",
                        "message": "Video regenerated",
                        "video_path": result["local_path"]
                    }
        
        raise HTTPException(status_code=404, detail="Asset not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve-entry")
async def approve_entry(request: ApproveEntryRequest):
    """Approve a calendar entry for publishing."""
    if request.campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[request.campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    try:
        from backend.agents.approval_agent import ApprovalAgent
        
        approval_agent = ApprovalAgent()
        entry = await approval_agent.approve_entry(
            entry_id=request.entry_id,
            approved_by=request.approved_by,
            calendar=calendar
        )
        
        return {
            "status": "success",
            "message": "Entry approved",
            "entry": {
                "id": str(id(entry)),
                "status": entry.status,
                "approval_status": entry.approval_status
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reject-entry")
async def reject_entry(request: RejectEntryRequest):
    """Reject a calendar entry."""
    if request.campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[request.campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    try:
        from backend.agents.approval_agent import ApprovalAgent
        
        approval_agent = ApprovalAgent()
        entry = await approval_agent.reject_entry(
            entry_id=request.entry_id,
            reason=request.reason,
            calendar=calendar
        )
        
        return {
            "status": "success",
            "message": "Entry rejected",
            "entry": {
                "id": str(id(entry)),
                "status": entry.status,
                "approval_status": entry.approval_status
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish-entry")
async def publish_entry(request: PublishEntryRequest):
    """Publish a single approved entry to social media."""
    if request.campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[request.campaign_id]
    calendar = campaign.get("calendar")
    content = campaign.get("content")
    
    if not calendar or not content:
        raise HTTPException(status_code=404, detail="Calendar or content not found")
    
    try:
        from backend.agents.social_publisher_agent import SocialPublisherAgent
        
        # Find the entry
        entry = None
        for e in calendar.entries:
            if str(id(e)) == request.entry_id:
                entry = e
                break
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        if entry.approval_status != "approved":
            raise HTTPException(status_code=400, detail="Entry must be approved before publishing")
        
        publisher_agent = SocialPublisherAgent()
        publish_context = {
            "calendar": calendar,
            "content": content
        }
        
        # Publish just this entry
        result = await publisher_agent.process(publish_context)
        
        return {
            "status": "success",
            "message": "Entry published",
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/approval-queue/{campaign_id}")
async def get_approval_queue(campaign_id: str):
    """Get all entries pending approval for a campaign."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    pending_entries = [
        {
            "id": str(id(entry)),
            "date": entry.date,
            "time": entry.time,
            "channel": entry.channel,
            "post_type": entry.post_type,
            "status": entry.status,
            "approval_status": entry.approval_status
        }
        for entry in calendar.entries
        if entry.approval_status == "pending"
    ]
    
    return {
        "campaign_id": campaign_id,
        "pending_count": len(pending_entries),
        "entries": pending_entries
    }

@router.post("/upload-asset")
async def upload_asset(
    campaign_id: str = Form(...),
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """Upload a brand asset (logo, product shot, etc.) to the media library."""
    try:
        from backend.services.media_storage import MediaStorageService
        
        storage_service = MediaStorageService()
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Add to media library
        metadata = await storage_service.save_user_asset(
            file_path=temp_path,
            asset_type=asset_type,
            description=description,
            tags=["user_upload", asset_type]
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "status": "success",
            "message": "Asset uploaded",
            "asset": metadata
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media-library/{campaign_id}")
async def get_media_library(campaign_id: str):
    """Get all media associated with a campaign."""
    try:
        from backend.services.media_storage import MediaStorageService
        
        storage_service = MediaStorageService()
        media = await storage_service.get_media_by_campaign(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "media": media
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

