"""
联网搜索逻辑服务
基于用户信息搜索大家族历史和相关信息
支持博查API（真正的联网搜索）和 DeepSeek（知识库搜索）
"""
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.dependencies.db import get_mongodb_db
from app.utils.logger import logger
from app.services.gateway_service import GatewayService
from app.config import settings
import json


class SearchService:
    """搜索服务类 - 支持博查API联网搜索和 DeepSeek 知识库搜索"""
    
    def __init__(self):
        """初始化搜索客户端"""
        self.gateway_service = GatewayService()
        self.bocha_api_key = settings.bocha_api_key
        self.bocha_api_base_url = settings.bocha_api_base_url
        
        if self.bocha_api_key:
            logger.info("SearchService initialized with BochaAI web search")
        else:
            logger.info("SearchService initialized with DeepSeek (knowledge base only)")
    
    async def search_with_bocha(self, query: str, num_results: int = 3, freshness: str = "oneYear") -> List[Dict[str, str]]:
        """
        使用博查API进行真正的联网搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            freshness: 结果新鲜度（oneYear, oneMonth, oneWeek, oneDay）
        
        Returns:
            搜索结果列表
        """
        if not self.bocha_api_key:
            logger.warning("BochaAI API key not configured, skipping web search")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.bocha_api_base_url}/web-search",
                    headers={
                        "Authorization": f"Bearer {self.bocha_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "freshness": freshness,
                        "summary": True,
                        "count": num_results
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"BochaAI API error: {response.status_code} - {response.text}")
                    return []
                
                data = response.json()
                
                # 解析博查API响应
                results = []
                web_pages = data.get("webPages", {}).get("value", [])
                
                for page in web_pages:
                    results.append({
                        "title": page.get("name", ""),
                        "snippet": page.get("snippet", ""),
                        "url": page.get("url", ""),
                        "source": "bochaai",
                        "datePublished": page.get("datePublished", ""),
                        "siteName": page.get("siteName", "")
                    })
                
                logger.info(f"BochaAI search returned {len(results)} results for query: {query}")
                return results
                
        except httpx.TimeoutException:
            logger.error(f"BochaAI API timeout for query: {query}")
            return []
        except Exception as e:
            logger.error(f"BochaAI search error: {e}")
            return []
    
    async def search_with_deepseek(self, query: str, num_results: int = 3, web_search_results: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        使用 DeepSeek 进行智能搜索和结果整理
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            web_search_results: 联网搜索结果（如果已通过博查API获取）
        
        如果提供了联网搜索结果，DeepSeek 会基于这些结果进行整理和总结
        如果没有，则基于知识库进行搜索
        """
        try:
            # 如果已有联网搜索结果，让 DeepSeek 基于这些结果进行整理
            if web_search_results and len(web_search_results) > 0:
                # 构建搜索结果摘要（只使用前3个结果以加快处理）
                search_summary = "\n\n".join([
                    f"**{r.get('title', '')}**\n{r.get('snippet', '')}\n来源：{r.get('url', '')}"
                    for r in web_search_results[:3]
                ])
                
                prompt = f"""
基于以下联网搜索的真实结果，整理和总结相关的历史信息，特别关注历史名人和家族历史：

搜索查询：{query}

联网搜索结果：
{search_summary}

请基于这些真实的搜索结果，提供简洁但完整的总结：
1. 相关的历史背景信息（基于搜索结果，200字以内）
2. 重要历史名人（列出3-5位，每位50-100字描述其成就和影响）
3. 地理位置和时间线（简要说明）
4. 文化传承和特色（100字以内）

请以温暖、有故事性的语言风格描述，但保持简洁。
请以结构化的方式返回信息，包括：
- 历史背景
- 重要历史名人（简要描述）
- 地理位置
- 时间线
- 文化特色

注意：请基于真实的搜索结果，不要编造信息。保持内容简洁但完整。
"""
            else:
                # 基于知识库的搜索
                prompt = f"""
请基于以下搜索查询，提供相关的历史信息摘要，特别关注历史名人和家族历史：

搜索查询：{query}

请提供简洁但完整的总结：
1. 相关的历史背景信息（200字以内）
2. 重要历史名人（列出3-5位，每位50-100字描述其成就和影响）
3. 地理位置和时间线（简要说明）
4. 文化传承和特色（100字以内）

请以温暖、有故事性的语言风格描述，但保持简洁。
请以结构化的方式返回信息，包括：
- 历史背景
- 重要历史名人（简要描述）
- 地理位置
- 时间线
- 文化特色

如果信息不足，请说明。保持内容简洁但完整。
"""
            
            # 使用 DeepSeek 进行整理（降低温度以加快响应速度）
            response = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # 降低温度以加快响应
                timeout=120  # 设置120秒超时
            )
            
            # 将响应转换为搜索结果格式
            return [{
                "title": query,
                "snippet": response,
                "url": "deepseek_processed",
                "source": "deepseek" if not web_search_results else "deepseek+bochaai"
            }]
        except Exception as e:
            logger.error(f"DeepSeek search error: {e}")
            return []
    
    async def search_family_history(self, family_name: str, location: Optional[str] = None) -> List[Dict[str, str]]:
        """
        搜索家族历史，特别关注历史名人
        优先使用博查API进行联网搜索，然后使用DeepSeek整理结果
        """
        query = f"{family_name} 家族历史 历史名人 著名人物"
        if location:
            query += f" {location}"
        
        # 1. 优先使用博查API进行联网搜索（减少结果数量以加快速度）
        web_results = await self.search_with_bocha(query, num_results=3)
        
        # 2. 使用DeepSeek基于联网搜索结果进行整理
        if web_results:
            logger.info(f"Using BochaAI web search results for: {query}")
            # 返回联网搜索结果 + DeepSeek整理后的摘要
            deepseek_summary = await self.search_with_deepseek(query, web_search_results=web_results)
            # 合并结果：先返回联网搜索结果，再返回DeepSeek整理的摘要
            return web_results + deepseek_summary
        else:
            # 如果联网搜索失败，回退到DeepSeek知识库搜索
            logger.info(f"Falling back to DeepSeek knowledge base for: {query}")
            return await self.search_with_deepseek(query)
    
    async def analyze_family_associations(self, collected_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分析用户可能与哪些大家族有关
        使用 DeepSeek 进行智能分析
        """
        try:
            # 提取关键信息，统一数据格式
            user_info_summary = []
            
            # 从不同可能的字段位置提取信息
            self_origin = (
                collected_data.get("self_origin") or 
                collected_data.get("self", {}).get("origin") or
                ""
            )
            father_origin = (
                collected_data.get("father_origin") or 
                collected_data.get("father", {}).get("origin") or
                ""
            )
            grandfather_name = (
                collected_data.get("grandfather_name") or 
                collected_data.get("grandfather", {}).get("name") or
                ""
            )
            surname = (
                collected_data.get("surname") or 
                collected_data.get("self", {}).get("surname") or
                ""
            )
            generation_char = (
                collected_data.get("generation_char") or 
                collected_data.get("self", {}).get("generation_name") or
                ""
            )
            
            # 构建用户信息摘要
            if surname:
                user_info_summary.append(f"姓氏：{surname}")
            if self_origin:
                user_info_summary.append(f"祖籍/籍贯：{self_origin}")
            if father_origin:
                user_info_summary.append(f"父亲籍贯：{father_origin}")
            if grandfather_name:
                user_info_summary.append(f"祖父姓名：{grandfather_name}")
            if generation_char:
                user_info_summary.append(f"辈分字：{generation_char}")
            
            # 获取未解析的对话内容
            unparsed_info = collected_data.get("_unparsed", [])
            if unparsed_info:
                user_info_summary.append("\n对话中的其他信息：")
                for item in unparsed_info[-5:]:  # 只取最近5条
                    user_info_summary.append(f"- {item.get('a', '')}")
            
            user_info_text = "\n".join(user_info_summary) if user_info_summary else "用户提供的信息较少"
            
            prompt = f"""
基于以下用户收集的家族信息，分析用户可能与哪些历史大家族有关：

**用户信息摘要：**
{user_info_text}

**完整数据（JSON格式）：**
{json.dumps(collected_data, ensure_ascii=False, indent=2)}

**重要要求：**
1. 即使信息较少，也要根据姓氏、籍贯等线索，推测可能的大家族（2-3个即可）
2. 如果信息不足，可以基于常见的历史大家族进行合理推测
3. 每个大家族包含3-5位历史名人，简要描述他们的成就和影响（每位50-100字）

请分析：
1. 根据姓氏、籍贯、辈分字等线索，判断可能与哪些历史大家族有关
2. 每个可能的大家族包括：
   - 家族名称
   - 历史背景（100字以内）
   - 主要分布地区
   - 著名人物（列出3-5位，每位50-100字描述其成就和影响）
   - 文化特色（50字以内）
   - 与用户信息的关联度（高/中/低）

特别注意：请为每个大家族列出3-5位历史名人，简要描述他们的成就和影响。保持内容简洁但完整。

请以 JSON 格式返回，格式如下：
{{
    "possible_families": [
        {{
            "family_name": "家族名称",
            "historical_background": "历史背景",
            "main_regions": ["地区1", "地区2"],
            "famous_figures": [
                {{
                    "name": "人物姓名",
                    "dynasty_period": "朝代/时期",
                    "achievements": "主要成就",
                    "story": "生平故事",
                    "influence": "历史影响"
                }}
            ],
            "cultural_features": "文化特色",
            "relevance": "高/中/低",
            "connection_clues": ["关联线索1", "关联线索2"]
        }}
    ]
}}

**重要**：即使信息不足，也要返回至少2-3个可能的大家族，不要返回空数组。
"""
            response = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # 降低温度以加快响应
                timeout=120  # 设置120秒超时
            )
            
            # 尝试解析 JSON 响应
            import json
            try:
                # 清理响应中的 markdown 代码块
                content = response.strip()
                if content.startswith("```"):
                    parts = content.split("```")
                    # 找到包含 json 的部分
                    for part in parts:
                        part = part.strip()
                        if part.startswith("json"):
                            content = part[4:].strip()
                            break
                        elif part.startswith("{"):
                            content = part.strip()
                            break
                else:
                    content = content.strip()
                
                # 如果内容以 { 开头，尝试直接解析
                if content.startswith("{"):
                    data = json.loads(content)
                    families = data.get("possible_families", [])
                    if families:
                        logger.info(f"Found {len(families)} possible families")
                        return families
                
                # 如果解析失败，尝试从文本中提取
                logger.warning("Failed to parse JSON directly, trying to extract from text")
                # 尝试找到 JSON 部分
                import re
                json_match = re.search(r'\{[^{}]*"possible_families"[^{}]*\[.*?\]', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        families = data.get("possible_families", [])
                        if families:
                            return families
                    except:
                        pass
                
                # 如果还是失败，基于响应内容创建默认结果
                logger.warning("Could not parse JSON, creating default family based on response")
                # 尝试从响应中提取姓氏或地区信息
                surname = collected_data.get("surname") or collected_data.get("self", {}).get("surname") or "未知"
                origin = collected_data.get("self_origin") or collected_data.get("self", {}).get("origin") or ""
                
                return [{
                    "family_name": f"{surname}氏家族" if surname != "未知" else "历史大家族",
                    "historical_background": "基于您提供的信息，这是一个可能的历史大家族",
                    "main_regions": [origin] if origin else ["中国"],
                    "famous_figures": [
                        {
                            "name": "待补充",
                            "dynasty_period": "待确认",
                            "achievements": "待补充",
                            "story": response[:200] if len(response) > 200 else response,
                            "influence": "待确认"
                        }
                    ],
                    "cultural_features": "待补充",
                    "relevance": "中",
                    "connection_clues": ["基于提供的信息推测"],
                    "raw_response": response  # 保存原始响应以便调试
                }]
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}, response: {response[:200]}")
                # 返回默认结果
                return [{
                    "family_name": "历史大家族",
                    "historical_background": "基于您提供的信息分析",
                    "main_regions": ["中国"],
                    "famous_figures": [],
                    "cultural_features": "待补充",
                    "relevance": "中",
                    "connection_clues": ["信息不足，基于常见模式推测"],
                    "raw_response": response
                }]
        except Exception as e:
            logger.error(f"Family association analysis error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 即使出错也返回一个默认结果，而不是空数组
            return [{
                "family_name": "历史大家族",
                "historical_background": "分析过程中出现错误，但基于常见历史模式推测",
                "main_regions": ["中国"],
                "famous_figures": [],
                "cultural_features": "待补充",
                "relevance": "低",
                "connection_clues": ["需要更多信息"],
                "error": str(e)
            }]
    
    async def perform_search(self, session_id: str) -> Dict[str, Any]:
        """
        执行搜索
        基于 session 中的家族图谱进行搜索
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        collected_data = session.get("family_graph", {}).get("collected_data", {})
        if not collected_data:
            # 尝试从 collected_data 字段获取
            collected_data = session.get("collected_data", {})
        
        results = {}
        
        # 1. 分析可能的大家族关联
        logger.info(f"Analyzing family associations for session {session_id}")
        possible_families = await self.analyze_family_associations(collected_data)
        
        # 2. 对每个可能的大家族进行历史搜索（并行执行，最多处理前3个最相关的家族）
        family_histories = {}
        # 只处理前3个最相关的家族，按关联度排序
        families_to_search = sorted(
            possible_families,
            key=lambda x: {"高": 3, "中": 2, "低": 1}.get(x.get("relevance", "低"), 1),
            reverse=True
        )[:3]  # 最多只搜索3个家族
        
        if families_to_search:
            logger.info(f"Searching history for {len(families_to_search)} families in parallel")
            # 并行执行多个家族的搜索
            search_tasks = []
            for family in families_to_search:
                family_name = family.get("family_name", "")
                if family_name:
                    task = self.search_family_history(
                        family_name,
                        location=family.get("main_regions", [None])[0] if family.get("main_regions") else None
                    )
                    search_tasks.append((family_name, family, task))
            
            # 并行执行所有搜索任务
            if search_tasks:
                results = await asyncio.gather(
                    *[task for _, _, task in search_tasks],
                    return_exceptions=True
                )
                
                for (family_name, family, _), history in zip(search_tasks, results):
                    if isinstance(history, Exception):
                        logger.error(f"Error searching for family {family_name}: {history}")
                        history = []
                    family_histories[family_name] = {
                        "family_info": family,
                        "history": history
                    }
        
        # 3. 对用户收集的具体信息进行搜索（仅在未找到家族时执行，减少不必要的搜索）
        user_searches = {}
        
        # 如果已经找到了家族，跳过额外的搜索以节省时间
        if not possible_families:
            # 从不同可能的字段位置提取信息
            surname = (
                collected_data.get("surname") or 
                collected_data.get("self", {}).get("surname") or
                None
            )
            origin = (
                collected_data.get("self_origin") or 
                collected_data.get("self", {}).get("origin") or
                None
            )
            
            if surname or origin:
                logger.info(f"No families found, searching based on surname={surname} or origin={origin}")
                search_query = f"{surname or ''} {origin or ''} 家族历史 历史名人".strip()
                if search_query:
                    # 使用联网搜索
                    additional_search = await self.search_family_history(search_query)
                    if additional_search:
                        user_searches["additional"] = additional_search
        
        return {
            "possible_families": possible_families,
            "family_histories": family_histories,
            "user_searches": user_searches,
            "summary": {
                "total_families_found": len(possible_families),
                "high_relevance_families": [f for f in possible_families if f.get("relevance") == "高"]
            }
        }
    
    async def search_historical_records(self, name: str, date: Optional[str] = None) -> List[Dict[str, str]]:
        """搜索历史记录"""
        query = f"{name} 历史记录"
        if date:
            query += f" {date}"
        return await self.search_with_deepseek(query)
