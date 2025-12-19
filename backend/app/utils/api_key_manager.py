"""
API 密钥管理器
支持运行时手动输入和管理 API 密钥
"""
from typing import Optional, Dict
from app.config import settings
from app.utils.logger import logger

# 运行时密钥存储（内存中）
_runtime_keys: Dict[str, str] = {}


class APIKeyManager:
    """API 密钥管理器"""
    
    @staticmethod
    def set_deepseek_key(api_key: str):
        """设置 DeepSeek API Key（运行时）"""
        _runtime_keys["deepseek"] = api_key
        logger.info("DeepSeek API Key 已设置（运行时）")
    
    @staticmethod
    def get_deepseek_key() -> Optional[str]:
        """获取 DeepSeek API Key（优先使用运行时设置的）"""
        return _runtime_keys.get("deepseek") or settings.deepseek_api_key
    
    @staticmethod
    def set_openai_key(api_key: str):
        """设置 OpenAI API Key（运行时）"""
        _runtime_keys["openai"] = api_key
        logger.info("OpenAI API Key 已设置（运行时）")
    
    @staticmethod
    def get_openai_key() -> Optional[str]:
        """获取 OpenAI API Key（优先使用运行时设置的）"""
        return _runtime_keys.get("openai") or settings.openai_api_key
    
    @staticmethod
    def clear_runtime_keys():
        """清除所有运行时设置的密钥"""
        _runtime_keys.clear()
        logger.info("已清除所有运行时密钥")
    
    @staticmethod
    def get_all_keys_status() -> Dict[str, bool]:
        """获取所有 API Key 的配置状态"""
        return {
            "openai": bool(APIKeyManager.get_openai_key()),
            "deepseek": bool(APIKeyManager.get_deepseek_key()),
            "google_search": bool(settings.google_search_api_key and settings.google_search_engine_id),
            "xunfei": bool(settings.xunfei_app_id and settings.xunfei_api_key and settings.xunfei_api_secret)
        }

