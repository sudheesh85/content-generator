# Human Approval & Social Media Publishing

## Overview

The system now supports **human-in-the-loop approval** before publishing to social media (Facebook & Instagram).

## Workflow

```
Generate Content → Images Generated → Approval Queue → Human Approval → Publish to Social Media
```

## API Endpoints

### 1. Get Approval Queue
```http
GET /api/approval/{campaign_id}/queue
```

**Response:**
```json
{
  "campaign_id": "abc123",
  "queue": [
    {
      "entry_index": 0,
      "channel": "Instagram",
      "caption": "Join Us for AI Conclave 2025! 🚀...",
      "media_type": "image",
      "date": "2025-12-12",
      "time": "10:00",
      "approval_status": "pending",
      "status": "pending_approval",
      "image_info": {
        "layout": "A carousel layout...",
        "text_overlay": "Join Us for AI Conclave 2025!",
        "generated_path": "media/images/image_abc123.png",
        "generated_url": "http://...",
        "media_id": "img_001"
      }
    }
  ],
  "pending_count": 5,
  "approved_count": 0,
  "rejected_count": 0
}
```

### 2. Approve/Reject Single Entry
```http
POST /api/approval/{campaign_id}/approve
```

**Request Body:**
```json
{
  "entry_index": 0,
  "action": "approve",  // or "reject"
  "notes": "Optional notes"
}
```

### 3. Bulk Approve/Reject
```http
POST /api/approval/{campaign_id}/approve-all
```

**Request Body:**
```json
{
  "entry_indices": [0, 1, 2, 3, 4],
  "action": "approve",
  "notes": "Approved all entries"
}
```

### 4. Publish to Social Media
```http
POST /api/approval/{campaign_id}/publish
```

**Request Body:**
```json
{
  "entry_indices": [0, 1, 2],  // Which entries to publish
  "platforms": ["instagram", "facebook"]  // Optional, defaults to all
}
```

**Response:**
```json
{
  "status": "success",
  "published_count": 3,
  "failed_count": 0,
  "published": [
    {
      "entry_index": 0,
      "platform": "instagram",
      "post_id": "12345",
      "url": "https://instagram.com/p/12345"
    }
  ],
  "failed": []
}
```

## Usage Flow

### Step 1: Generate Campaign
```bash
# Campaign generates and images are created
POST /api/campaign/start?background=true
```

### Step 2: Check Approval Queue
```bash
GET /api/approval/{campaign_id}/queue
```

### Step 3: Review & Approve
```bash
# Approve entry 0
POST /api/approval/{campaign_id}/approve
{
  "entry_index": 0,
  "action": "approve"
}

# Or approve all at once
POST /api/approval/{campaign_id}/approve-all
{
  "entry_indices": [0, 1, 2, 3, 4],
  "action": "approve"
}
```

### Step 4: Publish to Social Media
```bash
POST /api/approval/{campaign_id}/publish
{
  "entry_indices": [0, 1, 2, 3, 4],
  "platforms": ["instagram", "facebook"]
}
```

## Environment Setup

### Required API Keys

Add to `.env`:
```bash
# Required for publishing
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_id

FACEBOOK_ACCESS_TOKEN=your_facebook_token
FACEBOOK_PAGE_ID=your_page_id
```

### Getting API Tokens

#### Instagram:
1. Create Facebook App: https://developers.facebook.com/
2. Add Instagram Basic Display
3. Get User Access Token
4. Convert to Long-lived Token
5. Get Business Account ID

#### Facebook:
1. Same Facebook App
2. Add Page Publishing permissions
3. Get Page Access Token
4. Get Page ID

## Testing Without Real Tokens

The system will **simulate** posting if tokens are not configured:

```json
{
  "platform": "instagram",
  "post_id": "simulated_2025-12-11_10:00",
  "status": "simulated",
  "message": "API tokens not configured. This is a simulation."
}
```

## Example: Complete Flow

```bash
# 1. Start campaign
curl -X POST http://localhost:8000/api/campaign/start?background=true \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Promote AI Conclave 2025",
    "channels": ["Instagram", "Facebook"],
    "timeframe": "1 day"
  }'

# Response: { "campaign_id": "abc123", "status": "started" }

# 2. Wait for completion (poll status)
curl http://localhost:8000/api/campaign/abc123/status

# 3. Get approval queue
curl http://localhost:8000/api/approval/abc123/queue

# 4. Approve all entries
curl -X POST http://localhost:8000/api/approval/abc123/approve-all \
  -H "Content-Type: application/json" \
  -d '{
    "entry_indices": [0, 1, 2, 3, 4],
    "action": "approve"
  }'

# 5. Publish to Instagram and Facebook
curl -X POST http://localhost:8000/api/approval/abc123/publish \
  -H "Content-Type: application/json" \
  -d '{
    "entry_indices": [0, 1, 2, 3, 4],
    "platforms": ["instagram", "facebook"]
  }'
```

## Frontend Integration

### Display Approval Queue

Show generated images and captions for review:
```typescript
const queue = await fetch(`/api/approval/${campaignId}/queue`);
// Display each entry with:
// - Generated image
// - Caption
// - Approve/Reject buttons
```

### Approve & Publish

```typescript
// Approve entry
await fetch(`/api/approval/${campaignId}/approve`, {
  method: 'POST',
  body: JSON.stringify({
    entry_index: 0,
    action: 'approve'
  })
});

// Publish all approved
await fetch(`/api/approval/${campaignId}/publish`, {
  method: 'POST',
  body: JSON.stringify({
    entry_indices: [0, 1, 2, 3, 4]
  })
});
```

## Security Notes

1. **API Keys**: Never commit API keys to git
2. **Tokens**: Store in `.env` file
3. **Permissions**: Ensure tokens have required scopes
4. **Rate Limits**: Instagram/Facebook have rate limits
5. **Approval**: Always require human approval before publishing

## Next Steps

1. Restart backend to load new approval endpoints
2. Test approval queue endpoint
3. Approve generated content
4. Publish to social media (real or simulated)
5. Check published posts on Instagram/Facebook

