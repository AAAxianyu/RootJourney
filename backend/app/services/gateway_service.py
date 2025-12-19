"""
API Gateway 统一服务
封装所有第三方 API 调用
"""
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import AsyncOpenAI
import httpx
from app.config import settings
from app.dependencies.db import get_mongodb_db, get_redis
from app.services.voice_service import VoiceService
from app.services.gen_ai_service import GenAIService
from app.utils.logger import logger
from app.utils.api_key_manager import APIKeyManager


class GatewayService:
    """API Gateway 服务类"""
    
    def __init__(self):
        self.openai_client = None
        self.deepseek_client = None
        
        # 初始化 OpenAI 客户端
        openai_key = APIKeyManager.get_openai_key()
        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)
        
        # 初始化 DeepSeek 客户端
        deepseek_key = APIKeyManager.get_deepseek_key()
        if deepseek_key:
            self.deepseek_client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url=settings.deepseek_base_url
            )
        
        self.voice_service = VoiceService()
        self.gen_ai_service = GenAIService()
    
    def _get_llm_client(self, provider: str = "auto"):
        """
        获取 LLM 客户端（动态获取，支持运行时设置的密钥）
        provider: "openai", "deepseek", "auto"（自动选择）
        """
        # 动态获取密钥（优先使用运行时设置的）
        deepseek_key = APIKeyManager.get_deepseek_key()
        openai_key = APIKeyManager.get_openai_key()
        
        # 如果密钥变化，重新创建客户端
        if deepseek_key and (not self.deepseek_client or self.deepseek_client.api_key != deepseek_key):
            self.deepseek_client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url=settings.deepseek_base_url
            )
        
        if openai_key and (not self.openai_client or self.openai_client.api_key != openai_key):
            self.openai_client = AsyncOpenAI(api_key=openai_key)
        
        if provider == "deepseek":
            if not self.deepseek_client:
                raise ValueError("DeepSeek API key not configured")
            return self.deepseek_client, settings.deepseek_model
        
        if provider == "openai":
            if not self.openai_client:
                raise ValueError("OpenAI API key not configured")
            return self.openai_client, "gpt-4"
        
        # 自动选择：优先使用 DeepSeek，如果没有则使用 OpenAI
        if self.deepseek_client:
            return self.deepseek_client, settings.deepseek_model
        elif self.openai_client:
            return self.openai_client, "gpt-4"
        else:
            raise ValueError("No LLM API key configured (OpenAI or DeepSeek)")
    
    async def llm_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.7, provider: str = "auto") -> str:
        """
        LLM 问答（支持 OpenAI 和 DeepSeek）
        messages: 消息列表，格式 [{"role": "user", "content": "..."}]
        model: 模型名称（如果提供，会覆盖 provider 的选择）
        provider: "openai", "deepseek", "auto"（自动选择）
        """
        client, default_model = self._get_llm_client(provider)
        use_model = model or default_model
        
        try:
            response = await client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise
    
    async def llm_extract(self, text: str, schema: Dict[str, Any], model: Optional[str] = None, provider: str = "auto") -> Dict[str, Any]:
        """
        LLM 抽取 JSON（支持 OpenAI 和 DeepSeek）
        text: 要抽取的文本
        schema: JSON Schema 定义期望的结构
        model: 模型名称（可选）
        provider: "openai", "deepseek", "auto"（自动选择）
        """
        client, default_model = self._get_llm_client(provider)
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
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Google Custom Search
        query: 搜索关键词
        num_results: 返回结果数量
        """
        if not settings.google_search_api_key or not settings.google_search_engine_id:
            raise ValueError("Google Search API not configured")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "key": settings.google_search_api_key,
                    "cx": settings.google_search_engine_id,
                    "q": query,
                    "num": min(num_results, 10)  # Google API最多返回10条
                }
                response = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "google"
                    })
                
                return results
        except Exception as e:
            logger.error(f"Google search error: {e}")
            raise
    
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        """
        DALL·E 生成图片
        返回图片URL
        """
        return await self.gen_ai_service.text_to_image(prompt, size)
    
    async def create_video_task(self, prompt: str, duration: int = 10) -> str:
        """
        创建视频生成任务
        返回任务ID
        """
        task_id = str(uuid.uuid4())
        redis = await get_redis()
        db = await get_mongodb_db()
        
        # 存储任务信息到MongoDB
        task_doc = {
            "_id": task_id,
            "prompt": prompt,
            "duration": duration,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "result_url": None,
            "error": None
        }
        await db.video_tasks.insert_one(task_doc)
        
        # 存储任务状态到Redis（用于快速查询）
        await redis.setex(
            f"video_task:{task_id}",
            settings.video_task_timeout,
            json.dumps({"status": "pending"})
        )
        
        # 注意：视频生成任务需要在路由层使用 BackgroundTasks 来执行
        # 这里只创建任务记录，实际处理在路由层触发
        
        return task_id
    
    async def _process_video_task(self, task_id: str, prompt: str, duration: int):
        """处理视频生成任务（后台异步）"""
        redis = await get_redis()
        db = await get_mongodb_db()
        
        try:
            # 更新状态为处理中
            await db.video_tasks.update_one(
                {"_id": task_id},
                {"$set": {"status": "processing"}}
            )
            await redis.setex(
                f"video_task:{task_id}",
                settings.video_task_timeout,
                json.dumps({"status": "processing"})
            )
            
            # 调用视频生成API
            video_url = await self.gen_ai_service.text_to_video(prompt, duration)
            
            # 更新任务为完成
            await db.video_tasks.update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": "completed",
                        "result_url": video_url,
                        "completed_at": datetime.now().isoformat()
                    }
                }
            )
            await redis.setex(
                f"video_task:{task_id}",
                3600,  # 完成后保留1小时
                json.dumps({"status": "completed", "url": video_url})
            )
        except Exception as e:
            logger.error(f"Video task {task_id} error: {e}")
            # 更新任务为失败
            await db.video_tasks.update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.now().isoformat()
                    }
                }
            )
            await redis.setex(
                f"video_task:{task_id}",
                3600,
                json.dumps({"status": "failed", "error": str(e)})
            )
    
    async def get_video_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取视频生成任务状态
        返回任务状态信息
        """
        redis = await get_redis()
        db = await get_mongodb_db()
        
        # 先从Redis查询（快速）
        cache_str = await redis.get(f"video_task:{task_id}")
        if cache_str:
            cache_data = json.loads(cache_str)
            if cache_data.get("status") == "completed":
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "url": cache_data.get("url")
                }
            elif cache_data.get("status") == "failed":
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": cache_data.get("error")
                }
            else:
                return {
                    "task_id": task_id,
                    "status": cache_data.get("status", "pending")
                }
        
        # 从MongoDB查询
        task = await db.video_tasks.find_one({"_id": task_id})
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        return {
            "task_id": task_id,
            "status": task.get("status", "pending"),
            "url": task.get("result_url"),
            "error": task.get("error"),
            "created_at": task.get("created_at")
        }

