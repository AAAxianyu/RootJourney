"""
讯飞语音转写服务
"""
import base64
import hashlib
import hmac
import json
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse
import httpx
from app.config import settings
from app.utils.logger import logger


class VoiceService:
    """讯飞语音转写服务类"""
    
    def __init__(self):
        """初始化讯飞客户端"""
        self.app_id = settings.xunfei_app_id
        self.api_key = settings.xunfei_api_key
        self.api_secret = settings.xunfei_api_secret
        
        if not all([self.app_id, self.api_key, self.api_secret]):
            logger.warning("讯飞 API 配置不完整")
    
    def _generate_auth_url(self, host_url: str, api_key: str, api_secret: str) -> str:
        """生成鉴权URL"""
        url = urlparse(host_url)
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 拼接字符串
        signature_origin = f"host: {url.netloc}\ndate: {date}\nGET {url.path} HTTP/1.1"
        
        # 进行hmac-sha256加密
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 将请求的鉴权参数组合为字典
        values = {
            "authorization": authorization,
            "date": date,
            "host": url.netloc
        }
        
        # 拼接鉴权参数，生成url
        return host_url + '?' + urlencode(values)
    
    async def transcribe(self, audio_file: bytes, audio_format: str = "wav", language: str = "zh_cn") -> str:
        """
        语音转写
        audio_file: 音频文件字节流
        audio_format: 音频格式 (wav, mp3, m4a等)
        language: 语言代码 (zh_cn, en_us等)
        """
        if not all([self.app_id, self.api_key, self.api_secret]):
            raise ValueError("讯飞 API 配置不完整")
        
        # 讯飞实时转写API地址
        host_url = "https://iat-api.xfyun.cn/v2/iat"
        auth_url = self._generate_auth_url(host_url, self.api_key, self.api_secret)
        
        # 将音频文件转为base64
        audio_base64 = base64.b64encode(audio_file).decode('utf-8')
        
        # 构建请求参数
        params = {
            "common": {
                "app_id": self.app_id
            },
            "business": {
                "language": language,
                "domain": "iat",
                "accent": "mandarin",
                "vad_eos": 10000
            },
            "data": {
                "status": 2,  # 2表示数据发送完毕
                "format": audio_format,
                "encoding": "raw",
                "audio": audio_base64
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    auth_url,
                    json=params,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                # 解析结果
                if result.get("code") == 0:
                    text = ""
                    for item in result.get("data", {}).get("result", {}).get("ws", []):
                        for word in item.get("cw", []):
                            text += word.get("w", "")
                    return text
                else:
                    error_msg = result.get("message", "转写失败")
                    logger.error(f"讯飞转写错误: {error_msg}")
                    raise Exception(f"转写失败: {error_msg}")
        except Exception as e:
            logger.error(f"讯飞转写异常: {e}")
            raise

