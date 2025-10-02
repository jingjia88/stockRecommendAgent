"""Configuration management for the Stock Recommendation Agent."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Core AI API Keys
    anthropic_api_key: str = Field(..., description="Claude API key")
    
    # Yahoo Finance is free and doesn't require API keys
    
    # Voice Services (Optional)
    elevenlabs_api_key: Optional[str] = Field(None, description="ElevenLabs API key")
    twilio_account_sid: Optional[str] = Field(None, description="Twilio Account SID")
    twilio_auth_token: Optional[str] = Field(None, description="Twilio Auth Token")
    twilio_phone_number: Optional[str] = Field(None, description="Twilio phone number")
    webhook_base_url: Optional[str] = Field(None, description="Base URL for Twilio webhooks")
    
    # Manager Contact Information
    manager_phone: Optional[str] = Field(None, description="Manager phone number")
    manager_name: str = Field("Manager", description="Manager name")
    
    # Application Settings
    max_news_articles: int = Field(10, description="Maximum news articles to analyze")
    sentiment_threshold: float = Field(0.1, description="Sentiment analysis threshold")
    mock_voice_services: bool = Field(True, description="Whether to mock voice services")
    debug: bool = Field(False, description="Debug mode")
    
    # FastAPI Settings
    app_title: str = Field("AI Stock Recommendation Agent", description="Application title")
    app_version: str = Field("1.0.0", description="Application version")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()