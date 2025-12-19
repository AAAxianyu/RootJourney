# .env 文件字段名映射说明

## 问题说明

如果你的 `.env` 文件中使用了以下字段名，系统会自动兼容：

- `MONGO_URI` → 自动映射到 `MONGODB_URL`
- `SERPAPI_API_KEY` → 自动映射到 `SERPAPI_KEY`
- `ENV` → 会被忽略（不影响功能）
- `DEBUG` → 会被忽略（不影响功能）

## 推荐的字段名

为了保持一致性，建议使用以下字段名：

```env
# MongoDB 配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=genealogy_tracer

# Redis 配置
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# 讯飞语音转写配置
XUNFEI_APP_ID=your_app_id
XUNFEI_API_KEY=your_api_key
XUNFEI_API_SECRET=your_api_secret

# Google Search API 配置
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id

# SerpAPI 配置（可选）
SERPAPI_KEY=your_serpapi_key

# 认证配置
SECRET_KEY=your_secret_key
```

## 字段名对照表

| 旧字段名（兼容） | 新字段名（推荐） | 说明 |
|----------------|----------------|------|
| `MONGO_URI` | `MONGODB_URL` | MongoDB 连接地址 |
| `SERPAPI_API_KEY` | `SERPAPI_KEY` | SerpAPI 密钥 |
| `ENV` | - | 环境标识（会被忽略） |
| `DEBUG` | - | 调试模式（会被忽略） |

## 注意事项

1. **字段名不区分大小写**：`MONGODB_URL` 和 `mongodb_url` 都可以
2. **自动兼容**：如果使用旧字段名，系统会自动转换
3. **建议使用新字段名**：为了代码一致性和未来维护，建议使用推荐的字段名

