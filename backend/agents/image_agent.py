from typing import List, Any
try:
    from backend.models.campaign import ImageBrief
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import ImageBrief
    from agents.base import BaseAgent
import json

class ImageIdeaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ImageIdeaAgent",
            instructions="You are a Creative Director. Generate visual concepts and image briefs."
        )

    async def process(self, context: Any) -> List[ImageBrief]:
        prompt = f"""
        Context: {str(context)}
        
        Generate image briefs for the campaign.
        Return JSON with a list of objects under "results":
        - layout_description (str)
        - text_overlay (str)
        - style_suggestions (str)
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
            results = data.get("results", data.get("images", []))
            
        return [ImageBrief(**item) for item in results]
