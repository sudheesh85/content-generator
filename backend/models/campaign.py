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

class FAQ(BaseModel):
    question: str
    answer: str

class ResearchSummary(BaseModel):
    key_facts: List[str]
    topic_list: List[str]
    faq_list: List[Any]  # Can be either List[str] or List[FAQ]
    quotes_or_stats: List[str]
    
    @field_validator('faq_list', mode='before')
    @classmethod
    def validate_faq_list(cls, v):
        """Convert FAQ dictionaries to strings if needed."""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                # Convert dict to string format
                q = item.get('question', '')
                a = item.get('answer', '')
                result.append(f"Q: {q}\nA: {a}")
            elif isinstance(item, str):
                result.append(item)
            else:
                result.append(str(item))
        return result

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
    generated_image_path: Optional[str] = None
    generated_image_url: Optional[str] = None
    media_id: Optional[str] = None

class VideoScript(BaseModel):
    script_content: str
    scene_instructions: str
    voice_over: str
    generated_video_path: Optional[str] = None
    media_id: Optional[str] = None

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
    status: str = "draft"  # draft, pending_approval, approved, published, rejected
    approval_status: Optional[str] = None  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    published_at: Optional[str] = None
    post_id: Optional[str] = None  # Platform-specific post ID
    post_url: Optional[str] = None
    engagement_metrics: Optional[Dict[str, Any]] = None
    
    @field_validator('caption_ref', 'image_brief_ref', 'video_script_ref', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        if v is None:
            return v
        return str(v)

class ContentCalendar(BaseModel):
    entries: List[ContentCalendarEntry]
