import json
import logging
from typing import AsyncGenerator
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIClient:
    """Client for communicating with the AI Inference Server."""
    
    def __init__(self):
        self.base_url = settings.AI_INFERENCE_SERVER_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_sync(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> dict:
        """Call the synchronous generation endpoint."""
        url = f"{self.base_url}/v1/generate"
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error communicating with AI server: {e}")
            raise
            
    async def generate_stream(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Call the streaming generation endpoint and yield tokens."""
        url = f"{self.base_url}/v1/generate_stream"
        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature
        }
        
        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        token = line[6:]
                        if token == "[DONE]":
                            break
                        # Handle newlines that were escaped
                        yield token.replace("\\n", "\n")
        except httpx.HTTPError as e:
            logger.error(f"Error communicating with AI server for stream: {e}")
            raise
    
    async def close(self):
        await self.client.aclose()

ai_client = AIClient()
