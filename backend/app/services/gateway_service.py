"""
API Gateway 统一服务
封装 DeepSeek LLM API 调用
"""
import json
import asyncio
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from app.config import settings
from app.utils.logger import logger
from app.utils.api_key_manager import APIKeyManager


class GatewayService:
    """API Gateway 服务类 - 仅支持 DeepSeek"""
    
    def __init__(self):
        self.deepseek_client = None
        
        # 初始化 DeepSeek 客户端
        deepseek_key = APIKeyManager.get_deepseek_key()
        if deepseek_key:
            self.deepseek_client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url=settings.deepseek_base_url
            )
    
    def _get_llm_client(self):
        """
        获取 DeepSeek LLM 客户端（动态获取，支持运行时设置的密钥）
        """
        # 动态获取密钥（优先使用运行时设置的）
        deepseek_key = APIKeyManager.get_deepseek_key()
        
        # 如果密钥变化，重新创建客户端
        if deepseek_key and (not self.deepseek_client or self.deepseek_client.api_key != deepseek_key):
            self.deepseek_client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url=settings.deepseek_base_url
            )
        
        if not self.deepseek_client:
            raise ValueError("DeepSeek API key not configured")
        
        return self.deepseek_client, settings.deepseek_model
    
    async def llm_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.7, enable_web_search: bool = False, timeout: float = 180.0) -> str:
        """
        DeepSeek LLM 问答
        messages: 消息列表，格式 [{"role": "user", "content": "..."}]
        model: 模型名称（如果提供，会覆盖默认模型）
        temperature: 温度参数
        enable_web_search: 是否启用联网搜索（当前 DeepSeek API 可能不支持，需要额外配置）
        timeout: 超时时间（秒），默认180秒（3分钟）
        
        注意：标准的 DeepSeek API 可能不支持联网搜索。
        如果需要真正的联网搜索，建议：
        1. 使用 DeepSeek-R1 模型（如果支持）
        2. 或集成 Google Search API 等外部搜索服务
        """
        client, default_model = self._get_llm_client()
        use_model = model or default_model
        
        try:
            # 构建请求参数
            request_params = {
                "model": use_model,
                "messages": messages,
                "temperature": temperature
            }
            
            # 注意：当前 DeepSeek API 的标准接口可能不支持联网搜索
            # 如果需要联网搜索，可能需要：
            # 1. 使用 DeepSeek-R1 模型（如果支持）
            # 2. 或通过外部搜索 API 获取结果后再调用 LLM
            
            # 添加超时控制
            response = await asyncio.wait_for(
                client.chat.completions.create(**request_params),
                timeout=timeout
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            logger.error(f"LLM chat timeout after {timeout}s")
            raise TimeoutError(f"DeepSeek API 调用超时（{timeout}秒）")
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise
    
    async def llm_extract(self, text: str, schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """
        DeepSeek LLM 抽取 JSON
        text: 要抽取的文本
        schema: JSON Schema 定义期望的结构
        model: 模型名称（可选）
        """
        client, default_model = self._get_llm_client()
        use_model = model or default_model
        
        schema_str = json.dumps(schema, ensure_ascii=False)
        prompt = f"""
请从以下文本中提取信息，并按照指定的JSON Schema格式返回。

文本内容：
{text}

JSON Schema：
{schema_str}

要求：
1. 只返回符合Schema的JSON，不要其他文字
2. 如果信息不存在，使用null
3. 确保JSON格式正确
"""
        
        try:
            response = await client.chat.completions.create(
                model=use_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM extract error: {e}")
            raise
