"""
Social Media API Integration Service
Handles posting to Instagram and Facebook.
"""
import os
import aiohttp
import logging
from typing import Dict, Optional, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class SocialMediaAPIClient:
    """Client for posting to various social media platforms."""
    
    def __init__(self):
        # API credentials from environment
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.facebook_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        # Base URLs
        self.instagram_base = "https://graph.instagram.com"
        self.facebook_base = "https://graph.facebook.com/v18.0"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def post_to_instagram(
        self,
        image_path: str,
        caption: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post image to Instagram using Graph API.
        
        Requires:
        - Instagram Business Account
        - Facebook Page connected
        - Access token with instagram_basic, pages_show_list, pages_read_engagement permissions
        """
        if not self.instagram_token:
            # Return simulated result when token not configured
            logger.warning("Instagram tokens not configured. Returning simulated result.")
            from datetime import datetime
            return {
                "platform": "instagram",
                "status": "simulated",
                "post_id": f"simulated_ig_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "url": f"https://instagram.com/p/simulated",
                "published_at": datetime.now().isoformat(),
                "message": "Instagram API tokens not configured. This is a simulated post."
            }
        
        account_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
        if not account_id:
            # Return simulated result when account ID not configured
            logger.warning("Instagram account ID not configured. Returning simulated result.")
            from datetime import datetime
            return {
                "platform": "instagram",
                "status": "simulated",
                "post_id": f"simulated_ig_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "url": f"https://instagram.com/p/simulated",
                "published_at": datetime.now().isoformat(),
                "message": "Instagram account ID not configured. This is a simulated post."
            }
        
        try:
            # Step 1: Upload image and get media container ID
            async with aiohttp.ClientSession() as session:
                # Create media container
                container_url = f"{self.instagram_base}/{account_id}/media"
                
                # Read image file
                with open(image_path, 'rb') as img_file:
                    files = {'image': img_file}
                    data = {
                        'caption': caption,
                        'access_token': self.instagram_token
                    }
                    
                    async with session.post(container_url, data=data, files=files) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Failed to create media container: {error_text}")
                        
                        result = await response.json()
                        creation_id = result.get('id')
                
                # Step 2: Publish the media container
                publish_url = f"{self.instagram_base}/{account_id}/media_publish"
                publish_data = {
                    'creation_id': creation_id,
                    'access_token': self.instagram_token
                }
                
                async with session.post(publish_url, data=publish_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to publish: {error_text}")
                    
                    publish_result = await response.json()
                    
                    return {
                        "platform": "instagram",
                        "post_id": publish_result.get('id'),
                        "status": "published",
                        "url": f"https://www.instagram.com/p/{publish_result.get('id')}/"
                    }
        
        except Exception as e:
            logger.error(f"Error posting to Instagram: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def post_to_facebook(
        self,
        image_path: str,
        message: str,
        page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post image to Facebook Page using Graph API.
        
        Requires:
        - Facebook Page
        - Access token with pages_manage_posts permission
        """
        if not self.facebook_token:
            # Return simulated result when token not configured
            logger.warning("Facebook tokens not configured. Returning simulated result.")
            from datetime import datetime
            return {
                "platform": "facebook",
                "status": "simulated",
                "post_id": f"simulated_fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "url": f"https://facebook.com/simulated",
                "published_at": datetime.now().isoformat(),
                "message": "Facebook API tokens not configured. This is a simulated post."
            }
        
        page_id = page_id or os.getenv("FACEBOOK_PAGE_ID")
        if not page_id:
            # Return simulated result when page ID not configured
            logger.warning("Facebook page ID not configured. Returning simulated result.")
            from datetime import datetime
            return {
                "platform": "facebook",
                "status": "simulated",
                "post_id": f"simulated_fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "url": f"https://facebook.com/simulated",
                "published_at": datetime.now().isoformat(),
                "message": "Facebook page ID not configured. This is a simulated post."
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Upload photo to page
                url = f"{self.facebook_base}/{page_id}/photos"
                
                with open(image_path, 'rb') as img_file:
                    files = {'source': img_file}
                    data = {
                        'message': message,
                        'access_token': self.facebook_token
                    }
                    
                    async with session.post(url, data=data, files=files) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Failed to post to Facebook: {error_text}")
                        
                        result = await response.json()
                        
                        return {
                            "platform": "facebook",
                            "post_id": result.get('id'),
                            "status": "published",
                            "url": f"https://www.facebook.com/{result.get('id')}"
                        }
        
        except Exception as e:
            logger.error(f"Error posting to Facebook: {str(e)}")
            raise
    
    async def post_to_multiple_platforms(
        self,
        image_path: str,
        caption: str,
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Post to multiple platforms simultaneously."""
        import asyncio
        
        results = {}
        tasks = []
        
        if "instagram" in platforms:
            tasks.append(("instagram", self.post_to_instagram(image_path, caption)))
        if "facebook" in platforms:
            tasks.append(("facebook", self.post_to_facebook(image_path, caption)))
        
        for platform, task in tasks:
            try:
                results[platform] = await task
            except Exception as e:
                results[platform] = {"error": str(e), "status": "failed"}
        
        return results

