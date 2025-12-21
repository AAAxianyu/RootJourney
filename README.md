# RootJourney

家族历史探索平台 - DeepHackathon 项目

## 项目简介

RootJourney 是一个基于 AI 的家族历史探索平台，帮助用户发现和了解自己的家族历史。通过 AI 问答、联网搜索、家族图谱构建等功能，生成个性化的家族报告、时间轴和传记。

## 项目结构

```
.
├── backend/                  # 后端服务
│   ├── app/                  # FastAPI应用核心
│   │   ├── __init__.py
│   │   ├── main.py           # 入口文件，启动服务器
│   │   ├── config.py         # 配置（环境变量、API密钥）
│   │   ├── models/           # 数据模型 (Pydantic schemas)
│   │   │   ├── user.py       # 用户输入模型
│   │   │   ├── family.py     # 家族数据模型
│   │   │   └── output.py     # 输出模型 (报告、时间轴、传记)
│   │   ├── routers/          # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── user.py       # 用户相关路由
│   │   │   ├── ai_chat.py    # AI问答路由
│   │   │   ├── search.py     # 搜索路由
│   │   │   ├── generate.py   # 生成输出路由
│   │   │   └── export.py     # 导出路由
│   │   ├── services/         # 业务逻辑服务
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py # AI问答和NLP逻辑
│   │   │   ├── search_service.py # 联网搜索逻辑
│   │   │   ├── graph_service.py  # 家族图谱构建
│   │   │   ├── gen_ai_service.py # 文生图/文生视频封装
│   │   │   └── output_service.py # 输出生成
│   │   ├── utils/            # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # 认证工具
│   │   │   └── logger.py     # 日志工具
│   │   └── dependencies/     # 依赖注入 (e.g., DB session)
│   │       └── db.py
│   ├── tests/                # 单元测试
│   │   └── test_routers.py
│   ├── requirements.txt      # 依赖列表
│   └── Dockerfile            # Docker镜像
├── frontend/                 # 前端应用
│   ├── public/               # 静态资源
│   ├── src/                  # 源代码
│   │   ├── components/       # React组件
│   │   │   ├── InputForm.js  # 用户输入表单
│   │   │   ├── ChatInterface.js # AI聊天界面
│   │   │   ├── FamilyReport.js  # 家族报告渲染
│   │   │   ├── Timeline.js   # 时间轴组件 (使用Echarts)
│   │   │   └── Biography.js  # 个人传记渲染
│   │   ├── pages/            # 页面
│   │   │   └── Home.js       # 主页
│   │   ├── services/         # API调用服务
│   │   │   └── api.js        # Axios封装
│   │   ├── utils/            # 工具
│   │   │   └── constants.js  # 常量
│   │   ├── App.js            # 入口
│   │   └── index.js          # React根
│   ├── package.json          # 依赖
│   └── Dockerfile            # Docker镜像
├── docs/                     # 文档
│   └── api.md                # API文档 (Swagger生成)
├── scripts/                  # 脚本
│   └── deploy.sh             # 部署脚本
├── docker-compose.yml        # 多容器编排
└── README.md                 # 项目说明
```

## 技术栈

### 后端
- **FastAPI** - 现代、快速的 Web 框架
- **Pydantic** - 数据验证和设置管理
- **Motor** - MongoDB 异步驱动
- **Redis** - 缓存和会话存储
- **OpenAI** - GPT-4 和 DALL-E 集成
- **SerpAPI/Google Search** - 联网搜索
- **ReportLab** - PDF 生成
- **NetworkX** - 图谱构建
- **Uvicorn** - ASGI 服务器

### 前端
- **React** - UI 框架
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化
- **React Scripts** - 构建工具

## 🚀 快速开始

### 完整后端测试

想要完整测试所有后端功能？查看 [后端测试指南](BACKEND_TEST_GUIDE.md)

快速测试脚本：
```bash
cd backend
python scripts/test_all_features.py
```

## 快速开始

### 前置要求

- Python 3.10+
- MongoDB (本地或 Docker)
- Redis (本地或 Docker)
- API Keys: OpenAI, Google Search (可选: 讯飞)

### 🚀 5分钟快速测试

想要快速验证所有 API 连接？查看 [快速开始指南](QUICK_START.md)

需要详细步骤？查看 [详细测试步骤](TEST_STEP_BY_STEP.md)

### 本地开发

#### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端服务将在 `http://localhost:8000` 启动

#### 前端

```bash
cd frontend
npm install
npm start
```

前端应用将在 `http://localhost:3000` 启动

### Docker 部署

```bash
# 使用部署脚本
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 或手动部署
docker-compose up -d
```

## 环境变量配置

创建 `.env` 文件（后端根目录），参考 `backend/.env.example`：

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=genealogy_tracer

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# OpenAI API Key (for GPT-4 and DALL-E)
OPENAI_API_KEY=your_openai_api_key_here

# 讯飞语音转写配置
XUNFEI_APP_ID=your_xunfei_app_id
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret

# Search API Configuration (选择其一)
SERPAPI_KEY=your_serpapi_key_here
# 或
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_google_engine_id_here

# Authentication
SECRET_KEY=your_secret_key_here
```

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- API Gateway 文档: `docs/api_gateway.md`
- 测试指南: `docs/testing_guide.md`

### 测试 API 连接

在开始使用前，建议先测试所有 API 的连接状态：

```bash
# 方法1: 使用健康检查端点
curl http://localhost:8000/health/api-status
curl -X POST http://localhost:8000/health/test/all

# 方法2: 使用测试脚本
cd backend
python scripts/test_apis.py
```

详细说明请参考 [测试指南](docs/testing_guide.md)

### API Gateway

项目提供了统一的 API Gateway，封装了所有第三方 API 调用：

- `POST /api/voice/transcribe` - 讯飞语音转写
- `POST /api/llm/chat` - LLM 问答（支持 OpenAI 和 DeepSeek）
- `POST /api/llm/extract` - LLM 抽取 JSON（支持 OpenAI 和 DeepSeek）
- `GET /api/search` - Google Custom Search
- `POST /api/media/image` - DALL·E 生成图片
- `POST /api/media/video` - Sora 生成视频（任务）
- `GET /api/media/video/{task_id}` - 查询视频任务状态

**配置管理：**
- `POST /config/api-key` - 手动设置 API Key（支持 DeepSeek 和 OpenAI）
- `GET /config/api-key/status` - 查询配置状态

详细使用说明请参考：
- [API Gateway 文档](docs/api_gateway.md)
- [DeepSeek 配置指南](docs/deepseek_setup.md)
- [DeepSeek 快速开始](DEEPSEEK_QUICK_START.md)

## 功能特性

- ✅ 用户输入和数据处理
- ✅ AI 问答对话
- ✅ 联网搜索历史信息
- ✅ 家族图谱构建和可视化
- ✅ 家族报告生成
- ✅ 个人传记生成
- ✅ 时间轴生成和可视化
- ✅ 多格式导出 (PDF, JSON, 图片)

## 开发计划

- [x] 实现 AI 服务集成（GPT-4 问答循环）
- [x] 实现搜索服务集成（SerpAPI/Google Search）
- [x] 实现数据库持久化（MongoDB + Redis）
- [x] 实现文生图功能（DALL-E）
- [ ] 完善前端 UI/UX
- [ ] 添加用户认证系统
- [ ] 实现文生视频功能（Sora API）
- [ ] 添加单元测试和集成测试

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
