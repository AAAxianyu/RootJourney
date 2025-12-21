"""
记忆总结路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/memories", tags=["memories"])

ai_service = AIService()


class SummarizeRequest(BaseModel):
    """记忆总结请求模型"""
    session_id: str


class MemoryCard(BaseModel):
    """记忆卡片模型"""
    title: str
    content: str


class SummarizeResponse(BaseModel):
    """记忆总结响应模型"""
    memories: List[MemoryCard]


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_memories(request: SummarizeRequest):
    """
    总结对话历史，生成记忆卡片
    接收session_id，返回AI总结的记忆卡片列表
    """
    try:
        memories = await ai_service.summarize_memories(request.session_id)
        
        # 转换为响应格式
        memory_cards = [
            MemoryCard(title=mem["title"], content=mem["content"])
            for mem in memories
        ]
        
        return SummarizeResponse(memories=memory_cards)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error summarizing memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


















