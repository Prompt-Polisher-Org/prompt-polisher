import asyncio
from typing import Dict, Any
import logging

from celery import Task
from app.core.celery_app import celery_app
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class AsyncToSyncTask(Task):
    """Base Celery task class that allows running async code."""
    def run_async(self, coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

@celery_app.task(bind=True, base=AsyncToSyncTask, name="app.worker.generate_inference")
def generate_inference(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Celery task that delegates to the AI Inference Server synchronously.
    This can be used to process background generation requests.
    """
    logger.info(f"Running inference task for prompt: {prompt[:30]}...")
    
    # We call the async client using our base class helper
    try:
        result = self.run_async(
            ai_client.generate_sync(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature
            )
        )
        return result
    except Exception as e:
        logger.error(f"Inference task failed: {str(e)}")
        raise self.retry(exc=e, countdown=5, max_retries=3)
