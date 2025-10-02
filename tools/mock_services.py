"""Mock services for testing without external API dependencies."""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

from models import NewsArticle, StockData, SentimentScore


# Helper functions that can be called directly
async def fetch_mock_manager_approval(recommendations_summary: str) -> Dict[str, Any]:
    """Mock manager approval process for testing (helper function)."""
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    # Random approval decision (80% approval rate)
    approved = random.random() > 0.2
    
    responses = {
        True: [
            "Approved. These recommendations look solid.",
            "Good analysis. Proceed with these recommendations.",
            "Approved. The risk assessment seems appropriate.",
            "These picks align with our strategy. Approved."
        ],
        False: [
            "I need more analysis on the risk factors.",
            "These picks seem too aggressive for current market conditions.",
            "Please provide additional market research before proceeding.",
            "The timing doesn't feel right. Let's revisit next week."
        ]
    }
    
    return {
        "type": "mock_approval",
        "approved": approved,
        "manager_response": random.choice(responses[approved]),
        "method": "mock_approval",
        "timestamp": datetime.now().isoformat(),
        "processing_time": "1.2 seconds",
        "note": "This is a mock approval for demonstration purposes",
        "source": "mock_data"
    }


async def get_mock_financial_news(query: str = "stock market", max_articles: int = 10) -> str:
    """
    Generate mock financial news articles for testing.
    
    Args:
        query: Search query for news
        max_articles: Maximum number of articles to generate
        
    Returns:
        JSON string with mock news articles
    """
    mock_headlines = [
        "Tech Giants Report Strong Q4 Earnings, Stocks Surge",
        "Federal Reserve Signals Potential Rate Cut Next Quarter",
        "Renewable Energy Sector Sees Record Investment Growth",
        "Cryptocurrency Market Stabilizes After Recent Volatility",
        "Healthcare Stocks Rally on Breakthrough Drug Approvals",
        "Supply Chain Disruptions Impact Manufacturing Sector",
        "Banking Sector Outperforms Market Expectations",
        "AI and Machine Learning Stocks Gain Momentum",
        "Energy Prices Fluctuate Amid Global Economic Uncertainty",
        "Consumer Spending Data Shows Resilient Economic Growth",
        "International Trade Tensions Affect Market Sentiment",
        "Emerging Markets Show Signs of Recovery",
        "Technology IPOs Generate Strong Investor Interest",
        "Pharmaceutical Companies Lead Healthcare Innovation",
        "Green Energy Transition Creates Investment Opportunities"
    ]
    
    sources = ["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal", "MarketWatch", "CNBC"]
    
    articles = []
    base_time = datetime.now()
    
    for i in range(min(max_articles, len(mock_headlines))):
        # Create realistic published dates
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        published_date = base_time - timedelta(days=days_ago, hours=hours_ago)
        
        # Generate realistic snippets
        snippets = [
            "Market analysts report optimistic outlook following strong quarterly results...",
            "Economic indicators suggest continued growth despite global uncertainties...",
            "Industry experts predict significant developments in the coming months...",
            "Investors respond positively to recent corporate announcements...",
            "Regulatory changes may impact sector performance in the near term...",
            "Consumer confidence remains strong amid economic headwinds...",
            "Technical analysis suggests potential market movements ahead...",
            "Company fundamentals support current market valuations...",
            "Geopolitical factors continue to influence trading patterns...",
            "Earnings reports exceed analyst expectations across multiple sectors..."
        ]
        
        article = NewsArticle(
            title=mock_headlines[i],
            url=f"https://example.com/news/{i+1}",
            source=random.choice(sources),
            published_date=published_date,
            snippet=random.choice(snippets)
        )
        
        articles.append(article)
    
    result = {
        "type": "mock_news",
        "query": query,
        "articles": [article.dict() for article in articles],
        "count": len(articles),
        "source": "mock_data"
    }
    
    return json.dumps(result, default=str)


async def get_mock_stock_data(symbol: str) -> str:
    """
    Generate mock stock data for a given symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
        
    Returns:
        JSON string with mock stock data
    """
    # Common stock symbols with realistic data
    stock_database = {
        "AAPL": {"name": "Apple Inc.", "base_price": 175.0, "volatility": 0.02},
        "GOOGL": {"name": "Alphabet Inc.", "base_price": 2850.0, "volatility": 0.025},
        "MSFT": {"name": "Microsoft Corporation", "base_price": 420.0, "volatility": 0.018},
        "TSLA": {"name": "Tesla Inc.", "base_price": 245.0, "volatility": 0.04},
        "NVDA": {"name": "NVIDIA Corporation", "base_price": 890.0, "volatility": 0.035},
        "AMZN": {"name": "Amazon.com Inc.", "base_price": 3200.0, "volatility": 0.022},
        "META": {"name": "Meta Platforms Inc.", "base_price": 485.0, "volatility": 0.03},
        "NFLX": {"name": "Netflix Inc.", "base_price": 650.0, "volatility": 0.028},
        "AMD": {"name": "Advanced Micro Devices", "base_price": 180.0, "volatility": 0.032},
        "CRM": {"name": "Salesforce Inc.", "base_price": 290.0, "volatility": 0.025}
    }
    
    symbol_upper = symbol.upper()
    if symbol_upper in stock_database:
        stock_info = stock_database[symbol_upper]
    else:
        # Generate data for unknown symbols
        stock_info = {
            "name": f"{symbol_upper} Corporation",
            "base_price": random.uniform(50, 500),
            "volatility": random.uniform(0.015, 0.04)
        }
    
    # Generate realistic price movement
    base_price = stock_info["base_price"]
    volatility = stock_info["volatility"]
    
    # Random price change within realistic bounds
    change_percent = random.uniform(-volatility * 100, volatility * 100)
    change_amount = base_price * (change_percent / 100)
    current_price = base_price + change_amount
    
    # Generate volume (millions)
    volume = random.randint(1000000, 50000000)
    
    # Estimate market cap (billions)
    shares_outstanding = random.uniform(1, 10) * 1000000000  # 1-10 billion shares
    market_cap = current_price * shares_outstanding
    
    stock_data = StockData(
        symbol=symbol_upper,
        name=stock_info["name"],
        current_price=round(current_price, 2),
        change=round(change_amount, 2),
        change_percent=round(change_percent, 2),
        volume=volume,
        market_cap=round(market_cap / 1000000000, 2)  # In billions
    )
    
    result = {
        "type": "mock_stock",
        "symbol": symbol,
        "data": stock_data.dict(),
        "source": "mock_data"
    }
    
    return json.dumps(result)