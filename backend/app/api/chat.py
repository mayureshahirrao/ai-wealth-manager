"""
chat.py — Chat/AI endpoints with SSE streaming.
Stub — full agentic implementation in Phase 4.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_guard import get_current_user, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.database.transaction import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    client_id: str
    query: str = Field(..., max_length=2000)
    message_history: list[dict] = []


@router.post("/message")
async def chat_message(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Streaming chat endpoint — returns SSE stream.
    Phase 4 will wire in the full agentic Claude loop.
    """
    async def stub_stream():
        import json
        # Stub: echo back a placeholder response
        delta = {"type": "delta", "text": f"[AI coming in Phase 4] You asked: {payload.query}"}
        yield f"data: {json.dumps(delta)}\n\n"
        done = {"type": "done", "confidence": 0.0}
        yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(stub_stream(), media_type="text/event-stream")


@router.get("/history/{client_id}")
async def get_chat_history(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    from sqlalchemy import select
    from app.database.models import ChatMessage, Client
    import uuid

    client_result = await db.execute(select(Client).where(Client.id == uuid.UUID(client_id)))
    client = client_result.scalar_one_or_none()
    if not client:
        return success_response(data=[])

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.client_id == client.id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return success_response(data=[
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.created_at.isoformat(),
            "confidence": m.confidence_score,
        }
        for m in messages
    ])
