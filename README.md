# 🤖 AI Stock Recommendation Agent

A sophisticated multi-agent AI system that provides intelligent stock recommendations by analyzing financial news, market sentiment, and leveraging Claude LLM for investment insights.

## 🌟 Features

- **📰 News Analysis**: Real-time financial news fetching and sentiment analysis using Yahoo Finance API
- **🤖 AI-Powered Recommendations**: Intelligent stock picking using Claude LLM with detailed reasoning
- **📞 Manager Approval Workflow**: Optional approval process with voice services (ElevenLabs TTS + Twilio)
- **🎯 Risk Assessment**: Customizable risk preferences (Low/Medium/High)
- **🌐 Web Interface**: Beautiful, responsive web interface for easy interaction
- **📊 Comprehensive Analysis**: Market sentiment, technical indicators, and fundamental analysis
- **🔧 Mock Services**: Full functionality available even without external API credentials

## 🏗️ Architecture

The system uses the **Agno framework** for multi-agent orchestration with three specialized agents:

1. **News Analyst Agent**: Fetches and analyzes financial news, performs sentiment analysis
2. **Stock Recommender Agent**: Generates AI-powered stock recommendations using Claude LLM
3. **Approval Manager Agent**: Handles manager approval workflow with voice communication

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- API keys for external services (optional - mock services available)

### Installation

1. **Clone and setup**:
```bash
cd stockRecommendAgent
pip install -r requirements.txt
```

2. **Configure environment** (copy and modify):
```bash
cp env.example .env
# Edit .env with your API keys (optional)
```

3. **Run the application**:
```bash
python main.py
```

4. **Access the interface**:
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🔑 API Configuration

### Required for Full Functionality

```bash
# Core AI (Required)
ANTHROPIC_API_KEY=your_claude_api_key_here

# Yahoo Finance (Free - No API Key Required)

# Voice Services for Manager Approval (Optional)
ELEVENLABS_API_KEY=your_elevenlabs_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number
MANAGER_PHONE=+1234567890

# Webhook URL (Required for real voice approval)
# For development: Use ngrok to expose localhost
#   1. Install ngrok: https://ngrok.com
#   2. Run: ngrok http 8000
#   3. Copy the https URL (e.g., https://abc123.ngrok.io)
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io

# Application Settings
MOCK_VOICE_SERVICES=true  # Set to false for real voice services
DEBUG=true
```

### 📞 Setting Up Real Voice Approval (ElevenLabs + Twilio + ngrok)

To enable real phone call approval:

1. **Get API Keys**:
   - ElevenLabs: https://elevenlabs.io (for high-quality text-to-speech)
   - Twilio: https://www.twilio.com (for phone calls)

2. **Setup ngrok** (for development):
   ```bash
   # Download and install ngrok
   brew install ngrok  # macOS
   # or download from https://ngrok.com
   
   # Start ngrok tunnel
   ngrok http 8000
   
   # Copy the https URL (e.g., https://abc123.ngrok.io)
   # Add it to your .env file as WEBHOOK_BASE_URL
   ```

3. **Configure `.env`**:
   ```bash
   ELEVENLABS_API_KEY=sk_your_elevenlabs_key
   TWILIO_ACCOUNT_SID=ACxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+15551234567
   MANAGER_PHONE=+15559876543
   WEBHOOK_BASE_URL=https://abc123.ngrok.io
   MOCK_VOICE_SERVICES=false
   ```

4. **How it works**:
   - System generates recommendation summary
   - ElevenLabs converts it to high-quality speech (MP3)
   - Audio saved to `static/audio/` (accessible via ngrok)
   - Twilio calls manager and plays the audio
   - Manager says "YES" or "NO"
   - Twilio webhook sends response back to system
   - Recommendations approved or rejected accordingly
   - **Timeout**: 10 seconds (auto-reject if no answer)

### Mock Mode (Minimal API Keys)

The system works with minimal configuration:
- **Yahoo Finance**: Free stock data and news (no API key needed)
- **Mock services**: Available for voice services if not configured
- **Fallback mechanisms**: Automatic fallback to mock data if needed

## 📱 Usage Examples

### Web Interface

Visit http://localhost:8000 and try these example queries:

- "Which stocks should I buy today?"
- "Safe dividend stocks for retirement portfolio"
- "High growth tech stocks with AI exposure"
- "Best renewable energy stocks for 2024"

### API Usage

```python
import requests

# Basic recommendation request
response = requests.post("http://localhost:8000/recommend", json={
    "query": "Which stocks should I buy today?",
    "max_recommendations": 3,
    "risk_preference": "medium",
    "include_approval": False
})

recommendations = response.json()
```

### Individual Agent Testing

```python
# Test news analysis only
response = requests.post("http://localhost:8000/analyze/news", json={
    "query": "tech stocks",
    "max_articles": 10
})

# Test stock recommendations only
response = requests.post("http://localhost:8000/recommend/stocks", json={
    "market_analysis": "Positive market sentiment...",
    "max_recommendations": 3,
    "risk_preference": "medium"
})
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/recommend` | POST | Full recommendation workflow |
| `/analyze/news` | GET | News analysis only |
| `/recommend/stocks` | POST | Stock recommendations only |
| `/approve` | POST | Manager approval only |
| `/health` | GET | System health check |
| `/team/status` | GET | Agent team status |
| `/config` | GET | Current configuration |
| `/docs` | GET | Interactive API documentation |

## 🏢 Production Deployment

### Environment Setup

```bash
# Production environment variables
ANTHROPIC_API_KEY=your_production_claude_key
# Yahoo Finance is free - no credentials needed
ELEVENLABS_API_KEY=your_production_elevenlabs_key
TWILIO_ACCOUNT_SID=your_production_twilio_sid
TWILIO_AUTH_TOKEN=your_production_twilio_token
MOCK_VOICE_SERVICES=false
DEBUG=false
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Security Considerations

- Store API keys securely (environment variables, key vaults)
- Implement rate limiting for production
- Add authentication for sensitive endpoints
- Use HTTPS in production
- Validate and sanitize all inputs

## 🧪 Testing

### Manual Testing

1. **Start the application**: `python main.py`
2. **Visit health check**: http://localhost:8000/health
3. **Test team status**: http://localhost:8000/team/status
4. **Try the web interface**: http://localhost:8000

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Basic recommendation
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "tech stocks", "max_recommendations": 3, "risk_preference": "medium"}'
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **API Key Issues**: 
   - Check your `.env` file
   - Verify API key validity
   - Enable mock services if needed: `MOCK_VOICE_SERVICES=true`

3. **Port Conflicts**: Change the port in `main.py` if 8000 is occupied

4. **Memory Issues**: Claude API calls may require sufficient memory

### Debug Mode

Enable debug logging:
```bash
DEBUG=true python main.py
```

## 📚 Technical Details

### Dependencies

- **agno**: Multi-agent framework
- **fastapi**: Web framework
- **anthropic**: Claude LLM integration
- **vaderSentiment**: Sentiment analysis
- **elevenlabs**: Text-to-speech
- **twilio**: Phone calling
- **aiohttp**: Async HTTP client

### Architecture Benefits

- **Modular Design**: Each agent has specific responsibilities
- **Scalable**: Easy to add new agents or modify existing ones
- **Fault Tolerant**: Graceful degradation with mock services
- **Async Operations**: Efficient handling of API calls
- **RESTful API**: Standard HTTP interfaces

## ⚠️ Important Disclaimers

1. **Not Financial Advice**: This is a demonstration system for educational purposes only
2. **No Trading**: Do not use for actual trading without proper validation
3. **API Costs**: Be aware of costs for Claude, DataForSEO, ElevenLabs, and Twilio APIs
4. **Rate Limits**: Respect API rate limits and implement appropriate throttling
5. **Data Privacy**: Handle user queries and financial data responsibly

## 🤝 Contributing

This is a prototype system. For production use, consider:

- Adding comprehensive error handling
- Implementing user authentication
- Adding database persistence
- Enhancing security measures
- Adding comprehensive testing suite
- Implementing proper logging and monitoring

## 📄 License

This project is for demonstration purposes. Please ensure compliance with all applicable financial regulations and API terms of service.

---

**Happy Investing! 📈🤖**

*Remember: Past performance doesn't guarantee future results, but good code does guarantee better demos!*
