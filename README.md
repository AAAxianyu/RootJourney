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
- **SQLAlchemy** - ORM 框架
- **Python-JOSE** - JWT 认证
- **Uvicorn** - ASGI 服务器

### 前端
- **React** - UI 框架
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化
- **React Scripts** - 构建工具

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (可选)

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

创建 `.env` 文件（后端根目录）：

```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
SEARCH_API_KEY=your-search-key
```

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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

- [ ] 实现 AI 服务集成
- [ ] 实现搜索服务集成
- [ ] 实现数据库持久化
- [ ] 完善前端 UI/UX
- [ ] 添加用户认证系统
- [ ] 实现文生图/文生视频功能

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
