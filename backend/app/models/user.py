"""
用户输入模型
"""
from pydantic import BaseModel
from typing import Optional

class UserInput(BaseModel):
    """用户输入数据模型"""
    name: str
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    additional_info: Optional[str] = None

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    name: str
    created_at: str

