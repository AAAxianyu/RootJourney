# DeepSeek API 配置指南

## 📋 概述

项目现在支持 DeepSeek API，可以作为 OpenAI 的替代方案。DeepSeek API 与 OpenAI API 兼容，使用相同的接口。

## 🔑 配置方法

### 方法 1：环境变量配置（推荐）

在 `backend/.env` 文件中添加：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 方法 2：运行时手动输入（临时）

启动服务后，通过 API 接口手动设置：

#### 设置 DeepSeek API Key

```bash
curl -X POST http://127.0.0.1:8000/config/api-key \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-your-deepseek-api-key-here",
    "provider": "deepseek"
  }'
```

**使用 Swagger UI：**
1. 访问 http://127.0.0.1:8000/docs
2. 找到 `config` 标签
3. 点击 `POST /config/api-key`
4. 填写：
   - `api_key`: 你的 DeepSeek API Key
   - `provider`: `deepseek`
5. 点击 "Execute"

#### 查看配置状态

```bash
curl http://127.0.0.1:8000/config/api-key/status
```

**响应示例：**
```json
{
  "success": true,
  "status": {
    "openai": false,
    "deepseek": true,
    "google_search": false,
    "xunfei": false
  },
  "message": "配置状态查询成功"
}
```

#### 清除运行时密钥

```bash
# 清除 DeepSeek
curl -X DELETE "http://127.0.0.1:8000/config/api-key?provider=deepseek"

# 清除所有运行时密钥
curl -X DELETE http://127.0.0.1:8000/config/api-key
```

## 🚀 使用方法

### 自动选择（推荐）

系统会自动选择可用的 LLM：
- 如果配置了 DeepSeek，优先使用 DeepSeek
- 如果没有 DeepSeek，使用 OpenAI
- 如果都没有，返回错误

```bash
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "auto"
  }'
```

### 指定使用 DeepSeek

```bash
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "deepseek"
  }'
```

### 指定使用 OpenAI

```bash
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "openai"
  }'
```

## 📝 API 接口说明

### 1. 设置 API Key

**POST** `/config/api-key`

**请求体：**
```json
{
  "api_key": "sk-your-api-key",
  "provider": "deepseek"  // 或 "openai"
}
```

**响应：**
```json
{
  "success": true,
  "message": "DeepSeek API Key 已设置",
  "provider": "deepseek"
}
```

### 2. 查询配置状态

**GET** `/config/api-key/status`

**响应：**
```json
{
  "success": true,
  "status": {
    "openai": false,
    "deepseek": true,
    "google_search": false,
    "xunfei": false
  },
  "message": "配置状态查询成功"
}
```

### 3. LLM 聊天（支持 provider 参数）

**POST** `/api/llm/chat`

**请求体：**
```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "provider": "deepseek",  // "openai", "deepseek", "auto"
  "model": null,  // 可选，如果为 null 则自动选择
  "temperature": 0.7
}
```

### 4. LLM 抽取（支持 provider 参数）

**POST** `/api/llm/extract`

**请求体：**
```json
{
  "text": "张三，1990年出生于北京",
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "birth_year": {"type": "integer"}
    }
  },
  "provider": "deepseek"  // "openai", "deepseek", "auto"
}
```

## 🔄 优先级说明

1. **运行时设置的密钥** > **环境变量中的密钥**
2. **DeepSeek** > **OpenAI**（如果都配置了）
3. 如果指定了 `provider`，使用指定的 provider
4. 如果 `provider="auto"`，按优先级自动选择

## 💡 使用场景

### 场景 1：只使用 DeepSeek

```env
# .env 文件
DEEPSEEK_API_KEY=sk-xxx
```

所有 LLM 调用都会使用 DeepSeek。

### 场景 2：DeepSeek 作为主要，OpenAI 作为备用

```env
# .env 文件
DEEPSEEK_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
```

默认使用 DeepSeek，如果 DeepSeek 失败可以手动切换到 OpenAI。

### 场景 3：临时测试 DeepSeek

不修改 `.env` 文件，启动服务后通过 API 设置：

```bash
# 设置 DeepSeek Key
curl -X POST http://127.0.0.1:8000/config/api-key \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-xxx", "provider": "deepseek"}'

# 测试
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}]}'
```

## ⚠️ 注意事项

1. **运行时设置的密钥只在当前服务运行期间有效**，重启服务后会丢失
2. **环境变量配置是持久的**，推荐用于生产环境
3. **DeepSeek API Key 格式**：通常以 `sk-` 开头
4. **获取 DeepSeek API Key**：访问 https://platform.deepseek.com/

## 🧪 测试

### 测试 DeepSeek 连接

```bash
# 1. 设置 DeepSeek Key
curl -X POST http://127.0.0.1:8000/config/api-key \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-your-key", "provider": "deepseek"}'

# 2. 测试聊天
curl -X POST http://127.0.0.1:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "用一句话介绍你自己"}],
    "provider": "deepseek"
  }'
```

### 查看当前使用的模型

调用接口后，响应中会包含 `provider` 字段，显示实际使用的服务：

```json
{
  "success": true,
  "response": "...",
  "model": "deepseek-chat",
  "provider": "deepseek"
}
```

## 📚 相关文档

- [API Gateway 文档](api_gateway.md)
- [测试指南](testing_guide.md)
- [后端测试指南](../../BACKEND_TEST_GUIDE.md)

