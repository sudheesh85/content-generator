# AI Social Media Content Generator (MAF-based)

## Overview
This project is an AI-powered social media content generator and scheduler using the Microsoft Agent Framework (MAF) pattern. It takes high-level user goals and automatically generates posts, images, video scripts, schedules them, and tracks engagement.

## Architecture

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Markdown**: React Markdown
- **Icons**: Lucide React
- **Features**: Chat-style interface, file attachments, content review (calendar, captions, scripts).

### Backend
- **Framework**: FastAPI (Python)
- **Agent Framework**: Microsoft Agent Framework (MAF)
- **Database**: In-memory or simple JSON storage for this MVP.

## Agents DAG
The system follows a sequential DAG with parallel execution for content generation:

1. **UserInput**: Entry point.
2. **StrategyAgent**: Defines content pillars and frequency.
3. **ResearchAgent**: Gathers context and ideas.
4. **BrandVoiceAgent**: Adapts content to brand voice.
5. **ContentGeneratorAgent**: Orchestrates parallel agents:
    - **CaptionAgent**
    - **ImageIdeaAgent**
    - **VideoScriptAgent**
6. **CalendarAgent**: Schedules content.
7. **PublisherAgent**: Simulates publishing.
8. **EngagementAgent**: Tracks metrics.
9. **AnalyticsAgent**: Weekly reports.
10. **RecommendationAgent**: Improves future campaigns.

## Setup

### Prerequisites
- Node.js
- Python 3.10+

### Installation
1. Frontend: `cd frontend && npm install`
2. Backend: `cd backend && pip install -r requirements.txt --pre`

## Usage
Start the backend server and the frontend development server.
