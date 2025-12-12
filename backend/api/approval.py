"""
Approval API Endpoints
Human-in-the-loop approval system for generated content.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import logging
import os

router = APIRouter(prefix="/api/approval", tags=["approval"])
logger = logging.getLogger(__name__)

# Import campaign storage
try:
    from backend.api.content_management import campaign_storage
except ModuleNotFoundError:
    from api.content_management import campaign_storage

class ApprovalAction(BaseModel):
    entry_index: int
    action: str  # "approve" or "reject"
    notes: Optional[str] = None

class BulkApprovalAction(BaseModel):
    entry_indices: List[int]
    action: str  # "approve" or "reject"
    notes: Optional[str] = None

class PublishRequest(BaseModel):
    entry_indices: List[int]  # Which entries to publish
    platforms: Optional[List[str]] = None  # ["instagram", "facebook"]

@router.get("/{campaign_id}/queue")
async def get_approval_queue(campaign_id: str):
    """Get the approval queue for a campaign."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="No calendar found for this campaign")
    
    # Build approval queue
    queue = []
    content = campaign.get("content")
    
    for idx, entry in enumerate(calendar.entries):
        # Resolve actual caption from caption_ref
        caption_text = ""
        if content and hasattr(content, 'captions'):
            try:
                caption_ref_idx = int(entry.caption_ref) if entry.caption_ref else 0
                # Find matching caption set for this channel
                for caption_set in content.captions:
                    if caption_set.channel.lower() == entry.channel.lower():
                        if caption_ref_idx < len(caption_set.captions):
                            caption_text = caption_set.captions[caption_ref_idx]
                        break
            except (ValueError, IndexError, AttributeError):
                caption_text = f"Caption {entry.caption_ref}"
        
        # Get image info if available
        image_info = None
        if content and hasattr(content, 'image_briefs'):
            try:
                image_ref_idx = int(entry.image_brief_ref) if entry.image_brief_ref else idx
                if image_ref_idx < len(content.image_briefs):
                    image_brief = content.image_briefs[image_ref_idx]
                    image_info = {
                        "layout": image_brief.layout_description,
                        "text_overlay": image_brief.text_overlay,
                        "style": image_brief.style_suggestions,
                        "generated_path": getattr(image_brief, 'generated_image_path', None),
                        "generated_url": getattr(image_brief, 'generated_image_url', None),
                        "media_id": getattr(image_brief, 'media_id', None)
                    }
            except (ValueError, IndexError, AttributeError):
                pass
        
        queue.append({
            "entry_index": idx,
            "channel": entry.channel,
            "caption": caption_text,
            "media_type": entry.post_type,
            "date": entry.date,
            "time": entry.time,
            "approval_status": entry.approval_status or "pending",
            "status": entry.status,
            "image_info": image_info,
            "post_type": entry.post_type
        })
    
    return {
        "campaign_id": campaign_id,
        "queue": queue,
        "pending_count": len([e for e in calendar.entries if e.approval_status == "pending"]),
        "approved_count": len([e for e in calendar.entries if e.approval_status == "approved"]),
        "rejected_count": len([e for e in calendar.entries if e.approval_status == "rejected"])
    }

@router.post("/{campaign_id}/approve")
async def approve_entry(campaign_id: str, action: ApprovalAction):
    """Approve or reject a specific entry."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar or action.entry_index >= len(calendar.entries):
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry = calendar.entries[action.entry_index]
    
    if action.action == "approve":
        entry.approval_status = "approved"
        entry.status = "approved"
        logger.info(f"Entry {action.entry_index} approved for campaign {campaign_id}")
    elif action.action == "reject":
        entry.approval_status = "rejected"
        entry.status = "rejected"
        logger.info(f"Entry {action.entry_index} rejected for campaign {campaign_id}")
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
    
    if action.notes:
        entry.approval_notes = action.notes
    
    # Update campaign storage
    campaign_storage[campaign_id]["calendar"] = calendar
    
    return {
        "status": "success",
        "entry_index": action.entry_index,
        "new_status": entry.approval_status,
        "message": f"Entry {action.entry_index} {action.action}d successfully"
    }

@router.post("/{campaign_id}/approve-all")
async def approve_all(campaign_id: str, action: BulkApprovalAction):
    """Approve or reject multiple entries at once."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    calendar = campaign.get("calendar")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="No calendar found")
    
    updated_count = 0
    for idx in action.entry_indices:
        if idx < len(calendar.entries):
            entry = calendar.entries[idx]
            if action.action == "approve":
                entry.approval_status = "approved"
                entry.status = "approved"
            elif action.action == "reject":
                entry.approval_status = "rejected"
                entry.status = "rejected"
            
            if action.notes:
                entry.approval_notes = action.notes
            
            updated_count += 1
    
    # Update campaign storage
    campaign_storage[campaign_id]["calendar"] = calendar
    
    logger.info(f"Bulk {action.action} completed for {updated_count} entries in campaign {campaign_id}")
    
    return {
        "status": "success",
        "updated_count": updated_count,
        "message": f"{updated_count} entries {action.action}d successfully"
    }

@router.post("/{campaign_id}/publish")
async def publish_entries(campaign_id: str, publish_req: PublishRequest):
    """Publish approved entries to social media."""
    if campaign_id not in campaign_storage:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_storage[campaign_id]
    calendar = campaign.get("calendar")
    content = campaign.get("content")
    
    if not calendar:
        raise HTTPException(status_code=404, detail="No calendar found")
    
    # Import social media client
    try:
        from backend.services.social_media_api import SocialMediaAPIClient
    except ModuleNotFoundError:
        from services.social_media_api import SocialMediaAPIClient
    
    client = SocialMediaAPIClient()
    
    published = []
    failed = []
    
    for idx in publish_req.entry_indices:
        if idx >= len(calendar.entries):
            continue
        
        entry = calendar.entries[idx]
        
        # Check if approved
        if entry.approval_status != "approved":
            failed.append({
                "entry_index": idx,
                "error": "Entry not approved"
            })
            continue
        
        # Get media path by resolving image_brief_ref
        media_path = None
        if content and hasattr(content, 'image_briefs'):
            try:
                image_ref_idx = int(entry.image_brief_ref) if entry.image_brief_ref else idx
                if image_ref_idx < len(content.image_briefs):
                    image_brief = content.image_briefs[image_ref_idx]
                    media_path = getattr(image_brief, 'generated_image_path', None)
            except (ValueError, IndexError, AttributeError):
                pass
        
        if not media_path:
            failed.append({
                "entry_index": idx,
                "error": "No media found"
            })
            continue
        
        # Resolve caption text
        caption_text = ""
        if content and hasattr(content, 'captions'):
            try:
                caption_ref_idx = int(entry.caption_ref) if entry.caption_ref else 0
                for caption_set in content.captions:
                    if caption_set.channel.lower() == entry.channel.lower():
                        if caption_ref_idx < len(caption_set.captions):
                            caption_text = caption_set.captions[caption_ref_idx]
                        break
            except (ValueError, IndexError, AttributeError):
                caption_text = f"Post for {entry.channel}"
        
        # Post to platform
        try:
            platform = entry.channel.lower()
            result = None
            
            if platform == "instagram" and (not publish_req.platforms or "instagram" in publish_req.platforms):
                result = await client.post_to_instagram(media_path, caption_text)
            elif platform == "facebook" and (not publish_req.platforms or "facebook" in publish_req.platforms):
                result = await client.post_to_facebook(media_path, caption_text)
            else:
                failed.append({
                    "entry_index": idx,
                    "error": f"Platform {platform} not supported or not requested"
                })
                continue
            
            # Update entry
            entry.status = "published" if result.get("status") != "simulated" else "simulated"
            entry.published_at = result.get("published_at") if result else None
            entry.published_post_id = result.get("post_id") if result else None
            entry.published_url = result.get("url") if result else None
            
            published.append({
                "entry_index": idx,
                "platform": platform,
                "post_id": result.get("post_id") if result else None,
                "url": result.get("url") if result else None,
                "status": result.get("status", "published"),
                "message": result.get("message") if result.get("status") == "simulated" else None
            })
            
            logger.info(f"{'Simulated' if result.get('status') == 'simulated' else 'Published'} entry {idx} to {platform} for campaign {campaign_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish entry {idx}: {str(e)}", exc_info=True)
            failed.append({
                "entry_index": idx,
                "error": str(e)
            })
    
    # Update campaign storage
    campaign_storage[campaign_id]["calendar"] = calendar
    
    return {
        "status": "success" if published else "failed",
        "published_count": len(published),
        "failed_count": len(failed),
        "published": published,
        "failed": failed,
        "message": f"Published {len(published)} entries, {len(failed)} failed"
    }

