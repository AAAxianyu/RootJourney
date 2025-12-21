"""
输出生成服务
整合所有服务，生成最终输出（报告、传记、时间轴）
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.dependencies.db import get_mongodb_db
from app.models.output import FamilyReport, Biography, Timeline, TimelineEvent
from app.services.ai_service import AIService
from app.services.graph_service import GraphService
from app.services.gateway_service import GatewayService
from app.services.search_service import SearchService
from app.utils.logger import logger
import json


class OutputService:
    """输出服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.graph_service = GraphService()
        self.gateway_service = GatewayService()
        self.search_service = SearchService()
    
    async def generate_text(self, session_id: str) -> str:
        """生成文字描述"""
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        user_input = session.get("user_input", {})
        
        # 使用 DeepSeek 生成文字描述
        prompt = f"""
基于以下家族数据，生成一份详细的家族历史报告：
用户信息：{json.dumps(user_input, ensure_ascii=False)}
家族图谱：{json.dumps(family_graph, ensure_ascii=False)}

请生成包含以下内容的报告：
1. 家族起源和迁徙轨迹
2. 重要历史事件
3. 家族特色和文化传承
4. 可能的祖上名人

要求：文字流畅、有故事性、尊重历史事实。
"""
        try:
            response = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            return response
        except Exception as e:
            logger.error(f"Error generating text: {e}")
        
        # 简单返回
        return f"家族历史报告：基于收集的数据，{user_input.get('name', '用户')}的家族信息已整理完成。"
    
    async def generate_report(self, session_id: str) -> Dict[str, Any]:
        """
        生成家族报告
        包含大家族历史、族谱和详细分析
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 获取用户信息和收集的数据（兼容多种格式）
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
        
        user_input = session.get("user_input", {})
        
        # 执行家族关联分析和搜索
        logger.info(f"Starting family analysis and search for session {session_id}")
        try:
            search_results = await self.search_service.perform_search(session_id)
            if not search_results:
                logger.warning(f"Search returned empty results for session {session_id}")
                search_results = {
                    "possible_families": [],
                    "family_histories": {},
                    "summary": {"total_families_found": 0, "high_relevance_families": []}
                }
        except Exception as e:
            logger.error(f"Error during family search: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 即使搜索失败，也继续生成报告
            search_results = {
                "possible_families": [],
                "family_histories": {},
                "summary": {"total_families_found": 0, "high_relevance_families": []}
            }
        
        # 提取用户实际信息用于报告
        user_name = user_input.get("name", "用户")
        user_birth_place = user_input.get("birth_place", "")
        user_current_location = user_input.get("current_location", "")
        
        # 提取收集到的实际数据
        actual_data_summary = []
        if collected_data.get("self_origin"):
            actual_data_summary.append(f"祖籍/籍贯：{collected_data.get('self_origin')}")
        if collected_data.get("father_origin"):
            actual_data_summary.append(f"父亲籍贯：{collected_data.get('father_origin')}")
        if collected_data.get("grandfather_name"):
            actual_data_summary.append(f"祖父姓名：{collected_data.get('grandfather_name')}")
        if collected_data.get("generation_char"):
            actual_data_summary.append(f"辈分字：{collected_data.get('generation_char')}")
        if collected_data.get("migration_history"):
            actual_data_summary.append(f"迁徙历史：{collected_data.get('migration_history')}")
        
        # 获取未解析的对话内容
        unparsed_info = collected_data.get("_unparsed", [])
        if unparsed_info:
            actual_data_summary.append("\n对话中的其他信息：")
            for item in unparsed_info[-5:]:  # 只取最近5条
                actual_data_summary.append(f"- {item.get('a', '')}")
        
        # 生成综合报告（基于用户实际内容）
        report_prompt = f"""
请基于以下**用户实际提供的信息**，生成一份个性化的家族历史报告。

**重要要求：**
1. 必须基于用户实际提供的信息，不要使用模板化的占位符（如[用户姓名]、[用户姓氏]等）
2. 用户姓名：{user_name}
3. 用户出生地：{user_birth_place or '未提供'}
4. 用户当前地区：{user_current_location or '未提供'}

**用户实际收集到的家族信息：**
{chr(10).join(actual_data_summary) if actual_data_summary else '（用户提供的信息较少）'}

**完整的收集数据（JSON格式）：**
{json.dumps(collected_data, ensure_ascii=False, indent=2)}

**可能的大家族分析：**
{json.dumps(search_results.get("possible_families", []), ensure_ascii=False, indent=2)}

**大家族历史：**
{json.dumps(search_results.get("family_histories", {}), ensure_ascii=False, indent=2)}

请生成一份**完全基于用户实际信息**的家族历史报告，要求：

1. **报告标题**：使用用户真实姓名，例如"一脉相承，薪火相传——{user_name}家族历史寻根报告"

2. **报告内容必须基于用户实际提供的信息**：
   - 如果用户提供了祖籍，就基于这个祖籍来写
   - 如果用户提供了祖父姓名，就提到这个姓名
   - 如果用户提供了辈分字，就详细解释这个辈分字
   - 如果用户提供了迁徙历史，就基于这个历史来写
   - **绝对不要使用[用户姓名]、[用户姓氏]等占位符**

3. **报告结构**：
   - **第一章：根脉所系——家族的起源与迁徙故事**
     * 基于用户实际提供的祖籍、出生地等信息
     * 如果信息不足，明确说明"根据您提供的信息，我们推测..."
   
   - **第二章：历史大家族故事与名人**
     * 基于可能的大家族分析结果
     * 简要描述历史名人（3-5位，每位100-150字）
     * 用温暖、生动的语言讲述他们的故事
   
   - **第三章：文化传承**
     * 基于用户提供的辈分字、传统等信息
     * 如果用户提供了辈分字，简要解释其文化内涵（100-200字）
   
   - **第四章：个人与家族**
     * 使用用户真实姓名：{user_name}
     * 描述用户在家族历史中的位置（100-150字）

4. **语言风格**：
   - 使用温暖、亲切、有故事性的语言
   - 让历史人物变得生动、有血有肉
   - 用叙事的方式讲述历史
   - 体现家族传承的温度和情感
   - 尊重历史事实，区分推测和史实
   - **保持内容简洁但完整，总字数控制在1500-2000字左右**

5. **重要提醒**：
   - 报告开头必须使用用户真实姓名：亲爱的{user_name}
   - 所有涉及用户信息的地方都必须使用实际数据
   - 如果某些信息用户没有提供，明确说明"根据现有信息推测"或"信息不足"
   - 不要使用任何占位符或模板变量
"""
        
        try:
            report_text = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": report_prompt}],
                temperature=0.8,  # 适度降低温度以加快响应
                timeout=240  # 增加到240秒超时（4分钟）
            )
            if not report_text or len(report_text.strip()) < 100:
                # 如果生成的报告太短，使用备用方案
                logger.warning(f"Generated report too short, using fallback")
                report_text = f"""
亲爱的{user_name}：

感谢您参与这次寻根之旅。基于您提供的信息，我们为您整理了一份家族历史报告。

**第一章：根脉所系——家族的起源与迁徙故事**
根据您提供的信息：
- 祖籍/籍贯：{user_birth_place or '待补充'}
- 当前地区：{user_current_location or '待补充'}

**第二章：历史大家族故事与名人**
基于搜索到的历史大家族信息，我们为您找到了相关的历史名人和家族故事。

**第三章：文化传承**
家族文化是传承的重要载体，您的家族有着深厚的历史底蕴。

**第四章：个人与家族**
{user_name}，您是家族传承的重要一环，您的故事也是家族历史的一部分。

感谢您参与这次寻根之旅！
"""
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 使用更详细的备用报告
            report_text = f"""
亲爱的{user_name}：

感谢您参与这次寻根之旅。虽然报告生成过程中遇到了一些技术问题，但我们已为您保存了所有收集到的信息。

**您提供的信息：**
{chr(10).join(actual_data_summary) if actual_data_summary else '（信息较少，建议继续补充）'}

**下一步建议：**
1. 继续补充家族信息，特别是祖籍、祖父姓名等关键信息
2. 查看搜索到的历史大家族信息
3. 如有需要，可以重新生成报告

感谢您的参与！
"""
        
        # 确保report_text不为空
        if not report_text or len(report_text.strip()) < 50:
            logger.warning(f"Report text is too short or empty, using minimal report")
            report_text = f"""
亲爱的{user_name}：

感谢您参与这次寻根之旅。基于您提供的信息，我们为您整理了一份家族历史报告。

**您提供的信息：**
{chr(10).join(actual_data_summary) if actual_data_summary else '（信息较少，建议继续补充）'}

**家族历史探索：**
我们已为您搜索了相关的历史大家族信息，并整理了可能的家族关联。

**下一步建议：**
1. 继续补充家族信息，特别是祖籍、祖父姓名等关键信息
2. 查看搜索到的历史大家族信息
3. 如有需要，可以重新生成更详细的报告

感谢您的参与！
"""
        
        # 构建报告数据
        # 同时生成基于用户信息和搜索结果的时间轴（推测）
        try:
            timeline_data = await self.build_timeline(session_id)
        except Exception as e:
            logger.error(f"Error building timeline for session {session_id}: {e}")
            timeline_data = {"events": []}

        report_data = {
            "title": f"{user_name}家族历史报告",
            "summary": f"基于{user_name}提供的信息和联网搜索，为您生成的家族历史报告",
            "report_text": report_text,
            "possible_families": search_results.get("possible_families", []),
            "family_histories": search_results.get("family_histories", {}),
            "search_summary": search_results.get("summary", {}),
            "generated_at": datetime.now().isoformat(),
            "session_id": session_id,
            "user_info": {
                "name": user_name,
                "birth_place": user_birth_place,
                "current_location": user_current_location
            },
            "timeline": timeline_data
        }
        
        # 保存报告到数据库
        try:
            # 获取用户信息用于自动生成档案标题
            user_name = user_input.get("name", "用户")
            
            update_data = {
                "report": report_data,
                "report_generated_at": datetime.now().isoformat(),
                # 报告生成后自动标记为可归档，但还未归档（archived=False）
                "report_ready": True
            }
            
            # 如果还没有档案标题，自动生成一个
            if not session.get("archive_title"):
                update_data["archive_title"] = f"{user_name}的家族寻根档案"
            
            await db.sessions.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )
            logger.info(f"Report saved to database for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving report to database: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return report_data

    async def _build_timeline(self, session_id: str, family_filter: Optional[str] = None) -> Dict[str, Any]:
        """构建家族时间轴（内部实现）：整合用户输入、家族搜索结果及联网信息，使用 LLM 推测事件时间并返回 JSON 格式的事件列表"""
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 尝试获取已存在的搜索结果或重新触发搜索
        try:
            search_results = await self.search_service.perform_search(session_id)
        except Exception as e:
            logger.warning(f"Search failed while building timeline: {e}")
            search_results = {"possible_families": [], "family_histories": {}, "summary": {}}

        user_input = session.get("user_input", {})
        # 兼容 family_graph.collected_data 与 top-level collected_data 两种存储方式
        family_graph = session.get("family_graph", {})
        if isinstance(family_graph, dict) and "collected_data" in family_graph:
            collected_data = family_graph.get("collected_data", {}) or {}
        elif isinstance(family_graph, dict) and family_graph:
            collected_data = family_graph or {}
        else:
            collected_data = session.get("collected_data", {}) or {}

        prompt = f"""
请基于以下信息，为该姓氏家族生成一个推测性的时间轴（按时间先后排序），只返回 JSON，格式为：
{{
  "events": [
    {{"date": "YYYY 或 YYYY-MM-DD", "title": "事件标题", "description": "事件说明"}},
    ...
  ]
}}

要求：
1. 使用从对话与全网搜索得到的信息（如下所示）。
2. 即使没有确切年份，也请合理推测并写出大致年份（例如 1830s, 19th century 或 1873）。
3. 事件应为与该姓氏家族密切相关的重要历史节点（迁徙、建国、名人、重要产业变化等），每个事件简洁明了。
4. 如果信息不足，请基于最可能的历史背景推测（不要生成过度虚构的细节）。
5. 最多生成20个事件。

用户信息：{json.dumps(user_input, ensure_ascii=False)}
收集数据摘要：{json.dumps({k: collected_data.get(k) for k in ['self_origin','father_origin','migration_history','grandfather_name','generation_char']}, ensure_ascii=False)}
可能的大家族信息（摘要）：{json.dumps(search_results.get('family_histories', {}), ensure_ascii=False)[:2000]}
家族筛选：{family_filter}

请只返回 JSON，不要额外说明文字。
"""
        timeline = {"events": []}
        try:
            response = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=120
            )

            # 尝试解析为 JSON
            import json as _json
            try:
                parsed = _json.loads(response)
                if isinstance(parsed, dict) and "events" in parsed:
                    timeline = parsed
                else:
                    logger.warning("Timeline LLM response JSON did not contain 'events', falling back to parsing")
            except Exception:
                # 如果 LLM 没有直接返回 JSON，尝试提取 JSON 片段
                try:
                    start = response.find('{')
                    end = response.rfind('}')
                    if start != -1 and end != -1:
                        possible = response[start:end+1]
                        parsed = _json.loads(possible)
                        if isinstance(parsed, dict) and "events" in parsed:
                            timeline = parsed
                except Exception as e:
                    logger.warning(f"Failed to parse timeline JSON: {e}")

        except Exception as e:
            logger.error(f"Error calling LLM to build timeline: {e}")

        # 规范化可能存在的字段（兼容不同的 collected_data 结构）
        self_origin = collected_data.get('self_origin') or (collected_data.get('self') or {}).get('origin') or (collected_data.get('user_profile') or {}).get('birth_place')
        father_origin = collected_data.get('father_origin') or (collected_data.get('father') or {}).get('origin')
        migration_history = collected_data.get('migration_history') or collected_data.get('migration') or collected_data.get('_migration') or collected_data.get('_unparsed')
        grandfather_name = collected_data.get('grandfather_name') or (collected_data.get('grandfather') or {}).get('name') or (collected_data.get('grandfather_name') if 'grandfather_name' in collected_data else None)
        generation_char = collected_data.get('generation_char') or (collected_data.get('self') or {}).get('generation_name')

        logger.info(f"Building timeline for session {session_id} - self_origin={self_origin}, father_origin={father_origin}, migration_history={'present' if migration_history else 'none'}, grandfather_name={grandfather_name}")

        # 最后兜底：如果没有生成事件，基于已知信息构建简单时间点
        if not timeline.get('events'):
            events = []
            # 尝试使用迁徙历史（如果存在）
            migration = migration_history
            if migration:
                # migration 可能是字符串或数组
                parts = migration if isinstance(migration, list) else str(migration).split('\n')
                for part in parts[:5]:
                    # 尝试提取年份
                    import re
                    m = re.search(r"(\d{4})", part)
                    date = f"{m.group(1)}" if m else "未知年份"
                    events.append({"date": date, "title": "迁徙记录", "description": part})

            # 使用祖籍信息作为一个历史点
            origin = self_origin or father_origin
            if origin:
                events.append({"date": "约1800-1900", "title": "家族主要起源地", "description": f"据记录，家族与{origin}有重要渊源"})

            # 使用祖辈姓名做为历史点
            if grandfather_name:
                events.append({"date": "约1900-1950", "title": "家族重要人物", "description": f"家族记载中的人物：{grandfather_name}"})

            timeline['events'] = events

        # 最终确保事件按时间排序（尝试按年份排序，未知年份放后）
        def extract_year(d):
            import re
            m = re.search(r"(\d{4})", str(d))
            return int(m.group(1)) if m else 9999

        events = timeline.get('events', [])

        # 规范化每个事件，确保包含 details 字段（数组），并去重基本字段
        normalized = []
        seen_keys = set()
        for ev in events:
            date = ev.get('date', '未知年份')
            title = ev.get('title', ev.get('event', '')[:50])
            description = ev.get('description', ev.get('event', ''))
            key = f"{date}|{title}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            details = ev.get('details')
            if not details:
                details = [{
                    'type': ev.get('category', 'general'),
                    'title': title,
                    'description': description,
                    'person': ev.get('person_name') or ev.get('person')
                }]
            normalized.append({
                'date': date,
                'title': title,
                'description': description,
                'details': details
            })

        # 如果事件数量不足 3 条，尝试调用 LLM 补充事件
        if len(normalized) < 3:
            needed = 3 - len(normalized)
            try:
                supplement_prompt = f"""
基于以下已知信息与现有时间轴事件，补充至少 {needed} 个与该姓氏家族历史相关的重要时间点，使总事件数不少于 3 个，要求输出纯 JSON（只返回 JSON 对象），格式为：{{"events":[{{"date":"YYYY 或 YYYY-MM-DD","title":"事件标题","description":"事件说明","details":[{{"type":"migration|person|event|other","title":"","description":"","person":""}}]}}]}}。

已知信息：
用户输入：{json.dumps(user_input, ensure_ascii=False)}
收集数据摘要：{json.dumps({k: collected_data.get(k) for k in ['self_origin','father_origin','migration_history','grandfather_name','generation_char']}, ensure_ascii=False)}
现有事件：{json.dumps(normalized, ensure_ascii=False)}

补充时请避免与现有事件重复，优先生成代表迁徙、名人、重大事件的节点，并在描述中说明这是基于资料推测还是确证（例如“推测：… ”）。最多补充 {needed} 条。
"""
                response = await self.gateway_service.llm_chat(
                    messages=[{"role": "user", "content": supplement_prompt}],
                    temperature=0.7,
                    timeout=120
                )

                import json as _json
                try:
                    parsed = _json.loads(response)
                    if isinstance(parsed, dict) and 'events' in parsed:
                        for ev in parsed['events']:
                            date = ev.get('date', '未知年份')
                            title = ev.get('title', '')
                            description = ev.get('description', '')
                            details = ev.get('details') or [{'type': 'generated', 'title': title, 'description': description}]
                            key = f"{date}|{title}"
                            if key not in seen_keys:
                                seen_keys.add(key)
                                normalized.append({
                                    'date': date,
                                    'title': title,
                                    'description': description,
                                    'details': details
                                })
                except Exception:
                    logger.warning('Supplement timeline LLM response failed to parse as JSON')
            except Exception as e:
                logger.error(f"Error calling LLM to supplement timeline: {e}")

        # 兜底：如果仍不足 3 个，基于已有信息合成简单事件
        if len(normalized) < 3:
            origin = self_origin or father_origin
            if origin:
                key = f"约1800-1900|家族起源地：{origin}"
                if key not in seen_keys:
                    normalized.append({
                        'date': '约1800-1900',
                        'title': f'家族主要起源地：{origin}',
                        'description': f'据口述或档案，家族与 {origin} 有重要渊源（注：此为推测）。',
                        'details': [{
                            'type': 'origin',
                            'title': f'来自 {origin}',
                            'description': f'家族主要与 {origin} 有联系（推测）'
                        }]
                    })
            migration = migration_history
            if migration and len(normalized) < 3:
                parts = migration if isinstance(migration, list) else str(migration).split('\n')[:3]
                for part in parts:
                    import re
                    m = re.search(r"(\d{4})", part)
                    date = m.group(1) if m else '未知年份'
                    key = f"{date}|迁徙：{part[:30]}"
                    if key not in seen_keys and len(normalized) < 3:
                        normalized.append({
                            'date': date,
                            'title': '迁徙记录',
                            'description': part,
                            'details': [{
                                'type': 'migration',
                                'title': '迁徙',
                                'description': part
                            }]
                        })
            if grandfather_name and len(normalized) < 3:
                normalized.append({
                    'date': '约1900-1950',
                    'title': f"家族重要人物：{grandfather_name}",
                    'description': f"家族记载中的人物：{grandfather_name}（推测年代）。",
                    'details': [{
                        'type': 'person',
                        'title': grandfather_name,
                        'description': f"记载中的人物 {grandfather_name}（推测）。",
                        'person': grandfather_name
                    }]
                })

        # 最终兜底，确保至少 3 个时间点（用合成的占位事件）
        if len(normalized) < 3:
            # 添加用户出生年份（如果有）
            birth = user_input.get('birth_date')
            if birth:
                import re
                m = re.search(r"(\d{4})", str(birth))
                if m:
                    y = m.group(1)
                    key = f"{y}|用户出生"
                    if key not in seen_keys and len(normalized) < 3:
                        normalized.append({'date': y, 'title': '用户出生', 'description': f"用户出生于 {birth}", 'details': [{'type': 'birth', 'title': '出生', 'description': f'用户出生于 {birth}'}]})
            # 生成一些通用的推测节点
            while len(normalized) < 3:
                idx = len(normalized) + 1
                normalized.append({'date': f"约19{50+idx*5}", 'title': f'家族历史节点{idx}', 'description': '系统推测的历史节点（合成）', 'details': [{'type': 'generated', 'title': f'家族历史节点{idx}', 'description': '系统推测的历史节点（合成）'}]})

        # 按年份排序
        normalized.sort(key=lambda e: extract_year(e.get('date')))

        timeline['events'] = normalized

        return timeline
    
    async def generate_images_from_report(
        self,
        session_id: str,
        num_images: int = 1,
        size: str = "2K"
    ) -> List[str]:
        """
        基于报告生成图片（使用即梦4.0）
        
        Args:
            session_id: 会话ID
            num_images: 生成图片数量（1-2，默认1）
            size: 图片分辨率（默认"2K"）
        
        Returns:
            图片URL列表
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 获取报告
        report = session.get("report")
        if not report:
            raise ValueError(f"Report not found for session {session_id}. Please generate report first.")
        
        # 限制图片数量在1-2之间
        num_images = max(1, min(2, num_images))
        
        # 从报告中提取关键信息用于生成图片提示词
        report_text = report.get("report_text", "")
        user_name = report.get("user_info", {}).get("name", "用户")
        possible_families = report.get("possible_families", [])
        
        # 提取家族名称和主要地区
        family_names = [f.get("family_name", "") for f in possible_families[:2] if f.get("family_name")]
        main_regions = []
        for family in possible_families[:2]:
            regions = family.get("main_regions", [])
            if regions:
                main_regions.extend(regions[:2])
        
        # 使用DeepSeek生成图片提示词
        prompt_generation_text = f"""
基于以下家族历史报告，生成{num_images}个图片描述提示词，用于AI图片生成。

**用户信息：**
- 姓名：{user_name}
- 家族：{', '.join(family_names) if family_names else '历史大家族'}
- 主要地区：{', '.join(set(main_regions)) if main_regions else '中国'}

**报告摘要（前500字）：**
{report_text[:500]}

请生成{num_images}个图片描述提示词，要求：
1. 每个提示词描述一个与家族历史相关的场景
2. 可以包括：家族迁徙场景、历史人物形象、家族文化传承、家族建筑或地标等
3. 风格：中国风、历史感、温暖、有故事性
4. 每个提示词控制在100字以内
5. 用中文描述

请以JSON格式返回，格式如下：
{{
  "prompts": [
    "第一个图片描述",
    "第二个图片描述"
  ]
}}

只返回JSON，不要其他文字。
"""
        
        try:
            # 使用DeepSeek生成图片提示词
            prompt_response = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": prompt_generation_text}],
                temperature=0.8,
                timeout=60
            )
            
            # 解析JSON响应
            import re
            json_match = re.search(r'\{[^{}]*"prompts"[^{}]*\[.*?\]', prompt_response, re.DOTALL)
            if json_match:
                prompts_data = json.loads(json_match.group())
                prompts = prompts_data.get("prompts", [])
            else:
                # 如果解析失败，尝试直接解析整个响应
                try:
                    prompts_data = json.loads(prompt_response)
                    prompts = prompts_data.get("prompts", [])
                except:
                    # 如果还是失败，使用默认提示词
                    prompts = [
                        f"中国风家族历史场景，{user_name}的家族传承，{', '.join(family_names) if family_names else '历史大家族'}，温暖的历史氛围",
                        f"家族文化传承场景，{', '.join(set(main_regions)) if main_regions else '中国'}地区，历史建筑，家族故事"
                    ][:num_images]
            
            # 确保提示词数量正确
            prompts = prompts[:num_images]
            if len(prompts) < num_images:
                # 如果提示词不够，补充默认提示词
                default_prompt = f"中国风家族历史场景，{user_name}的家族传承，温暖的历史氛围"
                prompts.extend([default_prompt] * (num_images - len(prompts)))
            
            # 使用即梦4.0生成图片
            image_urls = []
            for i, prompt in enumerate(prompts):
                try:
                    logger.info(f"Generating image {i+1}/{num_images} with prompt: {prompt[:50]}...")
                    urls = await self.gateway_service.generate_image_seedream(
                        prompt=prompt,
                        num_images=1,
                        size=size,
                        watermark=False
                    )
                    if urls:
                        image_urls.extend(urls)
                except Exception as e:
                    logger.error(f"Error generating image {i+1}: {e}")
                    # 继续生成其他图片，不中断整个流程
            
            if not image_urls:
                raise Exception("未能生成任何图片")
            
            # 更新报告，添加图片URL
            report["images"] = image_urls
            report["images_generated_at"] = datetime.now().isoformat()
            
            # 保存到数据库
            try:
                await db.sessions.update_one(
                    {"_id": session_id},
                    {
                        "$set": {
                            "report": report
                        }
                    }
                )
                logger.info(f"Images saved to report for session {session_id}")
            except Exception as e:
                logger.error(f"Error saving images to database: {e}")
            
            return image_urls
            
        except Exception as e:
            logger.error(f"Error generating images from report: {e}")
            raise
    
    async def build_timeline(self, session_id: str, family_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        构建时间轴（对外方法，调用内部实现）
        """
        logger.info(f"OutputService.build_timeline called for session {session_id} with family_filter={family_filter}")
        return await self._build_timeline(session_id, family_filter)
    
    async def generate_bio(self, session_id: str) -> str:
        """
        生成个人传记
        整合用户输入和家族图谱，生成融入家族叙事的个人故事
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        user_input = session.get("user_input", {})
        
        prompt = f"""
基于以下信息，生成一份个人传记，融入家族叙事：
个人信息：{json.dumps(user_input, ensure_ascii=False)}
家族图谱：{json.dumps(family_graph, ensure_ascii=False)}

要求：
1. 以第一人称或第三人称叙述
2. 融入家族历史背景
3. 体现家族传承和文化
4. 文字优美、有感染力
5. 长度约500-800字
"""
        try:
            response = await self.gateway_service.llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            return response
        except Exception as e:
            logger.error(f"Error generating biography: {e}")
        
        return f"{user_input.get('name', '用户')}的个人传记：基于家族历史和个人经历的故事。"
    
    async def get_video_prompt(self, session_id: str) -> str:
        """获取视频生成的提示词"""
        text = await self.generate_text(session_id)
        # 简化文字用于视频生成
        return f"Family history animation: {text[:200]}"
    
    async def export_pdf(self, session_id: str) -> str:
        """
        导出为 PDF
        返回 PDF 文件 URL
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            import io
            import httpx
            
            report = await self.generate_report(session_id)
            
            # 创建 PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # 添加文字
            y = height - 50
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, "家族历史报告")
            y -= 30
            
            c.setFont("Helvetica", 12)
            report_text = report.get("report_text", report.get("text", ""))
            text_lines = report_text.split("\n")
            for line in text_lines[:50]:  # 限制行数
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line[:80])  # 限制每行长度
                y -= 20
            
            # 添加图片（如果有）
            if report.get("images"):
                c.showPage()
                y = height - 50
                for img_url in report["images"][:3]:  # 最多3张
                    try:
                        async with httpx.AsyncClient() as client:
                            img_response = await client.get(img_url)
                            img_data = img_response.content
                            img = ImageReader(io.BytesIO(img_data))
                            c.drawImage(img, 50, y - 200, width=500, height=200)
                            y -= 250
                    except Exception as e:
                        logger.error(f"Error adding image to PDF: {e}")
            
            c.save()
            buffer.seek(0)
            
            # 这里应该上传到 S3 或文件存储服务
            # 暂时返回 base64 或保存到本地
            # 实际实现需要根据部署环境调整
            
            # 保存到临时文件（实际应该上传到云存储）
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(buffer.read())
                tmp_path = tmp.name
            
            # 返回文件路径（实际应该返回 URL）
            return f"file://{tmp_path}"
            
        except ImportError:
            logger.error("reportlab not installed, cannot generate PDF")
            raise
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            raise
