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
    
    # 兼容其他可能的字段名
    env: Optional[str] = None
    debug: Optional[str] = None
    serpapi_api_key: Optional[str] = None
    
    # AI 服务配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # DeepSeek API 配置
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"  # 默认模型
    
    # 讯飞语音转写配置
    xunfei_app_id: Optional[str] = None
    xunfei_api_key: Optional[str] = None
    xunfei_api_secret: Optional[str] = None
    
    # 搜索服务配置
    serpapi_key: Optional[str] = None
    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    
    # 生成式AI配置
    dall_e_model: str = "dall-e-3"
    stable_diffusion_url: Optional[str] = None  # 本地Stable Diffusion地址
    
    # 视频生成任务配置
    video_task_timeout: int = 300  # 视频生成任务超时时间（秒）
    
    # 认证配置
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 其他配置
    session_expire_seconds: int = 3600  # 会话过期时间（秒）
    max_questions: int = 20  # 最大问答轮数
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略 .env 中未定义的字段，避免验证错误
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 兼容处理：如果使用旧字段名，自动转换
        if self.mongo_uri and not kwargs.get('mongodb_url'):
            self.mongodb_url = self.mongo_uri
        if self.serpapi_api_key and not kwargs.get('serpapi_key'):
            self.serpapi_key = self.serpapi_api_key

settings = Settings()

