"""Sentiment analysis tool using VADER sentiment analysis."""

from typing import List, Dict, Any
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from agno.tools import tool
from models import SentimentScore, NewsArticle


# Global analyzer instance
analyzer = SentimentIntensityAnalyzer()


def fetch_articles_sentiment(articles_data: List[Dict]) -> Dict[str, Any]:
    """
    Analyze sentiment of multiple news articles (helper function).
    
    Args:
        articles_data: List of article dictionaries
        
    Returns:
        Dictionary with comprehensive sentiment analysis
    """
    try:
        # Convert to NewsArticle objects
        articles = []
        for article_data in articles_data:
            if isinstance(article_data, dict):
                article = NewsArticle(**article_data)
                articles.append(article)
    except Exception as e:
        return {
            "error": f"Failed to parse articles: {str(e)}",
            "type": "articles_sentiment"
        }
    
    if not articles:
        return {
            "type": "articles_sentiment",
            "overall_sentiment": SentimentScore(compound=0.0, positive=0.0, negative=0.0, neutral=1.0).dict(),
            "article_sentiments": [],
            "summary": {
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "average_compound": 0.0,
                "total_articles": 0
            },
            "market_summary": "No articles provided for analysis."
        }
    
    article_sentiments = []
    compound_scores = []
    
    for article in articles:
        # Combine title and snippet for analysis
        text_to_analyze = f"{article.title} {article.snippet or ''}"
        sentiment = _analyze_text(text_to_analyze)
        
        # Update article with sentiment
        article.sentiment = sentiment
        article_sentiments.append({
            "title": article.title,
            "sentiment": sentiment.dict(),
            "url": article.url,
            "interpretation": _get_sentiment_interpretation(sentiment)
        })
        
        compound_scores.append(sentiment.compound)
    
    # Calculate overall sentiment
    if compound_scores:
        avg_compound = sum(compound_scores) / len(compound_scores)
        
        # Aggregate positive, negative, neutral scores
        avg_positive = sum(s["sentiment"]["positive"] for s in article_sentiments) / len(article_sentiments)
        avg_negative = sum(s["sentiment"]["negative"] for s in article_sentiments) / len(article_sentiments)
        avg_neutral = sum(s["sentiment"]["neutral"] for s in article_sentiments) / len(article_sentiments)
        
        overall_sentiment = SentimentScore(
            compound=avg_compound,
            positive=avg_positive,
            negative=avg_negative,
            neutral=avg_neutral
        )
    else:
        overall_sentiment = SentimentScore(compound=0.0, positive=0.0, negative=0.0, neutral=1.0)
        avg_compound = 0.0
    
    # Categorize sentiments
    positive_count = sum(1 for score in compound_scores if score > 0.05)
    negative_count = sum(1 for score in compound_scores if score < -0.05)
    neutral_count = len(compound_scores) - positive_count - negative_count
    
    # Generate market sentiment summary
    interpretation = _get_sentiment_interpretation(overall_sentiment)
    
    market_summary = f"""
                        Market Sentiment Analysis:
                        - Overall sentiment: {interpretation} (score: {overall_sentiment.compound:.3f})
                        - Article breakdown: {positive_count} positive, {negative_count} negative, {neutral_count} neutral
                        - Based on {len(articles)} news articles

                        Key insights:
                    """
    
    if overall_sentiment.compound > 0.1:
        market_summary += "- Market sentiment appears optimistic with positive news coverage\n"
        market_summary += "- This could indicate favorable conditions for stock investments\n"
    elif overall_sentiment.compound < -0.1:
        market_summary += "- Market sentiment appears pessimistic with negative news coverage\n"
        market_summary += "- Caution advised, consider defensive investment strategies\n"
    else:
        market_summary += "- Market sentiment is neutral with mixed news coverage\n"
        market_summary += "- Balanced approach recommended, focus on fundamentals\n"
    
    return {
        "type": "articles_sentiment",
        "overall_sentiment": overall_sentiment.dict(),
        "article_sentiments": article_sentiments,
        "summary": {
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "average_compound": avg_compound,
            "total_articles": len(articles)
        },
        "market_summary": market_summary.strip()
    }


def _analyze_text(text: str) -> SentimentScore:
    """
    Analyze sentiment of a single text.
    
    Args:
        text: Text to analyze
        
    Returns:
        SentimentScore object with sentiment scores
    """
    if not text or not text.strip():
        return SentimentScore(compound=0.0, positive=0.0, negative=0.0, neutral=1.0)
    
    scores = analyzer.polarity_scores(text)
    
    return SentimentScore(
        compound=scores['compound'],
        positive=scores['pos'],
        negative=scores['neg'],
        neutral=scores['neu']
    )


def _get_sentiment_interpretation(sentiment_score: SentimentScore) -> str:
    """
    Get human-readable interpretation of sentiment score.
    
    Args:
        sentiment_score: SentimentScore object
        
    Returns:
        String interpretation of sentiment
    """
    compound = sentiment_score.compound
    
    if compound >= 0.5:
        return "Very Positive"
    elif compound >= 0.1:
        return "Positive"
    elif compound > -0.1:
        return "Neutral"
    elif compound > -0.5:
        return "Negative"
    else:
        return "Very Negative"

