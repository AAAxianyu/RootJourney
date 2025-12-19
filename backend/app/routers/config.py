"""
配置管理路由
支持运行时手动输入和管理 API 密钥
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.utils.api_key_manager import APIKeyManager
from app.utils.logger import logger

router = APIRouter(prefix="/config", tags=["config"])


class SetAPIKeyRequest(BaseModel):
    """设置 API Key 请求"""
    api_key: str
    provider: str  # "deepseek" 或 "openai"


class APIKeyStatusResponse(BaseModel):
    """API Key 状态响应"""
    status: dict
    message: str


@router.post("/api-key")
async def set_api_key(request: SetAPIKeyRequest):
    """
    手动设置 API Key（运行时）
    支持 DeepSeek 和 OpenAI
    """
    try:
        if request.provider.lower() == "deepseek":
            APIKeyManager.set_deepseek_key(request.api_key)
            return {
                "success": True,
                "message": "DeepSeek API Key 已设置",
                "provider": "deepseek"
            }
        elif request.provider.lower() == "openai":
            APIKeyManager.set_openai_key(request.api_key)
            return {
                "success": True,
                "message": "OpenAI API Key 已设置",
                "provider": "openai"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的 provider: {request.provider}，支持: deepseek, openai"
            )
    except Exception as e:
        logger.error(f"设置 API Key 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-key/status")
async def get_api_key_status():
    """
    获取所有 API Key 的配置状态
    """
    try:
        status = APIKeyManager.get_all_keys_status()
        return {
            "success": True,
            "status": status,
            "message": "配置状态查询成功"
        }
    except Exception as e:
        logger.error(f"查询 API Key 状态错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-key")
async def clear_api_keys(provider: Optional[str] = None):
    """
    清除 API Key（运行时设置的）
    provider: 如果提供，只清除指定 provider；如果不提供，清除所有
    """
    try:
        if provider:
            if provider.lower() == "deepseek":
                APIKeyManager.set_deepseek_key("")
                return {"success": True, "message": "DeepSeek API Key 已清除"}
            elif provider.lower() == "openai":
                APIKeyManager.set_openai_key("")
                return {"success": True, "message": "OpenAI API Key 已清除"}
            else:
                raise HTTPException(status_code=400, detail=f"不支持的 provider: {provider}")
        else:
            APIKeyManager.clear_runtime_keys()
            return {"success": True, "message": "所有运行时 API Key 已清除"}
    except Exception as e:
        logger.error(f"清除 API Key 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

