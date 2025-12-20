# 前后端接口对齐说明

## 修改内容

### 1. 前端HTML文件 (`frontend/public/index.html`)

#### 添加的功能：

1. **API配置**
   - 自动检测运行环境，选择正确的API地址
   - 开发环境：`http://localhost:8000`
   - 生产环境：使用相对路径（通过nginx代理）

2. **API调用函数**
   - `createSession()` - 创建会话
   - `getInitialQuestion()` - 获取初始问题
   - `submitAnswer()` - 提交回答
   - `searchFamily()` - 搜索家族历史
   - `generateReport()` - 生成报告
   - `generateImages()` - 生成图片

3. **表单提交功能**
   - 已连接后端API
   - 提交表单后自动创建会话
   - 自动获取初始问题并显示

4. **文本输入功能**
   - 在语音页面添加了文本输入框
   - 支持直接输入答案
   - 支持回车键提交

5. **语音对话功能**
   - 保留原有语音录制功能
   - 添加文本输入作为补充
   - 提交答案后自动获取下一个问题

6. **下一步功能**
   - 已连接后端API
   - 自动触发搜索和生成报告

### 2. Nginx配置 (`frontend/nginx.conf`)

#### 修改内容：

- 添加了后端API路由代理
- 支持所有后端接口：`/user`, `/ai`, `/search`, `/generate`, `/session`, `/health`, `/export`, `/config`
- 保留了 `/api` 路径的兼容性

### 3. 后端CORS配置 (`backend/app/main.py`)

#### 修改内容：

- 扩展了允许的源地址
- 包括：`localhost:3000`, `localhost:80`, `localhost`, `127.0.0.1` 等

### 4. 前端Dockerfile (`frontend/Dockerfile`)

#### 修改内容：

- 简化为直接使用HTML文件
- 不再需要构建React应用
- 直接复制HTML文件到nginx目录

---

## API接口映射

### 前端调用 → 后端接口

| 前端函数 | 后端接口 | 方法 | 说明 |
|---------|---------|------|------|
| `createSession()` | `/user/input` | POST | 创建会话 |
| `getInitialQuestion()` | `/ai/question/{session_id}` | GET | 获取初始问题 |
| `submitAnswer()` | `/ai/chat` | POST | 提交回答 |
| `searchFamily()` | `/search/family?session_id=xxx` | GET | 搜索家族历史 |
| `generateReport()` | `/generate/report` | POST | 生成报告 |
| `generateImages()` | `/generate/images` | POST | 生成图片 |

---

## 数据流程

### 1. 用户填写表单

```
用户输入 → submitForm() → createSession() → 后端 /user/input
→ 返回 session_id → 保存到 window.appState.sessionId
→ getInitialQuestion() → 显示初始问题
```

### 2. 用户提交答案

```
用户输入答案 → submitTextAnswer() → submitAnswer() → 后端 /ai/chat
→ 返回下一个问题 → 显示在聊天界面
→ 如果对话完成，自动触发搜索和生成报告
```

### 3. 进入下一步

```
点击下一步 → goToNextStep() → searchFamily() → 后端 /search/family
→ generateReport() → 后端 /generate/report
→ 显示完成消息
```

---

## 运行方式

### 方式1：Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 访问前端
http://localhost:3000
```

### 方式2：本地开发

```bash
# 启动后端
cd backend
python -m uvicorn app.main:app --reload

# 前端直接打开HTML文件
# 或使用简单的HTTP服务器
cd frontend/public
python -m http.server 3000
```

---

## 测试步骤

1. **打开前端页面**
   - 访问 `http://localhost:3000`

2. **填写表单**
   - 输入姓名、出生日期、籍贯、出生地
   - 点击"提交信息"

3. **AI问答**
   - 在语音页面输入答案或选择主题
   - 系统会自动获取下一个问题
   - 继续对话直到完成

4. **查看结果**
   - 点击"下一步"按钮
   - 系统会自动搜索和生成报告

---

## 注意事项

1. **API地址**
   - 开发环境：前端直接访问 `http://localhost:8000`
   - 生产环境：通过nginx代理访问后端

2. **CORS配置**
   - 后端已配置允许前端访问
   - 如果遇到CORS错误，检查 `backend/app/main.py` 中的CORS配置

3. **会话管理**
   - `session_id` 保存在 `window.appState.sessionId`
   - 刷新页面会丢失，需要重新创建会话

4. **错误处理**
   - 所有API调用都有错误处理
   - 错误会显示在控制台和用户界面

---

## 功能验证清单

- [x] 表单提交 → 创建会话
- [x] 获取初始问题
- [x] 提交答案 → 获取下一个问题
- [x] 文本输入功能
- [x] 主题选择功能
- [x] 搜索家族历史
- [x] 生成报告
- [x] 生成图片（需要先有报告）
- [x] 下一步功能

---

**最后更新**：2024-01-01
