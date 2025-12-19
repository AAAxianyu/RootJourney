# API 文档

## 概述

RootJourney API 提供了家族历史探索平台的所有后端功能。

## 基础URL

```
http://localhost:8000
```

## 认证

大部分API端点需要认证。请在请求头中包含：

```
Authorization: Bearer <token>
```

## 端点列表

### 用户相关

#### 创建用户
- **POST** `/api/users/`
- 创建新用户

#### 获取用户信息
- **GET** `/api/users/{user_id}`
- 获取指定用户的信息

### AI聊天

#### 发送消息
- **POST** `/api/chat/`
- 与AI进行对话

### 搜索

#### 执行搜索
- **POST** `/api/search/`
- 联网搜索相关信息

### 生成

#### 生成家族报告
- **POST** `/api/generate/report`
- 生成完整的家族报告

#### 生成个人传记
- **POST** `/api/generate/biography/{person_id}`
- 生成指定人物的传记

#### 生成时间轴
- **POST** `/api/generate/timeline/{person_id}`
- 生成指定人物的时间轴

### 导出

#### 导出PDF
- **GET** `/api/export/pdf/{report_id}`
- 导出报告为PDF格式

#### 导出JSON
- **GET** `/api/export/json/{report_id}`
- 导出报告为JSON格式

#### 导出家族图谱图片
- **GET** `/api/export/image/{family_tree_id}`
- 导出家族图谱为图片

## Swagger文档

启动服务后，访问 `http://localhost:8000/docs` 查看交互式API文档。

