"""
AI问答路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/chat", tags=["ai_chat"])

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: dict = {}

class ChatResponse(BaseModel):
    message: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AI 聊天接口"""
    # TODO: 实现 AI 聊天逻辑
    raise HTTPException(status_code=501, detail="Not implemented")

