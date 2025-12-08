from backend.models.campaign import CampaignRequest
from backend.agents.strategy_agent import StrategyAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.brand_voice_agent import BrandVoiceAgent
from backend.agents.content_orchestrator import ContentGeneratorAgent
from backend.agents.post_production_agents import CalendarAgent, PublisherAgent, EngagementAgent, AnalyticsAgent, RecommendationAgent

class WorkflowManager:
    def __init__(self):
        self.strategy_agent = StrategyAgent()
        self.research_agent = ResearchAgent()
        self.brand_voice_agent = BrandVoiceAgent()
        self.content_generator = ContentGeneratorAgent()
        self.calendar_agent = CalendarAgent()
        self.publisher_agent = PublisherAgent()
        self.engagement_agent = EngagementAgent()
        self.analytics_agent = AnalyticsAgent()
        self.recommendation_agent = RecommendationAgent()

    async def run_campaign(self, request: CampaignRequest):
        # Step 1: Strategy
        strategy = await self.strategy_agent.process(request)
        
        # Step 2: Research
        research = await self.research_agent.process(strategy)
        
        # Step 3: Brand Voice
        brand_voice = await self.brand_voice_agent.process({"request": request, "strategy": strategy, "research": research})
        
        # Step 4: Content Generation (Parallel internally)
        content_context = {
            "strategy": strategy,
            "research": research,
            "brand_voice": brand_voice
        }
        draft_content = await self.content_generator.process(content_context)
        
        # Step 5: Calendar
        calendar_context = {
            "strategy": strategy,
            "draft_content": draft_content
        }
        calendar = await self.calendar_agent.process(calendar_context)
        
        # Step 6: Publish (Simulation)
        publish_result = await self.publisher_agent.process(calendar)
        
        return {
            "strategy": strategy,
            "research": research,
            "brand_voice": brand_voice,
            "draft_content": draft_content,
            "calendar": calendar,
            "publish_result": publish_result
        }
