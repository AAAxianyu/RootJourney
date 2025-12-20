# RootJourney 完整开发与使用指南

## 📚 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [技术栈](#技术栈)
4. [环境配置](#环境配置)
5. [快速开始](#快速开始)
6. [功能模块详解](#功能模块详解)
7. [API 接口文档](#api-接口文档)
8. [数据库设计](#数据库设计)
9. [性能优化](#性能优化)
10. [部署指南](#部署指南)
11. [开发指南](#开发指南)
12. [故障排查](#故障排查)
13. [常见问题](#常见问题)

---

## 项目概述

### 项目简介

**RootJourney** 是一个基于 AI 的家族历史探索平台，通过智能问答、联网搜索、知识图谱等技术，帮助用户发现和了解自己的家族历史，并生成个性化的家族报告、时间轴和传记。

### 核心价值

- 🔍 **智能探索**：通过 AI 问答逐步收集家族信息
- 🌐 **联网搜索**：自动搜索家族历史和相关名人
- 📊 **可视化**：构建家族图谱和时间轴
- 📝 **个性化报告**：生成专属的家族历史报告
- 💾 **档案管理**：保存和管理多个家族档案

### 目标用户

- 对家族历史感兴趣的个人
- 想要了解家族传承的用户
- 需要整理家族信息的用户

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                     前端层 (React)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ 用户输入  │  │ AI对话   │  │ 家族图谱 │  │ 报告展示 ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────┐
│                  后端层 (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ 用户管理 │  │ AI服务    │  │ 搜索服务 │  │ 生成服务 ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ 图谱服务 │  │ 导出服务 │  │ 会话管理 │  │ API网关 ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└──────┬──────────────┬──────────────┬──────────────┬─────┘
       │              │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  MongoDB    │ │  Redis    │ │ DeepSeek  │ │ 博查API   │
│  (数据存储)  │ │  (缓存)   │ │  (LLM)    │ │ (搜索)    │
└─────────────┘ └───────────┘ └───────────┘ └───────────┘
```

### 模块划分

#### 前端模块
- **用户输入模块**：收集用户基本信息
- **AI 对话模块**：与 AI 进行问答交互
- **可视化模块**：展示家族图谱和时间轴
- **报告展示模块**：展示生成的报告和传记

#### 后端模块
- **用户管理模块**：处理用户输入和会话创建
- **AI 服务模块**：处理 AI 问答和信息提取
- **搜索服务模块**：执行联网搜索和历史信息检索
- **图谱服务模块**：构建和更新家族图谱
- **生成服务模块**：生成报告、传记、时间轴
- **导出服务模块**：导出 PDF、JSON、图片
- **会话管理模块**：管理会话档案
- **API 网关模块**：统一第三方 API 调用

---

## 技术栈

### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 开发语言 |
| FastAPI | Latest | Web 框架 |
| Pydantic | Latest | 数据验证 |
| Motor | Latest | MongoDB 异步驱动 |
| Redis | Latest | 缓存和会话存储 |
| NetworkX | Latest | 图谱构建 |
| httpx | Latest | HTTP 客户端 |
| OpenAI SDK | Latest | DeepSeek API 调用 |
| Uvicorn | Latest | ASGI 服务器 |

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| React | Latest | UI 框架 |
| Axios | Latest | HTTP 客户端 |
| ECharts | Latest | 数据可视化 |
| React Scripts | Latest | 构建工具 |

### 数据库和存储

| 技术 | 用途 |
|------|------|
| MongoDB | 主数据库，存储会话、图谱、报告 |
| Redis | 缓存、临时会话状态 |

### 第三方服务

| 服务 | 用途 |
|------|------|
| DeepSeek API | LLM 问答、文本生成、信息提取 |
| 博查API | 联网搜索家族历史信息 |

---

## 环境配置

### 系统要求

- **操作系统**：Windows 10+, macOS, Linux
- **Python**：3.10 或更高版本
- **Node.js**：16.x 或更高版本（前端开发）
- **Docker**：可选，用于容器化部署

### 环境变量配置

创建 `backend/.env` 文件：

```env
# MongoDB 配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=genealogy_tracer

# Redis 配置
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# DeepSeek API 配置（必需）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 博查API 配置（可选，用于联网搜索）
BOCHA_API_KEY=your_bocha_api_key_here
BOCHA_API_BASE_URL=https://api.bochaai.com/v1

# 认证配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 会话配置
SESSION_EXPIRE_SECONDS=3600
MIN_QUESTIONS=5
```

### 获取 API 密钥

#### DeepSeek API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账号并登录
3. 进入 API 管理页面
4. 创建新的 API Key
5. 将 Key 配置到 `.env` 文件中

#### 博查API Key（可选）

1. 访问博查AI官网
2. 注册并获取 API Key
3. 配置到 `.env` 文件中

**注意**：如果不配置博查API，系统会回退到使用 DeepSeek 的知识库搜索。

---

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd ai-genealogy-tracer

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API 密钥

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f backend

# 5. 访问服务
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
# 前端: http://localhost:3000
```

### 方式二：本地开发

#### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 MongoDB 和 Redis（如果未运行）
# MongoDB: mongod
# Redis: redis-server

# 5. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm start
```

### 快速测试

```bash
# 进入后端目录
cd backend

# 运行快速测试脚本
python test_quick.py
```

测试脚本会：
1. 检查服务健康状态
2. 检查 API 配置
3. 创建测试会话
4. 进行 AI 问答
5. 搜索家族历史
6. 生成家族报告

---

## 功能模块详解

### 1. 用户管理模块

#### 功能说明

用户管理模块负责接收用户输入的基本信息，创建会话，并初始化家族图谱。

#### 核心接口

**POST `/user/input`**

创建新会话并接收用户基本信息。

**请求体**：
```json
{
  "name": "张三",
  "birth_date": "1990-01-01",
  "birth_place": "北京",
  "current_location": "上海"
}
```

**响应**：
```json
{
  "session_id": "abc123",
  "message": "会话创建成功"
}
```

#### 数据流程

1. 接收用户输入
2. 创建 MongoDB 会话记录
3. 初始化 Redis 会话状态
4. 返回 `session_id`

---

### 2. AI 问答模块

#### 功能说明

AI 问答模块通过多轮对话逐步收集家族信息，使用 DeepSeek LLM 生成智能问题，并从用户回答中提取结构化信息。

#### 核心接口

**GET `/ai/question/{session_id}`**

获取当前问题或初始问题。

**响应**：
```json
{
  "question": "请告诉我您的祖籍在哪里？",
  "round": 1
}
```

**POST `/ai/chat`**

提交用户回答，AI 生成下一个问题或结束收集。

**请求体**：
```json
{
  "session_id": "abc123",
  "answer": "我的祖籍是山东"
}
```

**响应**：
```json
{
  "status": "continue",
  "question": "请告诉我您父亲的姓名和出生年份？",
  "round": 2,
  "collected_data": {
    "self_origin": "山东"
  }
}
```

#### 工作流程

1. **问题生成**：基于已收集数据，使用 DeepSeek 生成下一个问题
2. **信息提取**：从用户回答中提取结构化信息（姓名、关系、日期、地点等）
3. **图谱更新**：将提取的信息更新到家族图谱
4. **状态判断**：判断是否收集到足够信息，决定继续或结束

#### 信息提取规则

系统会自动从用户回答中提取：
- **人物信息**：姓名、关系、出生年份、出生地
- **家族信息**：祖籍、辈分字、迁徙历史
- **关系信息**：父子关系、祖孙关系等

---

### 3. 搜索模块

#### 功能说明

搜索模块基于收集的家族信息，进行联网搜索，查找相关的历史大家族、历史名人和历史事件。

#### 核心接口

**GET `/search/family?session_id={session_id}`**

执行家族历史搜索。

**响应**：
```json
{
  "results": {
    "possible_families": [
      {
        "family_name": "张氏家族",
        "historical_background": "...",
        "main_regions": ["山东", "河南"],
        "famous_figures": [...],
        "relevance": "高"
      }
    ],
    "family_histories": {...},
    "summary": {
      "total_families_found": 2,
      "high_relevance_families": [...]
    }
  }
}
```

#### 搜索策略

1. **家族关联分析**：使用 DeepSeek 分析用户可能与哪些历史大家族有关
2. **并行搜索**：对多个可能的家族并行执行历史搜索
3. **结果整理**：使用 DeepSeek 整理和总结搜索结果

#### 性能优化

- 并行执行多个家族的搜索
- 只搜索前3个最相关的家族
- 减少搜索结果数量（3个结果）
- 优化提示词，加快 LLM 响应

**预计耗时**：60-90秒

---

### 4. 图谱构建模块

#### 功能说明

图谱构建模块使用 NetworkX 构建家族知识图谱，支持关系推断和可视化数据生成。

#### 核心功能

- **图谱构建**：基于收集的数据构建家族树
- **关系推断**：推测缺失的世代信息
- **可视化数据**：生成前端可视化所需的数据格式

#### 数据结构

```json
{
  "nodes": [
    {
      "id": "person_1",
      "name": "张三",
      "birth_year": 1990,
      "birth_place": "北京"
    }
  ],
  "edges": [
    {
      "source": "person_1",
      "target": "person_2",
      "relation": "父子"
    }
  ]
}
```

---

### 5. 生成服务模块

#### 功能说明

生成服务模块整合所有收集和搜索的数据，生成个性化的家族报告、个人传记和时间轴。

#### 核心接口

**POST `/generate/report`**

生成家族历史报告。

**请求体**：
```json
{
  "session_id": "abc123"
}
```

**响应**：
```json
{
  "report": {
    "title": "一脉相承，薪火相传——张三家族历史寻根报告",
    "report_text": "...",
    "possible_families": [...],
    "family_histories": {...},
    "generated_at": "2024-01-01T00:00:00"
  }
}
```

**POST `/generate/biography/{person_id}`**

生成个人传记。

**POST `/generate/timeline/{person_id}`**

生成时间轴。

#### 报告结构

生成的报告包含以下章节：

1. **第一章：根脉所系——家族的起源与迁徙故事**
2. **第二章：历史大家族故事与名人**
3. **第三章：文化传承**
4. **第四章：个人与家族**

#### 性能优化

- 报告长度控制在 1500-2000 字
- 历史名人描述简洁（每位 50-100 字）
- 优化提示词，加快生成速度

**预计耗时**：120-180秒

---

### 6. 会话管理模块

#### 功能说明

会话管理模块提供查看、保存和管理会话档案的功能。

#### 核心接口

**GET `/session/{session_id}`**

获取会话详情。

**GET `/session/{session_id}/report`**

获取会话报告。

**POST `/session/{session_id}/archive`**

保存会话为档案。

**请求体**：
```json
{
  "title": "张三的家族历史档案",
  "notes": "重要资料"
}
```

**GET `/session/list?archived=true`**

列出所有会话（支持筛选）。

详细文档请参考：[会话管理 API 文档](./session_api.md)

---

### 7. 导出服务模块

#### 功能说明

导出服务模块提供多种格式的导出功能。

#### 核心接口

**GET `/export/pdf/{report_id}`**

导出报告为 PDF。

**GET `/export/json/{report_id}`**

导出报告为 JSON。

**GET `/export/image/{family_tree_id}`**

导出家族图谱为图片。

---

## API 接口文档

### 基础信息

- **Base URL**：`http://localhost:8000`
- **API 版本**：v1.0.0
- **文档地址**：`http://localhost:8000/docs`（Swagger UI）

### 接口分类

#### 用户相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/user/input` | 创建会话并接收用户输入 |

#### AI 问答

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ai/question/{session_id}` | 获取问题 |
| POST | `/ai/chat` | 提交回答 |

#### 搜索

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/search/family` | 搜索家族历史 |

#### 生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/generate/report` | 生成家族报告 |
| POST | `/generate/biography/{person_id}` | 生成个人传记 |
| POST | `/generate/timeline/{person_id}` | 生成时间轴 |

#### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/session/{session_id}` | 获取会话详情 |
| GET | `/session/{session_id}/report` | 获取会话报告 |
| POST | `/session/{session_id}/archive` | 保存会话档案 |
| GET | `/session/list` | 列出所有会话 |

#### 导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/export/pdf/{report_id}` | 导出 PDF |
| GET | `/export/json/{report_id}` | 导出 JSON |
| GET | `/export/image/{family_tree_id}` | 导出图片 |

#### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health/` | 健康检查 |
| GET | `/health/api-status` | API 配置状态 |
| POST | `/health/test/all` | 测试所有 API |

### 完整 API 文档

访问 `http://localhost:8000/docs` 查看交互式 API 文档（Swagger UI）。

---

## 数据库设计

### MongoDB 集合结构

#### sessions 集合

存储会话和家族数据。

```json
{
  "_id": "session_id",
  "user_input": {
    "name": "张三",
    "birth_date": "1990-01-01",
    "birth_place": "北京",
    "current_location": "上海"
  },
  "family_graph": {
    "nodes": [...],
    "edges": [...],
    "collected_data": {
      "self_origin": "山东",
      "father_origin": "山东济南",
      "grandfather_name": "张建国",
      "generation_char": "建"
    }
  },
  "report": {
    "title": "...",
    "report_text": "...",
    "possible_families": [...]
  },
  "archived": false,
  "archive_title": null,
  "archive_notes": null,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Redis 数据结构

#### 会话状态

```
Key: session:{session_id}
Value: JSON string
TTL: 3600 seconds
```

存储临时会话状态，包括：
- 当前问题
- 问答轮数
- 收集的数据

---

## 性能优化

### 已实施的优化

1. **并行执行搜索**：多个家族搜索并行执行
2. **限制搜索数量**：只搜索前3个最相关的家族
3. **减少结果数量**：从5个结果减少到3个
4. **优化提示词**：要求更简洁的描述
5. **降低温度参数**：从0.8-0.9降低到0.7-0.8
6. **添加超时控制**：避免无限等待

### 性能指标

| 操作 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 搜索家族历史（3个家族） | 270秒 | 90秒 | 67% |
| 生成报告 | 420秒 | 180秒 | 57% |

详细优化说明请参考：[性能优化文档](./performance_optimization.md)

---

## 部署指南

### Docker Compose 部署

#### 1. 准备环境

```bash
# 确保已安装 Docker 和 Docker Compose
docker --version
docker-compose --version
```

#### 2. 配置环境变量

```bash
# 复制示例文件
cp backend/.env.example backend/.env

# 编辑配置文件
nano backend/.env
```

#### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试健康检查
curl http://localhost:8000/health/
```

### 生产环境部署

#### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 使用 Gunicorn（生产环境）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 开发指南

### 项目结构

```
backend/
├── app/
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   │   ├── user.py
│   │   ├── family.py
│   │   └── output.py
│   ├── routers/             # 路由模块
│   │   ├── user.py
│   │   ├── ai_chat.py
│   │   ├── search.py
│   │   ├── generate.py
│   │   ├── export.py
│   │   ├── session.py
│   │   └── health.py
│   ├── services/            # 业务逻辑
│   │   ├── ai_service.py
│   │   ├── search_service.py
│   │   ├── graph_service.py
│   │   ├── output_service.py
│   │   └── gateway_service.py
│   ├── utils/               # 工具函数
│   │   ├── logger.py
│   │   └── api_key_manager.py
│   └── dependencies/       # 依赖注入
│       └── db.py
├── tests/                   # 测试
├── requirements.txt         # 依赖列表
└── Dockerfile              # Docker 配置
```

### 开发规范

#### 代码风格

- 使用 **Black** 进行代码格式化
- 遵循 **PEP 8** 编码规范
- 使用 **类型提示**（Type Hints）

#### 提交规范

使用 **Conventional Commits** 格式：

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建/工具链相关
```

#### 测试

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_routers.py

# 运行快速测试脚本
python test_quick.py
```

### 添加新功能

1. **创建数据模型**（如需要）：`app/models/`
2. **实现业务逻辑**：`app/services/`
3. **创建路由**：`app/routers/`
4. **注册路由**：`app/main.py`
5. **编写测试**：`tests/`
6. **更新文档**：`docs/`

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

**问题**：后端服务无法启动

**排查步骤**：
1. 检查端口是否被占用：`netstat -ano | findstr :8000`
2. 检查 MongoDB 和 Redis 是否运行
3. 检查环境变量配置是否正确
4. 查看日志：`docker-compose logs backend`

#### 2. API 调用超时

**问题**：搜索或报告生成超时

**解决方案**：
1. 检查超时设置是否合理（已优化）
2. 检查 DeepSeek API 密钥是否有效
3. 查看后端日志，确认具体超时位置
4. 参考：[超时问题诊断文档](./troubleshooting_timeout.md)

#### 3. 数据库连接失败

**问题**：无法连接到 MongoDB 或 Redis

**排查步骤**：
1. 检查服务是否运行：`docker-compose ps`
2. 检查连接字符串是否正确
3. 检查网络连接
4. 查看容器日志：`docker-compose logs mongo`

#### 4. API 密钥无效

**问题**：DeepSeek API 调用失败

**排查步骤**：
1. 检查 `.env` 文件中的密钥是否正确
2. 验证密钥是否有效：访问 `/health/api-status`
3. 检查密钥是否有足够的配额

### 日志查看

```bash
# Docker 日志
docker-compose logs -f backend

# 实时日志
docker-compose logs -f --tail=100 backend

# 特定服务日志
docker-compose logs mongo
docker-compose logs redis
```

### 调试模式

```bash
# 后端调试模式
uvicorn app.main:app --reload --log-level debug

# 查看详细日志
export LOG_LEVEL=DEBUG
```

详细故障排查请参考：[超时问题诊断文档](./troubleshooting_timeout.md)

---

## 常见问题

### Q1: 如何获取 DeepSeek API Key？

A: 访问 [DeepSeek 官网](https://www.deepseek.com/)，注册账号后在 API 管理页面创建 Key。

### Q2: 搜索功能很慢怎么办？

A: 已进行性能优化，预计耗时 60-90 秒。如果仍然很慢，请检查：
- 网络连接
- API 密钥是否有效
- 查看后端日志确认具体问题

### Q3: 如何增加搜索的家族数量？

A: 修改 `backend/app/services/search_service.py` 中的 `families_to_search[:3]`，将 `3` 改为你想要的数字。

### Q4: 报告生成失败怎么办？

A: 检查：
1. 会话是否存在
2. 是否已执行搜索
3. DeepSeek API 是否正常
4. 查看后端日志

### Q5: 如何导出报告？

A: 使用导出接口：
- PDF：`GET /export/pdf/{report_id}`
- JSON：`GET /export/json/{report_id}`
- 图片：`GET /export/image/{family_tree_id}`

### Q6: 如何保存会话档案？

A: 使用会话管理接口：
```bash
POST /session/{session_id}/archive
{
  "title": "档案名称",
  "notes": "备注"
}
```

### Q7: 支持哪些数据库？

A: 目前支持：
- MongoDB（主数据库）
- Redis（缓存）

### Q8: 如何自定义报告格式？

A: 修改 `backend/app/services/output_service.py` 中的报告生成提示词。

---

## 相关文档

- [API 文档](./api.md)
- [会话管理 API](./session_api.md)
- [性能优化](./performance_optimization.md)
- [超时问题诊断](./troubleshooting_timeout.md)
- [功能特性](../FEATURES.md)

---

## 更新日志

### v1.0.0 (2024-01-01)

- ✅ 实现用户管理和会话创建
- ✅ 实现 AI 问答模块
- ✅ 实现搜索模块
- ✅ 实现图谱构建
- ✅ 实现报告生成
- ✅ 实现会话管理
- ✅ 性能优化（并行搜索、减少耗时）
- ✅ 添加超时控制

---

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'feat: Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

---

**最后更新**：2024-01-01
