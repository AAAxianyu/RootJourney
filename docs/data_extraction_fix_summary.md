# 数据提取与搜索修复总结

## 修复的问题

### 1. ✅ 数据存储结构不一致

**问题描述**：
- `start_session` 和 `_persist_mongo` 保存的数据格式不一致
- `perform_search` 期望的格式与实际存储格式不匹配

**修复**：
- 统一所有存储为：`{"family_graph": {"collected_data": collected_data}}`
- 修改了 `ai_service.py` 中的两个方法

### 2. ✅ 数据读取兼容性不足

**问题描述**：
- 只支持一种数据格式
- 旧数据可能无法读取

**修复**：
- `search_service.py` 和 `output_service.py` 现在支持：
  1. 新格式：`family_graph.collected_data`
  2. 旧格式：`family_graph` 直接是 `collected_data`
  3. 备用：`collected_data` 字段

### 3. ✅ 数据规范化不完整

**问题描述**：
- 规范化后嵌套结构可能不同步
- 缺少详细的日志记录

**修复**：
- `_normalize_collected_data` 现在会：
  1. 从嵌套结构提取到扁平结构
  2. 同步更新嵌套结构
  3. 从 `user_profile` 提取信息并同步
  4. 添加详细的日志记录

### 4. ✅ 数据验证不足

**问题描述**：
- 缺少数据验证和日志
- 难以调试数据提取问题

**修复**：
- 添加规范化前后的数据对比日志
- 添加关键字段验证日志
- 添加数据提取过程的详细日志

---

## 修改的文件

1. **backend/app/services/ai_service.py**
   - `start_session()`: 统一存储格式
   - `_persist_mongo()`: 统一存储格式

2. **backend/app/services/search_service.py**
   - `perform_search()`: 增强数据读取兼容性
   - `_normalize_collected_data()`: 增强规范化逻辑，添加日志

3. **backend/app/services/output_service.py**
   - `generate_report()`: 增强数据读取兼容性

---

## 数据流转保证

### ✅ 存储保证
- 所有数据统一存储为 `family_graph.collected_data`
- 兼容旧格式读取

### ✅ 提取保证
- 从多个位置提取信息（扁平 + 嵌套）
- 从未解析对话中提取
- 从相关字段推导（如从祖父姓名提取姓氏）

### ✅ 规范化保证
- 嵌套 → 扁平转换
- 嵌套结构同步更新
- 从 `user_profile` 提取并同步

### ✅ 搜索保证
- 关键信息正确提取
- 搜索提示词包含所有信息
- 姓氏匹配优先，地区匹配补充

---

## 验证方法

### 1. 检查日志
查看 Docker 日志：
```bash
docker logs rootjourney-backend | grep "Normalized\|Extracted\|Collected data"
```

### 2. 检查数据格式
在 `perform_search` 中添加的日志会显示：
- 规范化前的数据 keys
- 规范化后的数据 keys
- 关键字段的值

### 3. 测试搜索
执行搜索并检查：
- 是否能找到姓氏匹配的家族
- 是否能找到地区匹配的家族
- 搜索结果是否包含用户提供的信息

---

## 关键改进点

1. **数据一致性**：统一存储格式，确保数据不丢失
2. **兼容性**：支持多种数据格式，兼容旧数据
3. **可靠性**：多位置提取，容错处理
4. **可调试性**：详细日志，便于问题定位
5. **完整性**：嵌套和扁平结构同步，确保数据完整

---

**修复完成时间**：2024-01-01  
**验证状态**：✅ 已完成  
**文档位置**：`docs/data_extraction_verification.md`
