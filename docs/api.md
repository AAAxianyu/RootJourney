# API 文档

## 概述

RootJourney API 提供了家族历史探索平台的所有后端功能。

## 基础URL

```
http://localhost:8000
```

## 认证

大部分API端点需要认证。请在请求头中包含：

```
Authorization: Bearer <token>
```

## 端点列表

### API Gateway（统一第三方API接口）

#### 语音转写
- **POST** `/api/voice/transcribe`
- 讯飞语音转写，上传录音文件返回转写文本
- 请求参数：
  - `audio_file`: 音频文件（multipart/form-data）
  - `audio_format`: 音频格式（默认: wav）
  - `language`: 语言代码（默认: zh_cn）

#### LLM 问答
- **POST** `/api/llm/chat`
- GPT-4 问答接口
- 请求体：
  ```json
  {
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "model": "gpt-4",
    "temperature": 0.7
  }
  ```

#### LLM 抽取
- **POST** `/api/llm/extract`
- GPT-4 抽取 JSON 结构化信息
- 请求体：
  ```json
  {
    "text": "文本内容",
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"}
      }
    },
    "model": "gpt-4"
  }
  ```

#### 搜索
- **GET** `/api/search?query=关键词&num_results=10`
- Google Custom Search 搜索接口

#### 图片生成
- **POST** `/api/media/image`
- DALL·E 生成图片
- 请求体：
  ```json
  {
    "prompt": "图片描述",
    "size": "1024x1024"
  }
  ```

#### 视频生成（任务）
- **POST** `/api/media/video`
- 创建 Sora 视频生成任务
- 请求体：
  ```json
  {
    "prompt": "视频描述",
    "duration": 10
  }
  ```
- 返回：`{"task_id": "...", "status": "pending"}`

#### 查询视频任务状态
- **GET** `/api/media/video/{task_id}`
- 查询视频生成任务状态
- 返回：`{"status": "pending|processing|completed|failed", "url": "..."}`

### 用户相关

#### 创建用户
- **POST** `/api/users/`
- 创建新用户

#### 获取用户信息
- **GET** `/api/users/{user_id}`
- 获取指定用户的信息

### AI聊天

#### 发送消息
- **POST** `/api/chat/`
- 与AI进行对话

### 搜索

#### 执行搜索
- **POST** `/api/search/`
- 联网搜索相关信息

### 生成

#### 生成家族报告
- **POST** `/api/generate/report`
- 生成完整的家族报告

#### 生成个人传记
- **POST** `/api/generate/biography/{person_id}`
- 生成指定人物的传记

#### 生成时间轴
- **POST** `/api/generate/timeline/{person_id}`
- 生成指定人物的时间轴

### 导出

#### 导出PDF
- **GET** `/api/export/pdf/{report_id}`
- 导出报告为PDF格式

#### 导出JSON
- **GET** `/api/export/json/{report_id}`
- 导出报告为JSON格式

#### 导出家族图谱图片
- **GET** `/api/export/image/{family_tree_id}`
- 导出家族图谱为图片

## Swagger文档

启动服务后，访问 `http://localhost:8000/docs` 查看交互式API文档。

