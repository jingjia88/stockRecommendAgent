"""Tools package for API integrations and services."""

from .yfinance_tool import fetch_financial_news, fetch_stock_data
from .sentiment_analyzer import fetch_articles_sentiment
from .voice_services import request_manager_approval
from .mock_services import (
    get_mock_financial_news,
    get_mock_stock_data,
    fetch_mock_manager_approval
)

__all__ = [
    # Yahoo Finance tools
    "fetch_financial_news",
    "fetch_stock_data",
    
    # Sentiment analysis tools
    "fetch_articles_sentiment",
    
    # Voice service tools
    "request_manager_approval",
    
    # Mock service tools (for fallback/testing)
    "get_mock_financial_news",
    "get_mock_stock_data", 
    "fetch_mock_manager_approval"
]
