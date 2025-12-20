# 数据提取与搜索功能测试指南

## 测试脚本说明

### 文件位置
`backend/test_data_extraction.py`

### 功能
专门测试数据提取、规范化、存储和搜索的完整流程，验证：
1. 数据存储格式是否正确
2. 数据提取是否从多个位置读取
3. 数据规范化是否工作
4. 搜索时是否能正确识别和使用数据
5. 姓氏匹配是否优先
6. 地区匹配是否作为补充

---

## 运行测试

### 前置条件

1. **确保服务已启动**
   ```bash
   # 方式1: Docker Compose
   docker-compose up -d
   
   # 方式2: 直接运行
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **确保依赖已安装**
   ```bash
   pip install requests
   ```

### 运行测试

```bash
# 进入后端目录
cd backend

# 运行测试脚本
python test_data_extraction.py
```

### 测试流程

测试脚本会自动执行以下步骤：

1. **检查服务状态**
   - 验证服务是否运行
   - 检查健康检查接口

2. **创建测试会话**
   - 使用测试数据创建会话
   - 测试数据包含：姓名"张三"（姓氏"张"）、出生地"北京"

3. **获取初始问题**
   - 获取AI生成的第一个问题

4. **提交测试答案**
   - 提交4个测试答案：
     - "我的祖籍是山东"（提取祖籍）
     - "我姓张"（提取姓氏）
     - "我爷爷叫张建国"（提取祖父姓名，可用于推导姓氏）
     - "我爸爸的老家在山东济南"（提取父亲籍贯）

5. **验证数据存储结构**
   - 检查数据格式是否正确
   - 验证关键字段是否存在
   - 检查嵌套和扁平结构

6. **测试搜索功能**
   - 执行家族搜索（需要3-6分钟）
   - 验证姓氏匹配是否优先
   - 验证地区匹配是否作为补充
   - 检查搜索结果是否包含用户提供的信息

7. **验证数据规范化**
   - 提示查看服务器日志
   - 验证规范化过程

---

## 测试输出说明

### 成功标识
- ✅ 绿色：测试通过
- ⚠️ 黄色：警告信息
- ℹ️ 蓝色：信息提示
- ❌ 红色：测试失败

### 关键输出

#### 数据存储验证
```
✅ 数据格式正确: family_graph.collected_data
✅ surname: 张 (来源: surname)
✅ self_origin: 山东 (来源: self_origin)
✅ grandfather_name: 张建国 (来源: grandfather.name)
```

#### 搜索验证
```
✅ 找到姓氏匹配: 琅琊张氏
  关联度: 高
  关联线索: 姓氏：张
  著名人物数: 3
```

---

## 验证数据规范化

### 查看服务器日志

```bash
# Docker 方式
docker logs rootjourney-backend | grep -E "Normalized|Extracted|Collected data"

# 或者查看完整日志
docker logs rootjourney-backend --tail 100
```

### 关键日志信息

#### 规范化日志
```
INFO: Normalized: self.surname -> surname: 张
INFO: Normalized: self.origin -> self_origin: 山东
INFO: Normalized data - Found fields: ['surname', 'self_origin', 'grandfather_name']
```

#### 提取日志
```
INFO: Extracted info - surname: 张, self_origin: 山东, father_origin: 山东济南, grandfather_name: 张建国
INFO: Final extracted info - surname: '张', self_origin: '山东', father_origin: '山东济南', grandfather_name: '张建国'
```

#### 搜索日志
```
INFO: Collected data before normalization - keys: ['user_profile', 'self', 'grandfather', 'father']
INFO: Collected data after normalization - keys: ['user_profile', 'self', 'grandfather', 'father', 'surname', 'self_origin', 'father_origin', 'grandfather_name']
INFO: Key fields for search - surname: 张, self_origin: 山东, grandfather_name: 张建国
```

---

## 手动验证步骤

### 1. 检查数据存储

```bash
# 使用 curl 获取会话详情
curl http://localhost:8000/session/{session_id}
```

检查响应中的 `collected_data` 结构：
- 是否包含扁平字段（`surname`, `self_origin`等）
- 是否包含嵌套结构（`self`, `grandfather`等）
- 数据是否同步

### 2. 检查数据提取

查看日志中的提取信息：
- 是否从多个位置读取
- 是否从未解析对话中提取
- 是否从相关字段推导

### 3. 检查搜索功能

执行搜索并检查：
- 是否找到姓氏匹配的家族
- 是否找到地区匹配的家族
- 搜索结果是否包含用户提供的信息

---

## 常见问题

### Q1: 测试脚本无法连接到服务器

**解决方案**：
1. 确保服务已启动：`docker-compose up` 或 `uvicorn app.main:app --reload`
2. 检查端口是否正确：默认 `http://localhost:8000`
3. 检查防火墙设置

### Q2: 搜索超时

**原因**：搜索需要调用多个LLM API，可能需要较长时间

**解决方案**：
- 测试脚本已设置10分钟超时
- 如果仍然超时，检查网络连接和API配置

### Q3: 数据格式不正确

**解决方案**：
1. 检查服务器日志，查看数据规范化过程
2. 确认数据存储格式已统一
3. 检查是否有旧格式数据需要迁移

### Q4: 未找到关键字段

**解决方案**：
1. 检查AI问答是否成功提取信息
2. 查看日志中的提取过程
3. 确认数据规范化是否执行

---

## 测试数据说明

### 测试用例设计

测试脚本使用的测试数据：
- **姓名**：张三（用于提取姓氏"张"）
- **出生地**：北京（初始地区信息）
- **祖籍**：山东（用于地区匹配）
- **姓氏**：张（用于姓氏匹配）
- **祖父姓名**：张建国（用于推导姓氏）
- **父亲籍贯**：山东济南（用于地区匹配）

### 预期结果

1. **数据提取**：
   - 姓氏"张"应从多个位置提取（`user_profile.name[0]`, `self.surname`, `grandfather.name[0]`）
   - 地区"山东"应从多个位置提取（`self.origin`, `self_origin`, `father.origin`）

2. **数据规范化**：
   - 嵌套结构应转换为扁平结构
   - 嵌套结构应同步更新

3. **搜索匹配**：
   - 应优先找到姓氏"张"相关的家族（如"琅琊张氏"）
   - 应找到地区"山东"相关的家族
   - 搜索结果应包含用户提供的信息

---

## 扩展测试

### 测试其他姓氏

修改测试脚本中的测试数据：
```python
test_data = {
    "name": "李四",  # 改为其他姓氏
    "birth_place": "陕西",
    ...
}
```

### 测试边界情况

1. **只提供姓氏**：测试姓氏匹配
2. **只提供地区**：测试地区匹配
3. **只提供祖父姓名**：测试姓氏推导
4. **信息不足**：测试容错处理

---

## 相关文档

- [数据转换流程详解](data_transformation_flow.md)
- [数据提取修复说明](data_extraction_fix.md)
- [数据提取验证文档](data_extraction_verification.md)
- [用户信息收集与匹配](user_info_collection_and_matching.md)

---

**最后更新**：2024-01-01
