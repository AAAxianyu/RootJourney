"""
AI问答和NLP逻辑服务
处理AI问答循环，逐步丰富用户家族信息
"""
import uuid
from typing import Any, Dict, Optional, List, Tuple

from openai import AsyncOpenAI
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

from app.utils.logger import logger
from app.config import settings
import json


class AIService:
    """
    RootJourney AI Service (Option A)
    - 系统控制“阶段/主题”，保证逻辑不乱跳
    - AI 负责把问题问得更自然、更温暖、更叙事
    - 抽取失败不“纠错审问”，而是“换角度陪聊”
    - “不知道/不清楚/没有”视为有效回答：记录并继续
    """

    # 你可以在这里扩展整个“叙事采集流程”
    # 每一步包含：step_id, topic(给AI的主题), fallback(兜底问法), field_path(希望抽取到的字段，可选)
    FLOW: List[Tuple[str, str, str, Optional[str]]] = [
        (
            "self_origin",
            "用户自己的祖籍/籍贯与家乡印象（允许模糊）",
            "我们先从你的“根”开始聊起：你印象里自己（或家里人常说的）祖籍/籍贯大概在什么地方？不确定也没关系，说个省市也可以。",
            "self.origin",
        ),
        (
            "family_story_seed",
            "与家族有关的一段记忆或线索（比如谁常提起老家、家里口口相传的故事）",
            "如果你愿意的话：你小时候有没有听家里人提起过“老家/祖上”的一两句话？哪怕很零碎也行。",
            None,
        ),
        (
            "father_origin",
            "父亲的老家/籍贯/成长地（允许模糊）",
            "你爸爸常提起过他的老家吗？你印象里大概在哪个省市？",
            "father.origin",
        ),
        (
            "grandfather_origin",
            "爷爷的老家/籍贯/家族支系线索（允许模糊）",
            "那你对爷爷那边的“老家”有没有任何印象？不确定也没关系，说个大概方向也行。",
            "grandfather.origin",
        ),
        (
            "generation_name",
            "家族辈分字/辈分名（如果有的话）",
            "你们家族有没有“辈分字”（比如名字里某个字按辈分排列）？如果没有或不确定也没关系。",
            "self.generation_name",
        ),
        (
            "surname_clue",
            "姓氏与宗族线索（支系、堂号、祠堂/家谱是否见过）",
            "你家族的姓氏是？你有没有见过家谱、祠堂、或者听过“堂号/宗祠”之类的说法？",
            "self.surname",
        ),
    ]

    def __init__(self):
        self._mongo_client: Optional[AsyncIOMotorClient] = None
        self._redis: Optional[redis.Redis] = None

        self._llm_client: Optional[AsyncOpenAI] = None
        self._llm_model: str = "deepseek-chat"

    # --------------------------
    # settings helper
    # --------------------------
    def _get(self, *names: str, default: Any = None) -> Any:
        for n in names:
            if hasattr(settings, n):
                v = getattr(settings, n)
                if v is not None and v != "":
                    return v
        return default

    def _tone(self) -> str:
        t = str(self._get("TONE", "tone", default="neutral")).strip().lower()
        return "warm" if t == "warm" else "neutral"

    def _narrative_style_block(self) -> str:
        if self._tone() == "warm":
            return """
你是一位“家族记忆引导者”，不是信息采集器。
你在做的是“陪伴式寻根与家族叙事”，而不是查户口填表。

风格要求：
- 温和、尊重、带一点陪伴感
- 接受信息不完整、模糊或“不知道”
- 鼓励叙述（“你印象里…/你听谁提过…/大概也行”）
- 不要使用“请提供/请填写/必须回答”等表单语气
- 不要责备、不要审问、不要让用户觉得答错了
"""
        return """
你是家族寻根信息采集助手，语气自然友好，避免表单腔。
允许用户不确定或跳过。
"""

    # --------------------------
    # DB clients
    # --------------------------
    async def _get_redis(self) -> redis.Redis:
        if self._redis is not None:
            return self._redis
        redis_url = self._get("REDIS_URL", "redis_url", default="redis://localhost:6379/0")
        self._redis = redis.from_url(redis_url, decode_responses=True)
        return self._redis

    async def _get_mongo_db(self):
        if self._mongo_client is None:
            mongo_uri = self._get(
                "MONGO_URI",
                "mongo_uri",
                "MONGODB_URL",
                "mongodb_url",
                default="mongodb://localhost:27017",
            )
            self._mongo_client = AsyncIOMotorClient(mongo_uri)
        db_name = self._get("MONGODB_DB_NAME", "mongodb_db_name", default="rootjourney")
        return self._mongo_client[db_name]

    # --------------------------
    # LLM client (DeepSeek via OpenAI SDK)
    # --------------------------
    def _ensure_llm(self) -> None:
        if self._llm_client is not None:
            return

        key = self._get("DEEPSEEK_API_KEY", "deepseek_api_key", "OPENAI_API_KEY", "openai_api_key", default=None)
        if not key:
            raise RuntimeError("DEEPSEEK_API_KEY 未配置（或 OPENAI_API_KEY 未配置）")

        base_url = self._get("DEEPSEEK_BASE_URL", "deepseek_base_url", default="https://api.deepseek.com")
        model = self._get("DEEPSEEK_MODEL", "deepseek_model", default="deepseek-chat")

        self._llm_client = AsyncOpenAI(api_key=key, base_url=base_url)
        self._llm_model = model
        logger.info(f"使用 DeepSeek API: base_url={base_url}, model={model}, tone={self._tone()}")

    # --------------------------
    # Redis state helpers
    # --------------------------
    def _rk(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def _load_state(self, session_id: str) -> Dict[str, Any]:
        r = await self._get_redis()
        raw = await r.get(self._rk(session_id))
        if not raw:
            raise ValueError(f"Session {session_id} not found（请先调用 /user/input 创建 session）")
        return json.loads(raw)

    async def _save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        r = await self._get_redis()
        ttl = int(self._get("SESSION_EXPIRE_SECONDS", "session_expire_seconds", default=3600))
        await r.set(self._rk(session_id), json.dumps(state, ensure_ascii=False), ex=ttl)

    # --------------------------
    # Utilities
    # --------------------------
    def _is_end_request(self, answer: str) -> bool:
        """检查用户是否想要结束对话"""
        if not answer:
            return False
        answer_lower = answer.strip().lower()
        end_keywords = [
            "结束", "完成", "好了", "够了", "可以了", 
            "结束对话", "完成对话", "不再继续", "不想继续",
            "停止", "退出", "不聊了", "结束吧", "完成吧"
        ]
        return any(keyword in answer_lower for keyword in end_keywords)
    
    def _is_skip(self, answer: str) -> bool:
        a = (answer or "").strip()
        if a == "":
            return True
        skip_words = ["不知道", "不清楚", "不确定", "忘了", "没有", "暂无", "不记得", "不了解", "说不准", "不太清楚"]
        return any(w in a for w in skip_words)

    def _deep_merge(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(base, dict):
            base = {}
        if not isinstance(new, dict):
            return base

        out = dict(base)
        for k, v in new.items():
            if k in out and isinstance(out[k], dict) and isinstance(v, dict):
                out[k] = self._deep_merge(out[k], v)
            else:
                out[k] = v
        return out

    def _get_by_path(self, obj: Dict[str, Any], path: str) -> Any:
        cur: Any = obj
        for part in path.split("."):
            if not isinstance(cur, dict):
                return None
            if part not in cur:
                return None
            cur = cur[part]
        return cur

    def _pick_best_question(self, candidates: list[str], fallback: str, asked_before: list[str]) -> str:
        for q in candidates:
            q = (q or "").strip()
            if q and q not in asked_before:
                return q
        # 兜底也要避免完全重复：如果兜底问法也问过，就稍微变体一下
        if fallback in asked_before:
            return fallback + "（大概的省份/城市也可以）"
        return fallback

    def _find_next_step(self, collected_data: Dict[str, Any], current_step: str) -> Optional[Tuple[str, str, str, Optional[str]]]:
        """
        找到下一步应该问什么：
        - 从 current_step 往后走
        - 对于有 field_path 的步骤：如果该字段已存在且非空，则跳过
        - 对于 field_path=None 的步骤（叙事类）：默认仍会问一次（除非你想按标记跳过）
        """
        step_ids = [s for s, _, _, _ in self.FLOW]
        try:
            start_idx = step_ids.index(current_step)
        except ValueError:
            start_idx = -1

        for i in range(start_idx + 1, len(self.FLOW)):
            step, topic, fallback, field_path = self.FLOW[i]
            if field_path:
                v = self._get_by_path(collected_data, field_path)
                if v is not None and str(v).strip() != "":
                    continue
            return self.FLOW[i]
        return None

    # --------------------------
    # Public APIs (called by routers)
    # --------------------------
    async def start_session(self, user_profile: Any) -> str:
        """
        /user/input 会调用这里，创建一个 session_id，并初始化 state。
        user_profile 通常是 pydantic model（UserInput），这里兼容 model_dump()/dict()
        """
        session_id = str(uuid.uuid4())

        if hasattr(user_profile, "model_dump"):
            profile_dict = user_profile.model_dump()
        elif hasattr(user_profile, "dict"):
            profile_dict = user_profile.dict()
        elif isinstance(user_profile, dict):
            profile_dict = user_profile
        else:
            profile_dict = {"raw": str(user_profile)}

        # 初始化 collected_data：把用户基础信息也作为线索的一部分
        collected = {"user_profile": profile_dict}

        # 第一问：来自 FLOW[0]
        first_step, first_topic, first_fallback, _ = self.FLOW[0]
        asked_questions: list[str] = []

        # 用 AI 生成候选（温暖叙事）
        try:
            candidates = await self._generate_candidate_questions(
                topic=first_topic,
                collected_data=collected,
                n=4,
                avoid=[],
            )
            first_q = self._pick_best_question(candidates, first_fallback, asked_questions)
        except Exception:
            first_q = first_fallback

        asked_questions.append(first_q)

        state = {
            "session_id": session_id,
            "step": first_step,
            "current_question": first_q,
            "asked_questions": asked_questions,
            "collected_data": collected,
            "question_count": 0,
        }

        await self._save_state(session_id, state)

        # 可选：Mongo 持久化 session 记录（失败也不影响）
        try:
            db = await self._get_mongo_db()
            await db.sessions.update_one(
                {"_id": session_id},
                {"$set": {"user_profile": profile_dict, "family_graph": collected}},
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Mongo 写入 session 失败（不影响主流程）：{e}")

        logger.info(f"Session started: {session_id}")
        return session_id
    
    async def get_initial_question(self, session_id: str) -> str:
        """
        获取当前问题
        用于获取初始问题或重新获取问题
        """
        state = await self._load_state(session_id)
        current_q = state.get("current_question")
        if current_q:
            return current_q
        
        # 如果没有当前问题，从第一步开始
        step = state.get("step") or self.FLOW[0][0]
        step_ids = [s for s, _, _, _ in self.FLOW]
        try:
            step_idx = step_ids.index(step)
            _, _, fallback, _ = self.FLOW[step_idx]
            return fallback
        except ValueError:
            _, _, fallback, _ = self.FLOW[0]
            return fallback
    
    async def process_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """
        处理用户回答，生成下一个问题
        如果数据收集完成或达到最大轮数，返回完成状态
        """
        state = await self._load_state(session_id)

        step = state.get("step") or self.FLOW[0][0]
        current_q = state.get("current_question") or await self.get_initial_question(session_id)

        collected = state.get("collected_data") or {}
        asked = state.get("asked_questions") or []
        count = int(state.get("question_count") or 0)
        min_rounds = settings.min_questions
        
        # 检查用户是否想要主动结束对话
        if self._is_end_request(answer):
            # 如果至少完成了最少轮数，允许结束
            if count >= min_rounds:
                state["collected_data"] = collected
                state["question_count"] = count + 1
                state["current_question"] = None
                state["step"] = "complete"
                await self._save_state(session_id, state)
                await self._persist_mongo(session_id, collected)
                return {
                    "status": "complete",
                    "question": None,
                    "step": "complete",
                    "message": "感谢您的分享，对话已结束。您可以生成报告了。"
                }
            else:
                # 未达到最少轮数，提示用户
                return {
                    "status": "continue",
                    "question": f"我们还需要再聊几轮才能更好地了解您的家族历史。您刚才说\"{answer}\"，能再详细说说吗？",
                    "step": step,
                    "message": f"还需要至少 {min_rounds - count} 轮对话"
                }

        # 1) “不知道/没有” 不是错误：记录并继续推进
        if self._is_skip(answer):
            collected.setdefault("_unknown", {})
            collected["_unknown"][step] = (answer or "").strip() or "unknown"

            # 推进到下一步（按 FLOW 的逻辑）
            nxt = self._find_next_step(collected, step)
            if not nxt:
                state["collected_data"] = collected
                state["question_count"] = count + 1
                state["current_question"] = None
                state["step"] = "complete"
                await self._save_state(session_id, state)
                return {"status": "complete", "question": None, "step": "complete"}

            next_step, next_topic, next_fallback, _ = nxt
            candidates = await self._generate_candidate_questions(next_topic, collected, n=4, avoid=asked)
            next_q = self._pick_best_question(candidates, next_fallback, asked)

            state["collected_data"] = collected
            state["question_count"] = count + 1
            state["step"] = next_step
            state["current_question"] = next_q
            state["asked_questions"] = (asked + [next_q])[-30:]
            await self._save_state(session_id, state)

            return {"status": "continue", "question": next_q, "step": next_step}

        # 2) 尝试抽取结构化信息（AI Extractor）
        extracted = await self._extract_family_info(
            answer=answer,
            current_question=current_q,
            existing_data=collected,
        )

        if extracted and isinstance(extracted, dict) and extracted != {}:
            collected = self._deep_merge(collected, extracted)
        else:
            # 3) 抽取失败：不要“纠错”，改成“换角度陪聊式追问”
            collected.setdefault("_unparsed", [])
            collected["_unparsed"].append({"step": step, "q": current_q, "a": answer})

            soft_q = await self._generate_soft_clarify(
                current_question=current_q,
                user_answer=answer,
                topic_hint="围绕上一问的家族线索（允许模糊、不确定也可以）",
            )

            # 避免重复
            if soft_q in asked:
                candidates = await self._generate_candidate_questions(
                    topic="围绕上一问的主题，换一种更容易回答的问法（更温和、更叙事）",
                    collected_data=collected,
                    n=4,
                    avoid=asked,
                )
                soft_q = candidates[0] if candidates else (soft_q + "（大概方向也可以）")

            state["collected_data"] = collected
            state["question_count"] = count + 1
            state["step"] = step  # 仍停留在当前 step，等待用户给到可用线索
            state["current_question"] = soft_q
            state["asked_questions"] = (asked + [soft_q])[-30:]
            await self._save_state(session_id, state)

            # Mongo 持久化（失败也不影响）
            await self._persist_mongo(session_id, collected)

            return {"status": "continue", "question": soft_q, "step": "clarify"}

        # 4) 抽取成功：推进到下一步（按 FLOW 逻辑）
        nxt = self._find_next_step(collected, step)
        if not nxt:
            state["collected_data"] = collected
            state["question_count"] = count + 1
            state["current_question"] = None
            state["step"] = "complete"
            await self._save_state(session_id, state)
            await self._persist_mongo(session_id, collected)
            return {"status": "complete", "question": None, "step": "complete"}

        next_step, next_topic, next_fallback, _ = nxt
        candidates = await self._generate_candidate_questions(next_topic, collected, n=4, avoid=asked)
        next_q = self._pick_best_question(candidates, next_fallback, asked)

        state["collected_data"] = collected
        state["question_count"] = count + 1
        state["step"] = next_step
        state["current_question"] = next_q
        state["asked_questions"] = (asked + [next_q])[-30:]
        await self._save_state(session_id, state)
        await self._persist_mongo(session_id, collected)

        return {"status": "continue", "question": next_q, "step": next_step}

    # --------------------------
    # Mongo persist (optional)
    # --------------------------
    async def _persist_mongo(self, session_id: str, collected: Dict[str, Any]) -> None:
        try:
            db = await self._get_mongo_db()
            await db.sessions.update_one(
                {"_id": session_id},
                {"$set": {"family_graph": collected}},
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Mongo 持久化失败（不影响主流程）：{e}")

    # --------------------------
    # AI: candidate questions (Option A)
    # --------------------------
    async def _generate_candidate_questions(
        self,
        topic: str,
        collected_data: Dict[str, Any],
        n: int = 4,
        avoid: Optional[list[str]] = None,
    ) -> list[str]:
        self._ensure_llm()
        avoid = avoid or []

        prompt = f"""
{self._narrative_style_block()}

基于已收集的家族数据，生成{n}个候选问题来丰富家族信息。

主题：{topic}

已收集数据：{json.dumps(collected_data, ensure_ascii=False)}

已问过的问题（避免重复）：
{json.dumps(avoid, ensure_ascii=False)}

要求：
1. 避免重复已问过的问题
2. 围绕主题"{topic}"，逐步深入询问家族信息
3. 问题要自然、友好、温暖
4. 返回JSON数组格式，例如：["问题1", "问题2", "问题3", "问题4"]
5. 只返回JSON数组，不要其他文字
"""
        try:
            response = await self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8 if self._tone() == "warm" else 0.5,
            )
            content = (response.choices[0].message.content or "").strip()
            if content.startswith("```"):
                content = content.strip("`")
                content = content.replace("json", "", 1).strip()

            data = json.loads(content)
            if isinstance(data, list):
                out: list[str] = []
                for q in data:
                    if isinstance(q, str):
                        q = q.strip()
                        if q and q not in out:
                            out.append(q)
                return out[:n]
        except Exception as e:
            logger.warning(f"生成候选问题失败：{e}")

        return []

    async def _generate_soft_clarify(self, current_question: str, user_answer: str, topic_hint: str = "") -> str:
        self._ensure_llm()
        prompt = f"""
{self._narrative_style_block()}

用户刚才的回答可能没有提供到我们需要的线索，但不要责备用户。
请用“换个角度聊聊”的方式，给出一个更温柔、更容易回答的追问。

我们想了解的方向：
{topic_hint or "围绕上一问的主题"}

上一问：
{current_question}

用户回答：
{user_answer}

请返回一个更温柔、更容易回答的追问问题。
只返回问题文本，不要其他文字。
"""
        try:
            response = await self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8 if self._tone() == "warm" else 0.6,
            )
            q = (response.choices[0].message.content or "").strip()
            return q or "没关系，我们换个角度想想：你对这件事有没有任何模糊的印象（比如省份或城市）？"
        except Exception as e:
            logger.warning(f"soft clarify 生成失败：{e}")
            return "没关系，我们换个角度想想：你对这件事有没有任何模糊的印象（比如省份或城市）？"

    # --------------------------
    # AI: extract structured info
    # --------------------------
    async def _extract_family_info(self, answer: str, current_question: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_llm()

        prompt = f"""
你是“家族信息抽取器”。请结合【当前问题】与【用户回答】抽取结构化信息并输出 JSON。

【当前问题】：
{current_question}

【用户回答】：
{answer}

【已有数据】：
{json.dumps(existing_data, ensure_ascii=False)}

抽取规则：
- 只输出 JSON，不要 markdown，不要解释
- 如果是爸爸籍贯 -> father.origin
- 如果是爷爷籍贯 -> grandfather.origin
- 如果是我自己的籍贯/祖籍 -> self.origin
- 辈分字 -> self.generation_name
- 姓氏 -> self.surname
- 如果无法判断或没有新信息 -> 输出空 JSON：{{}}

示例：
{{"father": {{"origin": "山东枣庄"}}}}
"""
        try:
            resp = await self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            content = (resp.choices[0].message.content or "").strip()

            if content.startswith("```"):
                content = content.strip("`")
                content = content.replace("json", "", 1).strip()

            data = json.loads(content)
            if not isinstance(data, dict):
                return {}
            return data
        except Exception as e:
            logger.error(f"抽取失败：{e}")
            return {}
