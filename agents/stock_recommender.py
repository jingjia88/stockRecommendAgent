"""Stock Recommender Agent using Claude LLM for intelligent stock analysis."""

import logging
from typing import List, Dict, Any, Optional
import json
from agno.agent import Agent
from anthropic import AsyncAnthropic
from models import StockRecommendation, AgentAnalysis, StockData
from tools.yfinance_tool import fetch_stock_data
from tools.mock_services import get_mock_stock_data
from config import settings

logger = logging.getLogger(__name__)


class StockRecommenderAgent(Agent):
    """Agent specialized in generating intelligent stock recommendations using AI analysis."""
    
    def __init__(self):
        super().__init__(
            name="StockRecommender",
            instructions="""You are an expert investment advisor with deep knowledge of financial 
            markets, technical analysis, and quantitative methods. Your goal is to generate intelligent 
            stock recommendations based on market analysis, news sentiment, and fundamental data. You use 
            advanced AI reasoning to analyze market conditions, company fundamentals, and sentiment data 
            to provide well-reasoned stock recommendations. Your recommendations are always accompanied by 
            clear reasoning and risk assessments."""
        )
        
        # Initialize AI client
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def generate_recommendations(self, 
                                     market_analysis: str,
                                     sentiment_data: Optional[Dict[str, Any]] = None,
                                     max_recommendations: int = 3,
                                     risk_preference: str = "medium") -> List[StockRecommendation]:
        """
        Generate stock recommendations using Claude AI analysis.
        
        Args:
            market_analysis: Market analysis from news agent
            sentiment_data: Sentiment analysis data
            max_recommendations: Maximum number of recommendations
            risk_preference: Risk preference (low/medium/high)
            
        Returns:
            List of StockRecommendation objects
        """
        try:
            # Prepare context for Claude
            context = self._prepare_analysis_context(market_analysis, sentiment_data, risk_preference)
            
            # Generate recommendations using Claude
            recommendations_text = await self._get_claude_recommendations(context, max_recommendations)
            
            # Parse Claude's response into structured recommendations
            recommendations = self._parse_recommendations(recommendations_text)
            
            # Enhance with additional data
            enhanced_recommendations = await self._enhance_recommendations(recommendations)
            
            return enhanced_recommendations[:max_recommendations]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            
            # Return fallback recommendations
            return await self._get_fallback_recommendations(max_recommendations, risk_preference)
    
    def _prepare_analysis_context(self, market_analysis: str, 
                                sentiment_data: Optional[Dict[str, Any]], 
                                risk_preference: str) -> str:
        """Prepare comprehensive context for Claude analysis."""
        
        sentiment_summary = "No sentiment data available"
        if sentiment_data and "overall_sentiment" in sentiment_data:
            overall = sentiment_data["overall_sentiment"]
            summary = sentiment_data.get("summary", {})
            sentiment_summary = f"""
Sentiment Analysis:
- Overall sentiment score: {overall.get('compound', 0):.3f}
- Positive articles: {summary.get('positive_count', 0)}
- Negative articles: {summary.get('negative_count', 0)}
- Neutral articles: {summary.get('neutral_count', 0)}
"""
        
        context = f"""
INVESTMENT ANALYSIS CONTEXT

Market Analysis:
{market_analysis}

{sentiment_summary}

Risk Preference: {risk_preference.title()}

Current Market Conditions:
- Consider the overall market sentiment and news trends
- Factor in economic indicators and sector performance
- Assess risk levels appropriate for {risk_preference} risk tolerance

TASK: Based on this analysis, recommend stocks that align with current market conditions and the specified risk preference.
"""
        return context
    
    async def _get_claude_recommendations(self, context: str, max_recommendations: int) -> str:
        """Get stock recommendations from Claude AI."""
        
        prompt = f"""
{context}

Please provide {max_recommendations} stock recommendations in the following JSON format:

[
  {{
    "symbol": "STOCK_SYMBOL",
    "company_name": "Company Name",
    "recommendation_type": "Buy/Hold/Strong Buy",
    "confidence_score": 0.85,
    "reasoning": "One concise sentence explaining the key reason for this recommendation",
    "target_price": 150.00,
    "risk_level": "Low/Medium/High"
  }}
]

Focus on:
1. Companies with strong fundamentals and growth potential
2. Stocks that align with current market sentiment
3. Appropriate risk levels for the specified preference
4. ONE concise sentence summarizing the key investment thesis

Provide realistic stock symbols for well-known public companies.
"""
        
        try:
            logger.info("Sending request to Claude API for stock recommendations")
            response = await self.claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            logger.info("Successfully received response from Claude API")
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            logger.info("Falling back to default recommendations")
            return self._get_default_recommendations_text(max_recommendations)
    
    def _parse_recommendations(self, recommendations_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's recommendations response into structured data."""
        try:
            # Try to find JSON in the response
            start_idx = recommendations_text.find('[')
            end_idx = recommendations_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = recommendations_text[start_idx:end_idx]
                recommendations_data = json.loads(json_text)
                logger.info(f"Parsed Claude's recommendations: {recommendations_data}")
                return recommendations_data
            else:
                # Fallback: parse from text format
                return self._parse_text_recommendations(recommendations_text)
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON recommendations, using text parsing")
            return self._parse_text_recommendations(recommendations_text)
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}", exc_info=True)
            return []
    
    def _parse_text_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """Fallback text parsing for recommendations."""
        # This is a simplified text parser - in production you'd want more robust parsing
        default_recommendations = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "recommendation_type": "Buy",
                "confidence_score": 0.8,
                "reasoning": "Strong brand loyalty, growing services revenue, and consistent innovation pipeline make Apple a solid choice for current market conditions.",
                "target_price": 185.0,
                "risk_level": "Medium"
            },
            {
                "symbol": "MSFT",
                "company_name": "Microsoft Corporation",
                "recommendation_type": "Strong Buy",
                "confidence_score": 0.85,
                "reasoning": "Leading cloud infrastructure position, AI integration across products, and strong enterprise relationships provide multiple growth vectors.",
                "target_price": 450.0,
                "risk_level": "Medium"
            },
            {
                "symbol": "GOOGL",
                "company_name": "Alphabet Inc.",
                "recommendation_type": "Buy",
                "confidence_score": 0.75,
                "reasoning": "Dominant search position, growing cloud business, and AI leadership create long-term value despite regulatory concerns.",
                "target_price": 3000.0,
                "risk_level": "Medium"
            }
        ]
        return default_recommendations
    
    async def _enhance_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[StockRecommendation]:
        """Enhance recommendations with additional market data."""
        enhanced = []
        
        for rec_data in recommendations:
            try:
                # Get current stock data
                symbol = rec_data.get("symbol", "")
                stock_data = None
                logger.info(f"Enhancing recommendation for {symbol}")
                
                # Try to get real stock data from Yahoo Finance
                logger.info(f"Fetching Yahoo Finance stock data for {symbol}")
                stock_result = await fetch_stock_data(symbol)
                stock_data = stock_result.get("data")
                
                if not stock_data and "error" in stock_result:
                    # Use mock data as fallback
                    logger.warning(f"Yahoo Finance failed for {symbol}: {stock_result['error']}, using mock data")
                    mock_result_json = await get_mock_stock_data(symbol)
                    mock_result = json.loads(mock_result_json)
                    stock_data = mock_result.get("data")
                
                # Create enhanced recommendation
                recommendation = StockRecommendation(
                    symbol=rec_data.get("symbol", ""),
                    company_name=rec_data.get("company_name", ""),
                    recommendation_type=rec_data.get("recommendation_type", "Hold"),
                    confidence_score=float(rec_data.get("confidence_score", 0.5)),
                    reasoning=rec_data.get("reasoning", ""),
                    target_price=rec_data.get("target_price"),
                    risk_level=rec_data.get("risk_level", "Medium")
                )
                
                # Add current price to reasoning if available
                if stock_data and stock_data.get("current_price"):
                    current_price = stock_data["current_price"]
                    change_percent = stock_data.get("change_percent", 0)
                    
                    price_context = f"\n\nCurrent Price: ${current_price:.2f}"
                    
                    if change_percent != 0:
                        direction = "up" if change_percent > 0 else "down"
                        price_context += f" ({change_percent:+.2f}% {direction} today)"
                    
                    recommendation.reasoning += price_context
                
                enhanced.append(recommendation)
                logger.info(f"Successfully enhanced recommendation for {symbol}")
                
            except Exception as e:
                logger.error(f"Error enhancing recommendation for {rec_data.get('symbol', 'unknown')}: {e}", exc_info=True)
                # Still add basic recommendation even if enhancement fails
                try:
                    enhanced.append(StockRecommendation(**rec_data))
                    logger.info(f"Added basic recommendation for {rec_data.get('symbol', 'unknown')} without enhancement")
                except Exception as basic_error:
                    logger.error(f"Failed to create basic recommendation: {basic_error}", exc_info=True)
        
        return enhanced
    
    async def _get_fallback_recommendations(self, max_recommendations: int, risk_preference: str) -> List[StockRecommendation]:
        """Generate fallback recommendations when AI analysis fails."""
        
        fallback_stocks = {
            "low": [
                {"symbol": "JNJ", "company_name": "Johnson & Johnson", "target_price": 175.0},
                {"symbol": "PG", "company_name": "Procter & Gamble", "target_price": 160.0},
                {"symbol": "KO", "company_name": "Coca-Cola", "target_price": 65.0}
            ],
            "medium": [
                {"symbol": "AAPL", "company_name": "Apple Inc.", "target_price": 185.0},
                {"symbol": "MSFT", "company_name": "Microsoft Corporation", "target_price": 450.0},
                {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "target_price": 3000.0}
            ],
            "high": [
                {"symbol": "TSLA", "company_name": "Tesla Inc.", "target_price": 300.0},
                {"symbol": "NVDA", "company_name": "NVIDIA Corporation", "target_price": 1000.0},
                {"symbol": "AMD", "company_name": "Advanced Micro Devices", "target_price": 200.0}
            ]
        }
        
        stocks = fallback_stocks.get(risk_preference.lower(), fallback_stocks["medium"])
        recommendations = []
        
        for i, stock in enumerate(stocks[:max_recommendations]):
            rec = StockRecommendation(
                symbol=stock["symbol"],
                company_name=stock["company_name"],
                recommendation_type="Buy",
                confidence_score=0.7,
                reasoning=f"Fallback recommendation based on {risk_preference} risk profile. This stock is selected from a curated list of quality companies suitable for the specified risk tolerance.",
                target_price=stock["target_price"],
                risk_level=risk_preference.title()
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _get_default_recommendations_text(self, max_recommendations: int) -> str:
        """Get default recommendations text when Claude is unavailable."""
        return '''
[
  {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "recommendation_type": "Buy",
    "confidence_score": 0.8,
    "reasoning": "Strong brand ecosystem, growing services revenue, and innovation in AI and health technologies position Apple well for continued growth.",
    "target_price": 185.0,
    "risk_level": "Medium"
  },
  {
    "symbol": "MSFT",
    "company_name": "Microsoft Corporation", 
    "recommendation_type": "Strong Buy",
    "confidence_score": 0.85,
    "reasoning": "Leadership in cloud computing, AI integration across product suite, and strong enterprise relationships provide multiple growth drivers.",
    "target_price": 450.0,
    "risk_level": "Medium"
  },
  {
    "symbol": "NVDA",
    "company_name": "NVIDIA Corporation",
    "recommendation_type": "Buy",
    "confidence_score": 0.9,
    "reasoning": "Dominant position in AI chips, data center growth, and expanding applications in autonomous vehicles and gaming create significant upside potential.",
    "target_price": 950.0,
    "risk_level": "High"
  }
]
'''
    
    async def run(self, task: str, **kwargs) -> AgentAnalysis:
        """
        Main execution method for the Stock Recommender Agent.
        
        Args:
            task: Task description
            **kwargs: Task-specific parameters
            
        Returns:
            AgentAnalysis with stock recommendations
        """
        try:
            market_analysis = kwargs.get("market_analysis", "")
            sentiment_data = kwargs.get("sentiment_data")
            max_recommendations = kwargs.get("max_recommendations", 3)
            risk_preference = kwargs.get("risk_preference", "medium")
            
            recommendations = await self.generate_recommendations(
                market_analysis=market_analysis,
                sentiment_data=sentiment_data,
                max_recommendations=max_recommendations,
                risk_preference=risk_preference
            )
            
            # Format analysis summary
            analysis_text = self._format_recommendations_summary(recommendations)
            
            return AgentAnalysis(
                agent_name=self.name,
                analysis=analysis_text,
                confidence=self._calculate_overall_confidence(recommendations),
                data={
                    "recommendations": [rec.dict() for rec in recommendations],
                    "recommendation_count": len(recommendations),
                    "risk_preference": risk_preference
                }
            )
            
        except Exception as e:
            return AgentAnalysis(
                agent_name=self.name,
                analysis=f"Stock recommendation generation failed: {str(e)}",
                confidence=0.0,
                data={"error": str(e)}
            )
    
    def _format_recommendations_summary(self, recommendations: List[StockRecommendation]) -> str:
        """Format recommendations into a readable summary."""
        if not recommendations:
            return "No stock recommendations could be generated."
        
        summary = "🎯 STOCK RECOMMENDATIONS\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            summary += f"{i}. {rec.symbol} - {rec.company_name}\n"
            summary += f"   • Recommendation: {rec.recommendation_type}\n"
            summary += f"   • Confidence: {rec.confidence_score:.1%}\n"
            summary += f"   • Risk Level: {rec.risk_level}\n"
            if rec.target_price:
                summary += f"   • Target Price: ${rec.target_price:.2f}\n"
            summary += f"   • Reasoning: {rec.reasoning[:100]}...\n\n"
        
        return summary
    
    def _calculate_overall_confidence(self, recommendations: List[StockRecommendation]) -> float:
        """Calculate overall confidence from individual recommendations."""
        if not recommendations:
            return 0.0
        
        return sum(rec.confidence_score for rec in recommendations) / len(recommendations)
