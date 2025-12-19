"""
生成输出路由
"""
from fastapi import APIRouter, HTTPException
from app.models.output import FamilyReport, Biography, Timeline

router = APIRouter(prefix="/api/generate", tags=["generate"])

@router.post("/report", response_model=FamilyReport)
async def generate_report(user_id: int):
    """生成家族报告"""
    # TODO: 实现报告生成逻辑
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/biography/{person_id}", response_model=Biography)
async def generate_biography(person_id: str):
    """生成个人传记"""
    # TODO: 实现传记生成逻辑
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/timeline/{person_id}", response_model=Timeline)
async def generate_timeline(person_id: str):
    """生成时间轴"""
    # TODO: 实现时间轴生成逻辑
    raise HTTPException(status_code=501, detail="Not implemented")

