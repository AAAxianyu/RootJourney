"""
文生图/文生视频封装服务
独立封装 text_to_image 和 text_to_video
"""
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings
from app.utils.logger import logger
import httpx


class GenAIService:
    """生成式 AI 服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化生成式 AI 客户端"""
        self.api_key = api_key or settings.openai_api_key
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured for GenAI service")
        
        self.stable_diffusion_url = settings.stable_diffusion_url
    
    async def text_to_image(self, prompt: str, size: str = "1024x1024") -> str:
        """
        生成图片 URL
        使用 DALL-E 3 或本地 Stable Diffusion
        """
        # 优先使用 DALL-E
        if self.client:
            try:
                response = await self.client.images.generate(
                    model=settings.dall_e_model,
                    prompt=prompt,
                    n=1,
                    size=size
                )
                return response.data[0].url
            except Exception as e:
                logger.error(f"DALL-E image generation error: {e}")
        
        # 如果 DALL-E 失败，尝试本地 Stable Diffusion
        if self.stable_diffusion_url:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.stable_diffusion_url}/api/v1/txt2img",
                        json={
                            "prompt": prompt,
                            "width": int(size.split("x")[0]),
                            "height": int(size.split("x")[1]),
                            "steps": 20
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    # 假设返回格式包含图片URL或base64
                    if "images" in data and data["images"]:
                        return data["images"][0]
            except Exception as e:
                logger.error(f"Stable Diffusion image generation error: {e}")
        
        # 返回占位符
        logger.warning("Image generation failed, returning placeholder")
        return "https://via.placeholder.com/1024x1024?text=Image+Generation+Failed"
    
    async def text_to_video(self, prompt: str, duration: int = 10) -> str:
        """
        生成视频 URL
        假设使用 Sora API 或类似服务
        """
        if self.client:
            try:
                # 注意：OpenAI Sora API 可能还未公开，这里使用假设的接口
                # 实际使用时需要根据真实API调整
                response = await self.client.videos.generate(
                    model="sora",
                    prompt=prompt,
                    duration=duration
                )
                return response.data[0].url
            except AttributeError:
                # 如果 API 不存在，使用占位符
                logger.warning("Video generation API not available")
            except Exception as e:
                logger.error(f"Video generation error: {e}")
        
        # 返回占位符
        return "https://via.placeholder.com/1920x1080?text=Video+Generation+Not+Available"
    
    async def enhance_image(self, image_url: str, prompt: Optional[str] = None) -> str:
        """图片增强"""
        # 可以使用 DALL-E 的编辑功能或其他服务
        if self.client and prompt:
            try:
                # 下载原图
                async with httpx.AsyncClient() as client:
                    img_response = await client.get(image_url)
                    img_data = img_response.content
                
                # 使用 DALL-E 编辑（需要根据实际API调整）
                # 这里返回原图URL作为占位
                return image_url
            except Exception as e:
                logger.error(f"Image enhancement error: {e}")
        
        return image_url
