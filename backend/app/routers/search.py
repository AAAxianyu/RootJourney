"""
搜索路由
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.search_service import SearchService
from app.services.graph_service import GraphService
from app.utils.logger import logger

router = APIRouter(prefix="/search", tags=["search"])

search_service = SearchService()
graph_service = GraphService()


@router.get("/family")
async def search_family(session_id: str):
    """
    搜索家族历史
    基于 session_id 中的家族图谱进行联网搜索
    """
    try:
        results = await search_service.perform_search(session_id)
        # 更新图谱
        await graph_service.update_graph(session_id, results)
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
