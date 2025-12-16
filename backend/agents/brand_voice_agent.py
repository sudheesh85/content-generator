from typing import Any
try:
    from backend.models.campaign import BrandVoiceProfile
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import BrandVoiceProfile
    from agents.base import BaseAgent
import json

class BrandVoiceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="BrandVoiceAgent",
            instructions="You are a Brand Voice Expert. Define the brand voice profile based on context."
        )

    async def process(self, context_data: Any) -> BrandVoiceProfile:
        prompt = f"""
        Context: {str(context_data)}
        
        Define the brand voice profile.
        Return JSON with:
        - tone_descriptors (list)
        - sample_sentences (list)
        - style_rules (list)
        """
        
        content = await self._get_completion(prompt)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        return BrandVoiceProfile(**data)
