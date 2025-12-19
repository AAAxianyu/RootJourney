# API Gateway 使用文档

## 概述

API Gateway 统一封装了所有第三方 API 调用，项目内其他模块只需要调用这些统一接口，无需各自配置第三方 SDK。

## 基础URL

```
http://localhost:8000/api
```

## 接口列表

### 1. 语音转写

**POST** `/api/voice/transcribe`

讯飞语音转写接口，上传录音文件返回转写文本。

**请求参数：**
- `audio_file` (file): 音频文件（multipart/form-data）
- `audio_format` (form): 音频格式，默认 `wav`（可选：wav, mp3, m4a等）
- `language` (form): 语言代码，默认 `zh_cn`（可选：zh_cn, en_us等）

**响应示例：**
```json
{
  "success": true,
  "text": "转写后的文本内容",
  "format": "wav",
  "language": "zh_cn"
}
```

**使用示例：**
```python
import requests

files = {'audio_file': open('audio.wav', 'rb')}
data = {'audio_format': 'wav', 'language': 'zh_cn'}
response = requests.post('http://localhost:8000/api/voice/transcribe', files=files, data=data)
print(response.json())
```

---

### 2. LLM 问答

**POST** `/api/llm/chat`

GPT-4 问答接口。

**请求体：**
```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "model": "gpt-4",
  "temperature": 0.7
}
```

**响应示例：**
```json
{
  "success": true,
  "response": "你好！有什么可以帮助你的吗？",
  "model": "gpt-4"
}
```

**使用示例：**
```python
import requests

data = {
    "messages": [
        {"role": "user", "content": "请介绍一下家族历史的重要性"}
    ],
    "model": "gpt-4",
    "temperature": 0.7
}
response = requests.post('http://localhost:8000/api/llm/chat', json=data)
print(response.json())
```

---

### 3. LLM 抽取

**POST** `/api/llm/extract`

GPT-4 抽取 JSON 结构化信息。

**请求体：**
```json
{
  "text": "张三，1990年出生于北京，祖籍山东",
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "birth_year": {"type": "integer"},
      "birth_place": {"type": "string"},
      "origin": {"type": "string"}
    },
    "required": ["name"]
  },
  "model": "gpt-4"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "name": "张三",
    "birth_year": 1990,
    "birth_place": "北京",
    "origin": "山东"
  },
  "model": "gpt-4"
}
```

---

### 4. 搜索

**GET** `/api/search`

Google Custom Search 搜索接口。

**查询参数：**
- `query` (required): 搜索关键词
- `num_results` (optional): 返回结果数量，默认 10

**响应示例：**
```json
{
  "success": true,
  "query": "家族历史",
  "results": [
    {
      "title": "搜索结果标题",
      "url": "https://example.com",
      "snippet": "搜索结果摘要",
      "source": "google"
    }
  ],
  "count": 10
}
```

**使用示例：**
```python
import requests

params = {"query": "家族历史", "num_results": 5}
response = requests.get('http://localhost:8000/api/search', params=params)
print(response.json())
```

---

### 5. 图片生成

**POST** `/api/media/image`

DALL·E 生成图片。

**请求体：**
```json
{
  "prompt": "一幅描绘中国传统家族聚会的场景，温馨和谐",
  "size": "1024x1024"
}
```

**响应示例：**
```json
{
  "success": true,
  "url": "https://oaidalleapiprodscus.blob.core.windows.net/...",
  "prompt": "一幅描绘中国传统家族聚会的场景，温馨和谐",
  "size": "1024x1024"
}
```

**使用示例：**
```python
import requests

data = {
    "prompt": "中国传统家族场景",
    "size": "1024x1024"
}
response = requests.post('http://localhost:8000/api/media/image', json=data)
print(response.json())
```

---

### 6. 视频生成（任务）

**POST** `/api/media/video`

创建 Sora 视频生成任务（异步）。

**请求体：**
```json
{
  "prompt": "一个展示家族历史传承的动画视频",
  "duration": 10
}
```

**响应示例：**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "视频生成任务已创建，请使用任务ID查询状态"
}
```

**使用示例：**
```python
import requests
import time

# 创建任务
data = {
    "prompt": "家族历史视频",
    "duration": 10
}
response = requests.post('http://localhost:8000/api/media/video', json=data)
task_id = response.json()['task_id']

# 轮询查询状态
while True:
    status_response = requests.get(f'http://localhost:8000/api/media/video/{task_id}')
    status = status_response.json()
    print(f"Status: {status['status']}")
    
    if status['status'] == 'completed':
        print(f"Video URL: {status['url']}")
        break
    elif status['status'] == 'failed':
        print(f"Error: {status.get('error')}")
        break
    
    time.sleep(2)  # 等待2秒后再次查询
```

---

### 7. 查询视频任务状态

**GET** `/api/media/video/{task_id}`

查询视频生成任务状态。

**路径参数：**
- `task_id`: 任务ID

**响应示例：**

**进行中：**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

**已完成：**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "url": "https://example.com/video.mp4"
}
```

**失败：**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "错误信息"
}
```

---

## 配置要求

在 `backend/.env` 文件中配置以下环境变量：

```env
# OpenAI (LLM 和图片生成)
OPENAI_API_KEY=your_openai_api_key

# 讯飞语音转写
XUNFEI_APP_ID=your_app_id
XUNFEI_API_KEY=your_api_key
XUNFEI_API_SECRET=your_api_secret

# Google Custom Search
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id
```

## 错误处理

所有接口在出错时会返回标准错误格式：

```json
{
  "detail": "错误信息"
}
```

HTTP 状态码：
- `400`: 请求参数错误
- `404`: 资源不存在（如任务ID不存在）
- `500`: 服务器内部错误

## 测试 API 连接

在开始使用前，建议先测试所有 API 的连接状态。我们提供了多种测试方法：

### 快速测试（推荐）

访问健康检查端点：
- **GET** `/health/api-status` - 检查配置状态
- **POST** `/health/test/all` - 测试所有 API 连接
- **POST** `/health/test/openai` - 单独测试 OpenAI
- **POST** `/health/test/search` - 单独测试 Google Search
- **POST** `/health/test/image` - 单独测试 DALL·E
- **GET** `/health/test/database` - 测试数据库连接

### 使用测试脚本

```bash
cd backend
python scripts/test_apis.py
```

详细测试指南请参考：[测试指南](testing_guide.md)

## 注意事项

1. **视频生成是异步任务**：创建任务后需要轮询查询状态
2. **任务超时**：视频生成任务默认超时时间为 300 秒（5分钟）
3. **任务状态保留**：完成后的任务信息会在 Redis 中保留 1 小时
4. **文件大小限制**：语音转写接口建议音频文件不超过 10MB

