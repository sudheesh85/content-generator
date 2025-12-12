"""
Analytics Agent
Fetches real engagement metrics from social media platforms.
"""
from typing import Any, Dict, List
try:
    from backend.agents.base import BaseAgent
    from backend.models.campaign import ContentCalendar, ContentCalendarEntry
except ModuleNotFoundError:
    from agents.base import BaseAgent
    from models.campaign import ContentCalendar, ContentCalendarEntry
import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

class AnalyticsAgent(BaseAgent):
    """Agent that fetches and analyzes engagement metrics."""
    
    def __init__(self):
        super().__init__(
            name="AnalyticsAgent",
            instructions="You are an Analytics Expert. Analyze social media performance and provide insights."
        )
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.facebook_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    
    async def process(self, context: Any) -> Dict[str, Any]:
        """
        Fetch engagement metrics for published posts.
        
        Args:
            context: Dict with 'calendar' (ContentCalendar) containing published entries
            
        Returns:
            Dict with metrics, insights, and recommendations
        """
        calendar = context.get("calendar")
        if not calendar:
            raise ValueError("Calendar is required")
        
        # Get published entries
        published_entries = [
            entry for entry in calendar.entries
            if entry.status == "published" and entry.post_id
        ]
        
        metrics = []
        total_engagement = {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0
        }
        
        # Fetch metrics for each published post
        for entry in published_entries:
            try:
                entry_metrics = await self._fetch_post_metrics(entry)
                if entry_metrics:
                    metrics.append({
                        "entry_id": str(id(entry)),
                        "platform": entry.channel,
                        "post_id": entry.post_id,
                        "metrics": entry_metrics
                    })
                    
                    # Aggregate totals
                    total_engagement["likes"] += entry_metrics.get("likes", 0)
                    total_engagement["comments"] += entry_metrics.get("comments", 0)
                    total_engagement["shares"] += entry_metrics.get("shares", 0)
                    total_engagement["views"] += entry_metrics.get("views", 0)
                    
                    # Update entry with metrics
                    entry.engagement_metrics = entry_metrics
            except Exception as e:
                logger.warning(f"Failed to fetch metrics for entry {entry.post_id}: {str(e)}")
                continue
        
        # Generate insights using LLM
        insights = await self._generate_insights(metrics, total_engagement)
        
        return {
            "total_posts": len(published_entries),
            "total_engagement": total_engagement,
            "post_metrics": metrics,
            "insights": insights,
            "recommendations": insights.get("recommendations", [])
        }
    
    async def _fetch_post_metrics(self, entry: ContentCalendarEntry) -> Dict[str, Any]:
        """Fetch metrics for a specific post from platform API."""
        platform = entry.channel.lower()
        post_id = entry.post_id
        
        if not post_id:
            return {}
        
        try:
            if platform == "instagram":
                return await self._fetch_instagram_metrics(post_id)
            elif platform == "facebook":
                return await self._fetch_facebook_metrics(post_id)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error fetching {platform} metrics: {str(e)}")
            return {}
    
    async def _fetch_instagram_metrics(self, post_id: str) -> Dict[str, Any]:
        """Fetch Instagram post metrics."""
        if not self.instagram_token:
            return {}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://graph.instagram.com/{post_id}"
                params = {
                    "fields": "like_count,comments_count,media_type,timestamp",
                    "access_token": self.instagram_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "likes": data.get("like_count", 0),
                            "comments": data.get("comments_count", 0),
                            "views": data.get("video_views", 0) if data.get("media_type") == "VIDEO" else 0,
                            "timestamp": data.get("timestamp")
                        }
        except Exception as e:
            logger.error(f"Instagram metrics error: {str(e)}")
        
        return {}
    
    async def _fetch_facebook_metrics(self, post_id: str) -> Dict[str, Any]:
        """Fetch Facebook post metrics."""
        if not self.facebook_token:
            return {}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://graph.facebook.com/v18.0/{post_id}"
                params = {
                    "fields": "likes.summary(true),comments.summary(true),shares,created_time",
                    "access_token": self.facebook_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        likes_data = data.get("likes", {}).get("summary", {})
                        comments_data = data.get("comments", {}).get("summary", {})
                        
                        return {
                            "likes": likes_data.get("total_count", 0),
                            "comments": comments_data.get("total_count", 0),
                            "shares": data.get("shares", {}).get("count", 0),
                            "timestamp": data.get("created_time")
                        }
        except Exception as e:
            logger.error(f"Facebook metrics error: {str(e)}")
        
        return {}
    
    async def _generate_insights(
        self,
        metrics: List[Dict],
        total_engagement: Dict[str, int]
    ) -> Dict[str, Any]:
        """Use LLM to generate insights and recommendations."""
        prompt = f"""
        Analyze these social media engagement metrics:
        
        Total Engagement:
        - Likes: {total_engagement['likes']}
        - Comments: {total_engagement['comments']}
        - Shares: {total_engagement['shares']}
        - Views: {total_engagement['views']}
        
        Individual Post Metrics:
        {metrics}
        
        Provide:
        1. Key insights (top 3-5 observations)
        2. Best performing content types
        3. Optimal posting times based on engagement
        4. Recommendations for improving engagement
        5. Content strategy suggestions
        
        Return JSON with:
        - insights (list of strings)
        - best_performing_types (list)
        - optimal_times (list)
        - recommendations (list of strings)
        - strategy_suggestions (list of strings)
        """
        
        content = await self._get_completion(prompt)
        
        import json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(content)
        except:
            return {
                "insights": ["Analyze metrics to identify patterns"],
                "recommendations": ["Continue monitoring engagement", "A/B test different content types"]
            }

