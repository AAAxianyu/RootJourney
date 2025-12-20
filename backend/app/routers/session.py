"""
会话管理路由
用于查看和保存会话档案
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.dependencies.db import get_mongodb_db
from app.utils.logger import logger
from datetime import datetime

router = APIRouter(prefix="/session", tags=["session"])


class SessionArchive(BaseModel):
    """会话档案模型"""
    title: str  # 必填：用户自定义的档案名称
    notes: Optional[str] = None  # 可选：备注信息


@router.get("/{session_id}")
async def get_session(session_id: str):
    """
    获取会话详情
    返回完整的会话数据，包括用户输入、收集的数据、报告等
    """
    try:
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # 移除 MongoDB 的 _id，转换为可序列化的格式
        # 兼容多种数据格式
        family_graph = session.get("family_graph", {})
        if isinstance(family_graph, dict) and "collected_data" in family_graph:
            # 新格式：family_graph.collected_data
            collected_data = family_graph.get("collected_data", {})
        elif isinstance(family_graph, dict) and family_graph:
            # 旧格式：family_graph 直接是 collected_data
            collected_data = family_graph
        else:
            # 备用：从 collected_data 字段获取
            collected_data = session.get("collected_data", {})
        
        session_data = {
            "session_id": session_id,
            "user_input": session.get("user_input", {}),
            "user_profile": session.get("user_profile", {}),
            "collected_data": collected_data,
            "family_graph": session.get("family_graph", {}),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
        }
        
        return {"session": session_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/report")
async def get_session_report(session_id: str):
    """
    获取会话的报告（如果已生成）
    返回已保存的报告，包括用户自定义的档案名称
    """
    try:
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # 检查是否有保存的报告
        report = session.get("report")
        archive_info = {
            "archived": session.get("archived", False),
            "archive_title": session.get("archive_title"),
            "archive_notes": session.get("archive_notes"),
            "archived_at": session.get("archived_at")
        }
        
        if report:
            return {
                "report": report,
                "archive_info": archive_info
            }
        else:
            return {
                "report": None,
                "archive_info": archive_info,
                "message": "报告尚未生成，请先调用 /generate/report"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/archive")
async def archive_session(session_id: str, archive: SessionArchive):
    """
    保存会话档案
    用户可以为档案自定义名称和备注，便于后续查看和管理
    
    注意：title 是必填字段，用户必须提供档案名称
    """
    try:
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # 验证并处理档案名称
        archive_title = archive.title.strip() if archive.title else ""
        if not archive_title:
            # 如果用户没有提供标题，使用默认标题
            user_name = session.get("user_input", {}).get("name", "用户")
            archive_title = f"{user_name}的家族历史档案"
        
        # 更新会话，添加档案信息
        update_data = {
            "archived": True,
            "archived_at": datetime.now().isoformat(),
            "archive_title": archive_title,  # 用户自定义的档案名称
            "archive_notes": archive.notes  # 用户添加的备注
        }
        
        await db.sessions.update_one(
            {"_id": session_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "会话已保存为档案",
            "session_id": session_id,
            "archive_title": archive_title,
            "archived_at": update_data["archived_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_sessions(user_id: Optional[str] = None, archived: Optional[bool] = None):
    """
    列出所有会话（支持筛选）
    """
    try:
        db = await get_mongodb_db()
        query = {}
        
        if user_id:
            query["user_input.user_id"] = user_id
        
        if archived is not None:
            query["archived"] = archived
        
        sessions = await db.sessions.find(query).sort("created_at", -1).limit(100).to_list(length=100)
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.get("_id"),
                "user_name": session.get("user_input", {}).get("name"),
                "created_at": session.get("created_at"),
                "archived": session.get("archived", False),
                "archive_title": session.get("archive_title"),  # 用户自定义的档案名称
                "archive_notes": session.get("archive_notes"),  # 用户添加的备注
                "archived_at": session.get("archived_at"),
                "has_report": bool(session.get("report"))
            })
        
        return {"sessions": session_list, "count": len(session_list)}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
