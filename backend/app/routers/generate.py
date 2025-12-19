"""
生成输出路由
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.output_service import OutputService
from app.utils.logger import logger

router = APIRouter(prefix="/generate", tags=["generate"])

output_service = OutputService()


@router.post("/report")
async def generate_report(session_id: str):
    """
    生成家族报告
    返回包含文字和图片的完整报告
    """
    try:
        report = await output_service.generate_report(session_id)
        return {"report": report}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeline")
async def generate_timeline(session_id: str, family_filter: Optional[str] = None):
    """
    生成时间轴
    支持多轴设计，可锁定特定家族查看时间线
    """
    try:
        timeline_data = await output_service.build_timeline(session_id, family_filter)
        return {"timeline": timeline_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/biography")
async def generate_biography(session_id: str):
    """
    生成个人传记
    整合用户输入和推测家族轨迹，生成融入家族叙事的个人故事
    """
    try:
        bio = await output_service.generate_bio(session_id)
        return {"biography": bio}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating biography: {e}")
        raise HTTPException(status_code=500, detail=str(e))
