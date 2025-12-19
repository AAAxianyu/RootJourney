"""
API Gateway 路由
统一对外提供第三方 API 调用接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from app.services.gateway_service import GatewayService
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["gateway"])

gateway_service = GatewayService()


# ========== 语音转写 ==========
@router.post("/voice/transcribe")
async def transcribe_voice(
    audio_file: UploadFile = File(...),
    audio_format: str = Form("wav"),
    language: str = Form("zh_cn")
):
    """
    讯飞语音转写
    上传录音文件，返回转写文本
    """
    try:
        audio_bytes = await audio_file.read()
        text = await gateway_service.voice_service.transcribe(
            audio_bytes,
            audio_format=audio_format,
            language=language
        )
        return {
            "success": True,
            "text": text,
            "format": audio_format,
            "language": language
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Voice transcribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== LLM 问答 ==========
class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    model: Optional[str] = None  # 如果为 None，自动选择
    temperature: float = 0.7
    provider: str = "auto"  # "openai", "deepseek", "auto"


@router.post("/llm/chat")
async def llm_chat(request: ChatRequest):
    """
    LLM 问答（支持 OpenAI 和 DeepSeek）
    发送消息列表，返回AI回复
    """
    try:
        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        response = await gateway_service.llm_chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            provider=request.provider
        )
        
        return {
            "success": True,
            "response": response,
            "model": request.model or "auto",
            "provider": request.provider
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LLM chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== LLM 抽取 ==========
class ExtractRequest(BaseModel):
    """抽取请求模型"""
    model_config = ConfigDict(populate_by_name=True)  # 允许使用字段名或别名
    
    text: str
    json_schema: Dict[str, Any] = Field(..., alias="schema", description="JSON Schema for extraction")
    model: Optional[str] = None
    provider: str = "auto"  # "openai", "deepseek", "auto"


@router.post("/llm/extract")
async def llm_extract(request: ExtractRequest):
    """
    LLM 抽取 JSON（支持 OpenAI 和 DeepSeek）
    从文本中提取结构化信息
    """
    try:
        result = await gateway_service.llm_extract(
            text=request.text,
            schema=request.json_schema,
            model=request.model,
            provider=request.provider
        )
        
        return {
            "success": True,
            "data": result,
            "model": request.model or "auto",
            "provider": request.provider
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LLM extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 搜索 ==========
@router.get("/search")
async def search(query: str, num_results: int = 10):
    """
    Google Custom Search
    搜索关键词，返回搜索结果列表
    """
    try:
        results = await gateway_service.search(query, num_results)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 图片生成 ==========
class ImageRequest(BaseModel):
    """图片生成请求模型"""
    prompt: str
    size: str = "1024x1024"


@router.post("/media/image")
async def generate_image(request: ImageRequest):
    """
    DALL·E 生成图片
    根据提示词生成图片，返回图片URL
    """
    try:
        image_url = await gateway_service.generate_image(
            prompt=request.prompt,
            size=request.size
        )
        
        return {
            "success": True,
            "url": image_url,
            "prompt": request.prompt,
            "size": request.size
        }
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 视频生成 ==========
class VideoRequest(BaseModel):
    """视频生成请求模型"""
    prompt: str
    duration: int = 10


@router.post("/media/video")
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Sora 生成视频（创建任务）
    创建视频生成任务，返回任务ID
    """
    try:
        task_id = await gateway_service.create_video_task(
            prompt=request.prompt,
            duration=request.duration
        )
        
        # 使用 BackgroundTasks 异步执行视频生成
        background_tasks.add_task(
            gateway_service._process_video_task,
            task_id,
            request.prompt,
            request.duration
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "pending",
            "message": "视频生成任务已创建，请使用任务ID查询状态"
        }
    except Exception as e:
        logger.error(f"Video task creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/media/video/{task_id}")
async def get_video_status(task_id: str):
    """
    查询视频生成任务状态
    返回任务状态和结果URL（如果完成）
    """
    try:
        status = await gateway_service.get_video_task_status(task_id)
        
        return {
            "success": True,
            **status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Video status query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

