# 会话管理 API 文档

## 概述

会话管理 API 提供了查看和保存会话档案的功能。用户可以通过这些接口管理自己的家族历史探索会话，包括查看会话详情、获取报告、保存档案等。

## 基础路径

所有会话管理相关的 API 端点都以 `/session` 为前缀。

## 端点列表

### 获取会话详情

**GET** `/session/{session_id}`

获取指定会话的完整信息，包括用户输入、收集的数据、家族图谱等。

#### 路径参数
- `session_id` (string, 必填): 会话ID

#### 响应示例

```json
{
  "session": {
    "session_id": "abc123",
    "user_input": {
      "name": "张三",
      "user_id": "user001"
    },
    "collected_data": {
      "persons": [...],
      "relationships": [...]
    },
    "family_graph": {
      "nodes": [...],
      "edges": [...]
    },
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

#### 错误响应
- `404`: 会话不存在
- `500`: 服务器内部错误

---

### 获取会话报告

**GET** `/session/{session_id}/report`

获取指定会话的生成报告（如果已生成）。同时返回档案信息，包括是否已归档、档案名称、备注等。

#### 路径参数
- `session_id` (string, 必填): 会话ID

#### 响应示例（有报告）

```json
{
  "report": {
    "title": "家族历史报告",
    "content": "...",
    "generated_at": "2024-01-01T00:00:00"
  },
  "archive_info": {
    "archived": true,
    "archive_title": "张三的家族历史档案",
    "archive_notes": "这是备注信息",
    "archived_at": "2024-01-01T00:00:00"
  }
}
```

#### 响应示例（无报告）

```json
{
  "report": null,
  "archive_info": {
    "archived": false,
    "archive_title": null,
    "archive_notes": null,
    "archived_at": null
  },
  "message": "报告尚未生成，请先调用 /generate/report"
}
```

#### 错误响应
- `404`: 会话不存在
- `500`: 服务器内部错误

---

### 保存会话档案

**POST** `/session/{session_id}/archive`

将指定会话保存为档案。用户可以为档案自定义名称和备注，便于后续查看和管理。

#### 路径参数
- `session_id` (string, 必填): 会话ID

#### 请求体

```json
{
  "title": "张三的家族历史档案",  // 必填：用户自定义的档案名称
  "notes": "这是备注信息"         // 可选：备注信息
}
```

#### 请求参数说明
- `title` (string, 必填): 档案名称。如果为空，系统会自动生成默认名称（格式：`{用户名}的家族历史档案`）
- `notes` (string, 可选): 备注信息

#### 响应示例

```json
{
  "success": true,
  "message": "会话已保存为档案",
  "session_id": "abc123",
  "archive_title": "张三的家族历史档案",
  "archived_at": "2024-01-01T00:00:00"
}
```

#### 错误响应
- `404`: 会话不存在
- `500`: 服务器内部错误

---

### 列出所有会话

**GET** `/session/list`

列出所有会话，支持按用户ID和归档状态筛选。

#### 查询参数
- `user_id` (string, 可选): 用户ID，用于筛选特定用户的会话
- `archived` (boolean, 可选): 是否已归档
  - `true`: 只返回已归档的会话
  - `false`: 只返回未归档的会话
  - 不传: 返回所有会话

#### 请求示例

```
GET /session/list?user_id=user001&archived=true
```

#### 响应示例

```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "user_name": "张三",
      "created_at": "2024-01-01T00:00:00",
      "archived": true,
      "archive_title": "张三的家族历史档案",
      "archive_notes": "这是备注信息",
      "archived_at": "2024-01-01T00:00:00",
      "has_report": true
    },
    {
      "session_id": "def456",
      "user_name": "李四",
      "created_at": "2024-01-02T00:00:00",
      "archived": false,
      "archive_title": null,
      "archive_notes": null,
      "archived_at": null,
      "has_report": false
    }
  ],
  "count": 2
}
```

#### 说明
- 返回结果按创建时间倒序排列（最新的在前）
- 最多返回 100 条记录

#### 错误响应
- `500`: 服务器内部错误

---

## 使用流程示例

### 1. 创建会话并收集数据
```bash
# 通过 AI 聊天创建会话并收集家族信息
POST /api/chat/
```

### 2. 生成报告
```bash
# 生成家族历史报告
POST /api/generate/report
```

### 3. 查看会话详情
```bash
# 获取会话完整信息
GET /session/{session_id}
```

### 4. 查看报告
```bash
# 获取生成的报告
GET /session/{session_id}/report
```

### 5. 保存为档案
```bash
# 保存会话为档案
POST /session/{session_id}/archive
{
  "title": "我的家族历史档案",
  "notes": "重要资料"
}
```

### 6. 查看所有档案
```bash
# 列出所有已归档的会话
GET /session/list?archived=true
```

---

## 注意事项

1. **档案名称**: `title` 字段是必填的，但如果用户未提供，系统会自动生成默认名称
2. **数据格式**: 所有时间字段使用 ISO 8601 格式（例如：`2024-01-01T00:00:00`）
3. **分页**: 列表接口目前最多返回 100 条记录，如需更多数据，请使用筛选条件
4. **报告生成**: 在调用 `/session/{session_id}/report` 之前，需要先通过 `/api/generate/report` 生成报告

---

## Swagger 文档

启动服务后，访问 `http://localhost:8000/docs` 查看交互式 API 文档，可以测试所有端点。
