from typing import Any, List
try:
    from backend.models.campaign import ContentCalendar, ContentCalendarEntry
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from models.campaign import ContentCalendar, ContentCalendarEntry
    from agents.base import BaseAgent
import json
import datetime

class CalendarAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CalendarAgent",
            instructions="You are a Social Media Manager. Organize content into a cohesive schedule."
        )

    async def process(self, context: Any) -> ContentCalendar:
        # Context includes strategy and draft content
        prompt = f"""
        Context: {str(context)}
        
        Schedule the content into a calendar.
        Return JSON with "entries" list:
        - date (YYYY-MM-DD)
        - time (HH:MM)
        - channel
        - post_type
        - caption_ref (index or summary)
        - image_brief_ref (optional)
        - video_script_ref (optional)
        """
        
        content = await self._get_completion(prompt)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        entries = data.get("entries", [])
        return ContentCalendar(entries=[ContentCalendarEntry(**e) for e in entries])

class PublisherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="PublisherAgent",
            instructions="You are a Publishing Assistant. Handle content distribution."
        )

    async def process(self, calendar: ContentCalendar) -> dict:
        # Simulate publishing
        return {"status": "success", "published_count": len(calendar.entries)}

class EngagementAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="EngagementAgent",
            instructions="You are an Engagement Analyst. Track and analyze social media interactions."
        )

    async def process(self, data: Any) -> dict:
        return {"metrics": "simulated_metrics"}

class AnalyticsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AnalyticsAgent",
            instructions="You are a Data Analyst. Generate performance reports."
        )

    async def process(self, data: Any) -> dict:
        return {"report": "Weekly Performance Report: All metrics looking good."}

class RecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="RecommendationAgent",
            instructions="You are a Growth Strategist. Provide actionable recommendations for improvement."
        )

    async def process(self, data: Any) -> dict:
        return {"suggestions": "Post more video content on Tuesdays."}
