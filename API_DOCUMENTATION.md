# API Documentation

Complete API reference for the Social Media Content Generator.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. In production, add API key or OAuth2 authentication.

## Endpoints

### Campaign Management

#### Start Campaign
```http
POST /api/campaign/start
```

Start a new content generation campaign.

**Request Body:**
```json
{
  "goal": "Increase brand awareness",
  "target_audience": "Millennials aged 25-35",
  "channels": ["Instagram", "Facebook"],
  "timeframe": "2 weeks",
  "brand_tone": "Professional yet approachable",
  "assets": []
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "campaign_id": "abc123",
    "strategy": {...},
    "research": {...},
    "brand_voice": {...},
    "content": {...},
    "calendar": {...},
    "publish_result": {...}
  }
}
```

#### Get Campaign Status
```http
GET /api/campaign/{campaign_id}/status
```

Get the current status of a campaign.

**Response:**
```json
{
  "campaign_id": "abc123",
  "status": "completed",
  "has_strategy": true,
  "has_research": true,
  "has_brand_voice": true,
  "has_content": true,
  "has_calendar": true,
  "has_media": true,
  "approval_pending": 5,
  "approved": 3,
  "published": 2,
  "total_entries": 10
}
```

#### Get Campaign Data
```http
GET /api/campaign/{campaign_id}
```

Get full campaign data including all generated content.

#### List Campaigns
```http
GET /api/campaign/
```

List all campaigns.

**Response:**
```json
{
  "total": 5,
  "campaigns": [
    {
      "campaign_id": "abc123",
      "has_calendar": true,
      "has_media": true
    }
  ]
}
```

#### Get Campaign Media
```http
GET /api/campaign/{campaign_id}/media
```

Get all media files associated with a campaign.

### Content Management

#### Edit Caption
```http
POST /api/content/edit-caption
```

Edit a caption for a calendar entry.

**Request Body:**
```json
{
  "campaign_id": "abc123",
  "entry_id": "entry_456",
  "new_caption": "Updated caption text"
}
```

#### Regenerate Asset
```http
POST /api/content/regenerate-asset
```

Regenerate a specific image or video while optionally keeping the caption.

**Request Body:**
```json
{
  "campaign_id": "abc123",
  "asset_type": "image",
  "asset_id": "media_789",
  "keep_caption": true
}
```

#### Approve Entry
```http
POST /api/content/approve-entry
```

Approve a calendar entry for publishing.

**Request Body:**
```json
{
  "campaign_id": "abc123",
  "entry_id": "entry_456",
  "approved_by": "user@example.com"
}
```

#### Reject Entry
```http
POST /api/content/reject-entry
```

Reject a calendar entry.

**Request Body:**
```json
{
  "campaign_id": "abc123",
  "entry_id": "entry_456",
  "reason": "Does not match brand voice"
}
```

#### Publish Entry
```http
POST /api/content/publish-entry
```

Publish an approved entry to social media platforms.

**Request Body:**
```json
{
  "campaign_id": "abc123",
  "entry_id": "entry_456"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Entry published",
  "result": {
    "published_count": 1,
    "published_posts": [
      {
        "platform": "instagram",
        "post_id": "123456789",
        "post_url": "https://www.instagram.com/p/123456789/",
        "status": "published"
      }
    ]
  }
}
```

#### Get Approval Queue
```http
GET /api/content/approval-queue/{campaign_id}
```

Get all entries pending approval.

**Response:**
```json
{
  "campaign_id": "abc123",
  "pending_count": 5,
  "entries": [
    {
      "id": "entry_456",
      "date": "2025-12-15",
      "time": "10:00",
      "channel": "Instagram",
      "post_type": "Image Post",
      "status": "pending_approval",
      "approval_status": "pending"
    }
  ]
}
```

#### Upload Asset
```http
POST /api/content/upload-asset
```

Upload a brand asset (logo, product shot, etc.) to the media library.

**Form Data:**
- `campaign_id` (string): Campaign ID
- `asset_type` (string): Type of asset (logo, product_shot, brand_asset)
- `file` (file): Asset file
- `description` (string, optional): Asset description

#### Get Media Library
```http
GET /api/content/media-library/{campaign_id}
```

Get all media in the library for a campaign.

### Health & Info

#### Health Check
```http
GET /health
```

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "content-generator-api"
}
```

#### Root Endpoint
```http
GET /
```

Get API information.

**Response:**
```json
{
  "message": "AI Social Media Content Generator API is running",
  "version": "1.0.0",
  "endpoints": {
    "campaign": "/api/campaign/start",
    "content": "/api/content",
    "status": "/api/campaign/{campaign_id}/status"
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 404 Not Found
```json
{
  "detail": "Campaign not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message here"
}
```

## Workflow Example

1. **Start Campaign**
   ```bash
   curl -X POST http://localhost:8000/api/campaign/start \
     -H "Content-Type: application/json" \
     -d '{
       "goal": "Increase brand awareness",
       "channels": ["Instagram", "Facebook"],
       "timeframe": "1 week"
     }'
   ```

2. **Check Status**
   ```bash
   curl http://localhost:8000/api/campaign/{campaign_id}/status
   ```

3. **Get Approval Queue**
   ```bash
   curl http://localhost:8000/api/content/approval-queue/{campaign_id}
   ```

4. **Approve Entry**
   ```bash
   curl -X POST http://localhost:8000/api/content/approve-entry \
     -H "Content-Type: application/json" \
     -d '{
       "campaign_id": "...",
       "entry_id": "...",
       "approved_by": "user@example.com"
     }'
   ```

5. **Publish Entry**
   ```bash
   curl -X POST http://localhost:8000/api/content/publish-entry \
     -H "Content-Type: application/json" \
     -d '{
       "campaign_id": "...",
       "entry_id": "..."
     }'
   ```

## Notes

- All timestamps are in ISO 8601 format
- Media files are stored in the `media/` directory
- Campaign data is stored in-memory (use database in production)
- Image generation uses DALL-E 3 API (requires OpenAI API key)
- Social media posting requires platform-specific access tokens

