# 祖父姓名提取修复说明

## 问题描述

测试中发现，虽然用户在对话中明确提到了"我爷爷叫张建国"，但系统没有正确提取到 `grandfather_name` 字段。

### 问题表现

- 数据中确实有相关信息：`'a': '我爷爷叫张建国'` 在 `_unparsed` 中
- 但 `grandfather_name` 字段显示"未找到"
- 搜索功能虽然能工作，但可能缺少祖父姓名这个重要信息

## 问题原因

### 1. 条件限制过严

**原代码**：
```python
if unparsed_info and (not surname or not self_origin):
    # 只有在 surname 或 self_origin 缺失时才提取
```

**问题**：当用户已经提供了姓氏和地区后，这个条件就不满足了，导致不会进入提取逻辑。

### 2. 提取条件依赖问题内容

**原代码**：
```python
if ("爷爷" in question or "祖父" in question) and not grandfather_name:
    # 提取祖父姓名
```

**问题**：如果问题不包含"爷爷"或"祖父"关键词（例如："你父亲小时候是在山东长大的吗？"），即使回答中提到了"我爷爷叫张建国"，也不会被提取。

### 3. 正则表达式不够灵活

**原代码**：
```python
name_match = re.search(r'([张李王...][\u4e00-\u9fa5]{1,2})', answer)
```

**问题**：这个正则只匹配姓氏+1-2个汉字，但没有考虑"爷爷叫XXX"这种常见表达方式。

## 修复方案

### 1. 移除条件限制

**修复后**：
```python
if unparsed_info:
    # 尝试从对话内容中提取所有缺失的信息
    # 不再限制只在 surname 或 self_origin 缺失时提取
```

### 2. 改进提取逻辑

**修复后**：
```python
# 方法1: 从回答中提取"爷爷叫XXX"或"祖父叫XXX"的模式
name_match = re.search(
    r'(?:爷爷|祖父|外公|外祖父)[叫是]\s*([张李王...][\u4e00-\u9fa5]{1,2})', 
    answer
)

# 方法2: 如果回答中包含"爷爷"或"祖父"，尝试提取后面的姓名
elif "爷爷" in answer or "祖父" in answer:
    name_match = re.search(
        r'(?:爷爷|祖父)[\s，,。]?([张李王...][\u4e00-\u9fa5]{1,2})', 
        answer
    )
```

### 3. 增强提取能力

- 支持多种表达方式："爷爷叫XXX"、"祖父是XXX"、"我爷爷XXX"
- 不依赖问题内容，直接从回答中提取
- 支持多种称呼：爷爷、祖父、外公、外祖父

## 修复后的效果

### 提取示例

1. **"我爷爷叫张建国"**
   - ✅ 匹配：`(?:爷爷|祖父)[叫是]\s*([张李王...][\u4e00-\u9fa5]{1,2})`
   - ✅ 提取：`张建国`

2. **"我祖父是张建国"**
   - ✅ 匹配：`(?:爷爷|祖父)[叫是]\s*([张李王...][\u4e00-\u9fa5]{1,2})`
   - ✅ 提取：`张建国`

3. **"爷爷张建国"**
   - ✅ 匹配：`(?:爷爷|祖父)[\s，,。]?([张李王...][\u4e00-\u9fa5]{1,2})`
   - ✅ 提取：`张建国`

## 测试验证

### 测试用例

1. **测试1：直接表达**
   - 回答："我爷爷叫张建国"
   - 预期：提取到 `grandfather_name: "张建国"`

2. **测试2：间接表达**
   - 回答："我爷爷是张建国"
   - 预期：提取到 `grandfather_name: "张建国"`

3. **测试3：简短表达**
   - 回答："爷爷张建国"
   - 预期：提取到 `grandfather_name: "张建国"`

4. **测试4：问题不相关**
   - 问题："你父亲小时候是在山东长大的吗？"
   - 回答："我爷爷叫张建国"
   - 预期：仍然能提取到 `grandfather_name: "张建国"`

## 相关改进

### 1. 姓氏提取增强

同时改进了姓氏提取逻辑：
- 支持"我姓张"这种直接表达
- 不依赖问题内容

### 2. 测试脚本改进

- 显示 `_unparsed` 数据内容
- 提示哪些信息会在搜索时被提取
- 更友好的验证提示

## 验证方法

### 1. 运行测试脚本

```bash
cd backend
python test_data_extraction.py
```

### 2. 查看日志

```bash
docker logs rootjourney-backend | grep "Extracted grandfather name"
```

### 3. 检查数据

```bash
# 获取会话详情
curl http://localhost:8000/session/{session_id}

# 检查 collected_data 中是否有 grandfather_name
```

## 预期结果

修复后，系统应该能够：
1. ✅ 从 `_unparsed` 中提取祖父姓名
2. ✅ 不依赖问题内容，直接从回答中提取
3. ✅ 支持多种表达方式
4. ✅ 正确保存到 `grandfather_name` 和 `grandfather.name`

---

**修复完成时间**：2024-01-01  
**相关文件**：
- `backend/app/services/search_service.py` - 提取逻辑修复
- `backend/test_data_extraction.py` - 测试脚本改进
