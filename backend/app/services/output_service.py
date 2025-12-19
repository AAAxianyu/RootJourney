"""
输出生成服务
整合所有服务，生成最终输出（报告、传记、时间轴）
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.dependencies.db import get_mongodb_db
from app.models.output import FamilyReport, Biography, Timeline, TimelineEvent
from app.services.ai_service import AIService
from app.services.graph_service import GraphService
from app.services.gen_ai_service import GenAIService
from app.utils.logger import logger
import json


class OutputService:
    """输出服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.graph_service = GraphService()
        self.gen_ai_service = GenAIService()
    
    async def generate_text(self, session_id: str) -> str:
        """生成文字描述"""
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        user_input = session.get("user_input", {})
        
        # 使用 AI 生成文字描述
        if self.ai_service.client:
            prompt = f"""
基于以下家族数据，生成一份详细的家族历史报告：
用户信息：{json.dumps(user_input, ensure_ascii=False)}
家族图谱：{json.dumps(family_graph, ensure_ascii=False)}

请生成包含以下内容的报告：
1. 家族起源和迁徙轨迹
2. 重要历史事件
3. 家族特色和文化传承
4. 可能的祖上名人

要求：文字流畅、有故事性、尊重历史事实。
"""
            try:
                response = await self.ai_service.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generating text: {e}")
        
        # 简单返回
        return f"家族历史报告：基于收集的数据，{user_input.get('name', '用户')}的家族信息已整理完成。"
    
    async def generate_report(self, session_id: str) -> Dict[str, Any]:
        """
        生成家族报告
        返回包含文字和图片的完整报告
        """
        text = await self.generate_text(session_id)
        
        # 生成图片提示词
        image_prompts = [
            f"Historical family portrait, traditional Chinese family, {text[:100]}",
            f"Ancient Chinese genealogy book, family tree, elegant style",
            f"Chinese ancestral hall, traditional architecture, family heritage"
        ]
        
        # 生成图片
        images = []
        for prompt in image_prompts:
            try:
                image_url = await self.gen_ai_service.text_to_image(prompt)
                images.append(image_url)
            except Exception as e:
                logger.error(f"Error generating image: {e}")
        
        return {
            "text": text,
            "images": images,
            "generated_at": datetime.now().isoformat()
        }
    
    async def build_timeline(self, session_id: str, family_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        构建时间轴
        调用 graph_service
        """
        return await self.graph_service.build_timeline(session_id, family_filter)
    
    async def generate_bio(self, session_id: str) -> str:
        """
        生成个人传记
        整合用户输入和家族图谱，生成融入家族叙事的个人故事
        """
        db = await get_mongodb_db()
        session = await db.sessions.find_one({"_id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        family_graph = session.get("family_graph", {})
        user_input = session.get("user_input", {})
        
        if self.ai_service.client:
            prompt = f"""
基于以下信息，生成一份个人传记，融入家族叙事：
个人信息：{json.dumps(user_input, ensure_ascii=False)}
家族图谱：{json.dumps(family_graph, ensure_ascii=False)}

要求：
1. 以第一人称或第三人称叙述
2. 融入家族历史背景
3. 体现家族传承和文化
4. 文字优美、有感染力
5. 长度约500-800字
"""
            try:
                response = await self.ai_service.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generating biography: {e}")
        
        return f"{user_input.get('name', '用户')}的个人传记：基于家族历史和个人经历的故事。"
    
    async def get_video_prompt(self, session_id: str) -> str:
        """获取视频生成的提示词"""
        text = await self.generate_text(session_id)
        # 简化文字用于视频生成
        return f"Family history animation: {text[:200]}"
    
    async def export_pdf(self, session_id: str) -> str:
        """
        导出为 PDF
        返回 PDF 文件 URL
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            import io
            import httpx
            
            report = await self.generate_report(session_id)
            
            # 创建 PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # 添加文字
            y = height - 50
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, "家族历史报告")
            y -= 30
            
            c.setFont("Helvetica", 12)
            text_lines = report["text"].split("\n")
            for line in text_lines[:50]:  # 限制行数
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line[:80])  # 限制每行长度
                y -= 20
            
            # 添加图片（如果有）
            if report.get("images"):
                c.showPage()
                y = height - 50
                for img_url in report["images"][:3]:  # 最多3张
                    try:
                        async with httpx.AsyncClient() as client:
                            img_response = await client.get(img_url)
                            img_data = img_response.content
                            img = ImageReader(io.BytesIO(img_data))
                            c.drawImage(img, 50, y - 200, width=500, height=200)
                            y -= 250
                    except Exception as e:
                        logger.error(f"Error adding image to PDF: {e}")
            
            c.save()
            buffer.seek(0)
            
            # 这里应该上传到 S3 或文件存储服务
            # 暂时返回 base64 或保存到本地
            # 实际实现需要根据部署环境调整
            
            # 保存到临时文件（实际应该上传到云存储）
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(buffer.read())
                tmp_path = tmp.name
            
            # 返回文件路径（实际应该返回 URL）
            return f"file://{tmp_path}"
            
        except ImportError:
            logger.error("reportlab not installed, cannot generate PDF")
            raise
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            raise
