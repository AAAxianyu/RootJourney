"""
健康检查和 API 连接状态检查路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.config import settings
from app.services.gateway_service import GatewayService
from app.utils.logger import logger

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
    status = {
        "openai": {
            "configured": bool(settings.openai_api_key),
            "status": "configured" if settings.openai_api_key else "not_configured"
        },
        "xunfei": {
            "configured": all([
                settings.xunfei_app_id,
                settings.xunfei_api_key,
                settings.xunfei_api_secret
            ]),
            "status": "configured" if all([
                settings.xunfei_app_id,
                settings.xunfei_api_key,
                settings.xunfei_api_secret
            ]) else "not_configured"
        },
        "google_search": {
            "configured": bool(
                settings.google_search_api_key and 
                settings.google_search_engine_id
            ),
            "status": "configured" if (
                settings.google_search_api_key and 
                settings.google_search_engine_id
            ) else "not_configured"
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
        status["openai"]["configured"],
        status["xunfei"]["configured"],
        status["google_search"]["configured"],
        status["mongodb"]["configured"],
        status["redis"]["configured"]
    ])
    
    return {
        "overall": "ready" if all_configured else "partial",
        "services": status
    }


@router.post("/test/openai")
async def test_openai():
    """
    测试 OpenAI API 连接
    实际调用 API 验证连接
    """
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    
    try:
        # 测试简单的聊天请求
        response = await gateway_service.llm_chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4",
            temperature=0.7
        )
        
        return {
            "success": True,
            "service": "OpenAI",
            "message": "Connection successful",
            "test_response": response[:100] + "..." if len(response) > 100 else response
        }
    except Exception as e:
        logger.error(f"OpenAI test error: {e}")
        return {
            "success": False,
            "service": "OpenAI",
            "error": str(e)
        }


@router.post("/test/xunfei")
async def test_xunfei():
    """
    测试讯飞 API 连接
    注意：需要提供测试音频文件
    """
    if not all([settings.xunfei_app_id, settings.xunfei_api_key, settings.xunfei_api_secret]):
        raise HTTPException(status_code=400, detail="讯飞 API 配置不完整")
    
    # 这里只检查配置，实际测试需要音频文件
    # 可以通过 /api/voice/transcribe 接口进行实际测试
    return {
        "success": True,
        "service": "Xunfei",
        "message": "Configuration valid. Use /api/voice/transcribe to test with audio file",
        "configured": True
    }


@router.post("/test/search")
async def test_search():
    """
    测试 Google Search API 连接
    实际调用 API 验证连接
    """
    if not (settings.google_search_api_key and settings.google_search_engine_id):
        raise HTTPException(status_code=400, detail="Google Search API not configured")
    
    try:
        # 测试搜索
        results = await gateway_service.search("test", num_results=1)
        
        return {
            "success": True,
            "service": "Google Search",
            "message": "Connection successful",
            "test_results_count": len(results)
        }
    except Exception as e:
        logger.error(f"Google Search test error: {e}")
        return {
            "success": False,
            "service": "Google Search",
            "error": str(e)
        }


@router.post("/test/image")
async def test_image():
    """
    测试 DALL·E 图片生成
    实际调用 API 验证连接
    """
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    
    try:
        # 测试图片生成（使用简单提示词）
        image_url = await gateway_service.generate_image(
            prompt="a simple red circle on white background",
            size="256x256"
        )
        
        return {
            "success": True,
            "service": "DALL·E",
            "message": "Connection successful",
            "test_image_url": image_url
        }
    except Exception as e:
        logger.error(f"DALL·E test error: {e}")
        return {
            "success": False,
            "service": "DALL·E",
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
    
    # 测试 OpenAI
    try:
        if settings.openai_api_key:
            response = await gateway_service.llm_chat(
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4"
            )
            results["openai"] = {"success": True, "message": "Connected"}
        else:
            results["openai"] = {"success": False, "message": "Not configured"}
    except Exception as e:
        results["openai"] = {"success": False, "error": str(e)}
    
    # 测试 Google Search
    try:
        if settings.google_search_api_key and settings.google_search_engine_id:
            await gateway_service.search("test", num_results=1)
            results["google_search"] = {"success": True, "message": "Connected"}
        else:
            results["google_search"] = {"success": False, "message": "Not configured"}
    except Exception as e:
        results["google_search"] = {"success": False, "error": str(e)}
    
    # 测试 DALL·E
    try:
        if settings.openai_api_key:
            await gateway_service.generate_image("test", "256x256")
            results["dalle"] = {"success": True, "message": "Connected"}
        else:
            results["dalle"] = {"success": False, "message": "Not configured"}
    except Exception as e:
        results["dalle"] = {"success": False, "error": str(e)}
    
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
    
    # 检查讯飞配置
    if all([settings.xunfei_app_id, settings.xunfei_api_key, settings.xunfei_api_secret]):
        results["xunfei"] = {"success": True, "message": "Configured (requires audio file to test)"}
    else:
        results["xunfei"] = {"success": False, "message": "Not configured"}
    
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

