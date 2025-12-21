"""
配置模块
环境变量、API密钥等配置
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API 配置
    api_title: str = "RootJourney API"
    api_version: str = "1.0.0"
    
    # MongoDB 配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "genealogy_tracer"
    # 兼容旧的字段名
    mongo_uri: Optional[str] = None
    
    # Redis 配置
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # DeepSeek API 配置
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"  # 默认模型
    
    # 博查API配置（联网搜索）
    bocha_api_key: Optional[str] = None
    bocha_api_base_url: str = "https://api.bochaai.com/v1"
    
    # 即梦4.0 API配置（图片生成）
    seedream_api_key: Optional[str] = None
    seedream_api_base_url: str = "https://api.302.ai"
    seedream_model: str = "doubao-seedream-4-0-250828"
    
    # 认证配置
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 其他配置
    session_expire_seconds: int = 3600  # 会话过期时间（秒）
    min_questions: int = 5  # 最少问答轮数（至少问5轮）
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略 .env 中未定义的字段，避免验证错误
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 兼容处理：如果使用旧字段名，自动转换
        if self.mongo_uri and not kwargs.get('mongodb_url'):
            self.mongodb_url = self.mongo_uri

settings = Settings()
