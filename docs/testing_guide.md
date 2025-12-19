# API 连接测试指南

本文档说明如何验证所有第三方 API 的连接状态。

## 方法一：使用健康检查端点（推荐）

启动服务后，访问以下端点检查 API 状态：

### 1. 检查配置状态

**GET** `/health/api-status`

检查所有 API 的配置是否完整（不进行实际调用）。

```bash
curl http://localhost:8000/health/api-status
```

响应示例：
```json
{
  "overall": "ready",
  "services": {
    "openai": {"configured": true, "status": "configured"},
    "xunfei": {"configured": true, "status": "configured"},
    "google_search": {"configured": true, "status": "configured"},
    "mongodb": {"configured": true, "status": "configured"},
    "redis": {"configured": true, "status": "configured"}
  }
}
```

### 2. 测试所有 API 连接

**POST** `/health/test/all`

实际调用各个 API 验证连接。

```bash
curl -X POST http://localhost:8000/health/test/all
```

这会依次测试：
- OpenAI (GPT-4)
- Google Search
- DALL·E
- MongoDB
- Redis
- 讯飞配置检查

### 3. 单独测试各个服务

#### 测试 OpenAI
```bash
curl -X POST http://localhost:8000/health/test/openai
```

#### 测试 Google Search
```bash
curl -X POST http://localhost:8000/health/test/search
```

#### 测试 DALL·E
```bash
curl -X POST http://localhost:8000/health/test/image
```

#### 测试数据库
```bash
curl http://localhost:8000/health/test/database
```

#### 测试讯飞配置
```bash
curl -X POST http://localhost:8000/health/test/xunfei
```

## 方法二：使用测试脚本

运行测试脚本自动检查所有 API：

```bash
cd backend
python scripts/test_apis.py
```

脚本会：
1. 检查各个 API 的配置
2. 实际调用 API 验证连接
3. 显示详细的测试结果
4. 返回退出码（0=全部成功，1=有失败）

示例输出：
```
============================================================
API 连接测试
============================================================

[测试 OpenAI]
✅ OpenAI 连接成功
   响应: test successful...

[测试 DALL·E]
✅ DALL·E 连接成功
   图片URL: https://oaidalleapiprodscus.blob.core.windows.net/...

[测试 Google Search]
✅ Google Search 连接成功
   返回结果数: 2

[测试 讯飞 API]
✅ 讯飞 API 配置完整

[测试 MongoDB]
✅ MongoDB 连接成功
   数据库: genealogy_tracer

[测试 Redis]
✅ Redis 连接成功
   URL: redis://localhost:6379

============================================================
测试总结
============================================================
✅ OPENAI
✅ DALLE
✅ GOOGLE_SEARCH
✅ XUNFEI
✅ MONGODB
✅ REDIS

成功: 6/6

🎉 所有服务连接正常！
```

## 方法三：使用 Swagger UI 测试

1. 启动服务
2. 访问 `http://localhost:8000/docs`
3. 找到 `health` 标签下的端点
4. 点击 "Try it out" 测试各个端点

## 方法四：直接调用 API Gateway 接口

### 测试 LLM 问答
```bash
curl -X POST http://localhost:8000/api/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "gpt-4"
  }'
```

### 测试搜索
```bash
curl "http://localhost:8000/api/search?query=test&num_results=1"
```

### 测试图片生成
```bash
curl -X POST http://localhost:8000/api/media/image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a simple red circle",
    "size": "256x256"
  }'
```

### 测试语音转写（需要音频文件）
```bash
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio_file=@test_audio.wav" \
  -F "audio_format=wav" \
  -F "language=zh_cn"
```

## 常见问题排查

### OpenAI API 连接失败

1. **检查 API Key**
   ```bash
   echo $OPENAI_API_KEY  # 或在 .env 文件中检查
   ```

2. **检查网络连接**
   ```bash
   curl https://api.openai.com/v1/models
   ```

3. **检查 API 余额**
   - 访问 https://platform.openai.com/usage

### Google Search API 连接失败

1. **检查 API Key 和 Engine ID**
   ```bash
   echo $GOOGLE_SEARCH_API_KEY
   echo $GOOGLE_SEARCH_ENGINE_ID
   ```

2. **验证 API Key 权限**
   - 确保 Custom Search API 已启用
   - 检查 API Key 的配额限制

### MongoDB 连接失败

1. **检查 MongoDB 是否运行**
   ```bash
   # Linux/Mac
   systemctl status mongod
   
   # Docker
   docker ps | grep mongo
   ```

2. **测试连接**
   ```bash
   mongosh "mongodb://localhost:27017"
   ```

### Redis 连接失败

1. **检查 Redis 是否运行**
   ```bash
   # Linux/Mac
   systemctl status redis
   
   # Docker
   docker ps | grep redis
   ```

2. **测试连接**
   ```bash
   redis-cli ping
   ```

### 讯飞 API 配置问题

1. **检查三个配置项是否都设置**
   - XUNFEI_APP_ID
   - XUNFEI_API_KEY
   - XUNFEI_API_SECRET

2. **验证配置正确性**
   - 登录讯飞开放平台检查应用信息

## 快速检查清单

在部署前，确保：

- [ ] OpenAI API Key 已配置且有效
- [ ] 讯飞 API 三个配置项都已设置
- [ ] Google Search API Key 和 Engine ID 已配置
- [ ] MongoDB 服务正在运行
- [ ] Redis 服务正在运行
- [ ] 所有环境变量已正确加载（检查 `.env` 文件）
- [ ] 网络连接正常（可以访问外部 API）

运行以下命令快速检查：
```bash
# 检查配置
curl http://localhost:8000/health/api-status

# 测试所有连接
curl -X POST http://localhost:8000/health/test/all
```

## 自动化测试

可以将测试集成到 CI/CD 流程中：

```yaml
# GitHub Actions 示例
- name: Test API Connections
  run: |
    cd backend
    python scripts/test_apis.py
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    # ... 其他环境变量
```

