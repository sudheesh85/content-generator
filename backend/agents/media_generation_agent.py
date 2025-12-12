"""
Media Generation Agent
Generates actual images and videos from briefs.
"""
from typing import Any, List, Dict
try:
    from backend.agents.base import BaseAgent
    from backend.models.campaign import ImageBrief, VideoScript
    from backend.services.media_generation import MediaGenerationService
    from backend.services.media_storage import MediaStorageService
except ModuleNotFoundError:
    from agents.base import BaseAgent
    from models.campaign import ImageBrief, VideoScript
    from services.media_generation import MediaGenerationService
    from services.media_storage import MediaStorageService

class MediaGenerationAgent(BaseAgent):
    """Agent that generates actual media files from briefs."""
    
    def __init__(self):
        super().__init__(
            name="MediaGenerationAgent",
            instructions="You are a Media Production Specialist. Generate high-quality images and videos."
        )
        self.media_service = MediaGenerationService()
        self.storage_service = MediaStorageService()
    
    async def process(self, context: Any) -> Dict[str, Any]:
        """
        Generate media files from content bundle.
        
        Args:
            context: Dict with 'content' (DraftContentBundle) and 'campaign_id'
            
        Returns:
            Dict with generated_images and generated_videos
        """
        content = context.get("content")
        campaign_id = context.get("campaign_id", "default")
        
        if not content:
            raise ValueError("Content bundle is required")
        
        generated_images = []
        generated_videos = []
        
        # Generate images from image briefs (with timeout protection)
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        for image_brief in content.image_briefs:
            try:
                # Add timeout for image generation (60 seconds per image)
                image_result = await asyncio.wait_for(
                    self.media_service.generate_image_from_brief(image_brief.model_dump()),
                    timeout=60.0
                )
                
                # Save metadata
                metadata = await self.storage_service.save_image_metadata(
                    image_path=image_result["local_path"],
                    prompt=image_result["prompt"],
                    campaign_id=campaign_id,
                    tags=["generated", "ai"]
                )
                
                # Update image brief with generated media info
                image_brief.generated_image_path = image_result["local_path"]
                image_brief.generated_image_url = image_result.get("url")
                image_brief.media_id = metadata["id"]
                
                generated_images.append({
                    "brief_id": id(image_brief),
                    "image_path": image_result["local_path"],
                    "image_url": image_result.get("url"),
                    "media_id": metadata["id"]
                })
            except asyncio.TimeoutError:
                logger.warning(f"Image generation timed out for brief {id(image_brief)}. Skipping...")
                # Mark as failed but continue
                image_brief.generated_image_path = None
                continue
            except Exception as e:
                logger.error(f"Error generating image for brief {id(image_brief)}: {str(e)}", exc_info=True)
                # Mark as failed but continue
                image_brief.generated_image_path = None
                continue
        
        # Generate videos from video scripts
        for video_script in content.video_scripts:
            try:
                video_result = await self.media_service.generate_video(
                    script=video_script.script_content,
                    scene_instructions=video_script.scene_instructions
                )
                
                # Save metadata
                metadata = await self.storage_service.save_video_metadata(
                    video_path=video_result["local_path"],
                    script=video_script.script_content,
                    campaign_id=campaign_id,
                    tags=["generated", "ai", "video"]
                )
                
                # Update video script with generated media info
                video_script.generated_video_path = video_result["local_path"]
                video_script.media_id = metadata["id"]
                
                generated_videos.append({
                    "script_id": id(video_script),
                    "video_path": video_result["local_path"],
                    "media_id": metadata["id"]
                })
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error generating video for script {id(video_script)}: {str(e)}", exc_info=True)
                # Continue with other videos
                continue
        
        return {
            "generated_images": generated_images,
            "generated_videos": generated_videos,
            "content": content  # Return updated content with media paths
        }

