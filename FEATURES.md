# 项目功能实现总结

## 📋 项目概述

**RootJourney** 是一个基于 AI 的家族历史探索平台，帮助用户通过 AI 问答、联网搜索等方式发现和了解家族历史，并生成个性化的家族报告、时间轴和传记。

---

## ✅ 已实现的核心功能

### 1. 🎯 API Gateway（统一第三方 API 接口）

**目的**：统一封装所有第三方 API 调用，项目内其他模块只需调用统一接口，无需各自配置第三方 SDK。

**已实现的接口**：

#### 1.1 语音转写
- **接口**：`POST /api/voice/transcribe`
- **功能**：讯飞语音转写，上传录音文件返回转写文本
- **支持格式**：wav, mp3, m4a 等
- **支持语言**：中文、英文等

#### 1.2 LLM 问答
- **接口**：`POST /api/llm/chat`
- **功能**：GPT-4 问答接口
- **特性**：支持多轮对话、可调节温度参数

#### 1.3 LLM 抽取
- **接口**：`POST /api/llm/extract`
- **功能**：GPT-4 抽取 JSON 结构化信息
- **用途**：从文本中提取结构化数据（如姓名、日期、地点等）

#### 1.4 搜索
- **接口**：`GET /api/search`
- **功能**：Google Custom Search 搜索接口
- **特性**：支持自定义结果数量

#### 1.5 图片生成
- **接口**：`POST /api/media/image`
- **功能**：DALL·E 生成图片
- **特性**：支持自定义尺寸（256x256, 512x512, 1024x1024）

#### 1.6 视频生成（异步任务）
- **接口**：`POST /api/media/video` - 创建视频生成任务
- **接口**：`GET /api/media/video/{task_id}` - 查询任务状态
- **功能**：Sora 视频生成（异步任务模式）
- **特性**：支持任务状态查询和轮询

---

### 2. 👤 用户管理模块

**路由**：`/user`

#### 2.1 用户输入
- **接口**：`POST /user/input`
- **功能**：接收用户基本信息（姓名、出生日期、籍贯、当前地区）
- **返回**：创建会话，返回 `session_id`
- **数据存储**：MongoDB + Redis

---

### 3. 💬 AI 问答模块

**路由**：`/ai`

#### 3.1 AI 问答循环
- **接口**：`POST /ai/chat`
- **功能**：处理用户回答，AI 生成下一个问题或结束收集
- **特性**：
  - 逐步收集家族信息
  - 智能问题生成（基于已收集数据）
  - 信息提取（从用户回答中提取结构化信息）
  - 自动判断何时结束问答

#### 3.2 获取问题
- **接口**：`GET /ai/question/{session_id}`
- **功能**：获取当前问题或初始问题

**核心逻辑**：
- 使用 GPT-4 生成问题
- 从用户回答中提取家族信息（姓名、关系、籍贯、出生年份等）
- 更新家族图谱
- 支持多轮问答（最多 20 轮）

---

### 4. 🔍 搜索模块

**路由**：`/search`

#### 4.1 家族历史搜索
- **接口**：`GET /search/family?session_id=xxx`
- **功能**：基于会话中的家族图谱进行联网搜索
- **特性**：
  - 自动为每个家族成员构建搜索查询
  - 支持 SerpAPI 和 Google Custom Search
  - 提取历史事件和名人信息
  - 更新家族图谱

**搜索逻辑**：
- 对每个家族成员：`姓名 + 籍贯 + "家族历史"`
- 解析搜索结果，提取历史事件
- 总结搜索结果（历史事件、名人信息）

---

### 5. 📊 图谱构建模块

**服务**：`GraphService`

#### 5.1 家族图谱构建
- **功能**：构建家族树结构
- **特性**：
  - 使用 NetworkX 构建知识图谱
  - 支持关系推断（推测缺失的世代信息）
  - 可视化数据生成

#### 5.2 时间轴生成
- **功能**：生成多轴时间轴数据
- **特性**：
  - 从历史记录中提取年份和事件
  - 支持按家族过滤
  - 多轴格式：`[{year: int, families: {family_A: [events], ...}}]`

---

### 6. 📝 生成输出模块

**路由**：`/generate`

#### 6.1 家族报告生成
- **接口**：`POST /generate/report?session_id=xxx`
- **功能**：生成包含文字和图片的完整家族报告
- **特性**：
  - 使用 GPT-4 生成文字描述
  - 使用 DALL·E 生成配图（3张）
  - 包含家族历史、名人和文化传承

#### 6.2 时间轴生成
- **接口**：`POST /generate/timeline?session_id=xxx&family_filter=xxx`
- **功能**：生成多轴时间轴数据
- **特性**：
  - 支持多家族时间线
  - 可锁定特定家族查看
  - 事件按年份排序

#### 6.3 个人传记生成
- **接口**：`POST /generate/biography?session_id=xxx`
- **功能**：生成融入家族叙事的个人故事
- **特性**：
  - 整合用户输入和家族图谱
  - 文字优美、有感染力
  - 长度约 500-800 字

---

### 7. 📤 导出模块

**路由**：`/export`

#### 7.1 PDF 导出
- **接口**：`GET /export/pdf?session_id=xxx`
- **功能**：导出家族报告为 PDF
- **特性**：
  - 包含文字和图片
  - 使用 ReportLab 生成

#### 7.2 视频导出
- **接口**：`GET /export/video?session_id=xxx`
- **功能**：生成家族历史视频
- **特性**：异步任务模式

---

### 8. 🏥 健康检查和测试模块

**路由**：`/health`

#### 8.1 配置状态检查
- **接口**：`GET /health/api-status`
- **功能**：检查所有第三方 API 的配置状态（不实际调用）

#### 8.2 API 连接测试
- **接口**：`POST /health/test/all` - 测试所有 API
- **接口**：`POST /health/test/openai` - 测试 OpenAI
- **接口**：`POST /health/test/search` - 测试 Google Search
- **接口**：`POST /health/test/image` - 测试 DALL·E
- **接口**：`GET /health/test/database` - 测试数据库连接

**功能**：实际调用 API 验证连接状态

---

## 🗄️ 数据存储

### MongoDB
- **用途**：持久化存储
  - 用户会话数据
  - 家族图谱数据
  - 视频生成任务
- **集合**：
  - `sessions` - 用户会话
  - `video_tasks` - 视频任务

### Redis
- **用途**：缓存和会话管理
  - 临时会话状态
  - 对话历史缓存
  - 视频任务状态缓存
- **过期时间**：可配置（默认 3600 秒）

---

## 🔧 技术架构

### 后端技术栈
- **框架**：FastAPI（异步 Web 框架）
- **数据库**：MongoDB（Motor 异步驱动）+ Redis
- **AI 服务**：
  - OpenAI GPT-4（问答和文本生成）
  - OpenAI DALL·E（图片生成）
  - OpenAI Sora（视频生成，预留接口）
  - 讯飞语音转写
- **搜索服务**：Google Custom Search API / SerpAPI
- **其他**：
  - Pydantic（数据验证）
  - NetworkX（图谱构建）
  - ReportLab（PDF 生成）

### 项目结构
```
backend/
├── app/
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型
│   ├── routers/             # API 路由
│   ├── services/            # 业务逻辑服务
│   ├── dependencies/        # 依赖注入（数据库连接）
│   └── utils/               # 工具函数
└── scripts/
    └── test_apis.py         # API 测试脚本
```

---

## 📊 系统流程

### 完整用户流程

1. **用户输入** → `POST /user/input`
   - 输入基本信息（姓名、出生日期、籍贯等）
   - 创建会话，获得 `session_id`

2. **AI 问答循环** → `POST /ai/chat`（多次调用）
   - AI 逐步提问收集家族信息
   - 用户回答，系统提取信息
   - 更新家族图谱
   - 直到收集足够信息

3. **搜索历史** → `GET /search/family`
   - 基于收集的信息联网搜索
   - 丰富家族历史数据

4. **生成输出**：
   - `POST /generate/report` - 生成家族报告
   - `POST /generate/timeline` - 生成时间轴
   - `POST /generate/biography` - 生成个人传记

5. **导出**：
   - `GET /export/pdf` - 导出 PDF
   - `GET /export/video` - 生成视频

---

## 🎯 核心特性

### ✅ 已实现
- [x] 统一的 API Gateway（封装所有第三方 API）
- [x] AI 问答循环（GPT-4）
- [x] 信息提取（从文本中提取结构化数据）
- [x] 联网搜索（Google Search / SerpAPI）
- [x] 家族图谱构建（NetworkX）
- [x] 时间轴生成（多轴设计）
- [x] 报告生成（文字 + 图片）
- [x] 传记生成
- [x] PDF 导出
- [x] 语音转写（讯飞）
- [x] 图片生成（DALL·E）
- [x] 视频生成任务（Sora，异步）
- [x] 健康检查和测试工具
- [x] MongoDB + Redis 数据存储
- [x] 会话管理
- [x] 错误处理和日志

### 🚧 待完善
- [ ] 前端 UI/UX 完善
- [ ] 用户认证系统（JWT）
- [ ] 单元测试和集成测试
- [ ] 文生视频功能完善（Sora API 实际集成）
- [ ] 数据加密和隐私保护增强
- [ ] API 限流和防护

---

## 📚 文档

- [API Gateway 文档](docs/api_gateway.md) - API Gateway 详细使用说明
- [测试指南](docs/testing_guide.md) - API 连接测试方法
- [详细测试步骤](TEST_STEP_BY_STEP.md) - 分步测试指南
- [快速开始](QUICK_START.md) - 5分钟快速测试

---

## 🚀 快速开始

### 启动服务
```bash
cd backend
uvicorn app.main:app --reload
```

### 测试 API
```bash
# 检查配置
curl http://localhost:8000/health/api-status

# 测试所有连接
curl -X POST http://localhost:8000/health/test/all
```

### 查看 API 文档
访问：http://localhost:8000/docs

---

## 📝 总结

当前项目已经实现了：
1. **完整的后端 API 系统**：包括用户管理、AI 问答、搜索、生成、导出等核心功能
2. **统一的 API Gateway**：封装所有第三方 API，方便项目内调用
3. **数据持久化**：MongoDB + Redis 存储
4. **健康检查工具**：方便测试和调试
5. **完整的文档**：API 文档、测试指南等

项目已经具备了核心功能，可以开始集成前端或进行进一步开发。

