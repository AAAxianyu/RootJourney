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
        从多个来源提取时间信息：
        1. 用户提供的出生日期
        2. 家族图谱中的历史事件
        3. 搜索结果中的大家族历史
        4. 历史名人的生卒年份
        
        返回格式: [{"year": int, "families": {"family_name": ["event1", "event2"]}}]
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        events = []
        
        # 1. 从用户输入中提取出生日期
        user_input = session.get("user_input", {})
        if user_input.get("birth_date"):
            year = self._extract_year(user_input["birth_date"])
            if year:
                events.append({
                    "year": year,
                    "person": "用户",
                    "person_name": user_input.get("name", "用户"),
                    "event": f"{user_input.get('name', '用户')} 出生",
                    "source": "user_input",
                    "category": "birth"
                })
        
        # 2. 从家族图谱中提取历史事件
        family_graph = session.get("family_graph", {})
        collected_data = family_graph.get("collected_data", {})
        
        # 从收集的数据中提取出生日期
        if collected_data.get("grandfather_name"):
            # 如果有祖父信息，可以推测出生年份（假设祖父比父亲大约30岁）
            # 这里简化处理，如果有具体日期就提取
            pass
        
        # 3. 从搜索结果的大家族历史中提取时间信息
        report = session.get("report")
        if report:
            # 从报告中的大家族历史提取时间线
            possible_families = report.get("possible_families", [])
            for family in possible_families:
                family_name = family.get("family_name", "")
                famous_figures = family.get("famous_figures", [])
                
                for figure in famous_figures:
                    # 从历史名人的信息中提取年份
                    story = figure.get("story", "")
                    dynasty = figure.get("dynasty_period", "")
                    
                    # 尝试从朝代推断大致年份
                    year = self._extract_year_from_dynasty(dynasty)
                    if not year:
                        year = self._extract_year(story)
                    
                    if year:
                        events.append({
                            "year": year,
                            "person": figure.get("name", ""),
                            "person_name": figure.get("name", ""),
                            "event": f"{figure.get('name', '')} - {figure.get('achievements', '')[:50]}",
                            "source": f"family:{family_name}",
                            "category": "historical_figure"
                        })
        
        # 4. 从家族图谱的历史记录中提取
        for person_key, person_data in family_graph.items():
            if isinstance(person_data, dict):
                # 从历史记录中提取年份和事件
                history = person_data.get("history", [])
                for hist_item in history:
                    snippet = hist_item.get("snippet", "")
                    year = self._extract_year(snippet)
                    if year:
                        event_desc = snippet[:100]  # 限制长度
                        events.append({
                            "year": year,
                            "person": person_key,
                            "person_name": person_data.get("name", person_key),
                            "event": event_desc,
                            "source": hist_item.get("url", ""),
                            "category": "history"
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
                            "source": "",
                            "category": "birth"
                        })
        
        # 如果没有事件，尝试从收集的数据中生成一些基础时间线
        if not events:
            # 基于用户输入生成基础时间线
            if user_input.get("birth_date"):
                year = self._extract_year(user_input["birth_date"])
                if year:
                    events.append({
                        "year": year,
                        "person": "用户",
                        "person_name": user_input.get("name", "用户"),
                        "event": f"{user_input.get('name', '用户')} 出生",
                        "source": "user_input",
                        "category": "birth"
                    })
                    # 推测父辈和祖辈的大致年份
                    if year > 1950:
                        events.append({
                            "year": year - 30,  # 假设父亲比用户大约30岁
                            "person": "父亲",
                            "person_name": "父亲",
                            "event": "父亲出生（推测）",
                            "source": "inferred",
                            "category": "inferred"
                        })
                        events.append({
                            "year": year - 60,  # 假设祖父比用户大约60岁
                            "person": "祖父",
                            "person_name": "祖父",
                            "event": "祖父出生（推测）",
                            "source": "inferred",
                            "category": "inferred"
                        })
        
        # 按年份排序
        events.sort(key=lambda e: e["year"])
        
        # 如果指定了家族过滤
        if family_filter:
            events = [e for e in events if e.get("source", "").startswith(f"family:{family_filter}")]
        
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
                        "families": current_events.copy()
                    })
                current_year = year
                current_events = {}
            
            # 使用家族名称或人物名称作为键
            family_key = event.get("person_name") or event.get("person") or "其他"
            if family_key not in current_events:
                current_events[family_key] = []
            current_events[family_key].append({
                "event": event["event"],
                "category": event.get("category", "unknown"),
                "source": event.get("source", "")
            })
        
        # 添加最后一个年份
        if current_year is not None:
            timeline_data.append({
                "year": current_year,
                "families": current_events
            })
        
        return timeline_data
    
    def _extract_year_from_dynasty(self, dynasty_text: str) -> Optional[int]:
        """从朝代信息推断大致年份"""
        if not dynasty_text:
            return None
        
        # 简单的朝代到年份映射（可以扩展）
        dynasty_map = {
            "唐朝": 700,
            "宋朝": 1000,
            "元朝": 1300,
            "明朝": 1400,
            "清朝": 1700,
            "民国": 1920,
            "现代": 1950
        }
        
        for dynasty, year in dynasty_map.items():
            if dynasty in dynasty_text:
                return year
        
        return None
    
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
