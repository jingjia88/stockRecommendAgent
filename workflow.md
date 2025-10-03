# AI Stock Recommendation Agent - Complete Workflow & Error Handling

## 📋 Complete Workflow Process

### Phase 1: Request Processing
```
User Query → FastAPI /recommend endpoint → StockRecommendationTeam.process_recommendation_request()
```

**Input**: `StockRecommendationRequest`
- `query`: User's investment query (e.g., "recommend financial stocks")
- `max_recommendations`: Maximum number of recommendations (default: 3)
- `risk_preference`: Risk tolerance (low/medium/high)
- `include_approval`: Whether to require manager approval

**Error Handling**:
- Input validation via Pydantic models
- Malformed requests return structured error responses
- Missing parameters use sensible defaults

### Phase 2: News Analysis (NewsAnalystAgent)
```
Market News Fetching → Sentiment Analysis → Market Summary Generation
```

**Process Flow**:
1. **Query Analysis**: Determine if query is stock symbol or general market topic
2. **News Retrieval**: 
   - Primary: Yahoo Finance API for stock-specific news
   - Secondary: Google News RSS for keyword-based search
   - Fallback: Mock data for testing
3. **Sentiment Analysis**: Process articles through sentiment analyzer
4. **Market Summary**: Generate comprehensive market analysis

**Data Sources (in order of preference)**:
- Yahoo Finance API (real-time stock news)
- Google News RSS (keyword-based search)
- Mock financial news (testing/fallback)

**Error Handling**:
```python
try:
    news_result = await fetch_financial_news(query, max_articles)
    if not news_result.get("articles") and "error" in news_result:
        # Fallback to mock data
        mock_result = await get_mock_financial_news(query, max_articles)
        articles_data = mock_result.get("articles", [])
except Exception as e:
    logger.error(f"News analysis failed: {e}")
    return error_response()
```

### Phase 3: Stock Recommendations (StockRecommenderAgent)
```
Market Analysis Integration → Claude AI Processing → Recommendation Generation → Data Enhancement
```

**AI Processing Pipeline**:
1. **Context Preparation**: Combine market analysis, sentiment data, user query
2. **Claude AI Analysis**: 
   - Model: Claude Sonnet 4
   - Temperature: 0.3 (balanced creativity/consistency)
   - Max tokens: 2000
3. **JSON Parsing**: Extract structured recommendations
4. **Data Enhancement**: Fetch real-time stock prices and market data

**Claude AI Integration**:
```python
response = await self.claude_client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2000,
    temperature=0.3,
    messages=[{"role": "user", "content": context}]
)
```

**Error Handling**:
- Claude API failure → Fallback to predefined recommendations
- JSON parsing failure → Text-based parsing
- Stock data fetch failure → Mock data integration
- Enhancement failure → Basic recommendations without real-time data

### Phase 4: Manager Approval (ApprovalManagerAgent)
```
Approval Summary Generation → Voice Service Integration → Manager Response Processing
```

**Approval Methods**:

**Mock Mode**:
- 1-second processing time

**Real Voice Mode**:
1. **Text-to-Speech**: ElevenLabs API generates high-quality audio
2. **Audio Storage**: Save to local static directory
3. **Phone Call**: Twilio initiates call to manager
4. **Speech Recognition**: Twilio processes manager's voice response
5. **Webhook Processing**: Handle approval/rejection

**Voice Service Flow**:
```
ElevenLabs TTS → Audio File → Twilio Call → Manager Response → Webhook → Status Update
```

**Error Handling**:
- Missing credentials → Auto-reject with explanation
- TTS failure → Auto-reject
- Call failure → Auto-reject
- No response (10s timeout) → Auto-reject
- Webhook timeout (60s) → Auto-reject

### Phase 5: Response Compilation
```
Agent Results Integration → Final Response Generation → User Delivery
```

**Response Structure**:
- Stock recommendations with reasoning
- Market analysis summary
- Sentiment scores
- Manager approval status
- Agent analysis details
- Humor note for engagement

## 🛡️ Comprehensive Error Handling

### 1. Global Exception Handling

**FastAPI Level**:
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal server error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### 2. Agent-Level Error Handling

**NewsAnalystAgent**:
- Yahoo Finance API failure → Google News RSS fallback
- Google News failure → Mock data fallback

**StockRecommenderAgent**:
- Claude API failure → Predefined recommendation fallback
- Stock data fetch failure → Mock data integration
- JSON parsing failure → Text parsing fallback
- Enhancement failure → Basic recommendations

**ApprovalManagerAgent**:
- Voice service failure → Mock approval fallback
- Webhook timeout → Auto-rejection
- Call failure → Auto-rejection with explanation
- Missing credentials → Auto-rejection with clear message

### 3. Tool-Level Error Handling

**Yahoo Finance Tool**:
```python
try:
    # Attempt real data fetch
    stock_data = await fetch_real_stock_data(symbol)
except Exception as e:
    logger.warning(f"Real data fetch failed: {e}")
    # Fallback to mock data
    stock_data = await get_mock_stock_data(symbol)
```

**Voice Services Tool**:
```python
# Multi-layer fallback strategy
if not settings.elevenlabs_api_key:
    return await fetch_mock_manager_approval(summary)
if not settings.twilio_credentials:
    return await fetch_mock_manager_approval(summary)
if webhook_timeout:
    return auto_reject_with_explanation()
```

### 4. Data Validation & Transformation

**Pydantic Model Validation**:
- Automatic input data format validation
- Structured error responses for validation failures

**Configuration Management**:
- Environment variable validation
- Debug mode configuration

## 🔄 Fault Tolerance Mechanisms

### 1. Multi-Layer Fallback Strategy
```
Real API → Backup API → Mock Data → Error Response
```

**Example Flow**:
1. Try Yahoo Finance API
2. If fails, try Google News RSS
3. If fails, use mock financial news
4. If all fail, return error with explanation

### 2. Timeout Management
- **Twilio Calls**: 10-second ring timeout
- **Webhook Waiting**: 60-second maximum wait
- **HTTP Requests**: 10-second timeout


## 📊 Logging

### Logging Levels
- **INFO**: Normal process flow tracking
- **WARNING**: Fallback operations and degraded service
- **ERROR**: Exceptions and failures
- **DEBUG**: Detailed debugging information


## 📈 Performance Considerations

### Async Operations
- All I/O operations are async
- Parallel processing where possible
- Non-blocking external API calls

### Caching Strategy
- Static file serving for audio files
- In-memory storage for pending approvals


