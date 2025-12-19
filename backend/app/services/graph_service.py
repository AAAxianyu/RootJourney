"""
家族图谱构建服务
构建家族树和时间轴数据
"""
from typing import List, Dict, Any, Optional
from app.dependencies.db import get_mongodb_db
from app.models.family import Person, Relationship, FamilyTree
from app.utils.logger import logger


class GraphService:
    """图谱服务类"""
    
    def __init__(self):
        """初始化图谱构建工具"""
        pass
    
    async def update_graph(self, session_id: str, search_results: Dict[str, Any]) -> None:
        """
        更新图谱
        将搜索结果合并到家族图谱中
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        
        # 更新历史信息
        for person_key, person_data in family_graph.items():
            if isinstance(person_data, dict) and person_key in search_results.get("results", {}):
                search_data = search_results["results"][person_key]
                if "history" not in person_data:
                    person_data["history"] = []
                
                # 合并搜索结果
                for result in search_data.get("search_results", []):
                    person_data["history"].append({
                        "title": result.get("title"),
                        "snippet": result.get("snippet"),
                        "url": result.get("url"),
                        "source": result.get("source")
                    })
        
        # 推测缺失的世代信息
        inferred_data = await self._infer_missing_generations(family_graph)
        family_graph.update(inferred_data)
        
        # 更新数据库
        await db.sessions.update_one(
            {"_id": session_id},
            {"$set": {"family_graph": family_graph}}
        )
    
    async def _infer_missing_generations(self, family_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        推测缺失的世代信息
        基于已有数据使用AI推测可能的祖上信息
        """
        # 简单实现：检查是否有父亲但没有爷爷
        inferred = {}
        
        if "father" in family_graph and "grandfather" not in family_graph:
            father_data = family_graph.get("father", {})
            if isinstance(father_data, dict):
                # 可以在这里调用AI服务推测
                # 暂时返回空
                pass
        
        return inferred
    
    async def build_timeline(self, session_id: str, family_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        生成时间轴数据
        返回格式: [{"year": int, "events": {"family_A": "desc", ...}}]
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        events = []
        
        # 提取所有历史事件
        for person_key, person_data in family_graph.items():
            if isinstance(person_data, dict):
                # 从历史记录中提取年份和事件
                history = person_data.get("history", [])
                for hist_item in history:
                    snippet = hist_item.get("snippet", "")
                    # 简单提取年份（可以改进为更智能的提取）
                    year = self._extract_year(snippet)
                    if year:
                        event_desc = snippet[:100]  # 限制长度
                        events.append({
                            "year": year,
                            "person": person_key,
                            "person_name": person_data.get("name", person_key),
                            "event": event_desc,
                            "source": hist_item.get("url", "")
                        })
                
                # 从出生日期提取事件
                birth_date = person_data.get("birth_date")
                if birth_date:
                    year = self._extract_year(birth_date)
                    if year:
                        events.append({
                            "year": year,
                            "person": person_key,
                            "person_name": person_data.get("name", person_key),
                            "event": f"{person_data.get('name', person_key)} 出生",
                            "source": ""
                        })
        
        # 按年份排序
        events.sort(key=lambda e: e["year"])
        
        # 如果指定了家族过滤
        if family_filter:
            events = [e for e in events if e["person"] == family_filter]
        
        # 转换为多轴格式
        timeline_data = []
        current_year = None
        current_events = {}
        
        for event in events:
            year = event["year"]
            if year != current_year:
                if current_year is not None:
                    timeline_data.append({
                        "year": current_year,
                        "families": current_events
                    })
                current_year = year
                current_events = {}
            
            person_name = event["person_name"]
            if person_name not in current_events:
                current_events[person_name] = []
            current_events[person_name].append(event["event"])
        
        # 添加最后一个年份
        if current_year is not None:
            timeline_data.append({
                "year": current_year,
                "families": current_events
            })
        
        return timeline_data
    
    def _extract_year(self, text: str) -> Optional[int]:
        """从文本中提取年份"""
        import re
        # 匹配4位数字年份（1900-2100）
        matches = re.findall(r'\b(19|20)\d{2}\b', text)
        if matches:
            try:
                return int(matches[0] + matches[1] if len(matches) > 1 else matches[0])
            except:
                pass
        return None
    
    def build_family_tree(self, persons: List[Person], relationships: List[Relationship]) -> FamilyTree:
        """构建家族树"""
        # 找到根节点（没有父节点的人）
        root_person = None
        person_dict = {p.id: p for p in persons}
        
        # 找到没有父节点的人作为根
        parent_ids = {r.to_person_id for r in relationships if r.relationship_type == "parent"}
        for person in persons:
            if person.id not in parent_ids:
                root_person = person
                break
        
        if not root_person and persons:
            root_person = persons[0]
        
        return FamilyTree(
            root_person=root_person,
            persons=persons,
            relationships=relationships
        )
    
    def visualize_tree(self, family_tree: FamilyTree) -> Dict[str, Any]:
        """可视化家族树"""
        # 返回用于前端渲染的数据结构
        nodes = []
        edges = []
        
        for person in family_tree.persons:
            nodes.append({
                "id": person.id,
                "label": person.name,
                "title": f"{person.name}\n{person.birth_place or ''}",
                "birth_date": person.birth_date,
                "birth_place": person.birth_place
            })
        
        for rel in family_tree.relationships:
            edges.append({
                "from": rel.from_person_id,
                "to": rel.to_person_id,
                "label": rel.relationship_type,
                "arrows": "to"
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def find_ancestors(self, person_id: str, family_tree: FamilyTree) -> List[Person]:
        """查找祖先"""
        ancestors = []
        person_dict = {p.id: p for p in family_tree.persons}
        
        def find_parents(pid: str, visited: set):
            if pid in visited:
                return
            visited.add(pid)
            
            for rel in family_tree.relationships:
                if rel.from_person_id == pid and rel.relationship_type == "parent":
                    parent = person_dict.get(rel.to_person_id)
                    if parent:
                        ancestors.append(parent)
                        find_parents(rel.to_person_id, visited)
        
        find_parents(person_id, set())
        return ancestors
    
    def find_descendants(self, person_id: str, family_tree: FamilyTree) -> List[Person]:
        """查找后代"""
        descendants = []
        person_dict = {p.id: p for p in family_tree.persons}
        
        def find_children(pid: str, visited: set):
            if pid in visited:
                return
            visited.add(pid)
            
            for rel in family_tree.relationships:
                if rel.to_person_id == pid and rel.relationship_type == "parent":
                    child = person_dict.get(rel.from_person_id)
                    if child:
                        descendants.append(child)
                        find_children(rel.from_person_id, visited)
        
        find_children(person_id, set())
        return descendants
