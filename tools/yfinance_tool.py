"""Yahoo Finance API integration using yfinance for stock data and news."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import yfinance as yf
import pandas as pd

from agno.tools import tool
from models import NewsArticle, StockData

logger = logging.getLogger(__name__)


# Helper functions that can be called directly (not decorated with @tool)
async def fetch_financial_news(query: str = "stock market", max_articles: int = 10) -> Dict[str, Any]:
    """Helper function to fetch financial news (not decorated with @tool)."""
    try:
        logger.info(f"Fetching financial news for query: {query}")
        
        articles = []
        
        # Check if query looks like a stock symbol
        if len(query) <= 5 and query.replace('.', '').replace('-', '').isalnum():
            # Treat as stock symbol
            logger.info(f"Treating '{query}' as stock symbol")
            articles = _get_stock_news(query.upper(), max_articles)
        else:
            # General market news
            logger.info(f"Getting general market news for: {query}")
            articles = _get_market_news(query, max_articles)
        
        result = {
            "type": "news",
            "query": query,
            "articles": [article.dict() for article in articles],
            "count": len(articles),
            "source": "yahoo_finance"
        }
        
        logger.info(f"Successfully retrieved {len(articles)} articles")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching financial news: {e}", exc_info=True)
        # Return empty result instead of failing
        result = {
            "type": "news",
            "query": query,
            "articles": [],
            "count": 0,
            "source": "yahoo_finance",
            "error": str(e)
        }
        return result


async def fetch_stock_data(symbol: str) -> Dict[str, Any]:
    """Helper function to fetch stock data (not decorated with @tool)."""
    try:
        logger.info(f"Fetching stock data for symbol: {symbol}")
        
        ticker = yf.Ticker(symbol.upper())
        stock_data = _create_stock_data(ticker, symbol)
        
        if stock_data:
            result = {
                "type": "stock",
                "symbol": symbol.upper(),
                "data": stock_data.dict(),
                "source": "yahoo_finance"
            }
            logger.info(f"Successfully retrieved stock data for {symbol}")
        else:
            logger.warning(f"No stock data found for {symbol}")
            result = {
                "type": "stock",
                "symbol": symbol.upper(),
                "data": None,
                "source": "yahoo_finance",
                "error": "No data found"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}", exc_info=True)
        result = {
            "type": "stock",
            "symbol": symbol.upper(),
            "data": None,
            "source": "yahoo_finance",
            "error": str(e)
        }
        return result


def _create_stock_data(ticker: yf.Ticker, symbol: str) -> Optional[StockData]:
    """Create StockData object from yfinance ticker."""
    try:
        info = ticker.fast_info
        hist = ticker.history(period="2d")
        
        if hist.empty:
            logger.warning(f"No historical data found for {symbol}")
            return None
        
        current_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - previous_price
        change_percent = (change / previous_price * 100) if previous_price != 0 else 0
        
        return StockData(
            symbol=symbol.upper(),
            name=info.get('longName', info.get('shortName', f"{symbol} Inc.")),
            current_price=round(float(current_price), 2),
            change=round(float(change), 2),
            change_percent=round(float(change_percent), 2),
            volume=int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
            market_cap=info.get('marketCap', 0)
        )
    except Exception as e:
        logger.error(f"Error creating stock data for {symbol}: {e}")
        return None


def _get_stock_news(symbol: str, max_articles: int = 10) -> List[NewsArticle]:
    """Get news for a specific stock symbol."""
    try:
        
        ticker = yf.Ticker(symbol)
        news = ticker.news
        logger.info(f"Getting news for: {symbol}, number of news: {len(news)}")
        
        articles = []
        for item in news[:max_articles]:
            try:
                # Parse timestamp
                content = item.get("content", {})

                # Parse published date
                published_date = None
                pub_date_str = content.get("pubDate")
                if pub_date_str:
                    # Convert ISO format to datetime
                    published_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))

                # Build NewsArticle object
                article = NewsArticle(
                    title=content.get("title", ""),
                    url=content.get("clickThroughUrl", {}).get("url", ""),
                    source=content.get("provider", {}).get("displayName", "Yahoo Finance"),
                    snippet=content.get("summary", ""),
                    published_date=published_date
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing news item: {e}")
                continue
                
        return articles
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        return []


def _get_market_news(query: str = "stock market", max_articles: int = 10) -> List[NewsArticle]:
    """Get general market news by searching popular symbols."""
    # Use major indices and popular stocks to get market news
    market_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL']
    all_articles = []
    
    for symbol in market_symbols:
        articles = _get_stock_news(symbol, max_articles // len(market_symbols))
        all_articles.extend(articles)
        
        if len(all_articles) >= max_articles:
            break
    # Remove duplicates based on title
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        if article.title not in seen_titles:
            seen_titles.add(article.title)
            unique_articles.append(article)
    logger.info(f"Number of unique articles: {len(unique_articles)}")
    return unique_articles[:max_articles]
