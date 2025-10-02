"""Main FastAPI application for the AI Stock Recommendation Agent."""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from models import (
    StockRecommendationRequest, 
    StockRecommendationResponse,
    ManagerApproval,
    ApprovalStatus
)
from agents.team import StockRecommendationTeam

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Silence noisy third-party library loggers
logging.getLogger('yfinance').setLevel(logging.WARNING)
logging.getLogger('peewee').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('python_multipart').setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom StaticFiles to add ngrok header
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
from starlette.responses import Response as StarletteResponse
from starlette.types import Scope, Receive, Send

class NgrokStaticFiles(StarletteStaticFiles):
    """Custom StaticFiles that adds ngrok-skip-browser-warning header."""
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Override to add custom headers."""
        if scope["type"] == "http":
            # Get the response from parent
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Add ngrok header to skip browser warning
                    headers = list(message.get("headers", []))
                    headers.append((b"ngrok-skip-browser-warning", b"true"))
                    # Also add CORS header for Twilio
                    headers.append((b"access-control-allow-origin", b"*"))
                    message["headers"] = headers
                await send(message)
            
            await super().__call__(scope, receive, send_wrapper)
        else:
            await super().__call__(scope, receive, send)

# Mount static files with ngrok support
app.mount("/static", NgrokStaticFiles(directory="static"), name="static")

# Initialize team (lazy initialization)
_team = None

def get_team() -> StockRecommendationTeam:
    """Get or create the stock recommendation team."""
    global _team
    if _team is None:
        _team = StockRecommendationTeam()
    return _team


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    try:
        return FileResponse("static/index.html")
    except Exception as e:
        logger.error(f"Error serving index.html: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/test-audio")
async def test_audio():
    """Test if static audio files are accessible."""
    import os
    audio_dir = "static/audio"
    if os.path.exists(audio_dir):
        files = os.listdir(audio_dir)
        return {
            "audio_directory": audio_dir,
            "file_count": len(files),
            "files": files[:5],  # Show first 5 files
            "sample_url": f"/static/audio/{files[0]}" if files else None
        }
    return {"error": "Audio directory not found"}


@app.get("/config")
async def get_config():
    """Get public configuration."""
    return {
        "app_title": settings.app_title,
        "app_version": settings.app_version,
        "uses_yahoo_finance": True,
        "max_news_articles": settings.max_news_articles,
        "mock_voice_services": settings.mock_voice_services,
        "debug": settings.debug
    }


@app.get("/team/status")
async def get_team_status(team: StockRecommendationTeam = Depends(get_team)):
    """Get the status of all agents in the team."""
    try:
        status = await team.get_team_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting team status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get team status"
        )


@app.post("/recommend", response_model=StockRecommendationResponse)
async def get_stock_recommendations(
    request: StockRecommendationRequest,
    team: StockRecommendationTeam = Depends(get_team)
):
    """Generate stock recommendations based on user query."""
    try:
        logger.info(f"Processing recommendation request: {request.query}")
        
        # Generate recommendations
        response = await team.process_recommendation_request(request)
        
        logger.info("Successfully generated stock recommendations")
        return response
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations"
        )


@app.post("/analyze/news")
async def analyze_news(
    query: str,
    team: StockRecommendationTeam = Depends(get_team)
):
    """Analyze financial news for a given query."""
    try:
        logger.info(f"Analyzing news for query: {query}")
        
        analysis = await team.run_individual_agent(
            "NewsAnalyst",
            "Analyze financial news",
            query=query
        )
        
        return JSONResponse(content=analysis.dict())
        
    except Exception as e:
        logger.error(f"Error analyzing news: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze news"
        )


@app.post("/recommend/stocks")
async def recommend_stocks(
    market_analysis: str,
    max_recommendations: int = 3,
    risk_preference: str = "medium",
    team: StockRecommendationTeam = Depends(get_team)
):
    """Generate stock recommendations based on market analysis."""
    try:
        logger.info("Generating stock recommendations")
        
        analysis = await team.run_individual_agent(
            "StockRecommender",
            "Generate stock recommendations",
            market_analysis=market_analysis,
            sentiment_data=None,
            max_recommendations=max_recommendations,
            risk_preference=risk_preference
        )
        
        return JSONResponse(content=analysis.dict())
        
    except Exception as e:
        logger.error(f"Error recommending stocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to recommend stocks"
        )


@app.post("/approve")
async def request_approval(
    recommendations: list,
    team: StockRecommendationTeam = Depends(get_team)
):
    """Request manager approval for recommendations."""
    try:
        logger.info(f"Requesting approval for {len(recommendations)} recommendations")
        
        analysis = await team.run_individual_agent(
            "ApprovalManager",
            "Request manager approval",
            recommendations=recommendations
        )
        
        return JSONResponse(content=analysis.dict())
        
    except Exception as e:
        logger.error(f"Error requesting approval: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to request approval"
        )


@app.post("/log-frontend-error")
async def log_frontend_error(request: Request):
    """Log frontend JavaScript errors."""
    try:
        data = await request.json()
        error_msg = data.get("error", "Unknown error")
        stack = data.get("stack", "No stack trace")
        url = data.get("url", "Unknown URL")
        
        logger.error(f"Frontend error at {url}: {error_msg}")
        logger.error(f"Stack trace: {stack}")
        
        return JSONResponse(
            status_code=200,
            content={"status": "logged"}
        )
    except Exception as e:
        logger.error(f"Error logging frontend error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to log error"}
        )


# Store for pending approval calls (in production, use Redis or database)
_pending_approvals: Dict[str, Dict[str, Any]] = {}


# Twilio Webhook Endpoints for Real Voice Approval
@app.post("/webhooks/approval/gather")
async def twilio_gather_webhook(request: Request):
    """
    Webhook endpoint for Twilio <Gather> responses.
    This receives the manager's speech input (yes/no).
    """
    try:
        # Get form data from Twilio
        form_data = await request.form()
        form_dict = dict(form_data)
        
        call_sid = form_dict.get('CallSid', 'unknown')
        speech_result = form_dict.get('SpeechResult', '').lower().strip()
        confidence = form_dict.get('Confidence', '0')
        
        logger.info(f"Received Twilio Gather webhook for call {call_sid}")
        logger.info(f"Speech result: '{speech_result}' (confidence: {confidence})")
        logger.debug(f"Full form data: {form_dict}")
        
        # Parse speech result for yes/no
        approved = False
        if speech_result:
            # Check for approval keywords
            approval_keywords = ['yes', 'approve', 'approved', 'accept', 'okay', 'ok', 'sure', 'go ahead', 'affirmative', 'yeah']
            rejection_keywords = ['no', 'reject', 'rejected', 'deny', 'denied', 'refuse', 'not approved', 'negative']
            
            if any(keyword in speech_result for keyword in approval_keywords):
                approved = True
                response_msg = "Thank you. The recommendations have been APPROVED."
            elif any(keyword in speech_result for keyword in rejection_keywords):
                approved = False
                response_msg = "Thank you. The recommendations have been REJECTED."
            else:
                # Unclear response, default to reject for safety
                approved = False
                response_msg = "I didn't understand your response. The recommendations will be REJECTED."
        else:
            # No speech detected (timeout)
            approved = False
            response_msg = "No response detected. The recommendations will be REJECTED."
        
        # Store approval result (in production, update database)
        _pending_approvals[call_sid] = {
            "approved": approved,
            "speech_result": speech_result,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Approval decision for call {call_sid}: {'APPROVED' if approved else 'REJECTED'}")
        
        # Return TwiML response to confirm to manager
        from twilio.twiml.voice_response import VoiceResponse
        twiml_response = VoiceResponse()
        twiml_response.say(response_msg, voice='alice')
        twiml_response.hangup()
        
        return Response(content=str(twiml_response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing Twilio Gather webhook: {e}", exc_info=True)
        
        # Return error TwiML
        from twilio.twiml.voice_response import VoiceResponse
        twiml_response = VoiceResponse()
        twiml_response.say("An error occurred. The recommendations will be rejected.", voice='alice')
        twiml_response.hangup()
        
        return Response(content=str(twiml_response), media_type="application/xml")


@app.get("/webhooks/approval/result/{call_sid}")
async def get_approval_result(call_sid: str):
    """
    Get the approval result for a specific call.
    Used by the backend to check if manager has responded.
    """
    try:
        if call_sid in _pending_approvals:
            result = _pending_approvals[call_sid]
            logger.info(f"Retrieved approval result for call {call_sid}: {result}")
            return JSONResponse(content=result)
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "No approval result found for this call"}
            )
    except Exception as e:
        logger.error(f"Error retrieving approval result: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve approval result"}
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
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
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal server error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    os.makedirs("static/audio", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
