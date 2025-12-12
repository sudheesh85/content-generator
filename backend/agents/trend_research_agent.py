"""
Trend Research Agent
Fetches real-time trends from Google Trends and other sources.
"""
from typing import Any, Dict, List
try:
    from backend.agents.base import BaseAgent
except ModuleNotFoundError:
    from agents.base import BaseAgent
import json
import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

class TrendResearchAgent(BaseAgent):
    """Agent that gathers real-time trends for content suggestions."""
    
    def __init__(self):
        super().__init__(
            name="TrendResearchAgent",
            instructions="You are a Trend Analyst. Identify trending topics and suggest content opportunities."
        )
        self.google_trends_enabled = os.getenv("ENABLE_GOOGLE_TRENDS", "false").lower() == "true"
    
    async def process(self, context: Any) -> Dict[str, Any]:
        """
        Research current trends based on strategy context.
        
        Returns:
            Dict with trending_topics, hashtags, trending_keywords, content_suggestions
        """
        strategy = context.get("strategy", {})
        keywords = self._extract_keywords(strategy)
        
        # Gather trends from multiple sources
        trends_data = {
            "trending_topics": [],
            "trending_hashtags": [],
            "trending_keywords": [],
            "content_suggestions": [],
            "trend_sources": []
        }
        
        # Google Trends
        if self.google_trends_enabled:
            try:
                google_trends = await self._get_google_trends(keywords)
                trends_data["trending_keywords"].extend(google_trends.get("keywords", []))
                trends_data["trend_sources"].append("google_trends")
            except Exception as e:
                logger.warning(f"Google Trends fetch failed: {str(e)}")
        
        
        # Use LLM to analyze trends and suggest content
        prompt = f"""
        Strategy Context: {json.dumps(strategy, indent=2)}
        Current Trends: {json.dumps(trends_data, indent=2)}
        
        Analyze these trends and suggest:
        1. Top 5 trending topics relevant to the strategy
        2. Trending hashtags to use
        3. Content ideas that capitalize on these trends
        4. Best posting times based on trend activity
        
        Return JSON with:
        - top_trending_topics (list of 5)
        - recommended_hashtags (list)
        - trend_based_content_ideas (list of 3-5 ideas)
        - optimal_posting_times (list)
        """
        
        content = await self._get_completion(prompt)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(content)
        
        # Merge trend data with LLM analysis
        trends_data.update(analysis)
        
        return trends_data
    
    def _extract_keywords(self, strategy: Dict) -> List[str]:
        """Extract keywords from strategy for trend searching."""
        keywords = []
        if isinstance(strategy, dict):
            keywords.extend(strategy.get("pillars", []))
            # Extract keywords from post types
            post_types = strategy.get("post_types_by_channel", {})
            for channel, types in post_types.items():
                keywords.append(channel.lower())
                keywords.extend([t.lower() for t in types])
        return list(set(keywords))[:5]  # Limit to 5 keywords
    
    async def _get_google_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """Fetch trends from Google Trends API."""
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='en-US', tz=360)
            
            # Build payload for up to 5 keywords
            keywords_to_search = keywords[:5]
            pytrends.build_payload(keywords_to_search, cat=0, timeframe='today 3-m', geo='', gprop='')
            
            # Get related queries
            related_queries = pytrends.related_queries()
            
            # Get trending searches
            trending_searches = pytrends.trending_searches(pn='united_states')
            
            return {
                "keywords": keywords_to_search,
                "related_queries": related_queries,
                "trending_searches": trending_searches.head(10).values.tolist() if trending_searches is not None else []
            }
        except Exception as e:
            logger.error(f"Google Trends error: {str(e)}")
            return {"keywords": keywords, "error": str(e)}
    
