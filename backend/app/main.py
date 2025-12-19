"""
FastAPI 应用入口文件
启动服务器
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import user, ai_chat, search, generate, export

app = FastAPI(
    title="RootJourney API",
    description="家族历史探索平台 API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
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

@app.get("/")
async def root():
    return {"message": "RootJourney API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

