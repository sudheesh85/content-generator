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
        - key_facts (list of strings)
        - topic_list (list of strings)
        - faq_list (list - can be strings OR objects with 'question' and 'answer' keys)
        - quotes_or_stats (list of strings)
        
        Example format:
        {{
            "key_facts": ["fact 1", "fact 2"],
            "topic_list": ["topic 1", "topic 2"],
            "faq_list": ["Q: question1\\nA: answer1", "Q: question2\\nA: answer2"],
            "quotes_or_stats": ["stat 1", "stat 2"]
        }}
        """
        
        content = await self._get_completion(prompt)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            data = json.loads(content)
            return ResearchSummary(**data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error parsing research data: {str(e)}", exc_info=True)
            logger.error(f"Raw content: {content}")
            raise
