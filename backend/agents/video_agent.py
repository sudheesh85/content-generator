from typing import List, Any
try:
    from backend.models.campaign import VideoScript
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import VideoScript
    from agents.base import BaseAgent
import json

class VideoScriptAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="VideoScriptAgent",
            instructions="You are a Video Script Writer. Create engaging scripts for short-form video content."
        )

    async def process(self, context: Any) -> List[VideoScript]:
        prompt = f"""
        Context: {str(context)}
        
        Generate video scripts for Reels/TikToks.
        Return JSON with a list of objects under "results":
        - script_content (str)
        - scene_instructions (str)
        - voice_over (str)
        """
        
        content = await self._get_completion(prompt)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        
        # Handle both list and dict responses
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", data.get("videos", []))
            
        return [VideoScript(**item) for item in results]
