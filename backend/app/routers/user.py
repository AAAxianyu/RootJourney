"""
用户相关路由
"""
from fastapi import APIRouter, HTTPException
from app.models.user import UserInput, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(user_input: UserInput):
    """创建用户"""
    # TODO: 实现用户创建逻辑
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """获取用户信息"""
    # TODO: 实现用户查询逻辑
    raise HTTPException(status_code=501, detail="Not implemented")

