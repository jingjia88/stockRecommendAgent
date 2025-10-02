"""Approval Manager Agent for handling manager approval workflow."""

import logging
from typing import Dict, Any, List, Optional
import json
import asyncio
import httpx
from agno.agent import Agent
from models import AgentAnalysis, ManagerApproval, ApprovalStatus, StockRecommendation
from tools.voice_services import request_manager_approval
from tools.mock_services import fetch_mock_manager_approval
from config import settings
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ApprovalManagerAgent(Agent):
    """Agent specialized in managing the approval workflow for stock recommendations."""
    
    def __init__(self):
        super().__init__(
            name="ApprovalManager",
            instructions="""You are a professional investment approval coordinator responsible for 
            ensuring all stock recommendations receive proper managerial oversight. Your goal is to 
            manage the approval process for stock recommendations through voice communication and approval 
            tracking. You excel at clear communication, summarizing complex investment rationales, and 
            managing approval workflows efficiently. You maintain high standards for investment approval 
            processes while ensuring smooth operations.""",
            tools=[]
        )
    
    async def request_approval(self, recommendations: List[StockRecommendation]) -> ManagerApproval:
        """
        Request manager approval for stock recommendations.
        
        Args:
            recommendations: List of stock recommendations to approve
            
        Returns:
            ManagerApproval object with approval result
        """
        try:
            logger.info(f"Starting approval process for {len(recommendations)} recommendations")
            
            # Generate approval summary
            approval_summary = self._generate_approval_summary(recommendations)
            logger.info("Generated approval summary")
            
            # Determine approval method
            if settings.mock_voice_services or not self._has_voice_credentials():
                logger.info("Using mock approval service")
                # Use mock approval - call the helper function directly
                try:
                    approval_result = await fetch_mock_manager_approval(approval_summary)
                    logger.info(f"Mock approval result: {approval_result.get('approved', 'unknown')}")
                except Exception as tool_error:
                    logger.error(f"Mock approval tool failed: {tool_error}", exc_info=True)
                    # Fallback to rejection
                    approval_result = {
                        "approved": False,
                        "manager_response": "We can't help you today.",
                        "method": "fallback_error",
                        "timestamp": datetime.now().isoformat(),
                        "note": "Mock service encountered an error"
                    }
            else:
                logger.info("Using real voice services for approval")
                # Use real voice services
                try:
                    # For real voice approval, we need to provide a webhook URL
                    # Get webhook URL from configuration
                    webhook_base_url = settings.webhook_base_url
                    
                    if not webhook_base_url:
                        logger.warning("WEBHOOK_BASE_URL not configured, voice approval will auto-approve")
                    
                    approval_result = await request_manager_approval(
                        approval_summary, 
                        webhook_base_url=webhook_base_url
                    )
                    logger.info(f"Voice approval result: {approval_result.get('approved', 'unknown')}")
                    logger.info(f"Voice approval method: {approval_result.get('method', 'unknown')}")
                    
                    # If the call is pending, wait for webhook response
                    if approval_result.get('method') == 'phone_call_pending' and approval_result.get('call_sid'):
                        logger.info(f"Call is pending, waiting for webhook response (max 60s)...")
                        call_sid = approval_result['call_sid']
                        
                        # Wait for webhook to update the approval result
                        final_result = await self._wait_for_webhook_result(call_sid, webhook_base_url, timeout=60)
                        
                        if final_result:
                            logger.info(f"Received webhook result: {final_result}")
                            approval_result = {
                                "approved": final_result.get('approved', False),
                                "manager_response": final_result.get('speech_result', 'No response'),
                                "method": "phone_call_completed",
                                "call_sid": call_sid,
                                "timestamp": final_result.get('timestamp'),
                                "confidence": final_result.get('confidence'),
                                "note": f"Manager responded via phone call"
                            }
                        else:
                            logger.warning("Webhook timeout - no response received")
                            approval_result = {
                                "approved": False,
                                "manager_response": "No response received within timeout",
                                "method": "phone_call_timeout",
                                "call_sid": call_sid,
                                "timestamp": datetime.now().isoformat(),
                                "note": "Manager did not respond within 60 seconds"
                            }
                    
                    if approval_result.get('recording_url'):
                        logger.info(f"Recording available at: {approval_result['recording_url']}")
                        
                except Exception as voice_error:
                    logger.error(f"Voice approval tool failed: {voice_error}", exc_info=True)
                    # Fallback to manual approval creation
                    approval_result = {
                        "approved": False,
                        "manager_response": "Voice service failed",
                        "method": "fallback",
                        "timestamp": datetime.now().isoformat(),
                        "note": "Voice service encountered an error"
                    }
            
            # Convert to ManagerApproval object
            manager_approval = self._create_manager_approval(approval_result)
            logger.info(f"Approval process completed: {manager_approval.status}")
            
            return manager_approval
            
        except Exception as e:
            logger.error(f"Error in approval process: {str(e)}", exc_info=True)
            # Return a fallback approval
            return ManagerApproval(
                status=ApprovalStatus.REJECTED,
                manager_response=f"Approval process failed: {str(e)}",
                notes="System error during approval process"
            )
    
    def _generate_approval_summary(self, recommendations: List[StockRecommendation]) -> str:
        """
        Generate a concise summary for manager approval.
        
        Args:
            recommendations: List of stock recommendations
            
        Returns:
            Formatted approval summary string
        """
        if not recommendations:
            return "No stock recommendations to approve."
        
        summary_parts = []
        summary_parts.append(f"Stock Recommendation Approval Request - {len(recommendations)} stocks")
        
        # Add overall summary
        total_confidence = sum(r.confidence_score for r in recommendations) / len(recommendations)
        avg_confidence_pct = int(total_confidence * 100)
        
        summary_parts.append(f"\nOverall confidence: {avg_confidence_pct}%")
        summary_parts.append("Please approve or reject these recommendations.")
        
        return "\n".join(summary_parts)
    
    def _has_voice_credentials(self) -> bool:
        """Check if voice service credentials are available."""
        return bool(
            settings.elevenlabs_api_key and 
            settings.twilio_account_sid and 
            settings.twilio_auth_token and
            settings.manager_phone
        )
    
    async def _wait_for_webhook_result(self, call_sid: str, webhook_base_url: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """
        Wait for webhook to receive and process the manager's response.
        
        Polls the /webhooks/approval/result/{call_sid} endpoint to check if webhook has received the result.
        
        Args:
            call_sid: Twilio call SID
            webhook_base_url: Base URL for webhooks
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dictionary with approval result if received, None if timeout
        """
        endpoint = f"{webhook_base_url}/webhooks/approval/result/{call_sid}"
        start_time = asyncio.get_event_loop().time()
        poll_interval = 2  # Check every 2 seconds
        
        logger.info(f"Polling {endpoint} for approval result...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    response = await client.get(endpoint)
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Webhook result retrieved: {result}")
                        return result
                    elif response.status_code == 404:
                        # Not ready yet, keep polling
                        logger.debug(f"Approval not ready yet, waiting {poll_interval}s...")
                        await asyncio.sleep(poll_interval)
                    else:
                        logger.warning(f"Unexpected status code {response.status_code}, continuing to poll...")
                        await asyncio.sleep(poll_interval)
                        
                except Exception as e:
                    logger.debug(f"Error polling webhook: {e}, retrying...")
                    await asyncio.sleep(poll_interval)
            
            logger.warning(f"Timeout reached ({timeout}s) waiting for webhook response")
            return None
    
    def _create_manager_approval(self, approval_result: Dict[str, Any]) -> ManagerApproval:
        """
        Convert approval result to ManagerApproval object.
        
        Args:
            approval_result: Dictionary with approval result
            
        Returns:
            ManagerApproval object
        """
        approved = approval_result.get("approved", False)
        
        # Override manager_response based on approval status
        if approved:
            manager_response = "Even the senior manager thinks this is a great idea!"
        else:
            manager_response = "We can't help you today."
        
        return ManagerApproval(
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            manager_response=manager_response,
            notes=approval_result.get("note", ""),
            approval_method=approval_result.get("method", "unknown"),
            raw_response=approval_result.get("raw_manager_response", approval_result.get("manager_response", "")),
            call_sid=approval_result.get("call_sid"),
            recording_url=approval_result.get("recording_url")
        )
    
    async def run(self, task: str, **kwargs) -> AgentAnalysis:
        """
        Main execution method for the Approval Manager Agent.
        
        Args:
            task: Task description
            **kwargs: Task-specific parameters including 'recommendations'
            
        Returns:
            AgentAnalysis with approval results
        """
        try:
            recommendations = kwargs.get("recommendations", [])
            
            if not recommendations:
                return AgentAnalysis(
                    agent_name=self.name,
                    analysis="No recommendations provided for approval",
                    confidence=0.0,
                    data={"error": "No recommendations provided"}
                )
            
            # Request manager approval
            approval = await self.request_approval(recommendations)
            
            # Format analysis summary
            analysis_text = self._format_approval_summary(approval, recommendations)
            
            return AgentAnalysis(
                agent_name=self.name,
                analysis=analysis_text,
                confidence=1.0 if approval.status == ApprovalStatus.APPROVED else 0.0,
                data={
                    "approval": approval.dict(),
                    "recommendations_count": len(recommendations),
                    "approval_method": approval.approval_method
                }
            )
            
        except Exception as e:
            logger.error(f"Error in approval manager run: {str(e)}", exc_info=True)
            return AgentAnalysis(
                agent_name=self.name,
                analysis=f"Approval process failed: {str(e)}",
                confidence=0.0,
                data={"error": str(e)}
            )
    
    def _format_approval_summary(self, approval: ManagerApproval, recommendations: List[StockRecommendation]) -> str:
        """
        Format the approval results into a readable summary.
        
        Args:
            approval: ManagerApproval object
            recommendations: List of stock recommendations
            
        Returns:
            Formatted summary string
        """
        status_emoji = "✅" if approval.status == ApprovalStatus.APPROVED else "❌"
        
        summary = f"{status_emoji} MANAGER APPROVAL RESULTS\n\n"
        summary += f"Status: {approval.status.value}\n"
        summary += f"Method: {approval.approval_method}\n"
        summary += f"Response: {approval.manager_response}\n"
        
        if approval.raw_response:
            summary += f"Manager's exact words: \"{approval.raw_response}\"\n"
        
        if approval.recording_url:
            summary += f"Recording: {approval.recording_url}\n"
        
        if approval.notes:
            summary += f"Notes: {approval.notes}\n"
        
        summary += f"\nRecommendations processed: {len(recommendations)}\n"
        
        # Add recommendation summary
        if recommendations:
            summary += "\nRecommendations:\n"
            for i, rec in enumerate(recommendations, 1):
                summary += f"{i}. {rec.symbol} - {rec.recommendation_type}\n"
        
        return summary
    