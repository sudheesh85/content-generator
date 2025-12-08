from typing import Any
try:
    from backend.models.campaign import ResearchSummary
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import ResearchSummary
    from agents.base import BaseAgent
import json

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            instructions="You are a Research Assistant. Gather key facts, topics, and trends to support content creation."
        )

    async def process(self, strategy_data: Any) -> ResearchSummary:
        # In a real scenario, this would use search tools or document readers.
        # For now, we simulate research based on the strategy context.
        
        prompt = f"""
        Context: {str(strategy_data)}
        
        Gather key facts and topics.
        Return JSON with:
        - key_facts (list)
        - topic_list (list)
        - faq_list (list)
        - quotes_or_stats (list)
        """
        
        content = await self._get_completion(prompt)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        return ResearchSummary(**data)
