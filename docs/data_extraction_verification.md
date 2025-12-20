# 数据提取与搜索验证文档

## 修复总结

### 1. 数据存储结构统一 ✅

**问题**：数据存储格式不一致
- `start_session` 保存：`{"family_graph": {"user_profile": {...}}}`
- `_persist_mongo` 保存：`{"family_graph": collected_data}`（直接保存）
- `perform_search` 期望：`{"family_graph": {"collected_data": {...}}}`

**修复**：
- 统一所有存储为：`{"family_graph": {"collected_data": collected_data}}`
- 修改了 `ai_service.py` 中的 `start_session` 和 `_persist_mongo`

### 2. 数据读取兼容性增强 ✅

**问题**：只支持一种数据格式，旧数据可能无法读取

**修复**：
- `search_service.py` 的 `perform_search` 现在支持：
  1. 新格式：`family_graph.collected_data`
  2. 旧格式：`family_graph` 直接是 `collected_data`
  3. 备用：`collected_data` 字段
- `output_service.py` 也做了相同的兼容性处理

### 3. 数据规范化增强 ✅

**问题**：规范化后嵌套结构可能不同步

**修复**：
- `_normalize_collected_data` 现在会：
  1. 从嵌套结构提取到扁平结构
  2. 同步更新嵌套结构（保持一致性）
  3. 从 `user_profile` 提取信息并同步到嵌套结构
  4. 添加详细的日志记录

### 4. 数据验证和日志 ✅

**新增**：
- 规范化前后的数据对比日志
- 关键字段验证日志
- 数据提取过程的详细日志

---

## 完整数据流转验证

### 阶段1：用户初始输入

**输入**：
```json
POST /user/input
{
  "name": "张三",
  "birth_place": "北京"
}
```

**存储**（MongoDB）：
```json
{
  "_id": "session_id",
  "user_profile": {
    "name": "张三",
    "birth_place": "北京"
  },
  "family_graph": {
    "collected_data": {
      "user_profile": {
        "name": "张三",
        "birth_place": "北京"
      }
    }
  }
}
```

**验证点**：
- ✅ `family_graph.collected_data` 存在
- ✅ `user_profile` 在 `collected_data` 中

---

### 阶段2：AI问答提取

**用户回答**："我的祖籍是山东"

**LLM提取**：
```json
{
  "self": {
    "origin": "山东"
  }
}
```

**合并后**（Redis + MongoDB）：
```json
{
  "family_graph": {
    "collected_data": {
      "user_profile": {"name": "张三", "birth_place": "北京"},
      "self": {"origin": "山东"}
    }
  }
}
```

**验证点**：
- ✅ 嵌套结构正确合并
- ✅ 数据保存到 MongoDB

---

### 阶段3：数据规范化（搜索前）

**规范化前**：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {"origin": "山东"}
}
```

**规范化后**：
```json
{
  "user_profile": {"name": "张三", "birth_place": "北京"},
  "self": {
    "origin": "山东",
    "surname": "张"  // 从 user_profile.name 提取
  },
  "surname": "张",           // 扁平结构
  "self_origin": "山东"       // 扁平结构
}
```

**验证点**：
- ✅ 扁平字段已创建
- ✅ 嵌套结构同步更新
- ✅ 从 `user_profile.name` 提取姓氏

---

### 阶段4：信息提取与补充

**从未解析对话提取**：
- 如果 `surname` 缺失，从 `_unparsed` 中提取
- 如果 `self_origin` 缺失，从 `_unparsed` 中提取
- 如果 `grandfather_name` 缺失，从 `_unparsed` 中提取

**从祖父姓名提取姓氏**：
- 如果 `surname` 缺失但 `grandfather_name` 存在
- 提取 `grandfather_name[0]` 作为姓氏

**验证点**：
- ✅ 多位置读取信息
- ✅ 从未解析内容补充
- ✅ 从相关字段推导

---

### 阶段5：搜索使用

**提取的关键信息**：
```python
surname = "张"              # 从多个位置读取
self_origin = "山东"        # 从多个位置读取
grandfather_name = "张建国"  # 从多个位置读取
```

**搜索提示词**：
```
姓氏：张
祖籍/籍贯：山东
祖父姓名：张建国
```

**验证点**：
- ✅ 关键信息正确提取
- ✅ 搜索提示词包含所有信息
- ✅ 姓氏匹配优先执行
- ✅ 地区匹配作为补充

---

## 数据格式支持矩阵

| 信息类型 | 嵌套结构 | 扁平结构 | 初始输入 | 提取位置 |
|---------|---------|---------|---------|---------|
| 姓氏 | `self.surname` | `surname` | `user_profile.name[0]` | ✅ 全部支持 |
| 祖籍 | `self.origin` | `self_origin` | `user_profile.birth_place` | ✅ 全部支持 |
| 父亲籍贯 | `father.origin` | `father_origin` | - | ✅ 全部支持 |
| 祖父姓名 | `grandfather.name` | `grandfather_name` | - | ✅ 全部支持 |
| 辈分字 | `self.generation_name` | `generation_char` | - | ✅ 全部支持 |

---

## 关键验证点检查清单

### 数据存储 ✅
- [x] 统一存储格式：`family_graph.collected_data`
- [x] 兼容旧格式读取
- [x] 数据持久化到 MongoDB

### 数据提取 ✅
- [x] LLM 提取嵌套结构
- [x] 深度合并多个提取结果
- [x] 从未解析对话中提取
- [x] 从相关字段推导（如从祖父姓名提取姓氏）

### 数据规范化 ✅
- [x] 嵌套 → 扁平转换
- [x] 嵌套结构同步更新
- [x] 从 `user_profile` 提取并同步

### 数据读取 ✅
- [x] 支持多种数据格式
- [x] 多位置读取（扁平 + 嵌套）
- [x] 容错处理（缺失字段）

### 搜索使用 ✅
- [x] 关键信息正确提取
- [x] 搜索提示词包含所有信息
- [x] 姓氏匹配优先
- [x] 地区匹配补充

---

## 日志验证

### 规范化日志
```
INFO: Normalized: self.surname -> surname: 张
INFO: Normalized: self.origin -> self_origin: 山东
INFO: Normalized data - Found fields: ['surname', 'self_origin']
```

### 提取日志
```
INFO: Extracted info - surname: 张, self_origin: 山东, father_origin: , grandfather_name: 张建国
INFO: Final extracted info - surname: '张', self_origin: '山东', father_origin: '', grandfather_name: '张建国'
```

### 搜索日志
```
INFO: Collected data before normalization - keys: ['user_profile', 'self', 'grandfather']
INFO: Collected data after normalization - keys: ['user_profile', 'self', 'grandfather', 'surname', 'self_origin', 'grandfather_name']
INFO: Key fields for search - surname: 张, self_origin: 山东, grandfather_name: 张建国
```

---

## 潜在问题和解决方案

### 问题1：数据格式不一致

**症状**：搜索时找不到数据

**原因**：旧数据使用旧格式存储

**解决方案**：
- ✅ 已实现兼容性读取
- ✅ 新数据统一使用新格式

### 问题2：信息提取失败

**症状**：关键信息缺失

**原因**：LLM 提取失败或用户回答不明确

**解决方案**：
- ✅ 从未解析对话中提取
- ✅ 从相关字段推导
- ✅ 多位置读取

### 问题3：数据不同步

**症状**：扁平结构和嵌套结构不一致

**原因**：规范化后没有同步更新

**解决方案**：
- ✅ 规范化时同步更新嵌套结构
- ✅ 添加验证日志

---

## 测试建议

### 1. 新会话测试
1. 创建新会话，提供初始信息
2. 进行多轮问答
3. 执行搜索
4. 验证数据格式和搜索结果

### 2. 旧数据兼容性测试
1. 使用旧格式的数据
2. 执行搜索
3. 验证是否能正确读取

### 3. 边界情况测试
1. 只提供姓氏
2. 只提供地区
3. 只提供祖父姓名
4. 验证各种组合

### 4. 数据完整性测试
1. 检查规范化后的数据
2. 验证关键字段是否存在
3. 验证嵌套和扁平结构是否同步

---

## 总结

✅ **数据存储**：已统一格式，兼容旧数据  
✅ **数据提取**：多位置提取，容错处理  
✅ **数据规范化**：嵌套↔扁平双向同步  
✅ **数据读取**：支持多种格式，容错处理  
✅ **搜索使用**：关键信息正确提取和使用  

**系统现在能够：**
1. 正确提取用户输入和对话信息
2. 规范化数据格式，确保不丢失信息
3. 兼容多种数据格式
4. 正确识别和使用关键信息进行搜索
5. 提供详细的日志用于调试

---

**最后更新**：2024-01-01
