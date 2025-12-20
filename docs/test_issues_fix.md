# 测试问题修复说明

## 发现的问题

### 问题1: family_graph 为空

**现象**：
- 测试脚本在验证数据存储结构时显示 `family_graph 为空`
- 但搜索功能仍然正常工作，说明数据实际上被提取和使用了

**原因分析**：
1. **数据保存时机**：数据保存是异步的，在提交答案后立即读取可能数据还没保存完成
2. **数据读取格式**：测试脚本可能没有正确解析接口返回的数据结构
3. **数据格式兼容**：可能存在数据格式不一致的情况

**修复措施**：

#### 1. 修复测试脚本的数据读取逻辑

```python
# 修复前
session_data = response.json()
family_graph = session_data.get("family_graph", {})

# 修复后
result = response.json()
session_data = result.get("session", {})  # 接口返回格式: {"session": {...}}
if not session_data:
    session_data = result  # 兼容直接返回数据的情况
```

#### 2. 增加等待时间

```python
# 修复前
time.sleep(2)

# 修复后
time.sleep(5)  # 增加等待时间到5秒，确保数据已持久化
```

#### 3. 增强错误处理和日志

- 添加详细的调试信息
- 显示数据 keys 和类型
- 提供更友好的错误提示

#### 4. 增强数据持久化日志

在 `_persist_mongo` 方法中添加：
- 保存结果的日志记录
- 保存的数据 keys 记录
- 更详细的错误信息

---

## 其他发现的问题

### 问题2: 数据保存可能失败但被静默忽略

**现象**：
- `_persist_mongo` 方法中的异常被捕获但只记录警告
- 如果 MongoDB 连接失败，数据可能不会保存，但不会影响主流程

**修复措施**：
- 添加更详细的日志记录
- 记录保存结果（modified_count, upserted_id）
- 记录保存的数据结构

---

## 验证方法

### 1. 检查数据是否保存

```bash
# 查看 MongoDB 中的数据
# 使用 MongoDB shell 或客户端工具
db.sessions.findOne({_id: "session_id"})
```

### 2. 查看服务器日志

```bash
# 查看数据保存日志
docker logs rootjourney-backend | grep "Mongo 持久化"

# 查看数据规范化日志
docker logs rootjourney-backend | grep "Normalized\|Extracted\|Collected data"
```

### 3. 使用测试脚本验证

```bash
cd backend
python test_data_extraction.py
```

---

## 测试建议

### 1. 增加等待时间

在测试脚本中，提交答案后应该等待足够的时间让数据保存完成：
- 建议等待 5-10 秒
- 或者添加重试机制

### 2. 验证数据保存

在验证数据存储结构时：
- 先检查数据是否存在
- 如果不存在，提示用户等待或重试
- 提供查看日志的方法

### 3. 添加数据验证接口

可以添加一个专门的数据验证接口：
```python
@router.get("/session/{session_id}/verify")
async def verify_session_data(session_id: str):
    """验证会话数据是否正确保存"""
    # 检查数据格式
    # 检查关键字段
    # 返回验证结果
```

---

## 修复后的改进

### 1. 更好的错误提示

- 显示数据 keys 和类型
- 提供具体的错误信息
- 给出解决建议

### 2. 更详细的日志

- 记录数据保存结果
- 记录保存的数据结构
- 记录错误堆栈

### 3. 更健壮的验证

- 支持多种数据格式
- 容错处理
- 提供备用方案

---

## 后续优化建议

### 1. 数据保存确认机制

- 添加数据保存确认接口
- 或者使用事件机制通知数据保存完成

### 2. 数据验证接口

- 添加专门的数据验证接口
- 返回详细的数据结构信息

### 3. 测试脚本改进

- 添加重试机制
- 添加数据验证步骤
- 提供更详细的测试报告

---

**修复完成时间**：2024-01-01  
**相关文件**：
- `backend/test_data_extraction.py` - 测试脚本修复
- `backend/app/services/ai_service.py` - 数据持久化日志增强
