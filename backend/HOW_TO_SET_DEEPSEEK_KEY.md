# DeepSeek API Key 配置指南

## 📍 DeepSeek API Key 应该放在哪里？

有两种方式配置 DeepSeek API Key：

---

## 方法 1：放在 .env 文件中（推荐，持久化）

### 步骤 1：找到或创建 .env 文件

`.env` 文件应该放在 `backend` 目录下：

```
backend/
├── .env          ← 在这里！
├── app/
├── requirements.txt
└── ...
```

### 步骤 2：编辑 .env 文件

用文本编辑器打开 `backend/.env` 文件，添加以下内容：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
```

**完整示例：**
```env
# MongoDB 配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=genealogy_tracer

# Redis 配置
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# DeepSeek API Key（把你的密钥放在这里）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key（可选，如果不用可以不配置）
# OPENAI_API_KEY=sk-xxx

# 其他配置...
```

### 步骤 3：重启服务

修改 `.env` 文件后，需要重启服务才能生效：

1. 按 `Ctrl+C` 停止当前服务
2. 重新启动：
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 方法 2：通过 API 手动输入（临时，运行时）

如果不想修改文件，可以在服务启动后通过 API 设置：

### 步骤 1：启动服务

```bash
cd backend
uvicorn app.main:app --reload
```

### 步骤 2：设置 DeepSeek Key

**使用 Swagger UI（最简单）：**

1. 打开浏览器访问：http://127.0.0.1:8000/docs
2. 找到 `config` 标签
3. 点击 `POST /config/api-key`
4. 点击 "Try it out"
5. 在请求体中填写：
   ```json
   {
     "api_key": "sk-your-deepseek-api-key-here",
     "provider": "deepseek"
   }
   ```
6. 点击 "Execute"

**或使用 curl：**

```bash
curl -X POST http://127.0.0.1:8000/config/api-key \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"sk-your-deepseek-api-key-here\", \"provider\": \"deepseek\"}"
```

**Windows PowerShell：**
```powershell
curl -X POST http://127.0.0.1:8000/config/api-key `
  -H "Content-Type: application/json" `
  -d '{\"api_key\": \"sk-your-key\", \"provider\": \"deepseek\"}'
```

### 步骤 3：验证配置

```bash
curl http://127.0.0.1:8000/config/api-key/status
```

应该看到 `"deepseek": true`

---

## ✅ 验证配置是否生效

### 方法 1：查看配置状态

```bash
curl http://127.0.0.1:8000/config/api-key/status
```

**期望结果：**
```json
{
  "success": true,
  "status": {
    "deepseek": true,    ← 这里应该是 true
    "openai": false,
    ...
  }
}
```

### 方法 2：测试调用

```bash
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "deepseek"
  }'
```

如果返回正常的回复，说明配置成功！

---

## 📝 完整配置示例

### .env 文件示例

在 `backend/.env` 文件中：

```env
# ========== 数据库配置 ==========
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=genealogy_tracer
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# ========== AI 服务配置 ==========
# DeepSeek API Key（必须配置，把你的密钥放在这里）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key（可选，如果不用可以不配置）
# OPENAI_API_KEY=sk-xxx

# ========== 其他配置 ==========
SECRET_KEY=your-secret-key-here
```

---

## 🔍 常见问题

### Q1: .env 文件在哪里？

**A:** `.env` 文件应该在 `backend` 目录下，即：
```
D:\ZG\Hackson\ai-genealogy-tracer\ai-genealogy-tracer\backend\.env
```

### Q2: 没有 .env 文件怎么办？

**A:** 创建一个新文件：
- Windows: 在 `backend` 目录下创建名为 `.env` 的文件（注意前面有个点）
- 如果无法创建带点的文件，可以先创建 `env.txt`，然后重命名为 `.env`

### Q3: 如何获取 DeepSeek API Key？

**A:** 
1. 访问 https://platform.deepseek.com/
2. 注册/登录账号
3. 创建 API Key
4. 复制 Key（通常以 `sk-` 开头）

### Q4: 配置后还是不工作？

**A:** 检查：
1. `.env` 文件是否在 `backend` 目录下
2. Key 格式是否正确（通常以 `sk-` 开头）
3. 是否重启了服务（如果使用 .env 文件）
4. 查看服务日志是否有错误信息

### Q5: 两种方法有什么区别？

**A:**
- **.env 文件**：持久化配置，重启服务后仍然有效
- **API 设置**：临时配置，只在当前服务运行期间有效，重启后丢失

---

## 🎯 推荐做法

**推荐使用方法 1（.env 文件）**，因为：
- ✅ 配置持久化，重启后仍然有效
- ✅ 不需要每次启动都重新设置
- ✅ 更安全（不会在 API 调用中暴露）

---

## 📚 相关文档

- [DeepSeek 快速开始](../DEEPSEEK_QUICK_START.md)
- [DeepSeek 详细配置](../docs/deepseek_setup.md)

