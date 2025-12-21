"""
API 密钥管理器（简化版）
支持运行时手动输入和管理 API 密钥（仅 DeepSeek）
"""
from typing import Optional
from app.config import settings
from app.utils.logger import logger

# 运行时密钥存储（内存中）
_runtime_deepseek_key: Optional[str] = None


class APIKeyManager:
    """API 密钥管理器（仅支持 DeepSeek）"""
    
    @staticmethod
    def set_deepseek_key(api_key: str):
        """设置 DeepSeek API Key（运行时）"""
        global _runtime_deepseek_key
        _runtime_deepseek_key = api_key
        logger.info("DeepSeek API Key 已设置（运行时）")
    
    @staticmethod
    def get_deepseek_key() -> Optional[str]:
        """获取 DeepSeek API Key（优先使用运行时设置的）"""
        global _runtime_deepseek_key
        return _runtime_deepseek_key or settings.deepseek_api_key
    
    @staticmethod
    def clear_runtime_keys():
        """清除所有运行时设置的密钥"""
        global _runtime_deepseek_key
        _runtime_deepseek_key = None
        logger.info("已清除所有运行时密钥")
