# 超时问题诊断和解决方案

## 问题描述

在测试过程中遇到以下超时错误：
- 搜索家族历史：`Read timed out. (read timeout=60)`
- 生成家族报告：`Read timed out. (read timeout=120)`

## 可能的原因

### 1. 后端服务未运行 ⚠️ **最常见**

**症状**：所有请求都超时，无法连接到 `localhost:8000`

**检查方法**：
```bash
# 检查服务是否运行
curl http://localhost:8000/health/

# 或者访问
http://localhost:8000/docs
```

**解决方案**：
```bash
# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload

# 或使用 docker-compose
docker-compose up
```

---

### 2. API 调用串行执行导致耗时过长 ⏱️

**根本原因**：

#### 搜索家族历史（`/search/family`）的执行流程：
1. **分析家族关联** (`analyze_family_associations`)
   - 调用 DeepSeek LLM 分析可能的大家族
   - **耗时**：30-60秒

2. **对每个家族进行历史搜索** (`search_family_history`)
   - 每个家族会：
     - 调用博查API联网搜索（30秒超时）
     - 调用 DeepSeek 整理搜索结果（30-60秒）
   - **如果找到3个家族**：3 × (30 + 60) = **270秒** ⚠️
   - **远超60秒超时限制**

3. **对姓氏和籍贯进行搜索**
   - 额外的API调用，可能再增加60-120秒

**总耗时估算**：
- 最少：60秒（1个家族）
- 典型：180-300秒（2-3个家族）
- 最多：400+秒（多个家族 + 多次搜索）

#### 生成家族报告（`/generate/report`）的执行流程：
1. **先执行搜索** (`perform_search`)
   - 包含上述所有搜索步骤
   - **耗时**：180-300秒

2. **生成报告文本** (`llm_chat`)
   - 调用 DeepSeek 生成完整报告
   - **耗时**：60-120秒

**总耗时估算**：
- 最少：240秒（4分钟）
- 典型：360-420秒（6-7分钟）
- **远超120秒超时限制**

---

### 3. API 密钥未配置或无效 🔑

**症状**：
- 博查API未配置：会回退到DeepSeek，但DeepSeek也可能很慢
- DeepSeek API未配置：所有LLM调用失败

**检查方法**：
```bash
# 检查API状态
curl http://localhost:8000/health/api-status
```

**解决方案**：
- 确保 `.env` 文件中配置了 `DEEPSEEK_API_KEY`
- 可选：配置 `BOCHA_API_KEY` 以启用联网搜索

---

### 4. 网络问题或API服务响应慢 🌐

**可能原因**：
- DeepSeek API 响应慢（高峰期）
- 博查API 响应慢或超时
- 本地网络问题

---

## 解决方案

### 方案1：增加客户端超时时间（临时方案）

修改 `test_quick.py` 中的超时设置：

```python
# 搜索家族历史
response = requests.get(
    f"{BASE_URL}/search/family?session_id={session_id}",
    timeout=300  # 增加到5分钟
)

# 生成报告
response = requests.post(
    f"{BASE_URL}/generate/report",
    json=data,
    timeout=600  # 增加到10分钟
)
```

**注意**：这只是临时方案，不能解决根本问题。

---

### 方案2：优化后端代码（推荐）✨

#### 2.1 添加超时控制

在 `gateway_service.py` 中为 DeepSeek 调用添加超时：

```python
async def llm_chat(self, messages, model=None, temperature=0.7, timeout=120):
    client, model_name = self._get_llm_client()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature
            ),
            timeout=timeout
        )
        return response.choices[0].message.content
    except asyncio.TimeoutError:
        logger.error(f"LLM call timeout after {timeout}s")
        raise
```

#### 2.2 并行执行搜索

修改 `search_service.py` 中的 `perform_search` 方法，使用 `asyncio.gather` 并行执行：

```python
# 并行搜索多个家族
tasks = [
    self.search_family_history(
        family.get("family_name", ""),
        location=family.get("main_regions", [None])[0]
    )
    for family in possible_families
]
histories = await asyncio.gather(*tasks, return_exceptions=True)
```

这样可以显著减少总耗时。

#### 2.3 添加进度反馈

使用 WebSocket 或 Server-Sent Events (SSE) 向客户端发送进度更新。

---

### 方案3：使用异步任务队列（最佳方案）🚀

对于长时间运行的任务，使用后台任务队列：

1. **使用 Celery 或 RQ** 处理后台任务
2. **立即返回任务ID**
3. **客户端轮询任务状态**
4. **任务完成后获取结果**

**实现示例**：
```python
@router.post("/search/family")
async def search_family(session_id: str):
    # 创建后台任务
    task_id = await create_search_task(session_id)
    return {"task_id": task_id, "status": "processing"}

@router.get("/search/family/{task_id}")
async def get_search_result(task_id: str):
    # 获取任务状态和结果
    result = await get_task_result(task_id)
    return result
```

---

## 快速诊断步骤

1. **检查服务是否运行**
   ```bash
   curl http://localhost:8000/health/
   ```

2. **检查API配置**
   ```bash
   curl http://localhost:8000/health/api-status
   ```

3. **查看后端日志**
   - 检查是否有错误信息
   - 查看API调用是否成功
   - 确认超时发生在哪个步骤

4. **测试单个API调用**
   ```python
   # 测试 DeepSeek
   curl -X POST http://localhost:8000/api/llm/chat \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "test"}]}'
   ```

---

## 当前代码的性能瓶颈

### 搜索服务 (`search_service.py`)

| 步骤 | 耗时估算 | 是否可优化 |
|------|---------|-----------|
| `analyze_family_associations` | 30-60秒 | ✅ 可添加超时控制 |
| 每个家族的 `search_family_history` | 60-90秒 | ✅ 可并行执行 |
| 姓氏/籍贯搜索 | 60-120秒 | ✅ 可并行执行 |
| **总计（3个家族）** | **270-390秒** | ⚠️ 远超60秒超时 |

### 报告生成 (`output_service.py`)

| 步骤 | 耗时估算 | 是否可优化 |
|------|---------|-----------|
| `perform_search` | 180-300秒 | ✅ 见上 |
| `llm_chat` 生成报告 | 60-120秒 | ✅ 可添加超时控制 |
| **总计** | **240-420秒** | ⚠️ 远超120秒超时 |

---

## 建议的优化优先级

1. **立即**：增加客户端超时时间（临时方案）
2. **短期**：添加API调用超时控制，防止单个调用无限等待
3. **中期**：并行执行多个搜索任务
4. **长期**：实现异步任务队列，支持长时间运行的任务

---

## 相关文件

- `backend/test_quick.py` - 测试脚本（超时设置）
- `backend/app/services/search_service.py` - 搜索服务（性能瓶颈）
- `backend/app/services/output_service.py` - 报告生成服务（性能瓶颈）
- `backend/app/services/gateway_service.py` - API网关（需要添加超时）
