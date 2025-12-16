"""
Social Media Publisher Agent
Handles actual posting to social media platforms.
"""
from typing import Any, Dict, List
try:
    from backend.agents.base import BaseAgent
    from backend.models.campaign import ContentCalendar, ContentCalendarEntry
    from backend.services.social_media_api import SocialMediaAPIClient
    from backend.services.media_storage import MediaStorageService
except ModuleNotFoundError:
    from agents.base import BaseAgent
    from models.campaign import ContentCalendar, ContentCalendarEntry
    from services.social_media_api import SocialMediaAPIClient
    from services.media_storage import MediaStorageService
from datetime import datetime

class SocialPublisherAgent(BaseAgent):
    """Agent that publishes approved content to social media platforms."""
    
    def __init__(self):
        super().__init__(
            name="SocialPublisherAgent",
            instructions="You are a Social Media Publisher. Post approved content to platforms."
        )
        self.api_client = SocialMediaAPIClient()
        self.storage_service = MediaStorageService()
    
    async def process(self, context: Any) -> Dict[str, Any]:
        """
        Publish approved content to social media platforms.
        
        Args:
            context: Dict with 'calendar' (ContentCalendar) and 'content' (DraftContentBundle)
            
        Returns:
            Dict with publishing results
        """
        calendar = context.get("calendar")
        content = context.get("content")
        
        if not calendar:
            raise ValueError("Calendar is required")
        
        published_posts = []
        failed_posts = []
        
        # Get approved entries ready for publishing
        # Note: In initial workflow, entries are in "pending_approval" status
        # So we'll just simulate publishing without actually posting
        approved_entries = [
            entry for entry in calendar.entries
            if entry.approval_status == "approved" and entry.status != "published"
        ]
        
        # If no approved entries, return success without publishing
        if not approved_entries:
            return {
                "published_count": 0,
                "failed_count": 0,
                "published_posts": [],
                "failed_posts": [],
                "calendar": calendar,
                "message": "No approved entries to publish. Content is ready for approval."
            }
        
        for entry in approved_entries:
            try:
                # Get caption
                caption = self._get_caption_for_entry(entry, content)
                
                # Get media path
                media_path = self._get_media_path_for_entry(entry, content)
                
                if not media_path:
                    failed_posts.append({
                        "entry": entry,
                        "error": "Media path not found"
                    })
                    continue
                
                # Post to platform
                platform = entry.channel.lower()
                result = await self._post_to_platform(
                    platform=platform,
                    media_path=media_path,
                    caption=caption,
                    entry=entry
                )
                
                # Update entry with publishing info
                entry.status = "published"
                entry.published_at = datetime.now().isoformat()
                entry.post_id = result.get("post_id")
                entry.post_url = result.get("url")
                
                published_posts.append({
                    "entry_id": id(entry),
                    "platform": platform,
                    "post_id": result.get("post_id"),
                    "post_url": result.get("url"),
                    "status": "published"
                })
                
            except Exception as e:
                failed_posts.append({
                    "entry": entry,
                    "error": str(e)
                })
                continue
        
        return {
            "published_count": len(published_posts),
            "failed_count": len(failed_posts),
            "published_posts": published_posts,
            "failed_posts": failed_posts,
            "calendar": calendar  # Return updated calendar
        }
    
    def _get_caption_for_entry(self, entry: ContentCalendarEntry, content: Any) -> str:
        """Extract caption for calendar entry."""
        if not content:
            return ""
        
        # Find matching caption set
        for caption_set in content.captions:
            if caption_set.channel.lower() == entry.channel.lower():
                # Use caption_ref to get specific caption
                try:
                    idx = int(entry.caption_ref)
                    if 0 <= idx < len(caption_set.captions):
                        return caption_set.captions[idx]
                except (ValueError, IndexError):
                    # Fallback to first caption
                    if caption_set.captions:
                        return caption_set.captions[0]
        return ""
    
    def _get_media_path_for_entry(self, entry: ContentCalendarEntry, content: Any) -> str:
        """Get media file path for calendar entry."""
        if not content:
            return ""
        
        # Check for image
        if entry.image_brief_ref and content.image_briefs:
            try:
                idx = int(entry.image_brief_ref)
                if 0 <= idx < len(content.image_briefs):
                    image_brief = content.image_briefs[idx]
                    if image_brief.generated_image_path:
                        return image_brief.generated_image_path
            except (ValueError, IndexError):
                pass
        
        # Check for video
        if entry.video_script_ref and content.video_scripts:
            try:
                idx = int(entry.video_script_ref)
                if 0 <= idx < len(content.video_scripts):
                    video_script = content.video_scripts[idx]
                    if video_script.generated_video_path:
                        return video_script.generated_video_path
            except (ValueError, IndexError):
                pass
        
        return ""
    
    async def _post_to_platform(
        self,
        platform: str,
        media_path: str,
        caption: str,
        entry: ContentCalendarEntry
    ) -> Dict[str, Any]:
        """Post to specific platform."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if API tokens are configured
        if not self.api_client.instagram_token and not self.api_client.facebook_token:
            logger.warning("No social media API tokens configured. Simulating publish.")
            return {
                "platform": platform.lower(),
                "post_id": f"simulated_{entry.date}_{entry.time}",
                "status": "simulated",
                "url": None,
                "message": "API tokens not configured. This is a simulation."
            }
        
        platform_map = {
            "instagram": self.api_client.post_to_instagram,
            "facebook": self.api_client.post_to_facebook
        }
        
        post_func = platform_map.get(platform.lower())
        if not post_func:
            raise ValueError(f"Platform {platform} not supported")
        
        try:
            return await post_func(media_path, caption)
        except Exception as e:
            logger.error(f"Failed to post to {platform}: {str(e)}")
            # Return simulated result instead of crashing
            return {
                "platform": platform.lower(),
                "post_id": f"failed_{entry.date}_{entry.time}",
                "status": "failed",
                "url": None,
                "error": str(e)
            }

