"""
联网搜索逻辑服务
基于收集数据进行联网搜索，丰富历史轨迹
"""
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.dependencies.db import get_mongodb_db
from app.utils.logger import logger


class SearchService:
    """搜索服务类"""
    
    def __init__(self):
        """初始化搜索客户端"""
        self.serpapi_key = settings.serpapi_key
        self.google_api_key = settings.google_search_api_key
        self.google_engine_id = settings.google_search_engine_id
    
    async def perform_search(self, session_id: str) -> Dict[str, Any]:
        """
        执行搜索
        基于 session 中的家族图谱进行搜索
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        results = {}
        
        # 对每个家族成员进行搜索
        for person_key, person_data in family_graph.items():
            if isinstance(person_data, dict):
                name = person_data.get("name", "")
                origin = person_data.get("origin") or person_data.get("birth_place", "")
                
                if name:
                    query = f"{name} {origin} 家族历史 家谱"
                    search_results = await self._search(query)
                    results[person_key] = {
                        "name": name,
                        "origin": origin,
                        "search_results": search_results
                    }
                    
                    # 更新图谱中的历史信息
                    if search_results:
                        person_data["history"] = search_results
                        # 更新整个 family_graph
                        await db.sessions.update_one(
                            {"_id": session_id},
                            {"$set": {f"family_graph.{person_key}": person_data}}
                        )
        
        # 总结搜索结果
        summary = await self._summarize_results(results)
        
        return {
            "results": results,
            "summary": summary
        }
    
    async def _search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """执行搜索查询"""
        # 优先使用 SerpAPI
        if self.serpapi_key:
            return await self._search_serpapi(query, num_results)
        # 其次使用 Google Custom Search
        elif self.google_api_key and self.google_engine_id:
            return await self._search_google(query, num_results)
        else:
            logger.warning("No search API configured")
            return []
    
    async def _search_serpapi(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """使用 SerpAPI 搜索"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": num_results
                }
                response = await client.get("https://serpapi.com/search", params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("organic_results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "serpapi"
                    })
                
                return results
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return []
    
    async def _search_google(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """使用 Google Custom Search API 搜索"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_engine_id,
                    "q": query,
                    "num": num_results
                }
                response = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "google"
                    })
                
                return results
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    async def _summarize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """总结搜索结果"""
        historical_events = []
        famous_ancestors = []
        
        for person_key, person_data in results.items():
            search_results = person_data.get("search_results", [])
            for result in search_results:
                snippet = result.get("snippet", "").lower()
                title = result.get("title", "").lower()
                
                # 简单关键词匹配提取历史事件
                if any(keyword in snippet or keyword in title for keyword in ["迁徙", "移民", "历史", "事件", "年"]):
                    historical_events.append({
                        "person": person_data.get("name"),
                        "event": result.get("snippet"),
                        "source": result.get("url")
                    })
                
                # 提取名人信息
                if any(keyword in snippet or keyword in title for keyword in ["名人", "著名", "历史人物", "祖先"]):
                    famous_ancestors.append({
                        "person": person_data.get("name"),
                        "info": result.get("snippet"),
                        "source": result.get("url")
                    })
        
        return {
            "historical_events": historical_events[:10],  # 限制数量
            "famous_ancestors": famous_ancestors[:10]
        }
    
    async def search_historical_records(self, name: str, date: Optional[str] = None) -> List[Dict[str, str]]:
        """搜索历史记录"""
        query = f"{name} 历史记录"
        if date:
            query += f" {date}"

        return await self._search(query)
