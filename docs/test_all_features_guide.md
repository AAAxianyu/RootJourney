# 完整功能测试指南

## 测试脚本

### 文件位置
`backend/test_all_features.py`

### 功能
测试所有功能，包括：
1. ✅ 健康检查和API配置
2. ✅ 用户会话管理
3. ✅ AI问答对话
4. ✅ 家族搜索
5. ✅ 报告生成
6. ✅ **图片生成（即梦4.0）** ⭐
7. ✅ 时间轴生成
8. ✅ 传记生成

---

## 快速开始

### 1. 前置条件

确保：
- ✅ 服务已启动（`docker-compose up` 或 `uvicorn app.main:app --reload`）
- ✅ 即梦4.0 API Key 已配置（环境变量 `SEEDREAM_API_KEY`）
- ✅ DeepSeek API Key 已配置
- ✅ MongoDB 和 Redis 已启动

### 2. 运行测试

```bash
# 进入后端目录
cd backend

# 运行完整测试脚本
python test_all_features.py
```

---

## 测试流程

### 步骤1：健康检查
- 检查服务是否运行
- 检查API配置状态
- 验证即梦4.0 API Key是否配置

### 步骤2：创建会话
- 创建测试会话
- 获取 session_id

### 步骤3：AI问答
- 进行5轮问答
- 收集用户信息

### 步骤4：家族搜索（可选）
- 搜索家族历史
- 可能需要3-6分钟

### 步骤5：生成报告（必需，生图功能需要）
- 生成家族报告
- 可能需要4-7分钟
- **注意：生图功能需要先有报告**

### 步骤6：生成图片（即梦4.0）⭐
- 基于报告生成1-2张图片
- 可能需要1-3分钟
- 返回图片URL

### 步骤7：生成时间轴（可选）
- 生成家族时间轴

### 步骤8：生成传记（可选）
- 生成个人传记

---

## 生图功能测试详解

### 前置条件

1. **必须先生成报告**
   ```bash
   POST /generate/report
   {
     "session_id": "your_session_id"
   }
   ```

2. **即梦4.0 API Key 必须配置**
   ```bash
   # 检查配置
   GET /health/api-status
   
   # 应该看到：
   # "seedream": {"configured": true}
   ```

### 测试生图功能

#### 方法1：使用测试脚本

```bash
python test_all_features.py
```

按照提示操作：
1. 选择生成报告（y）
2. 选择测试生图功能（y）
3. 选择生成图片数量（1-2）

#### 方法2：使用 curl

```bash
# 1. 先确保有报告
POST /generate/report
{
  "session_id": "your_session_id"
}

# 2. 生成图片
POST /generate/images
{
  "session_id": "your_session_id",
  "num_images": 1,  # 1-2
  "size": "2K"      # 图片分辨率
}
```

#### 方法3：使用 Python

```python
import requests

BASE_URL = "http://localhost:8000"
session_id = "your_session_id"

# 1. 生成报告（如果还没有）
response = requests.post(
    f"{BASE_URL}/generate/report",
    json={"session_id": session_id},
    timeout=600
)

# 2. 生成图片
response = requests.post(
    f"{BASE_URL}/generate/images",
    json={
        "session_id": session_id,
        "num_images": 1,
        "size": "2K"
    },
    timeout=180
)

result = response.json()
images = result.get("images", [])

for i, image_url in enumerate(images, 1):
    print(f"图片 {i}: {image_url}")
```

---

## 生图功能参数

### 请求参数

```json
{
  "session_id": "string",      // 必需：会话ID
  "num_images": 1,              // 可选：生成图片数量（1-2，默认1）
  "size": "2K"                  // 可选：图片分辨率（默认"2K"）
}
```

### 响应格式

```json
{
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "count": 2,
  "session_id": "your_session_id"
}
```

---

## 常见问题

### Q1: 生图功能报错 "Report not found"

**原因**：需要先生成报告

**解决方案**：
```bash
# 先调用生成报告接口
POST /generate/report
{
  "session_id": "your_session_id"
}

# 然后再生成图片
POST /generate/images
{
  "session_id": "your_session_id"
}
```

### Q2: 生图功能报错 "即梦4.0 API key not configured"

**原因**：即梦4.0 API Key 未配置

**解决方案**：
1. 检查环境变量 `SEEDREAM_API_KEY` 是否设置
2. 检查 `.env` 文件或 Docker 环境变量
3. 重启服务使配置生效

### Q3: 生图超时

**原因**：即梦4.0 API 响应较慢

**解决方案**：
- 测试脚本已设置3分钟超时
- 如果仍然超时，检查网络连接和API配置

### Q4: 生成的图片URL无法访问

**原因**：图片URL可能有时效性

**解决方案**：
- 尽快保存图片URL
- 或者下载图片到本地

---

## 测试输出示例

### 成功示例

```
======================================================================
  7. 生成图片测试（即梦4.0）
======================================================================
ℹ️  准备生成 1 张图片...
⚠️  注意：需要先生成报告才能生成图片
✅ 图片生成完成（耗时: 45.2秒）
ℹ️  生成图片数: 1
✅ 图片 1: https://example.com/generated_image.jpg
ℹ️    可以在浏览器中打开查看
```

### 失败示例

```
❌ 生成图片失败，状态码: 404
❌ 错误信息: Report not found for session xxx. Please generate report first.
⚠️  提示：需要先调用 /generate/report 生成报告
```

---

## 验证生图功能

### 1. 检查API配置

```bash
curl http://localhost:8000/health/api-status | jq '.services.seedream'
```

应该返回：
```json
{
  "configured": true
}
```

### 2. 检查生成的图片

生成的图片URL应该：
- 可以正常访问
- 显示与家族历史相关的图片
- 图片质量符合要求

### 3. 查看日志

```bash
# Docker方式
docker logs rootjourney-backend | grep -i "seedream\|image\|即梦"

# 应该看到：
# INFO: Generated 1 images using Seedream 4.0
```

---

## 完整测试流程示例

```bash
# 1. 启动服务
docker-compose up -d

# 2. 运行测试
cd backend
python test_all_features.py

# 3. 按照提示操作：
# - 是否执行家族搜索？(y)
# - 是否生成报告？(y)
# - 是否测试生图功能？(y)
# - 生成几张图片？(1)

# 4. 查看结果
# - 报告已保存到数据库
# - 图片URL已返回
# - 可以在浏览器中打开图片URL查看
```

---

## 相关文档

- [图片生成功能指南](image_generation_guide.md)
- [API Gateway文档](api_gateway.md)
- [快速测试脚本](test_quick.py)

---

**最后更新**：2024-01-01
