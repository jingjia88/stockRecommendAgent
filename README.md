# 🤖 AI Stock Recommendation Agent

A sophisticated multi-agent AI system that provides intelligent stock recommendations by analyzing financial news, market sentiment, and leveraging Claude LLM for investment insights.

## 🌟 Features

- **📰 Smart News Analysis**: Real-time financial news with keyword-based search (Google News RSS + Yahoo Finance)
- **🤖 AI-Powered Recommendations**: Intelligent stock picking using Claude LLM with sector-specific targeting
- **📞 Manager Approval Workflow**: Optional voice approval process (ElevenLabs TTS + Twilio)
- **🎯 Risk Assessment**: Customizable risk preferences (Low/Medium/High)
- **🌐 Web Interface**: Beautiful, responsive web interface
- **🔧 Mock Services**: Full functionality without external API credentials

## 🏗️ Architecture

Multi-agent system using **Agno framework** with three specialized agents:

1. **News Analyst Agent**: Fetches and analyzes financial news with sentiment analysis
2. **Stock Recommender Agent**: Generates AI-powered recommendations using Claude LLM
3. **Approval Manager Agent**: Handles manager approval workflow with voice communication

## 🚀 Quick Start

### Installation

```bash
# Clone and setup
cd stockRecommendAgent
pip install -r requirements.txt

# Configure environment (optional)
cp env.example .env
# Edit .env with your API keys
```

### Run Application

```bash
python main.py
```

Access at:
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔑 Configuration

### Required (Core)
```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
```

### Optional (Voice Services)
```bash
# Voice approval workflow
ELEVENLABS_API_KEY=your_elevenlabs_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
MANAGER_PHONE=+1234567890
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io

# Settings
MOCK_VOICE_SERVICES=true  # Set to false for real voice services
DEBUG=true
```

### 📞 Voice Approval Setup

1. **Get API Keys**: ElevenLabs + Twilio
2. **Setup ngrok**: `ngrok http 8000`
3. **Configure webhook URL** in `.env`
4. **Set** `MOCK_VOICE_SERVICES=false`

## 📱 Usage

### Web Interface Examples

Try these queries at http://localhost:8000:

- "best financial bank services stocks"
- "renewable energy investment opportunities" 
- "high growth tech stocks with AI exposure"
- "safe dividend stocks for retirement"


## 🔍 Key Improvements

### Smart News Search
- **Google News RSS**: Real keyword-based news search
- **Sector Detection**: Automatically detects financial, tech, healthcare, etc.
- **Fallback**: Yahoo Finance for specific stock news

### Enhanced Recommendations
- **User Query Awareness**: Recommendations match user's specific request
- **Sector Targeting**: Only recommends stocks from requested sectors
- **Context-Aware**: Uses relevant news for each sector


### Security
- Store API keys securely
- Use HTTPS in production
- Implement rate limiting
- Add authentication for sensitive endpoints

## ⚠️ Disclaimers

1. **Not Financial Advice**: Educational/demonstration purposes only
2. **No Trading**: Do not use for actual trading without validation
3. **API Costs**: Be aware of Claude, ElevenLabs, and Twilio costs
4. **Rate Limits**: Respect API rate limits

## 🔧 Troubleshooting

### Common Issues
- **Import Errors**: `pip install -r requirements.txt`
- **API Key Issues**: Check `.env` file, enable mock services
- **Port Conflicts**: Change port in `main.py`

### Debug Mode
```bash
DEBUG=true python main.py
```

---

**Happy Investing! 📈🤖**

*Remember: Past performance doesn't guarantee future results, but good code does guarantee better demos!*