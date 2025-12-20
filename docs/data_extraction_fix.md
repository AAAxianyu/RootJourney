# 信息提取问题修复说明

## 问题描述

用户提供了姓氏"张"、地区"山东"、祖父和父亲的名字，但搜索时却显示"待确认家族"，说明系统无法正确获取用户输入的信息。

## 问题原因

### 1. 数据格式不统一

**信息提取阶段**（`ai_service.py`）：
- 使用嵌套结构存储：`{"self": {"surname": "张", "origin": "山东"}}`
- 使用嵌套结构存储：`{"grandfather": {"name": "张建国"}}`

**信息读取阶段**（`search_service.py`）：
- 虽然尝试从多个位置读取，但可能数据没有正确规范化
- 嵌套结构的数据可能没有被正确转换为扁平结构

### 2. 未解析对话内容未充分利用

- 如果信息提取失败，会保存到 `_unparsed` 中
- 但搜索时没有充分从 `_unparsed` 中提取信息

### 3. 数据规范化缺失

- 没有统一的数据规范化流程
- 嵌套结构和扁平结构混用，导致信息丢失

## 修复方案

### 1. 添加数据规范化方法

新增 `_normalize_collected_data` 方法，将嵌套结构转换为扁平结构：

```python
def _normalize_collected_data(self, collected_data: Dict[str, Any]) -> None:
    """
    规范化收集的数据，将嵌套结构转换为扁平结构，确保信息不丢失
    
    例如：
    - self.surname -> surname 和 self_origin
    - father.origin -> father_origin
    - grandfather.name -> grandfather_name
    """
    # 从嵌套结构中提取并设置扁平字段
    if "self" in collected_data:
        if "surname" in collected_data["self"]:
            collected_data["surname"] = collected_data["self"]["surname"]
        if "origin" in collected_data["self"]:
            collected_data["self_origin"] = collected_data["self"]["origin"]
    # ... 其他字段
```

### 2. 从未解析对话中提取信息

在 `analyze_family_associations` 方法中，添加从未解析对话中提取信息的逻辑：

```python
# 从未解析的对话内容中尝试提取信息（作为补充）
unparsed_info = collected_data.get("_unparsed", [])
if unparsed_info:
    for item in unparsed_info:
        answer = item.get("a", "")
        question = item.get("q", "")
        
        # 使用正则表达式提取姓氏、地区、姓名等信息
        # 如果提取成功，更新 collected_data
```

### 3. 从祖父姓名提取姓氏

如果用户提供了祖父姓名但没有提供姓氏，自动从祖父姓名中提取：

```python
# 如果从祖父姓名中提取姓氏（如果还没有姓氏）
if not surname and grandfather_name:
    surname = grandfather_name[0]
    collected_data["surname"] = surname
```

### 4. 增强日志记录

添加详细的日志记录，方便调试：

```python
logger.info(f"Extracted info - surname: {surname}, self_origin: {self_origin}")
logger.info(f"Collected data keys: {list(collected_data.keys())}")
logger.info(f"Unparsed items count: {len(collected_data.get('_unparsed', []))}")
```

## 修复后的数据流转

### 数据提取阶段

1. **AI问答收集信息**
   - 用户回答："我的姓氏是张"
   - LLM提取：`{"self": {"surname": "张"}}`
   - 保存到 `collected_data`

2. **数据规范化**
   - 调用 `_normalize_collected_data`
   - 将 `self.surname` 转换为 `surname`
   - 确保扁平字段存在

3. **未解析内容补充**
   - 如果提取失败，保存到 `_unparsed`
   - 搜索时从 `_unparsed` 中提取信息

### 数据读取阶段

1. **规范化数据**
   - 在 `analyze_family_associations` 开始时调用规范化
   - 确保所有信息都在扁平字段中

2. **多位置读取**
   - 从 `surname` 或 `self.surname` 读取
   - 从 `self_origin` 或 `self.origin` 读取
   - 从 `grandfather_name` 或 `grandfather.name` 读取

3. **未解析内容提取**
   - 如果关键信息缺失，从 `_unparsed` 中提取
   - 使用正则表达式匹配姓氏、地区、姓名

## 测试验证

### 测试场景1：嵌套结构数据

**输入数据**：
```json
{
  "self": {
    "surname": "张",
    "origin": "山东"
  },
  "grandfather": {
    "name": "张建国"
  }
}
```

**修复后**：
- 规范化后：`{"surname": "张", "self_origin": "山东", "grandfather_name": "张建国"}`
- 可以正确提取所有信息

### 测试场景2：未解析对话

**输入数据**：
```json
{
  "_unparsed": [
    {
      "q": "你家族的姓氏是？",
      "a": "我姓张"
    },
    {
      "q": "你的祖籍在哪里？",
      "a": "山东"
    }
  ]
}
```

**修复后**：
- 从 `_unparsed` 中提取：`{"surname": "张", "self_origin": "山东"}`
- 可以正确提取信息

### 测试场景3：祖父姓名提取姓氏

**输入数据**：
```json
{
  "grandfather": {
    "name": "张建国"
  }
}
```

**修复后**：
- 从祖父姓名提取姓氏：`{"surname": "张", "grandfather_name": "张建国"}`
- 可以正确提取姓氏

## 代码位置

- **数据规范化**：`backend/app/services/search_service.py` → `_normalize_collected_data`
- **信息提取增强**：`backend/app/services/search_service.py` → `analyze_family_associations`
- **未解析内容提取**：`backend/app/services/search_service.py` → `analyze_family_associations`（在提取信息部分）

## 使用建议

1. **查看日志**：如果仍然无法提取信息，查看日志中的详细信息
2. **检查数据**：可以通过 `/session/{session_id}` 接口查看实际存储的数据
3. **调试模式**：启用详细日志，查看数据提取过程

---

**最后更新**：2024-01-01
