# 数据转换流程详解：从用户输入到家族搜索

## 完整数据流转图

```
┌─────────────────────────────────────────────────────────────────┐
│  阶段1：用户初始输入                                             │
│  POST /user/input                                               │
│  {name: "张三", birth_place: "北京", ...}                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段2：数据初始化                                               │
│  start_session()                                                │
│  collected_data = {"user_profile": {...}}                       │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段3：AI问答循环（多次调用）                                   │
│  POST /ai/chat                                                  │
│  用户回答 → LLM提取 → 嵌套结构数据                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段4：数据合并与存储                                           │
│  _deep_merge() → collected_data                                 │
│  嵌套结构：{"self": {"surname": "张"}}                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段5：数据规范化（搜索前）                                     │
│  _normalize_collected_data()                                    │
│  嵌套 → 扁平：{"surname": "张", "self_origin": "山东"}         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段6：信息提取与补充                                           │
│  从未解析对话中提取 + 从祖父姓名提取姓氏                         │
│  最终数据：{surname: "张", self_origin: "山东", ...}           │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  阶段7：家族匹配搜索                                             │
│  analyze_family_associations()                                 │
│  使用规范化后的数据进行匹配                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 详细转换过程

### 阶段1：用户初始输入

**接口**：`POST /user/input`

**输入数据**：
```json
{
  "name": "张三",
  "birth_date": "1990-01-01",
  "birth_place": "北京",
  "current_location": "上海"
}
```

**代码位置**：`backend/app/routers/user.py` → `backend/app/services/ai_service.py`

```python
async def start_session(self, user_profile: Any) -> str:
    # 1. 转换用户输入为字典
    if hasattr(user_profile, "model_dump"):
        profile_dict = user_profile.model_dump()
    elif isinstance(user_profile, dict):
        profile_dict = user_profile
    
    # 2. 初始化 collected_data
    collected = {"user_profile": profile_dict}
    # 结果：{"user_profile": {"name": "张三", "birth_place": "北京", ...}}
    
    # 3. 保存到Redis和MongoDB
    await self._save_state(session_id, state)
    await db.sessions.update_one(
        {"_id": session_id},
        {"$set": {"user_profile": profile_dict, "family_graph": collected}}
    )
```

**存储结果**：
```json
{
  "_id": "abc123",
  "user_input": {
    "name": "张三",
    "birth_place": "北京"
  },
  "family_graph": {
    "collected_data": {
      "user_profile": {
        "name": "张三",
        "birth_place": "北京",
        "current_location": "上海"
      }
    }
  }
}
```

---

### 阶段2：AI问答循环

**接口**：`POST /ai/chat`（多次调用）

**用户回答示例**：
- 回答1："我的祖籍是山东"
- 回答2："我姓张"
- 回答3："我爷爷叫张建国"

**代码位置**：`backend/app/services/ai_service.py` → `process_answer()`

#### 步骤1：LLM信息提取

```python
async def _extract_family_info(self, answer, current_question, existing_data):
    prompt = f"""
    你是"家族信息抽取器"。请结合【当前问题】与【用户回答】抽取结构化信息并输出 JSON。
    
    【当前问题】：{current_question}
    【用户回答】：{answer}
    
    抽取规则：
    - 如果是爸爸籍贯 -> father.origin
    - 如果是爷爷籍贯 -> grandfather.origin
    - 如果是我自己的籍贯/祖籍 -> self.origin
    - 辈分字 -> self.generation_name
    - 姓氏 -> self.surname
    """
    
    # 调用DeepSeek LLM提取
    response = await self._llm_client.chat.completions.create(...)
    data = json.loads(response)
    return data
```

**提取结果示例**：

回答1："我的祖籍是山东"
```json
{
  "self": {
    "origin": "山东"
  }
}
```

回答2："我姓张"
```json
{
  "self": {
    "surname": "张"
  }
}
```

回答3："我爷爷叫张建国"
```json
{
  "grandfather": {
    "name": "张建国"
  }
}
```

#### 步骤2：数据深度合并

```python
if extracted and isinstance(extracted, dict) and extracted != {}:
    collected = self._deep_merge(collected, extracted)

def _deep_merge(self, base: Dict, new: Dict) -> Dict:
    """深度合并字典"""
    out = dict(base)
    for k, v in new.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = self._deep_merge(out[k], v)  # 递归合并
        else:
            out[k] = v
    return out
```

**合并过程**：

初始数据：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"}
}
```

第1次合并（祖籍）：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {"origin": "山东"}
}
```

第2次合并（姓氏）：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  }
}
```

第3次合并（祖父）：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  },
  "grandfather": {
    "name": "张建国"
  }
}
```

#### 步骤3：保存到数据库

```python
# 保存到Redis（临时状态）
await self._save_state(session_id, state)

# 保存到MongoDB（持久化）
await self._persist_mongo(session_id, collected)
```

**MongoDB存储结果**：
```json
{
  "_id": "abc123",
  "family_graph": {
    "collected_data": {
      "user_profile": {"name": "张三", "birth_place": "北京"},
      "self": {
        "origin": "山东",
        "surname": "张"
      },
      "grandfather": {
        "name": "张建国"
      },
      "_unparsed": [
        {"q": "...", "a": "我爷爷是1950年出生的", "step": "..."}
      ]
    }
  }
}
```

---

### 阶段3：数据规范化（搜索前）

**触发时机**：调用 `GET /search/family?session_id=xxx`

**代码位置**：`backend/app/services/search_service.py` → `perform_search()`

```python
async def perform_search(self, session_id: str):
    # 1. 从MongoDB读取数据
    collected_data = session.get("family_graph", {}).get("collected_data", {})
    
    # 2. 规范化数据（关键步骤！）
    self._normalize_collected_data(collected_data)
```

**规范化方法**：`_normalize_collected_data()`

```python
def _normalize_collected_data(self, collected_data: Dict[str, Any]) -> None:
    """
    将嵌套结构转换为扁平结构
    """
    # 从 self 嵌套结构中提取
    if "self" in collected_data:
        self_data = collected_data["self"]
        if "surname" in self_data:
            collected_data["surname"] = self_data["surname"]  # 嵌套 → 扁平
        if "origin" in self_data:
            collected_data["self_origin"] = self_data["origin"]  # 嵌套 → 扁平
    
    # 从 grandfather 嵌套结构中提取
    if "grandfather" in collected_data:
        grandfather_data = collected_data["grandfather"]
        if "name" in grandfather_data:
            collected_data["grandfather_name"] = grandfather_data["name"]  # 嵌套 → 扁平
    
    # 从 user_profile 中提取
    if "user_profile" in collected_data:
        user_profile = collected_data["user_profile"]
        if "birth_place" in user_profile:
            collected_data["self_origin"] = user_profile["birth_place"]  # 初始输入 → 扁平
        if "name" in user_profile and not collected_data.get("surname"):
            # 从用户姓名中提取姓氏
            collected_data["surname"] = user_profile["name"][0]
```

**规范化前后对比**：

**规范化前**（嵌套结构）：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  },
  "grandfather": {
    "name": "张建国"
  }
}
```

**规范化后**（扁平结构）：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  },
  "grandfather": {
    "name": "张建国"
  },
  "surname": "张",                    // ← 新增：从 self.surname 提取
  "self_origin": "山东",              // ← 新增：从 self.origin 提取
  "grandfather_name": "张建国"        // ← 新增：从 grandfather.name 提取
}
```

---

### 阶段4：信息提取与补充

**代码位置**：`backend/app/services/search_service.py` → `analyze_family_associations()`

#### 步骤1：从多个位置读取信息

```python
# 支持多种数据格式，确保兼容性
surname = (
    collected_data.get("surname") or           # 扁平结构（规范化后）
    collected_data.get("self", {}).get("surname") or  # 嵌套结构（原始）
    ""
)

self_origin = (
    collected_data.get("self_origin") or
    collected_data.get("self", {}).get("origin") or
    collected_data.get("user_profile", {}).get("birth_place") or  # 初始输入
    ""
)
```

#### 步骤2：从未解析对话中提取（补充）

```python
unparsed_info = collected_data.get("_unparsed", [])
if unparsed_info and (not surname or not self_origin):
    for item in unparsed_info:
        answer = item.get("a", "")
        question = item.get("q", "")
        
        # 使用正则表达式提取姓氏
        if "姓氏" in question or "姓" in question:
            surname_match = re.search(r'[姓是]\s*([张李王...])', answer)
            if surname_match and not surname:
                surname = surname_match.group(1)
                collected_data["surname"] = surname  # 补充到数据中
        
        # 使用正则表达式提取地区
        if ("籍贯" in question or "祖籍" in question) and not self_origin:
            region_match = re.search(r'(北京|上海|山东|...)', answer)
            if region_match and not self_origin:
                self_origin = region_match.group(1)
                collected_data["self_origin"] = self_origin  # 补充到数据中
```

#### 步骤3：从祖父姓名提取姓氏

```python
# 如果从祖父姓名中提取姓氏（如果还没有姓氏）
if not surname and grandfather_name:
    surname = grandfather_name[0]  # "张建国" → "张"
    collected_data["surname"] = surname
    collected_data.setdefault("self", {})["surname"] = surname
```

**最终提取结果**：
```python
surname = "张"              # 从 self.surname 或 祖父姓名提取
self_origin = "山东"        # 从 self.origin 或 user_profile.birth_place 提取
grandfather_name = "张建国"  # 从 grandfather.name 提取
```

---

### 阶段5：构建搜索提示词

**代码位置**：`backend/app/services/search_service.py` → `analyze_family_associations()`

```python
# 构建用户信息摘要
user_info_summary = []
if surname:
    user_info_summary.append(f"姓氏：{surname}")
if self_origin:
    user_info_summary.append(f"祖籍/籍贯：{self_origin}")
if grandfather_name:
    user_info_summary.append(f"祖父姓名：{grandfather_name}")

user_info_text = "\n".join(user_info_summary)
# 结果：姓氏：张\n祖籍/籍贯：山东\n祖父姓名：张建国

# 构建搜索提示词
prompt = f"""
基于以下用户收集的家族信息，分析用户可能与哪些历史大家族有关。

**用户信息摘要：**
{user_info_text}

**完整收集数据（JSON格式）：**
{json.dumps(collected_data, ensure_ascii=False, indent=2)}
...
"""
```

---

### 阶段6：执行家族匹配

**代码位置**：`backend/app/services/search_service.py` → `analyze_family_associations()`

#### 按姓氏匹配（第一步）

```python
if surname:
    surname_prompt = f"""
    基于用户提供的姓氏信息，查找一个与该姓氏相关的历史大家族。
    
    **用户信息：**
    - 姓氏：{surname}  # "张"
    - 祖籍/籍贯：{self_origin}  # "山东"
    ...
    """
    
    response = await self.gateway_service.llm_chat(...)
    surname_family = self._parse_family_response(response, surname)
    # 返回：{"family_name": "琅琊张氏", ...}
```

#### 按地区匹配（第二步）

```python
if main_region and len(families) > 0:
    region_prompt = f"""
    基于用户提供的地区信息，查找一个与该地区相关的历史大家族。
    
    **用户信息：**
    - 地区：{main_region}  # "山东"
    - 姓氏：{surname}  # "张"
    ...
    """
    
    response = await self.gateway_service.llm_chat(...)
    region_family = self._parse_family_response(response, None, main_region)
    # 返回：{"family_name": "山东地区历史家族", ...}
```

---

## 数据转换示例

### 完整示例：从输入到搜索

#### 输入1：用户初始信息

```json
POST /user/input
{
  "name": "张三",
  "birth_place": "北京"
}
```

**转换后**：
```json
{
  "user_profile": {
    "name": "张三",
    "birth_place": "北京"
  }
}
```

#### 输入2：AI问答回答

**问题**："你的祖籍/籍贯大概在什么地方？"  
**回答**："我的祖籍是山东"

**LLM提取**：
```json
{
  "self": {
    "origin": "山东"
  }
}
```

**合并后**：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {"origin": "山东"}
}
```

#### 输入3：AI问答回答

**问题**："你家族的姓氏是？"  
**回答**："我姓张"

**LLM提取**：
```json
{
  "self": {
    "surname": "张"
  }
}
```

**合并后**：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  }
}
```

#### 输入4：AI问答回答

**问题**："你对爷爷那边的老家有没有印象？"  
**回答**："我爷爷叫张建国"

**LLM提取**：
```json
{
  "grandfather": {
    "name": "张建国"
  }
}
```

**合并后**：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  },
  "grandfather": {
    "name": "张建国"
  }
}
```

#### 规范化后（搜索前）

```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"
  },
  "grandfather": {
    "name": "张建国"
  },
  "surname": "张",                    // ← 规范化：从 self.surname
  "self_origin": "山东",              // ← 规范化：从 self.origin
  "grandfather_name": "张建国"        // ← 规范化：从 grandfather.name
}
```

#### 最终用于搜索的数据

```python
surname = "张"              # 从多个位置读取，确保获取到
self_origin = "山东"        # 从多个位置读取，确保获取到
grandfather_name = "张建国"  # 从多个位置读取，确保获取到
```

---

## 关键转换点总结

### 1. 初始输入 → 嵌套结构

**转换方法**：`start_session()`
- 将用户输入转换为 `user_profile` 字典
- 初始化 `collected_data = {"user_profile": {...}}`

### 2. 对话回答 → 嵌套结构

**转换方法**：`_extract_family_info()`
- 使用 LLM 从自然语言回答中提取结构化信息
- 返回嵌套结构：`{"self": {"surname": "张"}}`

### 3. 嵌套结构 → 合并数据

**转换方法**：`_deep_merge()`
- 深度合并多个提取结果
- 保持嵌套结构，逐步丰富数据

### 4. 嵌套结构 → 扁平结构

**转换方法**：`_normalize_collected_data()`
- 将嵌套结构转换为扁平结构
- 确保信息不丢失，支持多种读取方式

### 5. 未解析内容 → 结构化数据

**转换方法**：正则表达式提取
- 从 `_unparsed` 中提取信息
- 补充缺失的关键信息

### 6. 扁平数据 → 搜索参数

**转换方法**：`analyze_family_associations()`
- 从扁平结构中提取关键信息
- 构建搜索提示词
- 执行家族匹配

---

## 数据格式对照表

| 信息类型 | 嵌套结构 | 扁平结构 | 提取位置 |
|---------|---------|---------|---------|
| 姓氏 | `self.surname` | `surname` | 1. `surname`<br>2. `self.surname`<br>3. 从祖父姓名提取 |
| 祖籍 | `self.origin` | `self_origin` | 1. `self_origin`<br>2. `self.origin`<br>3. `user_profile.birth_place` |
| 父亲籍贯 | `father.origin` | `father_origin` | 1. `father_origin`<br>2. `father.origin` |
| 祖父姓名 | `grandfather.name` | `grandfather_name` | 1. `grandfather_name`<br>2. `grandfather.name` |
| 辈分字 | `self.generation_name` | `generation_char` | 1. `generation_char`<br>2. `self.generation_name` |

---

## 调试方法

### 查看实际存储的数据

```bash
# 获取会话详情
GET /session/{session_id}

# 查看 collected_data 的实际结构
```

### 查看日志

```bash
# Docker方式
docker logs rootjourney-backend | grep "Extracted info"

# 查看数据规范化过程
docker logs rootjourney-backend | grep "Collected data"
```

### 检查数据提取

日志中会显示：
- `Extracted info - surname: '张', self_origin: '山东'`
- `Collected data keys: ['user_profile', 'self', 'grandfather', 'surname', 'self_origin']`
- `Unparsed items count: 2`

---

## 常见问题

### Q1: 为什么信息提取失败？

**可能原因**：
1. LLM 提取失败（返回空JSON）
2. 用户回答不明确
3. 信息保存到 `_unparsed` 但未正确提取

**解决方案**：
- 系统会自动从 `_unparsed` 中提取
- 查看日志确认提取过程

### Q2: 为什么规范化后信息丢失？

**可能原因**：
- 规范化方法没有覆盖所有字段
- 数据格式不符合预期

**解决方案**：
- 检查 `_normalize_collected_data` 方法
- 查看日志中的数据结构

### Q3: 如何确保信息不丢失？

**解决方案**：
1. 规范化数据（嵌套 → 扁平）
2. 多位置读取（支持嵌套和扁平）
3. 从未解析内容中提取
4. 从相关字段推导（如从祖父姓名提取姓氏）

---

**最后更新**：2024-01-01
