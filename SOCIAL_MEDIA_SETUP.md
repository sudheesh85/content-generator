# Social Media Account Setup Guide

## Which Accounts Will Posts Go To?

The system posts to accounts based on the API tokens you configure in your `.env` file.

## Required Setup

### Instagram Business Account Setup

#### Step 1: Create/Link Instagram Business Account
1. You need an **Instagram Business** or **Creator** account (personal accounts won't work)
2. Link it to a Facebook Page
3. Go to: [Facebook Developers](https://developers.facebook.com/)

#### Step 2: Create Facebook App
1. Go to https://developers.facebook.com/apps
2. Click "Create App"
3. Choose "Business" type
4. Fill in app details

#### Step 3: Get Instagram Access Token
1. In your app, go to **Settings > Basic**
2. Add **Instagram Basic Display** product
3. Configure Instagram Basic Display:
   - Valid OAuth Redirect URIs: `https://localhost/`
   - Add test user (your Instagram account)
4. Go to **Instagram Graph API** (in left sidebar)
5. Click "Generate Token"
6. Select your Instagram Business Account
7. Accept permissions
8. **Copy the access token** (starts with `IGQVJXYnp...`)

#### Step 4: Get Instagram Business Account ID
1. Use Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Run query: `me?fields=id,username`
4. **Copy the ID** (numeric)

#### Step 5: Convert to Long-Lived Token (Optional but Recommended)
Short-lived tokens expire in 1 hour. Convert to long-lived (60 days):

```bash
curl -X GET "https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=YOUR_APP_SECRET&access_token=SHORT_LIVED_TOKEN"
```

### Facebook Page Setup

#### Step 1: Get Facebook Page Access Token
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Click "Get Token" → "Get Page Access Token"
4. Select your Facebook Page
5. Grant permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
6. **Copy the Page Access Token**

#### Step 2: Get Facebook Page ID
1. Go to your Facebook Page
2. Click "About" on the left sidebar
3. Scroll down to "Page ID" or "Page Transparency"
4. **Copy the Page ID** (numeric)

Or use Graph API:
```bash
curl -X GET "https://graph.facebook.com/me/accounts?access_token=YOUR_USER_TOKEN"
```

## Configure Environment Variables

Add these to `backend/.env`:

```bash
# Instagram Configuration
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id_here

# Facebook Configuration
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token_here
FACEBOOK_PAGE_ID=your_facebook_page_id_here
```

### Example:
```bash
INSTAGRAM_ACCESS_TOKEN=IGQVJXYnpUa1hMZAkZAXVHRMZAWZA...
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841405309211844

FACEBOOK_ACCESS_TOKEN=EAABsbCS1iHgBOZC7cqm...
FACEBOOK_PAGE_ID=112233445566778
```

## Testing Without Real Tokens (Simulation Mode)

If you **don't** configure the tokens, the system will run in **simulation mode**:
- ✅ All workflow steps complete normally
- ✅ Images are generated
- ✅ Approval queue works
- ⚠️ Publishing is **simulated** (not actually posted)
- 📝 Returns fake post IDs like `simulated_2025-12-12_10:00`

**This is safe for testing!**

## Verify Your Setup

### Test Instagram Connection:
```bash
curl -X GET "https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN"
```

Should return:
```json
{
  "id": "17841405309211844",
  "username": "your_business_account"
}
```

### Test Facebook Connection:
```bash
curl -X GET "https://graph.facebook.com/YOUR_PAGE_ID?fields=name,id&access_token=YOUR_PAGE_TOKEN"
```

Should return:
```json
{
  "name": "Your Page Name",
  "id": "112233445566778"
}
```

## Which Account Receives Posts?

Once configured:

### Instagram:
- Posts to: **The Instagram Business Account** specified by `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- Example: `@your_business_account`

### Facebook:
- Posts to: **The Facebook Page** specified by `FACEBOOK_PAGE_ID`
- Example: "Your Company Page"

## Security Best Practices

1. **Never commit tokens to git**
   ```bash
   # .env is already in .gitignore
   ```

2. **Use long-lived tokens**
   - Short-lived tokens expire in 1 hour
   - Long-lived tokens last 60 days

3. **Rotate tokens regularly**
   - Regenerate tokens every 60 days
   - Update `.env` file

4. **Use environment-specific tokens**
   - Development: Test account tokens
   - Production: Real account tokens

## Troubleshooting

### "Invalid OAuth access token"
- Token expired → Generate new token
- Wrong token → Check you copied the full token

### "Unsupported post request"
- Check permissions: `pages_manage_posts` for Facebook
- Check account type: Must be Business/Creator for Instagram

### "User does not have sufficient permissions"
- Re-authorize with all required permissions
- Check app is in "Live Mode" (not Development Mode)

### Posts not appearing
- Check account: Posts to Business Account/Page, not personal profile
- Check status: Call GET endpoint to verify post was created
- Instagram: May take a few minutes to appear

## Summary

**Quick Setup:**
1. Create Facebook App
2. Get Instagram Business Account token + ID
3. Get Facebook Page token + ID
4. Add to `backend/.env`
5. Restart backend
6. Test with approval flow
7. ✅ Posts go to YOUR accounts!

**Without Tokens:**
- System works in simulation mode
- Safe for testing
- No actual posts made

---

Need help? Check the [Instagram API Docs](https://developers.facebook.com/docs/instagram-api/) or [Facebook Graph API Docs](https://developers.facebook.com/docs/graph-api/).

