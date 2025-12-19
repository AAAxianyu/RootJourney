"""
AI问答路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/ai", tags=["ai"])

ai_service = AIService()


class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: str
    answer: str


class ChatResponse(BaseModel):
    """聊天响应模型"""
    question: Optional[str] = None
    status: str  # "continue" or "complete"


@router.post("/chat", response_model=ChatResponse)
async def chat_response(request: ChatRequest):
    """
    AI问答接口
    输入用户回答，AI生成下一个问题或结束收集
    """
    try:
        next_question = await ai_service.process_answer(request.session_id, request.answer)
        
        if next_question is None:
            return ChatResponse(status="complete")
        
        return ChatResponse(question=next_question, status="continue")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/question/{session_id}")
async def get_question(session_id: str):
    """
    获取当前问题
    用于获取初始问题或重新获取问题
    """
    try:
        question = await ai_service.get_initial_question(session_id)
        return {"question": question}
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
