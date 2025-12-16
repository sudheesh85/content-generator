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
    brand_voice: BrandVoiceProfile
    research: ResearchSummary

@dataclass
class MediaGeneratedMessage:
    calendar: ContentCalendar
    content: DraftContentBundle
    strategy: CampaignStrategy
    brand_voice: BrandVoiceProfile
    research: ResearchSummary
    media_results: Dict[str, Any]

@dataclass
class ApprovalMessage:
    calendar: ContentCalendar
    content: DraftContentBundle
    strategy: CampaignStrategy
    brand_voice: BrandVoiceProfile
    research: ResearchSummary
    approval_queue: List[Dict[str, Any]]

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
    async def process_request(self, message: CampaignRequest, ctx: WorkflowContext) -> None:
        try:
            from backend.agents.strategy_agent import StrategyAgent
        except ModuleNotFoundError:
            from agents.strategy_agent import StrategyAgent
        
        agent = StrategyAgent()
        strategy = await agent.process(message)
        
        strategy_msg = StrategyMessage(
            strategy=strategy,
            request=message
        )
        
        # Send message to next executor in the DAG
        await ctx.send_message(strategy_msg)


class ResearchExecutor(Executor):
    """
    Executor that gathers research based on strategy.
    """
    
    @handler
    async def process_strategy(self, message: StrategyMessage, ctx: WorkflowContext) -> None:
        try:
            from backend.agents.research_agent import ResearchAgent
        except ModuleNotFoundError:
            from agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        research = await agent.process(message.strategy)
        
        research_msg = ResearchMessage(
            research=research,
            strategy=message.strategy,
            request=message.request
        )
        
        # Send message to next executor in the DAG
        await ctx.send_message(research_msg)


class BrandVoiceExecutor(Executor):
    """
    Executor that defines brand voice.
    """
    
    @handler
    async def process_research(self, message: ResearchMessage, ctx: WorkflowContext) -> None:
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
        
        brand_voice_msg = BrandVoiceMessage(
            brand_voice=brand_voice,
            research=message.research,
            strategy=message.strategy,
            request=message.request
        )
        
        # Send message to next executor in the DAG
        await ctx.send_message(brand_voice_msg)


class ContentGeneratorExecutor(Executor):
    """
    Executor that orchestrates parallel content generation.
    """
    
    @handler
    async def process_brand_voice(self, message: BrandVoiceMessage, ctx: WorkflowContext) -> None:
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
        
        content_msg = ContentMessage(
            content=content,
            brand_voice=message.brand_voice,
            research=message.research,
            strategy=message.strategy
        )
        
        # Send message to next executor in the DAG
        await ctx.send_message(content_msg)


class CalendarExecutor(Executor):
    """
    Executor that schedules content into a calendar.
    """
    
    @handler
    async def process_media(self, message: MediaGeneratedMessage, ctx: WorkflowContext) -> None:
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
        
        calendar_msg = CalendarMessage(
            calendar=calendar,
            content=message.content,
            strategy=message.strategy,
            brand_voice=message.brand_voice,
            research=message.research
        )
        
        # Send message to next executor in the DAG
        await ctx.send_message(calendar_msg)


class MediaGenerationExecutor(Executor):
    """
    Executor that generates actual images and videos from briefs.
    """
    
    @handler
    async def process_content(self, message: ContentMessage, ctx: WorkflowContext) -> None:
        try:
            from backend.agents.media_generation_agent import MediaGenerationAgent
        except ModuleNotFoundError:
            from agents.media_generation_agent import MediaGenerationAgent
        
        agent = MediaGenerationAgent()
        media_context = {
            "content": message.content,
            "campaign_id": "default"  # TODO: Get from request context
        }
        media_results = await agent.process(media_context)
        
        # Create MediaGeneratedMessage with updated content (now includes media paths)
        # Note: Calendar will be created by CalendarExecutor
        media_msg = MediaGeneratedMessage(
            calendar=ContentCalendar(entries=[]),  # Will be populated by calendar executor
            content=media_results["content"],  # Updated content with media paths
            strategy=message.strategy,
            brand_voice=message.brand_voice,
            research=message.research,
            media_results=media_results
        )
        
        await ctx.send_message(media_msg)


class ApprovalWorkflowExecutor(Executor):
    """
    Executor that manages human-in-the-loop approval workflow.
    This is the FINAL executor - workflow stops here for human approval.
    """
    
    @handler
    async def process_calendar(self, message: CalendarMessage, ctx: WorkflowContext) -> None:
        try:
            from backend.agents.approval_agent import ApprovalAgent
        except ModuleNotFoundError:
            from agents.approval_agent import ApprovalAgent
        
        agent = ApprovalAgent()
        approval_context = {
            "calendar": message.calendar,
            "content": message.content
        }
        approval_result = await agent.process(approval_context)
        
        # Create final result with all data - STOPS HERE for human approval
        final_result = FinalResult(
            strategy=message.strategy,
            research=message.research,
            brand_voice=message.brand_voice,
            content=message.content,
            calendar=approval_result["calendar"],
            publish_result={
                "status": "awaiting_approval",
                "approval_queue": approval_result["approval_queue"],
                "pending_count": approval_result.get("pending_count", 0),
                "message": "Content generated and ready for approval. Please review and approve before publishing."
            }
        )
        
        # Yield final result - workflow ends here
        await ctx.yield_output(final_result)


class PublisherExecutor(Executor):
    """
    Executor that publishes approved content to social media platforms.
    """
    
    @handler
    async def process_approval(self, message: ApprovalMessage, ctx: WorkflowContext) -> None:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from backend.agents.social_publisher_agent import SocialPublisherAgent
        except ModuleNotFoundError:
            from agents.social_publisher_agent import SocialPublisherAgent
        
        try:
            agent = SocialPublisherAgent()
            publish_context = {
                "calendar": message.calendar,
                "content": message.content
            }
            publish_result = await agent.process(publish_context)
        except Exception as e:
            logger.error(f"Error in publisher agent: {str(e)}", exc_info=True)
            # Return a safe result even if publishing fails
            publish_result = {
                "published_count": 0,
                "failed_count": 0,
                "published_posts": [],
                "failed_posts": [],
                "calendar": message.calendar,
                "error": str(e),
                "message": "Publishing step encountered an error, but content is ready for approval."
            }
        
        # Reconstruct full result from the message chain with all context
        final_result = FinalResult(
            strategy=message.strategy,
            research=message.research,
            brand_voice=message.brand_voice,
            content=message.content,
            calendar=publish_result.get("calendar", message.calendar),
            publish_result=publish_result
        )
        
        # Yield the final result as output (framework pattern for final outputs)
        await ctx.yield_output(final_result)


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
        self.media_generation_executor = MediaGenerationExecutor(id="media_generation")
        self.calendar_executor = CalendarExecutor(id="calendar")
        self.approval_executor = ApprovalWorkflowExecutor(id="approval")
        self.publisher_executor = PublisherExecutor(id="publisher")
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """
        Constructs the DAG using WorkflowBuilder.
        
        DAG Structure:
        StrategyExecutor → ResearchExecutor → BrandVoiceExecutor → 
        ContentGeneratorExecutor → MediaGenerationExecutor → CalendarExecutor → 
        ApprovalWorkflowExecutor (STOPS HERE for human approval)
        
        Note: PublisherExecutor is NOT connected - publishing happens via separate API call
        """
        builder = WorkflowBuilder()
        
        # Set the starting executor
        builder.set_start_executor(self.strategy_executor)
        
        # Define edges (data flow) - STOPS at approval, NOT auto-publishing
        builder.add_edge(self.strategy_executor, self.research_executor)
        builder.add_edge(self.research_executor, self.brand_voice_executor)
        builder.add_edge(self.brand_voice_executor, self.content_executor)
        builder.add_edge(self.content_executor, self.media_generation_executor)
        builder.add_edge(self.media_generation_executor, self.calendar_executor)
        builder.add_edge(self.calendar_executor, self.approval_executor)
        # NO EDGE TO PUBLISHER - human approval required first!
        
        return builder.build()
    
    async def run_campaign(self, request: CampaignRequest) -> FinalResult:
        """
        Execute the workflow using MAF framework's native DAG orchestration.
        
        The framework handles:
        - Message routing between executors
        - Type validation
        - Error propagation
        - State management
        - Execution flow based on defined edges
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Starting workflow execution...")
            # Execute the workflow using the framework's run method
            # The framework will automatically route messages through the DAG
            # based on the edges defined in _build_workflow()
            workflow_result = await self.workflow.run(request)
            logger.info("Workflow execution completed, extracting outputs...")
            
            # Extract the outputs from the WorkflowRunResult
            # The last executor (PublisherExecutor) returns FinalResult
            outputs = workflow_result.get_outputs()
            logger.info(f"Workflow produced {len(outputs)} output(s)")
            
            if not outputs:
                logger.error("No outputs from workflow")
                raise ValueError("Workflow execution completed but no outputs were produced")
            
            # Get the last output (should be FinalResult from PublisherExecutor)
            final_result = outputs[-1]
            logger.info(f"Final result type: {type(final_result)}")
            
            if isinstance(final_result, FinalResult):
                logger.info("FinalResult validated successfully")
                return final_result
            else:
                logger.error(f"Unexpected result type: {type(final_result)}, outputs: {outputs}")
                raise TypeError(
                    f"Expected FinalResult from PublisherExecutor, got {type(final_result)}. "
                    f"Outputs: {outputs}"
                )
        except Exception as e:
            logger.error(f"Error in run_campaign: {str(e)}", exc_info=True)
            raise
