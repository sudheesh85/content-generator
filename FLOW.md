# AI Social Media Content Generator - Flow Diagram

## Current Implementation Status

**Note:** This implementation uses **sequential async coordination** (not a true MAF DAG yet). The agents are orchestrated using Python's asyncio, with some parallel execution within the ContentGeneratorAgent.

## Agent Flow (DAG Pattern)

```
UserInput (Frontend)
    ↓
[CampaignRequest]
    ↓
┌─────────────────────┐
│  StrategyAgent      │ → Defines content pillars, post types, frequency
└─────────────────────┘
    ↓
[CampaignStrategy]
    ↓
┌─────────────────────┐
│  ResearchAgent      │ → Gathers key facts, topics, trends
└─────────────────────┘
    ↓
[ResearchSummary]
    ↓
┌─────────────────────┐
│  BrandVoiceAgent    │ → Adapts content to brand voice
└─────────────────────┘
    ↓
[BrandVoiceProfile]
    ↓
┌─────────────────────────────────────┐
│  ContentGeneratorAgent (orchestrator)│
│  ┌──────────────┐  ┌──────────────┐ │
│  │ CaptionAgent │  │ ImageAgent   │ │ → PARALLEL
│  └──────────────┘  └──────────────┘ │    EXECUTION
│  ┌──────────────┐                   │
│  │ VideoAgent   │                   │
│  └──────────────┘                   │
└─────────────────────────────────────┘
    ↓
[DraftContentBundle]
    ↓
┌─────────────────────┐
│  CalendarAgent      │ → Schedules posts across days/channels
└─────────────────────┘
    ↓
[ContentCalendar]
    ↓
┌─────────────────────┐
│  PublisherAgent     │ → Simulates publishing (or exports)
└─────────────────────┘
    ↓
[PublishResult]
    ↓
Frontend Display
```

## Input Example

```json
{
  "goal": "Promote AI Conclave 2025 on Facebook and Instagram for 7 days",
  "target_audience": "Students and AI enthusiasts",
  "channels": ["Instagram", "Facebook"],
  "timeframe": "7 days",
  "brand_tone": "Friendly, educational, exciting"
}
```

## Expected Output Structure

```json
{
  "status": "success",
  "data": {
    "strategy": {
      "pillars": ["Awareness", "Education", "Registration Push"],
      "post_types_by_channel": {
        "Instagram": ["Reel", "Carousel", "Story"],
        "Facebook": ["Image Post", "Text Post", "Event"]
      },
      "frequency_plan": "3 posts per week per channel",
      "success_metrics": ["Engagement Rate", "Click-through Rate", "Registrations"]
    },
    "research": {
      "key_facts": [
        "AI Conclave 2025 - Jan 15-17",
        "Venue: Tech Campus",
        "Topics: LLMs, Computer Vision, Ethics"
      ],
      "topic_list": ["AI trends 2025", "Career in AI", "Hands-on workshops"],
      "faq_list": ["What is the registration fee?", "Is it beginner-friendly?"],
      "quotes_or_stats": ["90% of companies will use AI by 2025"]
    },
    "brand_voice": {
      "tone_descriptors": ["friendly", "educational", "enthusiastic"],
      "sample_sentences": [
        "Join us for the biggest AI event of the year!",
        "Learn from industry experts..."
      ],
      "style_rules": ["Use emojis sparingly", "Keep it conversational"]
    },
    "draft_content": {
      "captions": [
        {
          "channel": "Instagram",
          "captions": [
            "🚀 AI Conclave 2025 is here! Join 500+ students... #AIConclave2025 #AI",
            "Want to learn about the future of AI? Register now! Link in bio 🔗"
          ]
        },
        {
          "channel": "Facebook",
          "captions": [
            "Mark your calendars! AI Conclave 2025 brings together..."
          ]
        }
      ],
      "image_briefs": [
        {
          "layout_description": "Split design with event logo on left, date on right",
          "text_overlay": "AI Conclave 2025 | Jan 15-17",
          "style_suggestions": "Modern gradient, tech-themed colors (blue, purple)"
        }
      ],
      "video_scripts": [
        {
          "script_content": "Scene 1: Opening shot of tech campus...",
          "scene_instructions": "Fast cuts between speakers, workshops, audience",
          "voice_over": "The future of AI is here. Join us at AI Conclave 2025..."
        }
      ]
    },
    "calendar": {
      "entries": [
        {
          "date": "2025-01-08",
          "time": "09:00",
          "channel": "Instagram",
          "post_type": "Reel",
          "caption_ref": "Instagram Caption 1",
          "video_script_ref": "Script 1",
          "status": "draft"
        },
        {
          "date": "2025-01-10",
          "time": "14:00",
          "channel": "Facebook",
          "post_type": "Image Post",
          "caption_ref": "Facebook Caption 1",
          "image_brief_ref": "Brief 1",
          "status": "draft"
        }
      ]
    },
    "publish_result": {
      "status": "success",
      "published_count": 7
    }
  }
}
```

## Agent Coordination Notes

### Current Implementation (Python async)
- Sequential execution with explicit `await` calls
- Parallel execution only within ContentGeneratorAgent (using `asyncio.gather`)
- Not using MAF's native workflow/DAG orchestration features

### To Implement True MAF DAG
Would need to:
1. Define workflow using MAF's Graph API
2. Use agent handoffs and state management
3. Leverage MAF's built-in orchestration patterns

## Next Steps for the User

1. **Test the current flow**: Submit a campaign request via the frontend
2. **Review the output**: Check if all agents produce expected results
3. **Decide on DAG**: Determine if native MAF DAG orchestration is needed
4. **Add features**: Engagement tracking, analytics, recommendations
