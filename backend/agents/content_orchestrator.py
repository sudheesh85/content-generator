import asyncio
from typing import Any
try:
    from backend.models.campaign import DraftContentBundle
    from backend.agents.base import BaseAgent
    from backend.agents.caption_agent import CaptionAgent
    from backend.agents.image_agent import ImageIdeaAgent
    from backend.agents.video_agent import VideoScriptAgent
except ModuleNotFoundError:
    from models.campaign import DraftContentBundle
    from agents.base import BaseAgent
    from agents.caption_agent import CaptionAgent
    from agents.image_agent import ImageIdeaAgent
    from agents.video_agent import VideoScriptAgent

class ContentGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ContentGeneratorAgent",
            instructions="You are a Content Orchestrator. Coordinate the generation of captions, images, and videos."
        )
        self.caption_agent = CaptionAgent()
        self.image_agent = ImageIdeaAgent()
        self.video_agent = VideoScriptAgent()

    async def process(self, context: Any) -> DraftContentBundle:
        # Run sub-agents in parallel
        captions_task = self.caption_agent.process(context)
        images_task = self.image_agent.process(context)
        videos_task = self.video_agent.process(context)
        
        captions, images, videos = await asyncio.gather(captions_task, images_task, videos_task)
        
        return DraftContentBundle(
            captions=captions,
            image_briefs=images,
            video_scripts=videos
        )
