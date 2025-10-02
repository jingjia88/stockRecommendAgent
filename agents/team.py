"""Agno Team orchestration for the Stock Recommendation System."""

import logging
from typing import Dict, Any, List, Optional
from agno.team import Team
from agno.agent import Agent
from models import (
    StockRecommendationRequest, 
    StockRecommendationResponse, 
    StockRecommendation,
    AgentAnalysis,
    ManagerApproval
)
from .news_analyst import NewsAnalystAgent
from .stock_recommender import StockRecommenderAgent
from .approval_manager import ApprovalManagerAgent
import random

logger = logging.getLogger(__name__)


class StockRecommendationTeam:
    """Orchestrates the multi-agent stock recommendation workflow."""
    
    def __init__(self):
        # Initialize individual agents
        self.news_analyst = NewsAnalystAgent()
        self.stock_recommender = StockRecommenderAgent()
        self.approval_manager = ApprovalManagerAgent()
        
        # Create Agno team
        self.team = Team(
            name="Stock Recommendation Team",
            members=[
                self.news_analyst,
                self.stock_recommender,
                self.approval_manager
            ],
            instructions="""
            You are a collaborative team of AI agents working together to provide 
            intelligent stock recommendations. Each agent has specialized expertise:
            
            1. NewsAnalyst: Analyzes market news and sentiment
            2. StockRecommender: Generates AI-powered stock recommendations
            3. ApprovalManager: Handles approval workflow with manager oversight
            
            Work together to provide comprehensive, well-reasoned stock recommendations
            with proper risk assessment and managerial approval when required.
            """
        )
    
    async def process_recommendation_request(self, request: StockRecommendationRequest) -> StockRecommendationResponse:
        """
        Process a complete stock recommendation request through the agent workflow.
        
        Args:
            request: StockRecommendationRequest with user query and preferences
            
        Returns:
            StockRecommendationResponse with complete analysis and recommendations
        """
        try:
            agent_analyses = []
            
            # Phase 1: News Analysis
            logger.info("🔍 Starting news analysis...")
            try:
                news_analysis = await self.news_analyst.run(
                    task="Analyze current market news and sentiment",
                    query=request.query,
                    max_articles=10
                )
                agent_analyses.append(news_analysis)
                logger.info("✅ News analysis completed successfully")
            except Exception as e:
                logger.error(f"❌ News analysis failed: {str(e)}", exc_info=True)
                raise
            
            # Extract news data for next phases
            news_data = news_analysis.data
            market_analysis = news_analysis.analysis
            sentiment_data = news_data.get("sentiment_analysis") if news_data else None
            
            # Phase 2: Stock Recommendations
            logger.info("🎯 Generating stock recommendations...")
            try:
                stock_analysis = await self.stock_recommender.run(
                    task="Generate intelligent stock recommendations",
                    market_analysis=market_analysis,
                    sentiment_data=sentiment_data,
                    max_recommendations=request.max_recommendations,
                    risk_preference=request.risk_preference
                )
                agent_analyses.append(stock_analysis)
                logger.info("✅ Stock recommendations completed successfully")
            except Exception as e:
                logger.error(f"❌ Stock recommendations failed: {str(e)}", exc_info=True)
                raise
            
            # Extract recommendations
            recommendations_data = stock_analysis.data.get("recommendations", []) if stock_analysis.data else []
            recommendations = [StockRecommendation(**rec) for rec in recommendations_data]
            
            # Phase 3: Approval (if requested)
            approval = None
            if request.include_approval and recommendations:
                logger.info("📞 Requesting manager approval...")
                try:
                    approval_analysis = await self.approval_manager.run(
                        task="Request manager approval for recommendations",
                        recommendations=recommendations
                    )
                    agent_analyses.append(approval_analysis)
                    logger.info("✅ Manager approval process completed")
                    
                    # Extract approval data
                    approval_data = approval_analysis.data.get("approval") if approval_analysis.data else None
                    if approval_data:
                        approval = ManagerApproval(**approval_data)
                        logger.info(f"Approval status: {approval.status}")
                    else:
                        logger.warning("No approval data returned from approval manager")
                        
                except Exception as e:
                    logger.error(f"❌ Manager approval failed: {str(e)}", exc_info=True)
                    # Create a failure approval instead of raising
                    from models import ApprovalStatus
                    approval = ManagerApproval(
                        status=ApprovalStatus.REJECTED,
                        manager_response=f"Approval process failed: {str(e)}",
                        notes="System error during approval process"
                    )
            
            # Phase 4: Generate Final Response
            response = self._compile_final_response(
                recommendations=recommendations,
                market_analysis=market_analysis,
                sentiment_data=sentiment_data,
                approval=approval,
                agent_analyses=agent_analyses,
                request=request
            )
            
            logger.info("✅ Stock recommendation process completed!")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in recommendation process: {e}", exc_info=True)
            return self._create_error_response(str(e), request)
    
    def _compile_final_response(self, 
                              recommendations: List[StockRecommendation],
                              market_analysis: str,
                              sentiment_data: Optional[Dict[str, Any]],
                              approval: Optional[ManagerApproval],
                              agent_analyses: List[AgentAnalysis],
                              request: StockRecommendationRequest) -> StockRecommendationResponse:
        """Compile the final response from all agent analyses."""
        
        # Generate overall market analysis summary
        overall_analysis = self._generate_market_summary(market_analysis, sentiment_data)
        
        # Extract overall sentiment score
        overall_sentiment = None
        if sentiment_data and "overall_sentiment" in sentiment_data:
            from models import SentimentScore
            sentiment_dict = sentiment_data["overall_sentiment"]
            overall_sentiment = SentimentScore(**sentiment_dict)
        
        # Add a light humor note
        humor_note = self._generate_humor_note(recommendations)
        
        return StockRecommendationResponse(
            recommendations=recommendations,
            market_analysis=overall_analysis,
            news_sentiment=overall_sentiment,
            approval=approval,
            agent_analyses=agent_analyses,
            humor_note=humor_note
        )
    
    def _generate_market_summary(self, market_analysis: str, sentiment_data: Optional[Dict[str, Any]]) -> str:
        """Generate an overall market analysis summary."""
        
        summary = "📊 COMPREHENSIVE MARKET ANALYSIS\n\n"
        
        # Add sentiment overview if available
        if sentiment_data and "overall_sentiment" in sentiment_data:
            sentiment = sentiment_data["overall_sentiment"]
            compound = sentiment.get("compound", 0)
            
            if compound > 0.1:
                sentiment_desc = "positive"
                market_outlook = "favorable for growth-oriented investments"
            elif compound < -0.1:
                sentiment_desc = "negative"
                market_outlook = "suggesting caution and defensive positioning"
            else:
                sentiment_desc = "neutral"
                market_outlook = "indicating mixed signals and balanced approach needed"
            
            summary += f"Current market sentiment is {sentiment_desc} (score: {compound:.3f}), "
            summary += f"{market_outlook}.\n\n"
        
        # Add the detailed market analysis
        summary += market_analysis
        
        # Add concluding remarks
        summary += "\n\n🔍 INVESTMENT STRATEGY IMPLICATIONS:\n"
        summary += "• Consider diversification across sectors and risk levels\n"
        summary += "• Monitor market developments and adjust positions accordingly\n"
        summary += "• Maintain appropriate risk management and position sizing\n"
        summary += "• Review recommendations regularly as market conditions evolve"
        
        return summary
    
    def _generate_humor_note(self, recommendations: List[StockRecommendation]) -> str:
        """Generate a light humor note based on recommendations."""
        
        if not recommendations:
            return "Remember: The best investment advice is diversification... and maybe a good sense of humor! 😄"
        
        humor_options = [
            f"Remember: Past performance doesn't guarantee future results, but {recommendations[0].symbol} might just surprise you! 📈",
            "Investing is like dating - sometimes you win, sometimes you learn, but always keep your portfolio diversified! 💕",
            f"Fun fact: {recommendations[0].company_name} stock doesn't come with a crystal ball, but our AI did its best impression! 🔮",
            "Market tip: Bulls make money, bears make money, but pigs get slaughtered... so don't be greedy! 🐷",
            "Investment wisdom: Time in the market beats timing the market (but good research doesn't hurt)! ⏰",
            f"Breaking: Local AI claims {recommendations[0].symbol} is 'totally awesome' - more research pending! 🤖",
            "Remember: The only free lunch on Wall Street is diversification... and maybe our recommendations! 🍕",
            "Pro tip: If you understand everything in this report, you're probably ready to run a hedge fund! 🎓"
        ]
        
        return random.choice(humor_options)
    
    def _create_error_response(self, error_message: str, request: StockRecommendationRequest) -> StockRecommendationResponse:
        """Create an error response when the process fails."""
        
        from models import AgentAnalysis
        
        error_analysis = AgentAnalysis(
            agent_name="System",
            analysis=f"Stock recommendation process failed: {error_message}",
            confidence=0.0,
            data={"error": error_message}
        )
        
        return StockRecommendationResponse(
            recommendations=[],
            market_analysis=f"Unable to complete market analysis due to system error: {error_message}",
            agent_analyses=[error_analysis],
            humor_note="Sometimes even AI needs a coffee break! ☕ Please try again."
        )
    
    async def get_team_status(self) -> Dict[str, Any]:
        """Get the current status of all team agents."""
        
        return {
            "team_name": self.team.name,
            "agents": [
                {
                    "name": agent.name,
                    "role": agent.role,
                    "status": "active"
                }
                for agent in self.team.agents
            ],
            "total_agents": len(self.team.agents),
            "capabilities": [
                "Financial news analysis",
                "Market sentiment analysis", 
                "AI-powered stock recommendations",
                "Risk assessment",
                "Manager approval workflow",
                "Voice communication integration"
            ]
        }
    
    async def run_individual_agent(self, agent_name: str, task: str, **kwargs) -> AgentAnalysis:
        """
        Run an individual agent for testing or specific tasks.
        
        Args:
            agent_name: Name of the agent to run
            task: Task description
            **kwargs: Task-specific parameters
            
        Returns:
            AgentAnalysis from the specified agent
        """
        agent_map = {
            "NewsAnalyst": self.news_analyst,
            "StockRecommender": self.stock_recommender,
            "ApprovalManager": self.approval_manager
        }
        
        agent = agent_map.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        return await agent.run(task, **kwargs)
