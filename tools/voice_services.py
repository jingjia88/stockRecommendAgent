"""Voice services integration with ElevenLabs and Twilio."""

import asyncio
import aiohttp
import json
import logging
import time
import os
import uuid
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

from config import settings

logger = logging.getLogger(__name__)


async def _text_to_speech(text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> Optional[bytes]:
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (default is Bella voice)
        
    Returns:
        Audio bytes or None if failed
    """
    if not settings.elevenlabs_api_key:
        logger.warning("ElevenLabs API key not configured, skipping TTS")
        return None
    
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    logger.info(f"ElevenLabs TTS successful: {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.error(f"ElevenLabs API error: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}", exc_info=True)
        return None


def _save_audio_to_file(audio_bytes: bytes, call_id: str) -> str:
    """
    Save audio bytes to a file in static/audio directory.
    
    Args:
        audio_bytes: Audio data
        call_id: Unique call identifier
        
    Returns:
        File path relative to static directory
    """
    try:
        # Create audio directory if it doesn't exist
        audio_dir = "static/audio"
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate filename
        filename = f"approval_{call_id}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Write audio file
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        logger.info(f"Audio file saved: {filepath}")
        
        # Return URL path (relative to domain)
        return f"/static/audio/{filename}"
        
    except Exception as e:
        logger.error(f"Error saving audio file: {e}", exc_info=True)
        return None


def _create_twiml_for_approval(audio_url: str, gather_webhook_url: str) -> str:
    """
    Create TwiML for the approval call with ElevenLabs audio.
    
    Args:
        audio_url: URL to the ElevenLabs generated audio file
        gather_webhook_url: Webhook URL for processing manager's response
        
    Returns:
        TwiML XML string
    """
    response = VoiceResponse()
    
    response.play(audio_url)
    
    # Gather speech input with 10 second timeout
    gather = Gather(
        input='speech',
        timeout=10,
        speech_timeout='auto',
        action=gather_webhook_url,
        method='POST'
    )
    gather.say("Please say YES to approve or NO to reject these recommendations.", voice='alice')
    response.append(gather)
    
    # If no response after timeout, reject
    response.say("No response received. Recommendations will be rejected.", voice='alice')
    response.hangup()
    
    return str(response)


async def _make_twilio_call_with_audio(phone_number: str, audio_url: str, gather_webhook_url: str) -> Optional[str]:
    """
    Make a Twilio call that plays ElevenLabs audio and gathers response.
    
    Args:
        phone_number: Manager's phone number
        audio_url: Full URL to the audio file (e.g., https://abc123.ngrok.io/static/audio/approval_xyz.mp3)
        gather_webhook_url: Webhook URL for gathering response
        
    Returns:
        Call SID if successful, None if failed
    """
    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number]):
        logger.error("Twilio credentials not configured")
        return None
    
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        
        # Create TwiML for the call
        twiml = _create_twiml_for_approval(audio_url, gather_webhook_url)
        
        logger.info(f"Making Twilio call to {phone_number}")
        logger.debug(f"TwiML: {twiml}")
        
        # Make the call with 10 second timeout
        call = client.calls.create(
            twiml=twiml,
            to=phone_number,
            from_=settings.twilio_phone_number,
            timeout=10  # Ring for 10 seconds, if no answer -> reject
        )
        
        logger.info(f"Twilio call initiated. SID: {call.sid}")
        return call.sid
        
    except Exception as e:
        logger.error(f"Failed to make Twilio call: {e}", exc_info=True)
        return None


async def request_manager_approval(recommendations_summary: str, webhook_base_url: str = None) -> Dict[str, Any]:
    """
    Request manager approval for stock recommendations via phone call.
    
    This function:
    1. Uses ElevenLabs to convert text to high-quality speech
    2. Saves the audio file locally (for ngrok access)
    3. Makes ONE Twilio call that plays the audio and gathers response
    4. Returns immediately (webhook will handle the actual response)
    
    Flow:
    - No answer in 10s → auto-reject
    - Answer + say "yes" → approve
    - Answer + say "no" → reject
    - Answer + timeout (10s) → reject
    
    Args:
        recommendations_summary: Summary of stock recommendations to approve
        webhook_base_url: Base URL for webhooks (e.g., https://abc123.ngrok.io)
        
    Returns:
        Dictionary with approval result (pending status, webhook will update)
    """
    logger.info("Starting manager approval process")
    
    # Check if manager phone is configured
    if not settings.manager_phone:
        logger.info("No manager phone configured, auto-rejecting")
        return {
            "action": "manager_approval",
            "approved": False,
            "method": "auto_rejected_no_phone",
            "manager_response": "We can't help you today. Manager approval is required but no phone is configured."
        }
    
    # Check if we have voice service credentials
    if not settings.elevenlabs_api_key or not settings.twilio_account_sid:
        logger.info("Voice credentials not configured, auto-rejecting")
        return {
            "action": "manager_approval",
            "approved": False,
            "method": "auto_rejected_no_credentials",
            "manager_response": "We can't help you today. Voice service credentials are not configured."
        }
    
    # Check if webhook URL is provided
    if not webhook_base_url:
        logger.warning("No webhook URL provided, auto-rejecting")
        return {
            "action": "manager_approval",
            "approved": False,
            "method": "auto_rejected_no_webhook",
            "manager_response": "We can't help you today. Webhook URL is not configured for voice approval."
        }
    
    try:
        # Step 1: Generate high-quality speech with ElevenLabs
        logger.info("Generating speech with ElevenLabs TTS")
        
        # Create approval message (concise version for TTS)
        manager_name = settings.manager_name or 'Manager'
        message = f"""
        Hello {manager_name}, this is your AI Stock Recommendation System.
        
        I need your approval for stock recommendations.
        
        {recommendations_summary}
        """
        
        audio_bytes = await _text_to_speech(message.strip())
        
        if not audio_bytes:
            logger.warning("ElevenLabs TTS failed, auto-rejecting")
            return {
                "action": "manager_approval",
                "approved": False,
                "method": "auto_rejected_tts_failed",
                "manager_response": "We can't help you today. Text-to-speech generation failed."
            }
        
        logger.info(f"Speech generated successfully ({len(audio_bytes)} bytes)")
        
        # Step 2: Save audio file to localhost
        call_id = str(uuid.uuid4())
        audio_path = _save_audio_to_file(audio_bytes, call_id)
        
        if not audio_path:
            logger.warning("Failed to save audio file, auto-rejecting")
            return {
                "action": "manager_approval",
                "approved": False,
                "method": "auto_rejected_save_failed",
                "manager_response": "We can't help you today. Failed to save audio file."
            }
        
        # Construct full audio URL (ngrok + local path)
        audio_url = f"{webhook_base_url}{audio_path}"
        logger.info(f"Audio URL: {audio_url}")
        
        # Step 3: Make ONE Twilio call
        gather_webhook_url = f"{webhook_base_url}/webhooks/approval/gather"
        
        call_sid = await _make_twilio_call_with_audio(
            settings.manager_phone,
            audio_url,
            gather_webhook_url
        )
        
        if not call_sid:
            logger.warning("Failed to make Twilio call, auto-rejecting")
            return {
                "action": "manager_approval",
                "approved": False,
                "method": "auto_rejected_call_failed",
                "manager_response": "We can't help you today. Failed to make phone call."
            }
        
        # Return pending status - webhook will update the actual result
        logger.info(f"Call initiated successfully. Call SID: {call_sid}")
        return {
            "action": "manager_approval",
            "approved": False,  # Pending - will be updated by webhook
            "method": "phone_call_pending",
            "call_sid": call_sid,
            "manager_response": "Call placed - awaiting manager response (10s timeout)",
            "audio_url": audio_url,
            "call_id": call_id,
            "note": "Call in progress. Webhook will update the result."
        }
        
    except Exception as e:
        logger.error(f"Exception during voice approval: {e}", exc_info=True)
        return {
            "action": "manager_approval",
            "approved": False,
            "method": "auto_rejected_exception",
            "manager_response": "We can't help you today. System error during approval process.",
            "error": str(e)
        }


