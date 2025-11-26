"""
HTTP Client for Analysis Microservice

This client handles communication between the main API (/app)
and the AI/ML analysis microservice (/analysis).
"""

import httpx
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AnalysisClient:
    """HTTP client to communicate with /analysis microservice"""
    
    def __init__(self):
        # Railway Private Networking URL
        # In Railway, services can communicate via: http://<service-name>.railway.internal:<port>
        self.base_url = os.getenv(
            "ANALYSIS_SERVICE_URL",
            "http://localhost:8001"  # Fallback for local development
        )
        self.timeout = httpx.Timeout(300.0, connect=10.0)  # 5 min for ML processing
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True
        )
        logger.info(f"AnalysisClient initialized with base_url: {self.base_url}")
    
    async def health_check(self) -> bool:
        """
        Check if analysis service is healthy and reachable
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=5.0
            )
            is_healthy = response.status_code == 200
            if is_healthy:
                logger.info("Analysis service health check: OK")
            else:
                logger.warning(f"Analysis service unhealthy: {response.status_code}")
            return is_healthy
        except Exception as e:
            logger.error(f"Analysis service health check failed: {e}")
            return False
    
    async def analyze_evaluation(
        self, 
        evaluation_id: int, 
        video_url: str,
        transcription: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger AI analysis for an evaluation
        
        Args:
            evaluation_id: ID of evaluation to analyze
            video_url: Cloudflare Stream URL or video path
            transcription: Optional pre-transcribed text (skips Whisper if provided)
        
        Returns:
            dict: Analysis results with structure:
                {
                    "analysis": "full GPT response",
                    "executive_view": "Vista Ejecutiva markdown",
                    "operative_view": "Vista Operativa JSON string"
                }
        
        Raises:
            Exception: If analysis service fails or times out
        """
        try:
            logger.info(f"Requesting analysis for evaluation {evaluation_id}")
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/evaluation-analysis",
                json={
                    "evaluation_id": evaluation_id,
                    "video_url": video_url,
                    "transcription": transcription
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Analysis completed for evaluation {evaluation_id}")
            return result
        
        except httpx.TimeoutException as e:
            error_msg = f"Analysis service timeout after {self.timeout.read}s"
            logger.error(f"{error_msg} for evaluation {evaluation_id}: {e}")
            raise Exception(error_msg)
        
        except httpx.HTTPStatusError as e:
            error_msg = f"Analysis service error: {e.response.status_code}"
            logger.error(f"{error_msg} for evaluation {evaluation_id}: {e.response.text}")
            raise Exception(f"{error_msg} - {e.response.text}")
        
        except Exception as e:
            logger.error(f"Unexpected error during analysis for evaluation {evaluation_id}: {e}")
            raise
    
    async def get_intelligence_insights(
        self, 
        company_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get intelligence insights from /analysis service
        
        Args:
            company_id: Company ID to get insights for
            filters: Optional filters (date range, campaign_ids, etc.)
        
        Returns:
            dict: Intelligence insights with trends, NPS, tagging, etc.
        """
        try:
            params = {"company_id": company_id}
            if filters:
                params.update(filters)
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/intelligence/company/{company_id}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Intelligence service error for company {company_id}: {e}")
            raise Exception(f"Intelligence service error: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Unexpected error getting intelligence for company {company_id}: {e}")
            raise
    
    async def transcribe_audio(
        self,
        audio_url: str
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_url: URL to audio file
        
        Returns:
            dict: {"transcription": "text", "language": "es"}
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/transcribe",
                json={"audio_url": audio_url}
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Transcription failed for {audio_url}: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client connection"""
        await self.client.aclose()


# Singleton instance
_analysis_client: Optional[AnalysisClient] = None


def get_analysis_client() -> AnalysisClient:
    """
    Dependency injection for FastAPI
    
    Usage in routes:
        async def my_route(client: AnalysisClient = Depends(get_analysis_client)):
            result = await client.analyze_evaluation(...)
    """
    global _analysis_client
    if _analysis_client is None:
        _analysis_client = AnalysisClient()
    return _analysis_client
