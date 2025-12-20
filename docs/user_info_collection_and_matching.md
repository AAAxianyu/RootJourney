# 用户信息获取与家族匹配实现详解

## 整体流程概览

```
用户输入 → AI问答收集 → 信息提取 → 数据存储 → 家族匹配分析 → 搜索结果
```

## 一、用户信息获取流程

### 1.1 初始信息收集（用户输入）

**入口**：`POST /user/input`

**代码位置**：`backend/app/routers/user.py`

```python
@router.post("/input")
async def submit_input(user_input: UserInput):
    session_id = await ai_service.start_session(user_input)
    return {"session_id": session_id}
```

**收集的初始信息**：
- 姓名（name）
- 出生日期（birth_date）
- 出生地（birth_place）
- 当前地区（current_location）

**数据模型**：`backend/app/models/user.py`

```python
class UserInput(BaseModel):
    name: str
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    current_location: Optional[str] = None
```

### 1.2 AI问答循环收集详细信息

**入口**：`POST /ai/chat`

**代码位置**：`backend/app/routers/ai_chat.py` → `backend/app/services/ai_service.py`

#### 问答流程定义

系统定义了6个阶段的问答流程（`FLOW`）：

```python
FLOW = [
    ("self_origin", "用户自己的祖籍/籍贯", "你的祖籍/籍贯大概在什么地方？", "self.origin"),
    ("family_story_seed", "家族记忆或线索", "你小时候有没有听家里人提起过老家？", None),
    ("father_origin", "父亲的老家/籍贯", "你爸爸常提起过他的老家吗？", "father.origin"),
    ("grandfather_origin", "爷爷的老家/籍贯", "你对爷爷那边的老家有没有印象？", "grandfather.origin"),
    ("generation_name", "家族辈分字", "你们家族有没有辈分字？", "self.generation_name"),
    ("surname_clue", "姓氏与宗族线索", "你家族的姓氏是？", "self.surname"),
]
```

#### 信息提取过程

**步骤1：用户回答处理**

```python
async def process_answer(self, session_id: str, answer: str):
    # 1. 加载会话状态
    state = await self._load_state(session_id)
    collected = state.get("collected_data", {})
    current_q = state.get("current_question")
    step = state.get("step")
    
    # 2. 判断是否为"不知道/没有"的回答
    if self._is_skip(answer):
        # 记录为未知，继续下一步
        collected["_unknown"][step] = answer
        # 推进到下一步
        ...
    
    # 3. 尝试提取结构化信息
    extracted = await self._extract_family_info(
        answer=answer,
        current_question=current_q,
        existing_data=collected,
    )
```

**步骤2：AI信息提取**

使用 DeepSeek LLM 从用户回答中提取结构化信息：

```python
async def _extract_family_info(self, answer, current_question, existing_data):
    # 构建提取提示词
    prompt = f"""
    从用户回答中提取家族信息：
    用户回答：{answer}
    当前问题：{current_question}
    已收集数据：{existing_data}
    
    请提取以下信息（如果存在）：
    - 姓名
    - 关系（父亲、祖父等）
    - 地点（籍贯、出生地等）
    - 时间（出生年份等）
    - 辈分字
    - 姓氏
    """
    
    # 定义提取的JSON Schema
    schema = {
        "type": "object",
        "properties": {
            "self": {
                "origin": {"type": "string"},
                "surname": {"type": "string"},
                "generation_name": {"type": "string"}
            },
            "father": {
                "origin": {"type": "string"},
                "name": {"type": "string"}
            },
            "grandfather": {
                "origin": {"type": "string"},
                "name": {"type": "string"}
            }
        }
    }
    
    # 调用LLM提取
    extracted = await self.gateway_service.llm_extract(
        text=answer,
        schema=schema
    )
    
    return extracted
```

**步骤3：数据合并与存储**

```python
# 合并提取的信息到已收集数据
if extracted:
    # 深度合并
    collected = self._merge_data(collected, extracted)
    
    # 保存未解析的原始回答（用于后续分析）
    if not self._is_fully_extracted(extracted, answer):
        collected.setdefault("_unparsed", []).append({
            "q": current_q,
            "a": answer,
            "step": step
        })
    
    # 保存到Redis和MongoDB
    await self._save_state(session_id, state)
    await self._save_to_mongo(session_id, collected)
```

### 1.3 数据存储结构

**Redis存储**（临时会话状态）：
```json
{
  "session_id": "abc123",
  "step": "surname_clue",
  "current_question": "你家族的姓氏是？",
  "collected_data": {
    "self": {
      "origin": "山东",
      "surname": "张"
    },
    "father": {
      "origin": "山东济南"
    },
    "grandfather": {
      "name": "张建国"
    },
    "_unparsed": [
      {"q": "...", "a": "我爷爷是1950年出生的", "step": "..."}
    ]
  },
  "question_count": 5
}
```

**MongoDB存储**（持久化）：
```json
{
  "_id": "abc123",
  "user_input": {
    "name": "张三",
    "birth_place": "北京"
  },
  "family_graph": {
    "collected_data": {
      "self_origin": "山东",
      "surname": "张",
      "father_origin": "山东济南",
      "grandfather_name": "张建国"
    }
  }
}
```

---

## 二、家族匹配搜索流程

### 2.1 触发搜索

**入口**：`GET /search/family?session_id=xxx`

**代码位置**：`backend/app/routers/search.py` → `backend/app/services/search_service.py`

```python
@router.get("/family")
async def search_family(session_id: str):
    results = await search_service.perform_search(session_id)
    return {"results": results}
```

### 2.2 信息提取与统一

**代码位置**：`backend/app/services/search_service.py` → `analyze_family_associations`

#### 步骤1：从多个位置提取信息

系统会从不同可能的字段位置提取信息，确保兼容性：

```python
async def analyze_family_associations(self, collected_data):
    # 从不同可能的字段位置提取信息
    self_origin = (
        collected_data.get("self_origin") or           # 直接字段
        collected_data.get("self", {}).get("origin") or # 嵌套字段
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
```

#### 步骤2：构建信息摘要

```python
# 构建用户信息摘要
user_info_summary = []

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

# 获取未解析的对话内容（补充信息）
unparsed_info = collected_data.get("_unparsed", [])
if unparsed_info:
    user_info_summary.append("\n对话中的其他信息：")
    for item in unparsed_info[-5:]:  # 只取最近5条
        user_info_summary.append(f"- {item.get('a', '')}")

user_info_text = "\n".join(user_info_summary)
```

### 2.3 AI智能匹配分析

#### 构建分析提示词

```python
prompt = f"""
基于以下用户收集的家族信息，分析用户可能与哪些历史大家族有关。

**用户信息摘要：**
{user_info_text}

**完整收集数据（JSON格式）：**
{json.dumps(collected_data, ensure_ascii=False, indent=2)}

**分析要求：**
1. **必须基于用户实际提供的信息进行分析**，不要使用通用模板
2. 如果用户提供了姓氏，优先查找该姓氏的历史大家族
3. 如果用户提供了籍贯/祖籍，优先查找该地区的历史大家族
4. 如果用户提供了祖父姓名，尝试分析该姓名可能关联的家族
5. 如果用户提供了辈分字，尝试查找使用该辈分字的家族

**输出要求：**
每个大家族必须包含：
- 家族名称（必须具体，不要用"历史大家族"这样的通用名称）
- 历史背景（100字以内，基于用户信息）
- 主要分布地区（基于用户提供的地区信息）
- 著名人物（列出3-5位，每位50-100字描述其成就和影响）
- 文化特色（50字以内）
- 与用户信息的关联度（高/中/低）
- 关联线索（说明为什么认为用户可能与这个家族有关）

请以 JSON 格式返回。
"""
```

#### 调用LLM分析

```python
response = await self.gateway_service.llm_chat(
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    timeout=120
)
```

#### 解析LLM响应

```python
# 1. 清理响应（移除markdown代码块）
content = response.strip()
if content.startswith("```"):
    # 提取JSON部分
    parts = content.split("```")
    for part in parts:
        if part.startswith("json") or part.startswith("{"):
            content = part.strip()
            break

# 2. 解析JSON
if content.startswith("{"):
    data = json.loads(content)
    families = data.get("possible_families", [])
    if families:
        return families

# 3. 如果解析失败，使用正则表达式提取
import re
json_match = re.search(r'\{[^{}]*"possible_families"[^{}]*\[.*?\]', content, re.DOTALL)
if json_match:
    data = json.loads(json_match.group())
    return data.get("possible_families", [])

# 4. 如果还是失败，基于用户实际信息创建结果
surname = collected_data.get("surname") or "未知"
origin = collected_data.get("self_origin") or ""

return [{
    "family_name": f"{surname}氏家族" if surname != "未知" else "历史大家族",
    "main_regions": [origin] if origin else ["中国"],
    "connection_clues": [f"姓氏：{surname}", f"地区：{origin}"]
}]
```

### 2.4 并行搜索家族历史

对于每个匹配到的家族，系统会并行搜索其历史：

```python
# 只处理前3个最相关的家族
families_to_search = sorted(
    possible_families,
    key=lambda x: {"高": 3, "中": 2, "低": 1}.get(x.get("relevance", "低"), 1),
    reverse=True
)[:3]

# 并行执行搜索
search_tasks = []
for family in families_to_search:
    family_name = family.get("family_name", "")
    location = family.get("main_regions", [None])[0]
    
    task = self.search_family_history(
        family_name,
        location=location
    )
    search_tasks.append((family_name, family, task))

# 并行执行
results = await asyncio.gather(
    *[task for _, _, task in search_tasks],
    return_exceptions=True
)
```

---

## 三、匹配策略详解

### 3.1 优先级策略

系统按以下优先级进行匹配：

1. **姓氏匹配**（最高优先级）
   - 如果用户提供了姓氏，优先查找该姓氏的历史大家族
   - 例如：用户提供"张"，优先匹配"张氏家族"

2. **地区匹配**（次高优先级）
   - 如果用户提供了籍贯/祖籍，优先查找该地区的历史大家族
   - 例如：用户提供"山东"，优先匹配山东地区的家族

3. **姓名匹配**（中等优先级）
   - 如果用户提供了祖父姓名，尝试从姓名中提取线索
   - 例如：祖父姓名"张建国"，提取姓氏"张"

4. **辈分字匹配**（辅助优先级）
   - 如果用户提供了辈分字，尝试查找使用该辈分字的家族

5. **综合推测**（最低优先级）
   - 如果信息不足，基于常见历史模式推测

### 3.2 关联度评估

系统会评估每个匹配家族的关联度：

- **高**：有明确的姓氏和地区匹配
- **中**：有姓氏或地区匹配
- **低**：信息不足，基于推测

### 3.3 匹配结果示例

**输入**：
```json
{
  "surname": "张",
  "self_origin": "山东",
  "grandfather_name": "张建国"
}
```

**输出**：
```json
{
  "possible_families": [
    {
      "family_name": "张氏家族",
      "historical_background": "张氏是中国大姓之一，在山东地区有深厚历史...",
      "main_regions": ["山东", "河南"],
      "famous_figures": [
        {
          "name": "张良",
          "dynasty_period": "汉朝",
          "achievements": "...",
          "influence": "..."
        }
      ],
      "relevance": "高",
      "connection_clues": ["姓氏：张", "地区：山东"]
    }
  ]
}
```

---

## 四、数据流转图

```
┌─────────────────────────────────────────────────────────┐
│  1. 用户输入基本信息                                      │
│     POST /user/input                                     │
│     {name, birth_place, ...}                            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  2. AI问答循环收集详细信息                               │
│     POST /ai/chat (多次调用)                            │
│     - 提取祖籍、姓氏、辈分字等                           │
│     - 存储到 collected_data                            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  3. 数据统一提取                                        │
│     analyze_family_associations()                       │
│     - 从多个字段位置提取信息                             │
│     - 构建信息摘要                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  4. AI智能匹配分析                                      │
│     - 使用DeepSeek LLM分析                              │
│     - 基于姓氏、地区、姓名等匹配                         │
│     - 返回可能的家族列表                                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  5. 并行搜索家族历史                                    │
│     - 对每个家族并行搜索历史信息                         │
│     - 使用博查API或DeepSeek                             │
│     - 返回家族历史详情                                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  6. 返回匹配结果                                        │
│     {                                                 │
│       "possible_families": [...],                    │
│       "family_histories": {...},                       │
│       "summary": {...}                                 │
│     }                                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 五、关键技术点

### 5.1 信息提取的容错性

- **多字段位置查找**：从 `self_origin` 和 `self.origin` 等多个位置查找
- **未解析内容保存**：保存原始对话内容，用于后续分析
- **"不知道"处理**：将"不知道"视为有效回答，记录并继续

### 5.2 匹配的智能性

- **基于实际信息**：强调必须基于用户实际信息，不用通用模板
- **优先级策略**：按姓氏、地区、姓名等优先级匹配
- **关联线索说明**：明确说明为什么认为用户与该家族有关

### 5.3 性能优化

- **并行搜索**：多个家族并行搜索，减少总耗时
- **限制数量**：只搜索前3个最相关的家族
- **超时控制**：设置120秒超时，避免无限等待

---

## 六、代码文件位置

| 功能 | 文件路径 |
|------|----------|
| 用户输入路由 | `backend/app/routers/user.py` |
| AI问答路由 | `backend/app/routers/ai_chat.py` |
| AI服务（信息收集） | `backend/app/services/ai_service.py` |
| 搜索路由 | `backend/app/routers/search.py` |
| 搜索服务（匹配分析） | `backend/app/services/search_service.py` |
| API网关（LLM调用） | `backend/app/services/gateway_service.py` |
| 数据模型 | `backend/app/models/user.py` |

---

## 七、总结

整个系统通过以下方式实现用户信息获取和家族匹配：

1. **渐进式收集**：通过AI问答逐步收集信息，而不是一次性表单
2. **智能提取**：使用LLM从自然语言回答中提取结构化信息
3. **容错处理**：支持信息不完整、模糊或"不知道"的情况
4. **智能匹配**：基于实际信息，使用LLM分析可能的家族关联
5. **并行搜索**：对匹配到的家族并行搜索历史信息

这种设计既保证了用户体验（自然对话），又确保了数据质量（结构化存储）和匹配准确性（基于实际信息）。
