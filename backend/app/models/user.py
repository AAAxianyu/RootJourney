"""
用户输入模型
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserInput(BaseModel):
    """用户输入数据模型"""
    name: str  # 姓名
    birth_date: Optional[str] = None  # 出生年月日
    birth_place: Optional[str] = None  # 籍贯
    current_location: Optional[str] = None  # 当前地区
    additional_info: Optional[str] = None  # 额外信息

class UserResponse(BaseModel):
    """用户响应模型"""
    session_id: str
    message: str = "会话已创建"

class ChatAnswer(BaseModel):
    """用户回答模型"""
    session_id: str
    answer: str  # 用户回答内容

