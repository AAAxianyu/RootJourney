"""
导出路由
"""
from fastapi import APIRouter, HTTPException
from app.services.output_service import OutputService
# 视频生成功能已移除
from app.utils.logger import logger

router = APIRouter(prefix="/export", tags=["export"])

output_service = OutputService()


@router.get("/{type}")
async def export_output(session_id: str, type: str):
    """
    导出输出
    支持 pdf 和 video 两种类型
    """
    try:
        if type == "pdf":
            pdf_url = await output_service.export_pdf(session_id)
            return {"url": pdf_url, "type": "pdf"}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export type: {type}. Only 'pdf' is supported.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting {type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
