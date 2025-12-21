"""
健康检查和 API 连接状态检查路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.config import settings
from app.services.gateway_service import GatewayService
from app.utils.logger import logger
from app.utils.api_key_manager import APIKeyManager

router = APIRouter(prefix="/health", tags=["health"])

gateway_service = GatewayService()


@router.get("/")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "service": "RootJourney API"
    }


@router.get("/api-status")
async def api_status():
    """
    检查所有第三方 API 的配置状态
    不进行实际调用，只检查配置是否完整
    """
    deepseek_key = APIKeyManager.get_deepseek_key()
    
    bocha_key = settings.bocha_api_key
    
    status = {
        "deepseek": {
            "configured": bool(deepseek_key or settings.deepseek_api_key),
            "status": "configured" if (deepseek_key or settings.deepseek_api_key) else "not_configured"
        },
        "bochaai": {
            "configured": bool(bocha_key),
            "status": "configured" if bocha_key else "not_configured",
            "note": "博查API - 真正的联网搜索"
        },
        "mongodb": {
            "configured": bool(settings.mongodb_url),
            "status": "configured" if settings.mongodb_url else "not_configured"
        },
        "redis": {
            "configured": bool(settings.redis_url),
            "status": "configured" if settings.redis_url else "not_configured"
        }
    }
    
    # 计算总体状态
    all_configured = all([
        status["deepseek"]["configured"],
        status["mongodb"]["configured"],
        status["redis"]["configured"]
    ])
    # 博查API是可选的，不影响总体状态
    
    return {
        "overall": "ready" if all_configured else "partial",
        "services": status
    }


@router.post("/test/deepseek")
async def test_deepseek():
    """
    测试 DeepSeek API 连接
    实际调用 API 验证连接
    """
    deepseek_key = APIKeyManager.get_deepseek_key()
    if not deepseek_key:
        raise HTTPException(status_code=400, detail="DeepSeek API key not configured")
    
    try:
        # 测试简单的聊天请求
        response = await gateway_service.llm_chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7
        )
        
        return {
            "success": True,
            "service": "DeepSeek",
            "message": "Connection successful",
            "test_response": response[:100] + "..." if len(response) > 100 else response
        }
    except Exception as e:
        logger.error(f"DeepSeek test error: {e}")
        return {
            "success": False,
            "service": "DeepSeek",
            "error": str(e)
        }


@router.get("/test/database")
async def test_database():
    """
    测试 MongoDB 和 Redis 连接
    """
    results = {
        "mongodb": {"success": False, "error": None},
        "redis": {"success": False, "error": None}
    }
    
    # 测试 MongoDB
    try:
        from app.dependencies.db import get_mongodb_db
        db = await get_mongodb_db()
        # 尝试执行一个简单操作
        await db.command("ping")
        results["mongodb"] = {"success": True, "message": "Connected"}
    except Exception as e:
        logger.error(f"MongoDB test error: {e}")
        results["mongodb"] = {"success": False, "error": str(e)}
    
    # 测试 Redis
    try:
        from app.dependencies.db import get_redis
        redis = await get_redis()
        # 尝试执行一个简单操作
        await redis.ping()
        results["redis"] = {"success": True, "message": "Connected"}
    except Exception as e:
        logger.error(f"Redis test error: {e}")
        results["redis"] = {"success": False, "error": str(e)}
    
    return {
        "success": results["mongodb"]["success"] and results["redis"]["success"],
        "services": results
    }


@router.post("/test/all")
async def test_all():
    """
    测试所有 API 连接
    依次测试各个服务
    """
    results = {}
    
    # 测试 DeepSeek
    try:
        deepseek_key = APIKeyManager.get_deepseek_key()
        if deepseek_key:
            response = await gateway_service.llm_chat(
                messages=[{"role": "user", "content": "test"}]
            )
            results["deepseek"] = {"success": True, "message": "Connected"}
        else:
            results["deepseek"] = {"success": False, "message": "Not configured"}
    except Exception as e:
        results["deepseek"] = {"success": False, "error": str(e)}
    
    # 测试博查API（如果配置了）
    try:
        if settings.bocha_api_key:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.bocha_api_base_url}/web-search",
                    headers={
                        "Authorization": f"Bearer {settings.bocha_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": "测试",
                        "count": 1
                    }
                )
                if response.status_code == 200:
                    results["bochaai"] = {"success": True, "message": "BochaAI web search connected"}
                else:
                    results["bochaai"] = {"success": False, "error": f"HTTP {response.status_code}"}
        else:
            results["bochaai"] = {"success": False, "message": "Not configured"}
    except Exception as e:
        results["bochaai"] = {"success": False, "error": str(e)}
    
    # 测试数据库
    try:
        from app.dependencies.db import get_mongodb_db, get_redis
        db = await get_mongodb_db()
        await db.command("ping")
        redis = await get_redis()
        await redis.ping()
        results["database"] = {"success": True, "message": "MongoDB and Redis connected"}
    except Exception as e:
        results["database"] = {"success": False, "error": str(e)}
    
    # 计算总体状态
    all_success = all(
        result.get("success", False) 
        for result in results.values() 
        if result.get("message") != "Not configured"
    )
    
    return {
        "overall": "all_connected" if all_success else "partial",
        "results": results
    }
