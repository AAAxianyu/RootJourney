"""
数据库依赖注入
MongoDB 和 Redis 连接管理
"""
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# MongoDB 客户端
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_db = None

# Redis 客户端
_redis_client: Optional[aioredis.Redis] = None


async def get_mongodb_client() -> AsyncIOMotorClient:
    """获取 MongoDB 客户端"""
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        logger.info(f"Connected to MongoDB: {settings.mongodb_url}")
    return _mongodb_client


async def get_mongodb_db():
    """获取 MongoDB 数据库实例"""
    global _mongodb_db
    if _mongodb_db is None:
        client = await get_mongodb_client()
        _mongodb_db = client[settings.mongodb_db_name]
    return _mongodb_db


async def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端"""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.redis_url,
            db=settings.redis_db,
            decode_responses=True
        )
        logger.info(f"Connected to Redis: {settings.redis_url}")
    return _redis_client


async def close_db_connections():
    """关闭数据库连接"""
    global _mongodb_client, _redis_client
    if _mongodb_client:
        _mongodb_client.close()
        _mongodb_client = None
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    logger.info("Database connections closed")

