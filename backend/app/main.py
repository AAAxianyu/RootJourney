"""
FastAPI 应用入口文件
启动服务器
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import user, ai_chat, search, generate, export, gateway, health, session, memories

app = FastAPI(
    title="RootJourney API",
    description="家族历史探索平台 API",
    version="1.0.0"
)

# 配置CORS - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:80",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user.router)
app.include_router(ai_chat.router)
app.include_router(search.router)
app.include_router(generate.router)
app.include_router(export.router)
app.include_router(session.router)  # 会话管理（查看和保存档案）
app.include_router(memories.router)  # 记忆总结
app.include_router(health.router)  # 健康检查和测试

@app.get("/")
async def root():
    return {"message": "RootJourney API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

