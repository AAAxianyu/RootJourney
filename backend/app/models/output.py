"""
输出模型
报告、时间轴、传记等
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TimelineEvent(BaseModel):
    """时间轴事件"""
    date: str
    title: str
    description: str
    person_id: Optional[str] = None

class Timeline(BaseModel):
    """时间轴模型"""
    events: List[TimelineEvent]

class Biography(BaseModel):
    """传记模型"""
    person_id: str
    person_name: str
    content: str
    timeline: Timeline

class FamilyReport(BaseModel):
    """家族报告模型"""
    title: str
    summary: str
    biographies: List[Biography]
    family_tree: Dict[str, Any]
    generated_at: str

