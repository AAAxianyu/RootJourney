"""
用户相关路由
"""
from fastapi import APIRouter, HTTPException
from app.models.user import UserInput, UserResponse
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/user", tags=["user"])

ai_service = AIService()


@router.post("/input", response_model=UserResponse)
async def submit_input(input: UserInput):
    """
    用户输入基本信息，启动会话
    返回 session_id
    """
    try:
        session_id = await ai_service.start_session(input)
        return UserResponse(session_id=session_id, message="会话已创建")
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
