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
    
    # 数据库配置
    database_url: Optional[str] = None
    
    # AI 服务配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # 搜索服务配置
    search_api_key: Optional[str] = None
    
    # 认证配置
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

