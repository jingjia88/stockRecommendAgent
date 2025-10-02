# System Design Document

## **1. Architecture Overview**

The AI Stock Recommendation Agent orchestrates multiple APIs to provide intelligent stock recommendations. Optional manager approval can be mocked for prototype purposes.

### **High-Level Architecture**

```markdown
User Interface (CLI / Web)
         ↓
    Agno Agent Team
┌───────────────────────────┐
│ • News Analyst Agent      │ → Yahoo Finance / Sentiment Analysis
│ • Stock Recommender Agent │ → Claude LLM
│ • Approval Manager Agent* │ → ElevenLabs TTS / Twilio
│ • Response Coordinator    │
└───────────────────────────┘
         ↓
   Final Response → User
```

---

## **2. Technology Stack Choices**

- **Agno Framework**: Multi-agent orchestration with shared memory
- **Python**: Backend simplicity
- **Claude LLM**: Reasoning & analysis
- **Sentiment Analysis**: VADER
- **DataForSEO Google Finance API**: Real-time market data
- **ElevenLabs / Twilio**: Optional approval voice workflow
- **Frontend**: simple web interface

---

## **3. Workflow Design**

**Phase 1: Analysis**

- News Analyst Agent fetches news using DataForSEO Google Finance Explore API, performs sentiment analysis, updates team context
- Stock Recommender Agent selects top 3 stocks using Claude reasoning

**Phase 2: Optional Approval**

- Approval Manager Agent generates TTS and calls manager via Twilio
- Fallback: skip approval or mock response

**Phase 3: Response**

- Response Coordinator compiles recommendations, adds light joke, returns to user

---

## **4. Data Flow Architecture**

```jsx
User Query → News Analyst → Sentiment → Stock Recommender →
(Optional) Approval Manager → Response Coordinator → User
```

---

## **5. Security & Reliability Considerations**

- **API Security**: Environment variables for API keys, rate limiting, retries, input validation
- **Error Handling**: Graceful degradation, logging, fallback for critical steps
- **Data Privacy**: No persistent storage of user queries, secure manager info handling
- **Financial Disclaimer**: Prototype is for demonstration only; not financial advice

---

## 6. Assumptions & Limitations

- Twilio/ElevenLabs may be mocked due to trial limits
- Stock recommendations illustrative; no real trading
- Sentiment analysis on limited sample (e.g., 10 news articles)
- Prototype handles single “Which stocks to buy?” queries only