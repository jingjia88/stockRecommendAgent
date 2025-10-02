"""News Analyst Agent for fetching and analyzing financial news."""

import logging
from typing import List, Dict, Any
import json
from agno.agent import Agent
from models import NewsArticle, AgentAnalysis, SentimentScore
from tools.yfinance_tool import fetch_financial_news
from tools.sentiment_analyzer import fetch_articles_sentiment
from tools.mock_services import get_mock_financial_news
from config import settings

logger = logging.getLogger(__name__)


class NewsAnalystAgent(Agent):
    """Agent specialized in analyzing financial news and market sentiment."""
    
    def __init__(self):
        super().__init__(
            name="NewsAnalyst",
            instructions="""You are an expert financial news analyst with years of experience in 
            market sentiment analysis. Your goal is to analyze current financial news and determine 
            market sentiment to inform stock recommendations. You excel at identifying key market 
            trends from news sources and determining how current events might impact stock performance. 
            You provide clear, actionable insights based on comprehensive news analysis."""
        )
    
    async def analyze_market_news(self, query: str = "stock market news") -> Dict[str, Any]:
        """
        Fetch and analyze current market news.
        
        Args:
            query: News search query
            
        Returns:
            Dictionary with news analysis results
        """
        try:
            logger.info(f"Starting news analysis for query: {query}")
            # Fetch news articles using Yahoo Finance helper function
            news_result = await fetch_financial_news(query, settings.max_news_articles)
            articles_data = news_result.get("articles", [])
            
            # If no articles found, fallback to mock data
            if not articles_data and "error" in news_result:
                logger.warning(f"Yahoo Finance failed: {news_result['error']}, using mock data")
                mock_result_json = await get_mock_financial_news(query, settings.max_news_articles)
                mock_result = json.loads(mock_result_json)
                articles_data = mock_result.get("articles", [])
                
            logger.info(f"Retrieved {len(articles_data)} articles")
            
            # Convert to NewsArticle objects
            articles = [NewsArticle(**article) for article in articles_data]
            
            if not articles:
                logger.warning("No articles found for analysis")
                return {
                    "articles": [],
                    "sentiment_analysis": None,
                    "market_summary": "No news articles found for analysis.",
                    "confidence": 0.0
                }
            
            # Perform sentiment analysis
            logger.info("Performing sentiment analysis on articles")
            sentiment_result = fetch_articles_sentiment(articles_data)
            logger.info("Sentiment analysis completed")
            
            sentiment_analysis = sentiment_result
            market_summary = sentiment_result.get("market_summary", "")
            
            # Generate comprehensive analysis
            analysis_summary = self._generate_analysis_summary(
                articles, sentiment_analysis, market_summary
            )
            
            return {
                "articles": articles_data,
                "sentiment_analysis": sentiment_analysis,
                "market_summary": market_summary,
                "analysis_summary": analysis_summary,
                "confidence": self._calculate_confidence(sentiment_analysis),
                "article_count": len(articles),
                "news_sources": list(set(article.source for article in articles))
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze market news: {str(e)}", exc_info=True)
            return {
                "error": f"Failed to analyze market news: {str(e)}",
                "articles": [],
                "sentiment_analysis": None,
                "confidence": 0.0
            }
    
    def _generate_analysis_summary(self, articles: List[NewsArticle], 
                                 sentiment_analysis: Dict[str, Any], 
                                 market_summary: str) -> str:
        """Generate a comprehensive analysis summary."""
        
        if not sentiment_analysis:
            return "Unable to generate analysis due to insufficient data."
        
        overall_sentiment = sentiment_analysis.get("overall_sentiment", {})
        summary_stats = sentiment_analysis.get("summary", {})
        
        compound_score = overall_sentiment.get("compound", 0.0)
        positive_count = summary_stats.get("positive_count", 0)
        negative_count = summary_stats.get("negative_count", 0)
        neutral_count = summary_stats.get("neutral_count", 0)
        total_articles = summary_stats.get("total_articles", 0)
        
        analysis = f"""
📰 NEWS ANALYSIS REPORT

📊 Sentiment Overview:
• Overall Market Sentiment: {self._get_sentiment_label(compound_score)} (score: {compound_score:.3f})
• Article Breakdown: {positive_count} positive, {negative_count} negative, {neutral_count} neutral
• Total Articles Analyzed: {total_articles}

🔍 Key Insights:
{market_summary}

📈 Investment Implications:
"""
        
        if compound_score > 0.2:
            analysis += """• Strong positive sentiment suggests favorable market conditions
• Consider growth-oriented investment strategies
• Monitor for potential overvaluation in high-momentum stocks"""
        elif compound_score > 0.05:
            analysis += """• Moderately positive sentiment indicates cautious optimism
• Balanced investment approach recommended
• Focus on fundamentally strong companies"""
        elif compound_score < -0.2:
            analysis += """• Strong negative sentiment suggests challenging market conditions
• Consider defensive investment strategies
• Look for quality stocks at discounted valuations"""
        elif compound_score < -0.05:
            analysis += """• Moderately negative sentiment indicates market uncertainty
• Exercise increased caution in stock selection
• Prioritize companies with strong balance sheets"""
        else:
            analysis += """• Neutral sentiment suggests mixed market conditions
• Stock-picking based on individual company fundamentals
• Consider diversified portfolio approach"""
        
        # Add trending topics if available
        if articles:
            # Simple keyword extraction from headlines
            all_headlines = " ".join([article.title for article in articles])
            trending_keywords = self._extract_trending_topics(all_headlines)
            if trending_keywords:
                analysis += f"\n\n🔥 Trending Topics: {', '.join(trending_keywords[:5])}"
        
        return analysis.strip()
    
    def _get_sentiment_label(self, compound_score: float) -> str:
        """Convert compound score to human-readable label."""
        if compound_score >= 0.5:
            return "Very Positive"
        elif compound_score >= 0.1:
            return "Positive"
        elif compound_score > -0.1:
            return "Neutral"
        elif compound_score > -0.5:
            return "Negative"
        else:
            return "Very Negative"
    
    def _extract_trending_topics(self, text: str) -> List[str]:
        """Extract trending topics from news headlines."""
        # Simple keyword extraction (in a real implementation, you might use NLP)
        keywords = [
            "earnings", "fed", "inflation", "tech", "energy", "healthcare", 
            "banking", "crypto", "ai", "electric", "climate", "supply chain",
            "employment", "gdp", "trade", "merger", "acquisition", "ipo"
        ]
        
        text_lower = text.lower()
        trending = []
        
        for keyword in keywords:
            if keyword in text_lower:
                count = text_lower.count(keyword)
                if count >= 2:  # Appears in multiple headlines
                    trending.append(keyword.title())
        
        return trending[:5]  # Return top 5
    
    def _calculate_confidence(self, sentiment_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on analysis quality."""
        if not sentiment_analysis:
            return 0.0
        
        summary = sentiment_analysis.get("summary", {})
        total_articles = summary.get("total_articles", 0)
        
        # Base confidence on number of articles and sentiment clarity
        if total_articles == 0:
            return 0.0
        elif total_articles < 3:
            return 0.3
        elif total_articles < 7:
            return 0.6
        elif total_articles < 10:
            return 0.8
        else:
            return 0.9
    
    async def get_sector_news(self, sector: str) -> Dict[str, Any]:
        """Get news specific to a market sector."""
        sector_queries = {
            "technology": "technology stocks tech earnings",
            "healthcare": "healthcare pharma biotech stocks", 
            "financial": "banking financial services stocks",
            "energy": "energy oil gas renewable stocks",
            "consumer": "consumer goods retail stocks",
            "industrial": "industrial manufacturing stocks"
        }
        
        query = sector_queries.get(sector.lower(), f"{sector} stocks")
        return await self.analyze_market_news(query)
    
    async def run(self, task: str, **kwargs) -> AgentAnalysis:
        """
        Main execution method for the News Analyst Agent.
        
        Args:
            task: Task description
            **kwargs: Task-specific parameters
            
        Returns:
            AgentAnalysis with news analysis results
        """
        try:
            query = kwargs.get("query", "stock market news")
            sector = kwargs.get("sector", None)
            
            if sector:
                analysis_result = await self.get_sector_news(sector)
            else:
                analysis_result = await self.analyze_market_news(query)
            
            # Format analysis for team consumption
            if "error" in analysis_result:
                analysis_text = f"News analysis failed: {analysis_result['error']}"
                confidence = 0.0
            else:
                analysis_text = analysis_result.get("analysis_summary", "No analysis available")
                confidence = analysis_result.get("confidence", 0.0)
            
            return AgentAnalysis(
                agent_name=self.name,
                analysis=analysis_text,
                confidence=confidence,
                data=analysis_result
            )
            
        except Exception as e:
            return AgentAnalysis(
                agent_name=self.name,
                analysis=f"News analysis failed with error: {str(e)}",
                confidence=0.0,
                data={"error": str(e)}
            )
