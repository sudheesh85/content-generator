from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

class CampaignRequest(BaseModel):
    goal: str
    target_audience: Optional[str] = None
    channels: List[str] = ["Instagram", "Facebook"]
    timeframe: str = "1 week"
    brand_tone: Optional[str] = None
    assets: List[str] = []

class CampaignStrategy(BaseModel):
    pillars: List[str]
    post_types_by_channel: Dict[str, List[str]]
    frequency_plan: str
    success_metrics: List[str]

class ResearchSummary(BaseModel):
    key_facts: List[str]
    topic_list: List[str]
    faq_list: List[str]
    quotes_or_stats: List[str]

class BrandVoiceProfile(BaseModel):
    tone_descriptors: List[str]
    sample_sentences: List[str]
    style_rules: List[str]

class CaptionSet(BaseModel):
    channel: str
    captions: List[str]

class ImageBrief(BaseModel):
    layout_description: str
    text_overlay: str
    style_suggestions: str

class VideoScript(BaseModel):
    script_content: str
    scene_instructions: str
    voice_over: str

class DraftContentBundle(BaseModel):
    captions: List[CaptionSet]
    image_briefs: List[ImageBrief]
    video_scripts: List[VideoScript]

class ContentCalendarEntry(BaseModel):
    date: str
    time: str
    channel: str
    post_type: str
    caption_ref: str
    image_brief_ref: Optional[str] = None
    video_script_ref: Optional[str] = None
    status: str = "draft"
    
    @field_validator('caption_ref', 'image_brief_ref', 'video_script_ref', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        if v is None:
            return v
        return str(v)

class ContentCalendar(BaseModel):
    entries: List[ContentCalendarEntry]
