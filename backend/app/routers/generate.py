"""
生成输出路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.output_service import OutputService
from app.utils.logger import logger

router = APIRouter(prefix="/generate", tags=["generate"])

output_service = OutputService()


class ReportRequest(BaseModel):
    """生成报告请求模型"""
    session_id: str


class TimelineRequest(BaseModel):
    """生成时间轴请求模型"""
    session_id: str
    family_filter: Optional[str] = None


class BiographyRequest(BaseModel):
    """生成传记请求模型"""
    session_id: str


class ImageGenerationRequest(BaseModel):
    """生成图片请求模型"""
    session_id: str
    num_images: int = 1  # 生成图片数量（1-2）
    size: str = "2K"  # 图片分辨率


@router.post("/report")
async def generate_report(request: ReportRequest):
    """
    生成家族报告
    返回包含文字和图片的完整报告
    
    报告生成后，会话会自动标记为可归档状态
    """
    try:
        report = await output_service.generate_report(request.session_id)
        
        # 报告生成成功，返回成功消息
        return {
            "report": report,
            "message": "报告生成成功！您可以查看报告，或将其保存为档案。",
            "can_archive": True
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"生成报告时出错：{str(e)}")


@router.post("/timeline")
async def generate_timeline(request: TimelineRequest):
    """
    生成时间轴
    支持多轴设计，可锁定特定家族查看时间线
    """
    try:
        timeline_data = await output_service.build_timeline(request.session_id, request.family_filter)
        return {"timeline": timeline_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/biography")
async def generate_biography(request: BiographyRequest):
    """
    生成个人传记
    整合用户输入和推测家族轨迹，生成融入家族叙事的个人故事
    """
    try:
        bio = await output_service.generate_bio(request.session_id)
        return {"biography": bio}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating biography: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images")
async def generate_images(request: ImageGenerationRequest):
    """
    基于报告生成图片（使用即梦4.0）
    根据已生成的家族报告，生成1-2张相关的图片
    
    注意：需要先调用 /generate/report 生成报告
    """
    try:
        # 验证参数
        if request.num_images < 1 or request.num_images > 2:
            raise HTTPException(
                status_code=400,
                detail="num_images must be between 1 and 2"
            )
        
        image_urls = await output_service.generate_images_from_report(
            session_id=request.session_id,
            num_images=request.num_images,
            size=request.size
        )
        
        return {
            "images": image_urls,
            "count": len(image_urls),
            "session_id": request.session_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating images: {e}")
        raise HTTPException(status_code=500, detail=str(e))
