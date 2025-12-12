"""
Media Generation Service
Handles actual image and video generation using AI models.
"""
import os
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

class MediaGenerationService:
    """Service for generating images and videos using AI models."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.media_dir = os.getenv("MEDIA_DIR", "media")
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "videos"), exist_ok=True)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def generate_image(
        self, 
        prompt: str, 
        style: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate an image using DALL-E.
        
        Args:
            prompt: Text description for image generation
            style: Optional style descriptor
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, hd)
            
        Returns:
            Dict with 'url', 'local_path', 'prompt', 'metadata'
        """
        try:
            # Enhance prompt with style if provided
            enhanced_prompt = f"{prompt}, {style}" if style else prompt
            
            logger.info(f"Generating image with prompt: {enhanced_prompt[:100]}...")
            
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download and save image locally
            local_path = await self._download_and_save_image(image_url, prompt)
            
            # Extract filename for URL
            filename = os.path.basename(local_path)
            
            return {
                "url": f"/media/images/{filename}",  # Local URL for serving via FastAPI
                "dalle_url": image_url,  # Original DALL-E URL
                "local_path": local_path,
                "prompt": enhanced_prompt,
                "metadata": {
                    "size": size,
                    "quality": quality,
                    "model": "dall-e-3"
                }
            }
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise
    
    async def _download_and_save_image(self, url: str, prompt: str) -> str:
        """Download image from URL and save to local storage."""
        import hashlib
        import aiofiles
        
        # Create filename from prompt hash
        filename_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        filename = f"image_{filename_hash}.png"
        filepath = os.path.join(self.media_dir, "images", filename)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    logger.info(f"Image saved to {filepath}")
                    return filepath
                else:
                    raise Exception(f"Failed to download image: {response.status}")
    
    async def generate_video(
        self,
        script: str,
        scene_instructions: str,
        style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a video from script and scene instructions.
        
        Note: Full video generation requires specialized services like:
        - RunwayML API
        - Synthesia API
        - Pika Labs API
        - Or local video generation tools
        
        For now, this creates a placeholder structure.
        In production, integrate with actual video generation APIs.
        
        Args:
            script: Video script content
            scene_instructions: Scene-by-scene instructions
            style: Optional style descriptor
            
        Returns:
            Dict with 'local_path', 'script', 'metadata'
        """
        # TODO: Integrate with actual video generation API
        # For now, create a metadata file that can be used later
        
        import hashlib
        import json
        import aiofiles
        
        filename_hash = hashlib.md5(script.encode()).hexdigest()[:12]
        metadata_path = os.path.join(self.media_dir, "videos", f"video_{filename_hash}_metadata.json")
        
        metadata = {
            "script": script,
            "scene_instructions": scene_instructions,
            "style": style,
            "status": "pending_generation",
            "local_path": None,  # Will be populated when video is generated
            "generation_service": None  # Will specify which service was used
        }
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        logger.warning(
            "Video generation not fully implemented. "
            "Integrate with RunwayML, Synthesia, or similar service."
        )
        
        return {
            "local_path": metadata_path,
            "script": script,
            "metadata": metadata
        }
    
    async def generate_image_from_brief(
        self, 
        image_brief: Dict[str, Any],
        brand_assets: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate image from an ImageBrief with optional brand assets.
        
        Args:
            image_brief: Dict with layout_description, text_overlay, style_suggestions
            brand_assets: Optional list of brand asset paths to reference
            
        Returns:
            Generated image metadata
        """
        # Build comprehensive prompt from brief
        prompt_parts = [
            image_brief.get("layout_description", ""),
            f"Style: {image_brief.get('style_suggestions', '')}",
        ]
        
        if image_brief.get("text_overlay"):
            prompt_parts.append(f"Include text overlay: {image_brief['text_overlay']}")
        
        if brand_assets:
            prompt_parts.append("Incorporate brand elements and maintain brand consistency")
        
        prompt = ", ".join(filter(None, prompt_parts))
        
        return await self.generate_image(
            prompt=prompt,
            style=image_brief.get("style_suggestions")
        )

