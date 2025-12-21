# 快速启动指南

## 前置条件

1. **安装Docker和Docker Compose**
   ```bash
   # 检查Docker版本
   docker --version
   docker-compose --version
   ```

2. **配置环境变量**
   - 复制 `example.env` 到 `backend/.env`
   - 填写必要的API Key：
     - `DEEPSEEK_API_KEY` - DeepSeek API密钥（必需）
     - `SEEDREAM_API_KEY` - 即梦4.0 API密钥（生图功能需要）
     - `MONGODB_URL` - MongoDB连接字符串（可选，默认使用Docker中的MongoDB）
     - `REDIS_URL` - Redis连接字符串（可选，默认使用Docker中的Redis）

---

## 启动服务

### 方式1：Docker Compose（推荐）

```bash
# 1. 进入项目目录
cd ai-genealogy-tracer

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 方式2：本地开发

```bash
# 1. 启动MongoDB和Redis（如果未运行）
docker-compose up -d mongo redis

# 2. 启动后端
cd backend
python -m uvicorn app.main:app --reload

# 3. 前端直接打开HTML文件
# 或使用简单的HTTP服务器
cd frontend/public
python -m http.server 3000
```

---

## 访问应用

### 前端
- **地址**：http://localhost:3000
- **说明**：移动端风格的家族历史探索应用

### 后端API
- **地址**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health/

---

## 功能测试

### 1. 基本流程测试

1. **打开前端**：http://localhost:3000
2. **填写表单**：
   - 姓名：张三
   - 出生日期：1990-01-01
   - 籍贯：山东
   - 出生地：北京
3. **提交表单**：点击"提交信息"按钮
4. **AI问答**：
   - 在文本框中输入答案（如"我的祖籍是山东"）
   - 或选择故事主题
   - 系统会自动获取下一个问题
5. **完成对话**：继续回答直到对话完成
6. **查看结果**：点击"下一步"按钮，系统会自动搜索和生成报告

### 2. 完整功能测试

使用测试脚本：

```bash
cd backend
python test_all_features.py
```

---

## 常见问题

### Q1: 前端无法访问后端API

**解决方案**：
1. 检查nginx配置是否正确
2. 检查后端服务是否运行：`docker logs rootjourney-backend`
3. 检查CORS配置：`backend/app/main.py`

### Q2: 创建会话失败

**解决方案**：
1. 检查MongoDB是否运行：`docker logs rootjourney-mongo`
2. 检查环境变量配置：`backend/.env`
3. 查看后端日志：`docker logs rootjourney-backend`

### Q3: AI问答无响应

**解决方案**：
1. 检查DeepSeek API Key是否配置
2. 检查网络连接
3. 查看后端日志中的错误信息

### Q4: 生图功能报错

**解决方案**：
1. 检查即梦4.0 API Key是否配置
2. 确保已先生成报告
3. 查看后端日志

---

## 服务管理

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 重建服务
```bash
# 重建并启动
docker-compose up -d --build

# 仅重建前端
docker-compose up -d --build frontend
```

---

## 开发模式

### 后端热重载
后端已配置热重载，修改代码后自动重启：
```bash
# Docker方式（已配置）
docker-compose up -d backend

# 本地方式
cd backend
python -m uvicorn app.main:app --reload
```

### 前端开发
前端是静态HTML文件，修改后需要：
1. 如果使用Docker，需要重建容器：
   ```bash
   docker-compose up -d --build frontend
   ```
2. 如果本地开发，直接刷新浏览器即可

---

## 验证服务

### 1. 健康检查
```bash
curl http://localhost:8000/health/
```

### 2. API状态
```bash
curl http://localhost:8000/health/api-status
```

### 3. 前端访问
```bash
curl http://localhost:3000
```

---

## 下一步

- 查看 [完整功能测试指南](docs/test_all_features_guide.md)
- 查看 [前后端集成说明](docs/frontend_backend_integration.md)
- 查看 [API文档](http://localhost:8000/docs)

---

**最后更新**：2024-01-01
