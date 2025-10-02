"""Pydantic models for the Stock Recommendation Agent."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SentimentScore(BaseModel):
    """Sentiment analysis result."""
    compound: float = Field(..., description="Overall sentiment compound score (-1 to 1)")
    positive: float = Field(..., description="Positive sentiment score")
    negative: float = Field(..., description="Negative sentiment score")
    neutral: float = Field(..., description="Neutral sentiment score")


class NewsArticle(BaseModel):
    """News article data."""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="News source")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    snippet: Optional[str] = Field(None, description="Article snippet")
    sentiment: Optional[SentimentScore] = Field(None, description="Sentiment analysis")


class StockData(BaseModel):
    """Stock market data."""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    current_price: Optional[float] = Field(None, description="Current stock price")
    change: Optional[float] = Field(None, description="Price change")
    change_percent: Optional[float] = Field(None, description="Price change percentage")
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")


class StockRecommendation(BaseModel):
    """Individual stock recommendation."""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    recommendation_type: str = Field(..., description="Buy/Hold/Sell recommendation")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    reasoning: str = Field(..., description="Detailed reasoning for recommendation")
    target_price: Optional[float] = Field(None, description="Target price")
    risk_level: str = Field("Medium", description="Risk level (Low/Medium/High)")


class ApprovalStatus(str, Enum):
    """Approval status for recommendations."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ManagerApproval(BaseModel):
    """Manager approval result."""
    status: ApprovalStatus = Field(..., description="Approval status")
    manager_response: Optional[str] = Field(None, description="Manager's response")
    timestamp: datetime = Field(default_factory=datetime.now, description="Approval timestamp")
    notes: Optional[str] = Field(None, description="Additional notes")
    approval_method: Optional[str] = Field(None, description="Method used for approval (e.g., phone_call, mock)")
    raw_response: Optional[str] = Field(None, description="Raw response from manager")
    call_sid: Optional[str] = Field(None, description="Twilio call SID if applicable")
    recording_url: Optional[str] = Field(None, description="Recording URL if applicable")


class StockRecommendationRequest(BaseModel):
    """Request for stock recommendations."""
    query: str = Field(..., description="User query for stock recommendations")
    max_recommendations: int = Field(3, description="Maximum number of recommendations")
    risk_preference: Optional[str] = Field("medium", description="Risk preference (low/medium/high)")
    include_approval: bool = Field(False, description="Whether to include manager approval")


class AgentAnalysis(BaseModel):
    """Analysis result from an individual agent."""
    agent_name: str = Field(..., description="Name of the agent")
    analysis: str = Field(..., description="Agent's analysis")
    confidence: float = Field(..., description="Confidence in analysis (0-1)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class StockRecommendationResponse(BaseModel):
    """Complete response with stock recommendations."""
    recommendations: List[StockRecommendation] = Field(..., description="List of stock recommendations")
    market_analysis: str = Field(..., description="Overall market analysis")
    news_sentiment: Optional[SentimentScore] = Field(None, description="Overall news sentiment")
    approval: Optional[ManagerApproval] = Field(None, description="Manager approval if requested")
    agent_analyses: List[AgentAnalysis] = Field(default_factory=list, description="Individual agent analyses")
    disclaimer: str = Field(
        "This is for demonstration purposes only and not financial advice. "
        "Please consult with a qualified financial advisor before making investment decisions.",
        description="Financial disclaimer"
    )
    humor_note: Optional[str] = Field(None, description="Light humor note")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class APIError(BaseModel):
    """API error response."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
