from typing import Any
try:
    from backend.models.campaign import CampaignRequest, CampaignStrategy
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import CampaignRequest, CampaignStrategy
    from agents.base import BaseAgent
import json

class StrategyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="StrategyAgent",
            instructions="You are a Social Media Strategy Expert. Develop high-level content strategies based on user goals."
        )

    async def process(self, request: CampaignRequest) -> CampaignStrategy:
        prompt = f"""
        Goal: {request.goal}
        Audience: {request.target_audience}
        Channels: {', '.join(request.channels)}
        Timeframe: {request.timeframe}
        
        Develop a high-level content strategy.
        Return JSON with:
        - pillars (list of strings)
        - post_types_by_channel (dict of channel -> list of post types)
        - frequency_plan (string)
        - success_metrics (list of strings)
        """
        
        content = await self._get_completion(prompt)
        
        # Strip markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        return CampaignStrategy(**data)
