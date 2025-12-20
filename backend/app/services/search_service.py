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
            # 首先，从嵌套结构中提取并转换为扁平结构，确保信息不丢失
            self._normalize_collected_data(collected_data)
            
            # 提取关键信息，统一数据格式
            user_info_summary = []
            
            # 从不同可能的字段位置提取信息（支持多种数据格式）
            self_origin = (
                collected_data.get("self_origin") or 
                collected_data.get("self", {}).get("origin") or
                collected_data.get("user_profile", {}).get("birth_place") or
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
            
            # 不再从未解析对话中提取关键词，而是直接将所有对话内容传递给LLM
            # 这样LLM可以自己理解和提取所有信息，不会丢失任何细节
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
            
            # 如果从祖父姓名中提取姓氏（如果还没有姓氏）
            if not surname and grandfather_name:
                surname = grandfather_name[0]
                collected_data["surname"] = surname
                collected_data.setdefault("self", {})["surname"] = surname
                logger.info(f"Extracted surname '{surname}' from grandfather name '{grandfather_name}'")
            
            # 记录提取到的信息（用于调试）
            logger.info(f"Extracted info - surname: {surname}, self_origin: {self_origin}, father_origin: {father_origin}, grandfather_name: {grandfather_name}")
            
            # 构建用户信息摘要
            # 1. 首先添加结构化信息（来自用户初始输入和AI成功提取的）
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
            
            # 2. 添加所有对话内容（让LLM自己理解和提取信息）
            unparsed_info = collected_data.get("_unparsed", [])
            if unparsed_info:
                user_info_summary.append("\n完整对话记录（包含所有用户提供的信息）：")
                for item in unparsed_info:
                    question = item.get("q", "")
                    answer = item.get("a", "")
                    if question and answer:
                        user_info_summary.append(f"Q: {question}")
                        user_info_summary.append(f"A: {answer}")
            
            # 3. 添加用户初始输入信息
            user_profile = collected_data.get("user_profile", {})
            if user_profile:
                user_info_summary.append("\n用户初始信息：")
                if user_profile.get("name"):
                    user_info_summary.append(f"姓名：{user_profile.get('name')}")
                if user_profile.get("birth_place"):
                    user_info_summary.append(f"出生地：{user_profile.get('birth_place')}")
                if user_profile.get("current_location"):
                    user_info_summary.append(f"当前地区：{user_profile.get('current_location')}")
            
            # 记录最终提取到的信息（用于调试）
            logger.info(f"Final extracted info - surname: '{surname}', self_origin: '{self_origin}', father_origin: '{father_origin}', grandfather_name: '{grandfather_name}'")
            logger.info(f"Collected data keys: {list(collected_data.keys())}")
            if "self" in collected_data:
                logger.info(f"Self data: {collected_data.get('self', {})}")
            if "_unparsed" in collected_data:
                logger.info(f"Unparsed items count: {len(collected_data.get('_unparsed', []))}")
            
            user_info_text = "\n".join(user_info_summary) if user_info_summary else "用户提供的信息较少"
            
            # 检查用户是否提供了信息（包括对话内容）
            has_key_info = bool(surname or self_origin or father_origin or grandfather_name or generation_char or unparsed_info)
            
            if not has_key_info:
                # 如果没有关键信息，返回一个通用的提示
                logger.warning(f"No key information found in collected_data: {collected_data}")
                return [{
                    "family_name": "待确认家族",
                    "historical_background": "由于您提供的信息较少，暂时无法准确匹配到具体的历史大家族。建议提供以下信息以获得更准确的分析：姓氏、祖籍/籍贯、祖父姓名、辈分字等。",
                    "main_regions": ["待确认"],
                    "famous_figures": [],
                    "cultural_features": "待补充",
                    "relevance": "低",
                    "connection_clues": ["信息不足，需要更多线索"],
                    "note": "用户未提供关键信息（姓氏、地区、祖父姓名等），无法进行准确匹配",
                    "suggestion": "建议提供：1. 家族姓氏 2. 祖籍/籍贯 3. 祖父姓名 4. 辈分字"
                }]
            
            # 分两步匹配：先按姓氏，再按地区
            # 如果没有结构化信息，但有对话内容，也进行搜索（让LLM从对话中提取信息）
            families = []
            
            # 第一步：按姓氏匹配（最高优先级）
            # 如果有姓氏信息（来自结构化数据或从祖父姓名推导），优先按姓氏匹配
            # 如果没有姓氏但有对话内容，也进行搜索（LLM会从对话中提取姓氏）
            if surname or unparsed_info:
                # 如果有姓氏，明确指定；如果没有，让LLM从对话中提取
                surname_hint = surname if surname else "请从对话内容中提取用户的姓氏"
                surname_prompt = f"""
基于用户提供的所有信息，查找一个与该姓氏相关的历史大家族。

**用户提供的所有信息：**
{user_info_text}

**重点信息：**
- 姓氏：{surname_hint}
- 祖籍/籍贯：{self_origin or "未提供"}
- 父亲籍贯：{father_origin or "未提供"}
- 祖父姓名：{grandfather_name or "未提供"}

**要求：**
1. **必须返回与用户姓氏相关的家族**，家族名称必须包含用户的姓氏
   - 如果已提供姓氏"{surname}"，则必须匹配该姓氏
   - 如果未提供姓氏，请从对话内容中提取用户的姓氏，然后匹配该姓氏的家族
2. 只返回1个最相关的家族
3. 如果用户提供了地区信息，优先选择该地区的{surname}氏家族
4. 仔细阅读用户提供的所有对话内容，从中提取姓氏、地区、祖父姓名等关键信息
5. 必须说明这些历史名人与用户可能的关系（例如：可能是用户的祖先、同族、同宗等）

**输出格式：**
{{
    "family_name": "{surname}氏家族（具体名称，如'琅琊{surname}氏'）",
    "historical_background": "历史背景（100字以内）",
    "main_regions": ["地区1", "地区2"],
    "famous_figures": [
        {{
            "name": "人物姓名",
            "dynasty_period": "朝代/时期",
            "achievements": "主要成就",
            "story": "生平故事",
            "influence": "历史影响",
            "possible_relation": "与用户可能的关系（例如：可能是用户的祖先、同族、同宗等，基于姓氏和地区推测）"
        }}
    ],
    "cultural_features": "文化特色（50字以内）",
    "relevance": "高",
    "connection_clues": ["姓氏：{surname}"],
    "match_basis": "姓氏匹配"
}}
"""
                try:
                    surname_response = await self.gateway_service.llm_chat(
                        messages=[{"role": "user", "content": surname_prompt}],
                        temperature=0.7,
                        timeout=120
                    )
                    # 解析姓氏匹配结果
                    surname_family = self._parse_family_response(surname_response, surname)
                    if surname_family:
                        families.append(surname_family)
                        logger.info(f"Found surname-matched family: {surname_family.get('family_name')}")
                except Exception as e:
                    logger.error(f"Error in surname matching: {e}")
            
            # 第二步：按地区匹配（如果提供了地区且姓氏匹配已找到）
            main_region = self_origin or father_origin or ""
            if main_region and len(families) > 0:
                # 如果已经有姓氏匹配，再按地区匹配一个
                region_prompt = f"""
基于用户提供的所有信息，查找一个与该地区相关的历史大家族。

**用户提供的所有信息：**
{user_info_text}

**重点信息：**
- 地区：{main_region}（这是最重要的匹配依据）
- 姓氏：{surname or "未提供"}
- 祖父姓名：{grandfather_name or "未提供"}

**要求：**
1. **必须返回与地区"{main_region}"相关的家族**
2. 只返回1个最相关的家族
3. 仔细阅读用户提供的所有对话内容，从中提取姓氏、地区、祖父姓名等关键信息
4. 如果用户也提供了姓氏，优先选择该地区且该姓氏的家族；如果没有，则选择该地区最著名的家族
5. 必须说明这些历史名人与用户可能的关系（例如：可能是用户的同乡、同地区的历史名人等）

**输出格式：**
{{
    "family_name": "家族名称（与{main_region}地区相关）",
    "historical_background": "历史背景（100字以内，强调与{main_region}地区的关系）",
    "main_regions": ["{main_region}", "其他相关地区"],
    "famous_figures": [
        {{
            "name": "人物姓名",
            "dynasty_period": "朝代/时期",
            "achievements": "主要成就",
            "story": "生平故事",
            "influence": "历史影响",
            "possible_relation": "与用户可能的关系（例如：可能是用户的同乡、同地区的历史名人等，基于地区推测）"
        }}
    ],
    "cultural_features": "文化特色（50字以内）",
    "relevance": "高",
    "connection_clues": ["地区：{main_region}"],
    "match_basis": "地区匹配"
}}
"""
                try:
                    region_response = await self.gateway_service.llm_chat(
                        messages=[{"role": "user", "content": region_prompt}],
                        temperature=0.7,
                        timeout=120
                    )
                    # 解析地区匹配结果
                    region_family = self._parse_family_response(region_response, None, main_region)
                    if region_family:
                        # 检查是否与姓氏匹配的家族重复
                        if not any(f.get("family_name") == region_family.get("family_name") for f in families):
                            families.append(region_family)
                            logger.info(f"Found region-matched family: {region_family.get('family_name')}")
                except Exception as e:
                    logger.error(f"Error in region matching: {e}")
            elif main_region and not surname:
                # 如果只有地区没有姓氏，按地区匹配
                region_prompt = f"""
基于用户提供的所有信息，查找一个与该地区相关的历史大家族。

**用户提供的所有信息：**
{user_info_text}

**重点信息：**
- 地区：{main_region}（这是最重要的匹配依据）
- 姓氏：未提供

**要求：**
1. **必须返回与地区"{main_region}"相关的家族**
2. 只返回1个最相关的家族
3. 仔细阅读用户提供的所有对话内容，从中提取姓氏、地区、祖父姓名等关键信息
4. 必须说明这些历史名人与用户可能的关系（例如：可能是用户的同乡、同地区的历史名人等）

**输出格式：**
{{
    "family_name": "家族名称（与{main_region}地区相关）",
    "historical_background": "历史背景（100字以内）",
    "main_regions": ["{main_region}"],
    "famous_figures": [
        {{
            "name": "人物姓名",
            "dynasty_period": "朝代/时期",
            "achievements": "主要成就",
            "story": "生平故事",
            "influence": "历史影响",
            "possible_relation": "与用户可能的关系（例如：可能是用户的同乡、同地区的历史名人等）"
        }}
    ],
    "cultural_features": "文化特色",
    "relevance": "高",
    "connection_clues": ["地区：{main_region}"],
    "match_basis": "地区匹配"
}}
"""
                try:
                    region_response = await self.gateway_service.llm_chat(
                        messages=[{"role": "user", "content": region_prompt}],
                        temperature=0.7,
                        timeout=120
                    )
                    region_family = self._parse_family_response(region_response, None, main_region)
                    if region_family:
                        families.append(region_family)
                except Exception as e:
                    logger.error(f"Error in region matching: {e}")
            
            # 如果都没有匹配到，返回基于用户信息的推测
            if not families:
                logger.warning("No families matched, creating default based on user info")
                if surname:
                    return [{
                        "family_name": f"{surname}氏家族",
                        "historical_background": f"基于您提供的姓氏{surname}，推测可能与{surname}氏家族有关",
                        "main_regions": [main_region] if main_region else ["待确认"],
                        "famous_figures": [],
                        "cultural_features": "待补充",
                        "relevance": "中",
                        "connection_clues": [f"姓氏：{surname}"],
                        "note": "基于姓氏推测，需要更多信息确认"
                    }]
                elif main_region:
                    return [{
                        "family_name": f"{main_region}地区历史家族",
                        "historical_background": f"基于您提供的地区{main_region}，推测可能与{main_region}地区的历史家族有关",
                        "main_regions": [main_region],
                        "famous_figures": [],
                        "cultural_features": "待补充",
                        "relevance": "中",
                        "connection_clues": [f"地区：{main_region}"],
                        "note": "基于地区推测，需要更多信息确认"
                    }]
            
            return families
        
        except Exception as e:
            logger.error(f"Family association analysis error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 即使出错也基于用户实际信息返回结果
            surname = collected_data.get("surname") or collected_data.get("self", {}).get("surname") or ""
            origin = collected_data.get("self_origin") or collected_data.get("self", {}).get("origin") or ""
            
            family_name = f"{surname}氏家族" if surname else "历史大家族"
            connection_clues = []
            if surname:
                connection_clues.append(f"姓氏：{surname}")
            if origin:
                connection_clues.append(f"地区：{origin}")
            if not connection_clues:
                connection_clues = ["需要更多信息"]
            
            return [{
                "family_name": family_name,
                "historical_background": f"分析过程中出现错误，但基于您提供的信息（{', '.join(connection_clues)}）进行推测",
                "main_regions": [origin] if origin else ["中国"],
                "famous_figures": [],
                "cultural_features": "待补充",
                "relevance": "低",
                "connection_clues": connection_clues,
                "error": str(e),
                "note": "分析过程出错，基于用户信息推测"
            }]
    
    def _parse_family_response(self, response: str, expected_surname: Optional[str] = None, expected_region: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        解析LLM返回的家族信息
        
        Args:
            response: LLM响应文本
            expected_surname: 期望的姓氏（用于验证）
            expected_region: 期望的地区（用于验证）
        
        Returns:
            解析后的家族信息字典，如果解析失败返回None
        """
        try:
            # 清理响应中的 markdown 代码块
            content = response.strip()
            if content.startswith("```"):
                parts = content.split("```")
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
            
            # 尝试直接解析JSON
            if content.startswith("{"):
                data = json.loads(content)
                
                # 处理不同的响应格式
                if "possible_families" in data:
                    # 如果是数组格式，取第一个
                    families_list = data.get("possible_families", [])
                    family = families_list[0] if families_list else None
                elif "family_name" in data:
                    # 如果直接是家族对象
                    family = data
                else:
                    # 尝试其他可能的格式
                    family = data
                
                if isinstance(family, dict):
                    # 验证姓氏一致性
                    if expected_surname:
                        family_name = family.get("family_name", "")
                        if expected_surname not in family_name:
                            logger.warning(f"Family name '{family_name}' doesn't match expected surname '{expected_surname}'")
                            # 修正家族名称，确保包含姓氏
                            if not family_name.startswith(expected_surname):
                                family["family_name"] = f"{expected_surname}氏家族（{family_name}）"
                    
                    # 验证地区一致性
                    if expected_region:
                        main_regions = family.get("main_regions", [])
                        if expected_region not in str(main_regions):
                            logger.warning(f"Family regions {main_regions} don't match expected region '{expected_region}'")
                            # 添加期望的地区到首位
                            if expected_region not in main_regions:
                                main_regions.insert(0, expected_region)
                                family["main_regions"] = main_regions
                    
                    # 确保每个历史名人都包含 possible_relation 字段
                    famous_figures = family.get("famous_figures", [])
                    for figure in famous_figures:
                        if "possible_relation" not in figure:
                            # 根据匹配依据添加关系说明
                            if expected_surname:
                                figure["possible_relation"] = f"可能是用户的祖先、同族或同宗，基于姓氏'{expected_surname}'推测"
                            elif expected_region:
                                figure["possible_relation"] = f"可能是用户的同乡或同地区的历史名人，基于地区'{expected_region}'推测"
                            else:
                                figure["possible_relation"] = "可能是与用户家族相关的历史名人"
                    
                    return family
            
            # 如果直接解析失败，尝试正则提取
            import re
            json_match = re.search(r'\{[^{}]*"family_name"[^{}]*\}', content, re.DOTALL)
            if json_match:
                try:
                    family = json.loads(json_match.group())
                    return family
                except:
                    pass
            
            return None
        except Exception as e:
            logger.error(f"Error parsing family response: {e}")
            return None
    
    def _normalize_collected_data(self, collected_data: Dict[str, Any]) -> None:
        """
        规范化收集的数据，将嵌套结构转换为扁平结构，确保信息不丢失
        同时保持嵌套结构同步更新，确保数据一致性
        
        例如：
        - self.surname -> surname（扁平）和 self.surname（嵌套，同步）
        - self.origin -> self_origin（扁平）和 self.origin（嵌套，同步）
        - grandfather.name -> grandfather_name（扁平）和 grandfather.name（嵌套，同步）
        """
        if not isinstance(collected_data, dict):
            logger.warning("collected_data is not a dict, skipping normalization")
            return
        
        # 从嵌套结构中提取并设置扁平字段，同时保持嵌套结构同步
        if "self" in collected_data and isinstance(collected_data["self"], dict):
            self_data = collected_data["self"]
            if "surname" in self_data and not collected_data.get("surname"):
                collected_data["surname"] = self_data["surname"]
                logger.debug(f"Normalized: self.surname -> surname: {self_data['surname']}")
            if "origin" in self_data and not collected_data.get("self_origin"):
                collected_data["self_origin"] = self_data["origin"]
                logger.debug(f"Normalized: self.origin -> self_origin: {self_data['origin']}")
            if "generation_name" in self_data and not collected_data.get("generation_char"):
                collected_data["generation_char"] = self_data["generation_name"]
                logger.debug(f"Normalized: self.generation_name -> generation_char: {self_data['generation_name']}")
        
        if "father" in collected_data and isinstance(collected_data["father"], dict):
            father_data = collected_data["father"]
            if "origin" in father_data and not collected_data.get("father_origin"):
                collected_data["father_origin"] = father_data["origin"]
                logger.debug(f"Normalized: father.origin -> father_origin: {father_data['origin']}")
            if "name" in father_data and not collected_data.get("father_name"):
                collected_data["father_name"] = father_data["name"]
                logger.debug(f"Normalized: father.name -> father_name: {father_data['name']}")
        
        if "grandfather" in collected_data and isinstance(collected_data["grandfather"], dict):
            grandfather_data = collected_data["grandfather"]
            if "name" in grandfather_data and not collected_data.get("grandfather_name"):
                collected_data["grandfather_name"] = grandfather_data["name"]
                logger.debug(f"Normalized: grandfather.name -> grandfather_name: {grandfather_data['name']}")
            if "origin" in grandfather_data and not collected_data.get("grandfather_origin"):
                collected_data["grandfather_origin"] = grandfather_data["origin"]
                logger.debug(f"Normalized: grandfather.origin -> grandfather_origin: {grandfather_data['origin']}")
        
        # 从user_profile中提取信息
        if "user_profile" in collected_data and isinstance(collected_data["user_profile"], dict):
            user_profile = collected_data["user_profile"]
            if "birth_place" in user_profile and not collected_data.get("self_origin"):
                collected_data["self_origin"] = user_profile["birth_place"]
                # 同步到嵌套结构
                collected_data.setdefault("self", {})["origin"] = user_profile["birth_place"]
                logger.debug(f"Normalized: user_profile.birth_place -> self_origin: {user_profile['birth_place']}")
            if "name" in user_profile:
                # 从用户姓名中提取姓氏（如果还没有）
                if not collected_data.get("surname"):
                    user_name = user_profile["name"]
                    if user_name and len(user_name) > 0:
                        surname = user_name[0]
                        collected_data["surname"] = surname
                        collected_data.setdefault("self", {})["surname"] = surname
                        logger.debug(f"Normalized: user_profile.name -> surname: {surname}")
        
        # 验证关键字段是否存在（用于调试）
        key_fields = ["surname", "self_origin", "father_origin", "grandfather_name"]
        found_fields = [f for f in key_fields if collected_data.get(f)]
        if found_fields:
            logger.info(f"Normalized data - Found fields: {found_fields}")
        else:
            logger.warning(f"Normalized data - No key fields found in collected_data")
    
    async def perform_search(self, session_id: str) -> Dict[str, Any]:
        """
        执行搜索
        基于 session 中的家族图谱进行搜索
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 兼容多种数据格式
        family_graph = session.get("family_graph", {})
        if isinstance(family_graph, dict) and "collected_data" in family_graph:
            # 新格式：family_graph.collected_data
            collected_data = family_graph.get("collected_data", {})
        elif isinstance(family_graph, dict) and family_graph:
            # 旧格式：family_graph 直接就是 collected_data
            collected_data = family_graph
        else:
            # 尝试从 collected_data 字段获取
            collected_data = session.get("collected_data", {})
        
        if not collected_data:
            logger.warning(f"No collected_data found for session {session_id}, using empty dict")
            collected_data = {}
        
        # 规范化数据，确保信息不丢失
        logger.info(f"Performing search for session {session_id}")
        logger.info(f"Collected data before normalization - keys: {list(collected_data.keys())}")
        self._normalize_collected_data(collected_data)
        
        # 记录收集到的数据（用于调试）
        logger.info(f"Collected data after normalization - keys: {list(collected_data.keys())}")
        logger.info(f"Collected data structure: {json.dumps(collected_data, ensure_ascii=False, indent=2)[:500]}")
        
        # 验证关键字段
        surname = collected_data.get("surname") or collected_data.get("self", {}).get("surname")
        self_origin = collected_data.get("self_origin") or collected_data.get("self", {}).get("origin")
        grandfather_name = collected_data.get("grandfather_name") or collected_data.get("grandfather", {}).get("name")
        logger.info(f"Key fields for search - surname: {surname}, self_origin: {self_origin}, grandfather_name: {grandfather_name}")
        
        results = {}
        
        # 1. 分析可能的大家族关联（会从未解析对话中提取信息）
        logger.info(f"Analyzing family associations for session {session_id}")
        possible_families = await self.analyze_family_associations(collected_data)
        
        # 保存提取后的数据回 MongoDB（因为 analyze_family_associations 可能从未解析对话中提取了信息）
        try:
            await db.sessions.update_one(
                {"_id": session_id},
                {"$set": {"family_graph": {"collected_data": collected_data}}}
            )
            logger.info(f"Saved extracted data back to MongoDB for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to save extracted data to MongoDB: {e}")
        
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
