# Testing the Human Approval Flow

## Overview
The workflow now **STOPS** after generating images and waits for human approval before publishing.

## Flow:
1. Generate Campaign → Images Created
2. **PAUSE** → Human reviews and approves content  
3. Publish to Instagram & Facebook

## How to Test:

### Step 1: Start Backend
```bash
cd /Users/sudheeshmadathil/Documents/content-generator/content-generator/backend
python -m uvicorn main:app --reload --port 8000
```

### Step 2: Start Frontend  
```bash
cd /Users/sudheeshmadathil/Documents/content-generator/content-generator/frontend
npm run dev
```

### Step 3: Generate Campaign
1. Open http://localhost:3000
2. Enter: "Promote AI Conclave 2025 on Instagram and Facebook for 1 day to attract students"
3. Wait for generation (5-10 minutes)

### Step 4: Review Generated Content
You should see:
- ✅ "Campaign generated! Images created. Please review and approve..."
- **Approval Queue UI** with:
  - Generated images displayed
  - Captions shown
  - Approve/Reject buttons for each post

### Step 5: Approve Content
- Click "Approve" on posts you want to publish
- Or reject posts you don't want

### Step 6: Publish to Social Media
- Once approved, click the "Publish X Posts" button
- This will post to Instagram & Facebook

## API Testing (Alternative):

```bash
# 1. Start campaign and get campaign_id
curl -X POST http://localhost:8000/api/campaign/start?background=true \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Promote AI Conclave 2025",
    "channels": ["Instagram", "Facebook"],
    "timeframe": "1 day"
  }'

# 2. Check status (wait for "completed")
curl http://localhost:8000/api/campaign/{campaign_id}/status

# 3. View approval queue
curl http://localhost:8000/api/approval/{campaign_id}/queue

# 4. Approve all entries
curl -X POST http://localhost:8000/api/approval/{campaign_id}/approve-all \
  -H "Content-Type: application/json" \
  -d '{
    "entry_indices": [0, 1, 2, 3, 4],
    "action": "approve"
  }'

# 5. Publish approved posts
curl -X POST http://localhost:8000/api/approval/{campaign_id}/publish \
  -H "Content-Type: application/json" \
  -d '{
    "entry_indices": [0, 1, 2, 3, 4],
    "platforms": ["instagram", "facebook"]
  }'
```

## Expected Behavior:

✅ **What Should Happen:**
- Workflow generates strategy, research, content, and images
- Workflow **STOPS** at approval stage (no auto-publishing)
- UI shows approval queue with generated images
- User can approve/reject each post
- Only approved posts get published to social media

❌ **What Should NOT Happen:**
- Auto-publishing without approval
- Workflow proceeding to PublisherExecutor automatically
- No approval UI shown

## Troubleshooting:

If images don't show:
- Check `backend/media/images/` folder for generated images
- Verify DALL-E API key is set in `.env`
- Check browser console for image loading errors

If publishing fails:
- Without API tokens: Should show "simulated" publish result
- With API tokens: Check token permissions

## Notes:

- Publishing without API tokens = **Simulation mode** (safe for testing)
- To actually publish, add Instagram/Facebook tokens to `.env`
- See `APPROVAL_AND_PUBLISHING.md` for full documentation
