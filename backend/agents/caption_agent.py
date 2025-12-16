from typing import List, Any
try:
    from backend.models.campaign import CaptionSet
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import CaptionSet
    from agents.base import BaseAgent
import json

class CaptionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CaptionAgent",
            instructions="You are a Social Media Copywriter. Generate engaging captions for social media posts."
        )

    async def process(self, context: Any) -> List[CaptionSet]:
        prompt = f"""
        Context: {str(context)}
        
        Generate captions for the campaign.
        Return JSON with a list of objects, each having:
        - channel (str)
        - captions (list of strings)
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
            results = data.get("results", data.get("captions", []))
            
        return [CaptionSet(**item) for item in results]
