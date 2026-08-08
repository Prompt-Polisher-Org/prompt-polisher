import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import asyncio

from app.db.session import get_db
from app.core.redis import get_redis
from app.dependencies import get_current_user
from app.models.user import User
from app.models.message import Message
from app.services.ai_client import ai_client

router = APIRouter()

class InferenceGenerateRequest(BaseModel):
    prompt: str = Field(..., description="The user's prompt to optimize")
    session_id: Optional[uuid.UUID] = Field(None, description="Chat session ID to attach to")
    preferences_override: Optional[Dict[str, Any]] = Field(None, description="Overrides for user preferences")

class InferenceGenerateResponse(BaseModel):
    generated_prompt: str
    token_count: int
    latency_ms: float

@router.post("/generate", response_model=InferenceGenerateResponse)
async def generate_rest_fallback(
    request: InferenceGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """REST fallback for prompt inference."""
    try:
        # 1. Call AI inference server
        # For simplicity, we extract temperature from preferences override if present
        temperature = 0.7
        if request.preferences_override and "temperature" in request.preferences_override:
            temperature = float(request.preferences_override["temperature"])
            
        ai_response = await ai_client.generate_sync(
            prompt=request.prompt,
            max_new_tokens=512,
            temperature=temperature
        )
        
        generated_prompt = ai_response["generated_text"]
        token_count = ai_response["token_count"]
        latency_ms = ai_response["latency_ms"]
        
        # 2. Save message to DB if session_id is provided
        if request.session_id:
            message = Message(
                session_id=request.session_id,
                raw_content=request.prompt,
                polished_content=generated_prompt
            )
            db.add(message)
            await db.commit()

        return InferenceGenerateResponse(
            generated_prompt=generated_prompt,
            token_count=token_count,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/stream/{session_id}")
async def websocket_stream(
    websocket: WebSocket,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time prompt generation stream.
    Auth via query param or first message (simplified for now: accepts connection).
    """
    await websocket.accept()
    
    try:
        # Wait for the first message to get the prompt
        data = await websocket.receive_json()
        prompt = data.get("prompt")
        preferences = data.get("preferences_override", {})
        temperature = float(preferences.get("temperature", 0.7))
        
        if not prompt:
            await websocket.send_json({"error": "No prompt provided"})
            await websocket.close(code=1003)
            return

        generated_prompt = ""
        
        # Stream from AI client and forward to WebSocket
        async for token in ai_client.generate_stream(prompt=prompt, temperature=temperature):
            generated_prompt += token
            # Forward the token text directly
            await websocket.send_json({"type": "token", "text": token})
            
        # Send a final DONE signal
        await websocket.send_json({"type": "done", "full_text": generated_prompt})
        
        # Save to DB
        message = Message(
            session_id=session_id,
            raw_content=prompt,
            polished_content=generated_prompt
        )
        db.add(message)
        await db.commit()
        
    except WebSocketDisconnect:
        print(f"Client disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"error": "Internal server error during generation"})
        try:
            await websocket.close(code=1011)
        except:
            pass
