"""
Media Storage Service
Manages storage, retrieval, and organization of generated media files.
"""
import os
import json
import shutil
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import aiofiles
import logging

logger = logging.getLogger(__name__)

class MediaStorageService:
    """Service for managing media file storage and organization."""
    
    def __init__(self, base_dir: str = "media"):
        self.base_dir = base_dir
        self.images_dir = os.path.join(base_dir, "images")
        self.videos_dir = os.path.join(base_dir, "videos")
        self.assets_dir = os.path.join(base_dir, "assets")
        self.metadata_file = os.path.join(base_dir, "media_library.json")
        
        # Create directories
        for dir_path in [self.images_dir, self.videos_dir, self.assets_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        if not os.path.exists(self.metadata_file):
            self._initialize_metadata()
    
    def _initialize_metadata(self):
        """Initialize the media library metadata file."""
        initial_data = {
            "images": [],
            "videos": [],
            "assets": [],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    async def save_image_metadata(
        self,
        image_path: str,
        prompt: str,
        campaign_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Save image metadata to the media library."""
        metadata = {
            "id": self._generate_id(),
            "type": "image",
            "path": image_path,
            "prompt": prompt,
            "campaign_id": campaign_id,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        
        await self._add_to_library(metadata)
        return metadata
    
    async def save_video_metadata(
        self,
        video_path: str,
        script: str,
        campaign_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Save video metadata to the media library."""
        metadata = {
            "id": self._generate_id(),
            "type": "video",
            "path": video_path,
            "script": script,
            "campaign_id": campaign_id,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        
        await self._add_to_library(metadata)
        return metadata
    
    async def save_user_asset(
        self,
        file_path: str,
        asset_type: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Save user-uploaded asset to the library."""
        # Copy file to assets directory
        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.assets_dir, filename)
        shutil.copy2(file_path, dest_path)
        
        metadata = {
            "id": self._generate_id(),
            "type": asset_type,  # "logo", "product_shot", "brand_asset", etc.
            "path": dest_path,
            "description": description,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "source": "user_upload"
        }
        
        await self._add_to_library(metadata)
        return metadata
    
    async def _add_to_library(self, metadata: Dict[str, Any]):
        """Add metadata entry to the library."""
        async with aiofiles.open(self.metadata_file, 'r') as f:
            content = await f.read()
            library = json.loads(content)
        
        library[metadata["type"] + "s"].append(metadata)
        library["last_updated"] = datetime.now().isoformat()
        
        async with aiofiles.open(self.metadata_file, 'w') as f:
            await f.write(json.dumps(library, indent=2))
    
    async def get_media_by_campaign(self, campaign_id: str) -> Dict[str, List[Dict]]:
        """Retrieve all media associated with a campaign."""
        async with aiofiles.open(self.metadata_file, 'r') as f:
            content = await f.read()
            library = json.loads(content)
        
        result = {
            "images": [],
            "videos": [],
            "assets": []
        }
        
        for media_type in ["images", "videos", "assets"]:
            result[media_type] = [
                item for item in library.get(media_type, [])
                if item.get("campaign_id") == campaign_id
            ]
        
        return result
    
    async def search_media(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        media_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search media library by query, tags, or type."""
        async with aiofiles.open(self.metadata_file, 'r') as f:
            content = await f.read()
            library = json.loads(content)
        
        results = []
        
        for media_type_key in ["images", "videos", "assets"]:
            if media_type and media_type_key != media_type + "s":
                continue
            
            for item in library.get(media_type_key, []):
                match = True
                
                if query:
                    query_lower = query.lower()
                    match = (
                        query_lower in item.get("prompt", "").lower() or
                        query_lower in item.get("script", "").lower() or
                        query_lower in item.get("description", "").lower()
                    )
                
                if tags and match:
                    item_tags = [t.lower() for t in item.get("tags", [])]
                    match = any(tag.lower() in item_tags for tag in tags)
                
                if match:
                    results.append(item)
        
        return results
    
    def _generate_id(self) -> str:
        """Generate a unique ID for media items."""
        import uuid
        return str(uuid.uuid4())[:8]

