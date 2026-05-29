"""
chat.py — Chat/AI endpoints with SSE streaming.

Implements the full agentic Claude loop with:
- Tool-use (portfolio, goals, tax, market, retirement)
- SEBI compliance (disclaimer injection, query classification)
- ChatMessage + AIAuditLog persistence after each response
- Role-based tool selection (investor vs RM)
"""

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.role_guard import get_current_user, CurrentUser
from app.core.base_response import success_response, APIResponse
from app.database.transaction import get_db
from app.database.models import ChatMessage, AIAuditLog, Client
from app.database.base_model import UserRole
from app.ai.tools import build_tool_registry
from app.ai.tool_registry import ToolNames
from app.ai.streaming import (
    stream_chat_response,
    build_investor_system_prompt,
    build_rm_system_prompt,
)
from app.ai.compliance_injector import classify_query, estimate_confidence
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    client_id: str
    query: str = Field(..., min_length=1, max_length=2000)
    message_history: list[dict] = Field(default_factory=list)


@router.post("/message")
async def chat_message(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Streaming chat endpoint — returns SSE stream.

    Implements the agentic Claude tool-use loop. After the stream ends,
    persists ChatMessage and AIAuditLog records to DB.
    """
    # Validate client access
    try:
        client_uuid = uuid.UUID(payload.client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id format")

    # Investors can only query their own data
    if current_user.role == UserRole.INVESTOR:
        if current_user.client_id != client_uuid:
            raise HTTPException(status_code=403, detail="Access denied: cannot query another client's data")

    # Fetch client info for system prompt
    client_result = await db.execute(select(Client).where(Client.id == client_uuid))
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Build tool registry + select tools by role
    tool_registry = build_tool_registry(db)

    if current_user.role == UserRole.INVESTOR:
        tool_names = ToolNames.INVESTOR_TOOLS
        system_prompt = build_investor_system_prompt(
            client_name=client.name,
            risk_profile=client.risk_profile.value if hasattr(client.risk_profile, "value") else str(client.risk_profile),
        )
    else:
        # RM and Compliance see all tools
        tool_names = ToolNames.RM_TOOLS
        system_prompt = build_rm_system_prompt()

    # Build Claude messages array
    messages = list(payload.message_history)
    messages.append({"role": "user", "content": payload.query})

    # Accumulate response for DB persistence
    accumulated_text = ""
    accumulated_tools: list[str] = []
    final_confidence = 0.0
    start_ms = int(time.monotonic() * 1000)

    async def event_stream():
        nonlocal accumulated_text, accumulated_tools, final_confidence

        try:
            async for event_str in stream_chat_response(
                messages=messages,
                system_prompt=system_prompt,
                tool_registry=tool_registry,
                tool_names=tool_names,
                client_id=payload.client_id,
                user_query=payload.query,
            ):
                # Parse event to accumulate text + done metadata
                try:
                    event_data = json.loads(event_str.replace("data: ", "").strip())
                    if event_data.get("type") == "delta":
                        accumulated_text += event_data.get("text", "")
                    elif event_data.get("type") == "done":
                        accumulated_tools = event_data.get("tools_used", [])
                        final_confidence = event_data.get("confidence", 0.0)
                except (json.JSONDecodeError, AttributeError):
                    pass

                yield event_str

        finally:
            # Persist to DB after stream ends (runs even if client disconnects)
            if accumulated_text:
                await _persist_chat(
                    db=db,
                    client_id=client_uuid,
                    user_query=payload.query,
                    ai_response=accumulated_text,
                    tools_used=accumulated_tools,
                    confidence=final_confidence,
                    duration_ms=int(time.monotonic() * 1000) - start_ms,
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering for SSE
        },
    )


async def _persist_chat(
    db: AsyncSession,
    client_id: uuid.UUID,
    user_query: str,
    ai_response: str,
    tools_used: list[str],
    confidence: float,
    duration_ms: int,
) -> None:
    """
    Save ChatMessage (user + assistant) and AIAuditLog after a chat turn.
    Called from the stream's finally block.
    """
    try:
        # User message
        db.add(ChatMessage(
            client_id=client_id,
            role="user",
            content=user_query,
        ))

        # Assistant message
        db.add(ChatMessage(
            client_id=client_id,
            role="assistant",
            content=ai_response,
            confidence_score=confidence,
            tools_used=tools_used or None,
        ))

        # SEBI Audit Log
        primary_tool = tools_used[0] if tools_used else "general"
        db.add(AIAuditLog(
            client_id=client_id,
            tool_name=primary_tool,
            user_query=user_query[:500],
            ai_response_summary=ai_response[:500],
            confidence_score=confidence,
            disclaimer_injected=True,
            sebi_compliant=confidence >= 0.5,
            duration_ms=duration_ms,
        ))

        await db.commit()
        logger.info(
            "chat_persisted",
            client_id=str(client_id),
            tools_used=tools_used,
            confidence=confidence,
        )

    except Exception as exc:
        logger.error("chat_persist_failed", error=str(exc), client_id=str(client_id))
        # Don't raise — persistence failure shouldn't break the user experience
        await db.rollback()


@router.get("/history/{client_id}")
async def get_chat_history(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> APIResponse:
    """Get chat history for a client."""
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id format")

    # Investors can only see their own history
    if current_user.role == UserRole.INVESTOR and current_user.client_id != cid:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.client_id == cid)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return success_response(data=[
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.created_at.isoformat(),
            "confidence": m.confidence_score,
            "tools_used": m.tools_used,
        }
        for m in messages
    ])
