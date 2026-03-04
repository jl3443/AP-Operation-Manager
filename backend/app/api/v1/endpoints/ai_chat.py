"""AI Chat assistant endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.chat_service import chat

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = Field(None, max_length=64)


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the AI chat assistant."""
    result = chat(
        db=db,
        message=payload.message,
        conversation_id=payload.conversation_id,
        user_id=str(current_user.id),
    )
    return result
