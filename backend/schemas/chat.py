from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ChatMode(str, Enum):
    CHAT = "chat"
    REASONER = "reasoner"


class Message(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=4096)
    mode: ChatMode = ChatMode.CHAT
    history: List[Message] = Field(default_factory=list)


class ConversationMeta(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    conversations: List[ConversationMeta]
