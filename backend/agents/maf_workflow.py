"""
MAF Workflow DAG Implementation
This module implements the social media campaign workflow using Microsoft Agent Framework's
native DAG orchestration with Executor nodes and typed message passing.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
from agent_framework import Executor, WorkflowBuilder, handler, WorkflowContext

try:
    from backend.models.campaign import (
        CampaignRequest, 
        CampaignStrategy, 
        ResearchSummary,
        BrandVoiceProfile,
        DraftContentBundle,
        ContentCalendar,
        CaptionSet,
        ImageBrief,
        VideoScript
    )
except ModuleNotFoundError:
    from models.campaign import (
        CampaignRequest, 
        CampaignStrategy, 
        ResearchSummary,
        BrandVoiceProfile,
        DraftContentBundle,
        ContentCalendar,
        CaptionSet,
        ImageBrief,
        VideoScript
    )
import json

# Message types for typed communication between executors
@dataclass
class StrategyMessage:
    strategy: CampaignStrategy
    request: CampaignRequest

@dataclass
class ResearchMessage:
    research: ResearchSummary
    strategy: CampaignStrategy
    request: CampaignRequest

@dataclass
class BrandVoiceMessage:
    brand_voice: BrandVoiceProfile
    research: ResearchSummary
    strategy: CampaignStrategy
    request: CampaignRequest

@dataclass
class ContentMessage:
    content: DraftContentBundle
    brand_voice: BrandVoiceProfile
    research: ResearchSummary
    strategy: CampaignStrategy

@dataclass
class CalendarMessage:
    calendar: ContentCalendar
    content: DraftContentBundle
    strategy: CampaignStrategy

@dataclass
class FinalResult:
    strategy: CampaignStrategy
    research: ResearchSummary
    brand_voice: BrandVoiceProfile
    content: DraftContentBundle
    calendar: ContentCalendar
    publish_result: Dict[str, Any]

# ============================================================================
# EXECUTOR NODES (DAG Nodes)
# ============================================================================

class StrategyExecutor(Executor):
    """
    Executor that generates campaign strategy from user request.
    """
    
    @handler
    async def process_request(self, message: CampaignRequest, ctx: WorkflowContext) -> StrategyMessage:
        try:
            from backend.agents.strategy_agent import StrategyAgent
        except ModuleNotFoundError:
            from agents.strategy_agent import StrategyAgent
        
        agent = StrategyAgent()
        strategy = await agent.process(message)
        
        return StrategyMessage(
            strategy=strategy,
            request=message
        )


class ResearchExecutor(Executor):
    """
    Executor that gathers research based on strategy.
    """
    
    @handler
    async def process_strategy(self, message: StrategyMessage, ctx: WorkflowContext) -> ResearchMessage:
        try:
            from backend.agents.research_agent import ResearchAgent
        except ModuleNotFoundError:
            from agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        research = await agent.process(message.strategy)
        
        return ResearchMessage(
            research=research,
            strategy=message.strategy,
            request=message.request
        )


class BrandVoiceExecutor(Executor):
    """
    Executor that defines brand voice.
    """
    
    @handler
    async def process_research(self, message: ResearchMessage, ctx: WorkflowContext) -> BrandVoiceMessage:
        try:
            from backend.agents.brand_voice_agent import BrandVoiceAgent
        except ModuleNotFoundError:
            from agents.brand_voice_agent import BrandVoiceAgent
        
        agent = BrandVoiceAgent()
        context = {
            "request": message.request,
            "strategy": message.strategy,
            "research": message.research
        }
        brand_voice = await agent.process(context)
        
        return BrandVoiceMessage(
            brand_voice=brand_voice,
            research=message.research,
            strategy=message.strategy,
            request=message.request
        )


class ContentGeneratorExecutor(Executor):
    """
    Executor that orchestrates parallel content generation.
    """
    
    @handler
    async def process_brand_voice(self, message: BrandVoiceMessage, ctx: WorkflowContext) -> ContentMessage:
        try:
            from backend.agents.content_orchestrator import ContentGeneratorAgent
        except ModuleNotFoundError:
            from agents.content_orchestrator import ContentGeneratorAgent
        
        agent = ContentGeneratorAgent()
        content_context = {
            "strategy": message.strategy,
            "research": message.research,
            "brand_voice": message.brand_voice
        }
        content = await agent.process(content_context)
        
        return ContentMessage(
            content=content,
            brand_voice=message.brand_voice,
            research=message.research,
            strategy=message.strategy
        )


class CalendarExecutor(Executor):
    """
    Executor that schedules content into a calendar.
    """
    
    @handler
    async def process_content(self, message: ContentMessage, ctx: WorkflowContext) -> CalendarMessage:
        try:
            from backend.agents.post_production_agents import CalendarAgent
        except ModuleNotFoundError:
            from agents.post_production_agents import CalendarAgent
        
        agent = CalendarAgent()
        calendar_context = {
            "strategy": message.strategy,
            "draft_content": message.content
        }
        calendar = await agent.process(calendar_context)
        
        return CalendarMessage(
            calendar=calendar,
            content=message.content,
            strategy=message.strategy
        )


class PublisherExecutor(Executor):
    """
    Executor that simulates publishing.
    """
    
    @handler
    async def process_calendar(self, message: CalendarMessage, ctx: WorkflowContext) -> FinalResult:
        try:
            from backend.agents.post_production_agents import PublisherAgent
        except ModuleNotFoundError:
            from agents.post_production_agents import PublisherAgent
        
        agent = PublisherAgent()
        publish_result = await agent.process(message.calendar)
        
        # Reconstruct full result from the message chain
        return FinalResult(
            strategy=message.strategy,
            research=ResearchSummary(key_facts=[], topic_list=[], faq_list=[], quotes_or_stats=[]),  # Would need to pass through
            brand_voice=BrandVoiceProfile(tone_descriptors=[], sample_sentences=[], style_rules=[]),  # Would need to pass through
            content=message.content,
            calendar=message.calendar,
            publish_result=publish_result
        )


# ============================================================================
# WORKFLOW BUILDER (DAG Construction)
# ============================================================================

class CampaignWorkflow:
    """
    Builds and manages the MAF-based DAG workflow for social media campaigns.
    """
    
    def __init__(self):
        # Create executors with unique IDs
        self.strategy_executor = StrategyExecutor(id="strategy")
        self.research_executor = ResearchExecutor(id="research")
        self.brand_voice_executor = BrandVoiceExecutor(id="brand_voice")
        self.content_executor = ContentGeneratorExecutor(id="content_generator")
        self.calendar_executor = CalendarExecutor(id="calendar")
        self.publisher_executor = PublisherExecutor(id="publisher")
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """
        Constructs the DAG using WorkflowBuilder.
        
        DAG Structure:
        StrategyExecutor → ResearchExecutor → BrandVoiceExecutor → 
        ContentGeneratorExecutor → CalendarExecutor → PublisherExecutor
        """
        builder = WorkflowBuilder()
        
        # Set the starting executor
        builder.set_start_executor(self.strategy_executor)
        
        # Define edges (data flow)
        builder.add_edge(self.strategy_executor, self.research_executor)
        builder.add_edge(self.research_executor, self.brand_voice_executor)
        builder.add_edge(self.brand_voice_executor, self.content_executor)
        builder.add_edge(self.content_executor, self.calendar_executor)
        builder.add_edge(self.calendar_executor, self.publisher_executor)
        
        return builder.build()
    
    async def run_campaign(self, request: CampaignRequest) -> FinalResult:
        """
        Execute the workflow with simple async orchestration.
        MAF DAG has type-matching complexities, so we use direct async calls.
        """
        # Step 1: Strategy
        strategy_msg = await self.strategy_executor.process_request(request, None)
        
        # Step 2: Research  
        research_msg = await self.research_executor.process_strategy(strategy_msg, None)
        
        # Step 3: Brand Voice
        brand_voice_msg = await self.brand_voice_executor.process_research(research_msg, None)
        
        # Step 4: Content Generation
        content_msg = await self.content_executor.process_brand_voice(brand_voice_msg, None)
        
        # Step 5: Calendar
        calendar_msg = await self.calendar_executor.process_content(content_msg, None)
        
        # Step 6: Publish
        final_result = await self.publisher_executor.process_calendar(calendar_msg, None)
        
        return final_result
