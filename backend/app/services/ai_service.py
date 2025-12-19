"""
AI问答和NLP逻辑服务
处理AI问答循环，逐步丰富用户家族信息
"""
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import AsyncOpenAI
from app.config import settings
from app.models.user import UserInput
from app.dependencies.db import get_mongodb_db, get_redis
from app.utils.logger import logger
from app.utils.api_key_manager import APIKeyManager


class AIService:
    """AI 服务类"""
    
    def __init__(self):
        """初始化 AI 客户端（支持 OpenAI 和 DeepSeek）"""
        self.client = None
        self.model = "gpt-4"
        self._init_client()
    
    def _init_client(self):
        """初始化或更新客户端（支持运行时密钥）"""
        # 优先使用 DeepSeek，如果没有则使用 OpenAI
        deepseek_key = APIKeyManager.get_deepseek_key()
        if deepseek_key:
            # 如果客户端不存在或密钥变化，重新创建
            if not self.client or (hasattr(self.client, 'api_key') and self.client.api_key != deepseek_key):
                self.client = AsyncOpenAI(
                    api_key=deepseek_key,
                    base_url=settings.deepseek_base_url
                )
                self.model = settings.deepseek_model
                logger.info("使用 DeepSeek API")
        else:
            openai_key = APIKeyManager.get_openai_key()
            if openai_key:
                # 如果客户端不存在或密钥变化，重新创建
                if not self.client or (hasattr(self.client, 'api_key') and self.client.api_key != openai_key):
                    self.client = AsyncOpenAI(api_key=openai_key)
                    self.model = "gpt-4"
                    logger.info("使用 OpenAI API")
            else:
                if self.client:
                    self.client = None
                    logger.warning("LLM API key 已清除")
                else:
                    logger.warning("未配置 LLM API key (OpenAI 或 DeepSeek)")
    
    def _ensure_client(self):
        """确保客户端已初始化（在每次调用前检查）"""
        self._init_client()
        if not self.client:
            raise ValueError("未配置 LLM API key (OpenAI 或 DeepSeek)")
    
    async def start_session(self, input: UserInput) -> str:
        """
        初始化会话
        返回 session_id
        """
        session_id = str(uuid.uuid4())
        db = await get_mongodb_db()
        redis = await get_redis()
        
        # 存储到 MongoDB
        session_doc = {
            "_id": session_id,
            "user_input": input.dict(),
            "family_graph": {},
            "created_at": datetime.now().isoformat(),
            "status": "collecting"
        }
        await db.sessions.insert_one(session_doc)
        
        # 存储到 Redis
        cache_data = {
            "current_question": "initial",
            "collected_data": {"self": input.dict()},
            "question_count": 0
        }
        await redis.setex(
            f"session:{session_id}",
            settings.session_expire_seconds,
            json.dumps(cache_data)
        )
        
        logger.info(f"Session started: {session_id}")
        return session_id
    
    async def process_answer(self, session_id: str, answer: str) -> Optional[str]:
        """
        处理用户回答，生成下一个问题
        如果数据收集完成，返回 None
        """
        db = await get_mongodb_db()
        redis = await get_redis()
        
        # 获取当前状态
        cache_str = await redis.get(f"session:{session_id}")
        if not cache_str:
            raise ValueError(f"Session {session_id} not found")
        
        state = json.loads(cache_str)
        
        # 解析用户回答，提取家族信息
        extracted_info = await self._extract_family_info(answer, state["collected_data"])
        
        # 更新收集的数据
        state["collected_data"].update(extracted_info)
        state["question_count"] += 1
        
        # 更新 MongoDB
        await db.sessions.update_one(
            {"_id": session_id},
            {"$set": {"family_graph": state["collected_data"]}}
        )
        
        # 检查是否收集足够数据
        if state["question_count"] >= settings.max_questions or len(state["collected_data"]) >= 10:
            state["status"] = "complete"
            await redis.setex(
                f"session:{session_id}",
                settings.session_expire_seconds,
                json.dumps(state)
            )
            return None
        
        # 生成下一个问题
        next_question = await self._generate_next_question(state["collected_data"])
        
        # 更新状态
        state["current_question"] = next_question
        await redis.setex(
            f"session:{session_id}",
            settings.session_expire_seconds,
            json.dumps(state)
        )
        
        return next_question
    
    async def _extract_family_info(self, answer: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """从用户回答中提取家族信息"""
        if not self.client:
            # 如果没有配置 OpenAI，简单返回
            return {}
        
        prompt = f"""
基于用户回答和已有数据，提取家族信息（姓名、关系、籍贯、出生年份等）。
用户回答：{answer}
已有数据：{json.dumps(existing_data, ensure_ascii=False)}
请以JSON格式返回提取的信息，例如：{{"father": {{"name": "xxx", "origin": "xxx"}}}}
只返回JSON，不要其他文字。
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
            # 尝试解析JSON
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            extracted = json.loads(content)
            return extracted
        except Exception as e:
            logger.error(f"Error extracting family info: {e}")
            return {}
    
    async def _generate_next_question(self, collected_data: Dict[str, Any]) -> str:
        """基于已收集数据生成下一个问题"""
        if not self.client:
            return "请告诉我更多关于您家族的信息。"
        
        prompt = f"""
基于已收集的家族数据，生成下一个问题来丰富家族信息。
已收集数据：{json.dumps(collected_data, ensure_ascii=False)}
要求：
1. 避免重复已问过的问题
2. 逐步深入，询问祖上信息（如：你爸爸的籍贯是哪里？你爷爷的名字和出生年份？）
3. 问题要自然、友好
4. 只返回问题，不要其他文字
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return "请告诉我更多关于您家族的信息。"
    
    async def summarize_family_data(self, session_id: str) -> Dict[str, Any]:
        """
        总结收集的数据
        返回结构化的家族轨迹数据
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        
        if not self.client:
            # 简单返回原始数据
            return {
                "generations": [{"gen1": [family_graph]}],
                "locations": list(set([v.get("birth_place") for v in family_graph.values() if isinstance(v, dict) and v.get("birth_place")]))
            }
        
        prompt = f"""
将以下家族数据总结为结构化格式：
{json.dumps(family_graph, ensure_ascii=False)}

请返回JSON格式：
{{
    "generations": [
        {{"gen1": [人物列表]}},
        {{"gen2": [人物列表]}}
    ],
    "locations": ["地点1", "地点2"],
    "timeline": [{{"year": 年份, "event": "事件描述"}}]
}}
只返回JSON，不要其他文字。
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            summary = json.loads(content)
            return summary
        except Exception as e:
            logger.error(f"Error summarizing family data: {e}")
            return {
                "generations": [{"gen1": [family_graph]}],
                "locations": [],
                "timeline": []
            }
    
    async def get_initial_question(self, session_id: str) -> str:
        """获取初始问题"""
        redis = await get_redis()
        cache_str = await redis.get(f"session:{session_id}")
        if cache_str:
            state = json.loads(cache_str)
            if state.get("current_question") != "initial":
                return state["current_question"]
        
        # 生成初始问题
        if self.client:
            prompt = "作为家族寻根助手，请生成第一个问题来了解用户的家族信息。问题要友好、自然。只返回问题，不要其他文字。"
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                question = response.choices[0].message.content.strip()
                
                # 更新缓存
                if cache_str:
                    state = json.loads(cache_str)
                    state["current_question"] = question
                    await redis.setex(
                        f"session:{session_id}",
                        settings.session_expire_seconds,
                        json.dumps(state)
                    )
                
                return question
            except Exception as e:
                logger.error(f"Error generating initial question: {e}")
        
        return "您好！请告诉我您的姓名、出生日期和籍贯，让我们开始探索您的家族历史。"
