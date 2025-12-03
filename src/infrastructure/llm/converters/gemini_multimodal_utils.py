"""Gemini多模态内容处理工具

专门处理Gemini API的多模态内容，包括图像、音频、视频和文本等。
"""

from typing import Dict, Any, List, Union, Optional
import base64
import mimetypes
from src.services.logger import get_logger


class GeminiMultimodalUtils:
    """Gemini多模态内容处理工具类"""
    
    # 支持的图像格式
    SUPPORTED_IMAGE_FORMATS = {
        "image/jpeg",
        "image/png", 
        "image/webp",
        "image/heic",
        "image/heif"
    }
    
    # 支持的音频格式
    SUPPORTED_AUDIO_FORMATS = {
        "audio/wav",
        "audio/mp3",
        "audio/aac",
        "audio/ogg",
        "audio/flac"
    }
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = {
        "video/mp4",
        "video/mpeg",
        "video/mov",
        "video/avi",
        "video/webm"
    }
    
    # 文件大小限制（10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self) -> None:
        """初始化多模态工具"""
        self.logger = get_logger(__name__)
    
    def process_content_to_gemini_format(
        self, 
        content: Union[str, List[Union[str, Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        """将内容转换为Gemini格式
        
        Args:
            content: 输入内容，可以是字符串或列表
            
        Returns:
            List[Dict[str, Any]]: Gemini格式的内容列表
        """
        if isinstance(content, str):
            return [{"text": content}]
        elif isinstance(content, list):
            return self._process_content_list(content)
        else:
            return [{"text": str(content)}]
    
    def _process_content_list(self, content_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理内容列表"""
        gemini_content = []
        
        for item in content_list:
            if isinstance(item, str):
                gemini_content.append({"text": item})
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    gemini_content.append({
                        "text": item.get("text", "")
                    })
                elif item.get("type") == "image":
                    processed_image = self._process_image_content(item)
                    if processed_image:
                        gemini_content.append(processed_image)
                elif item.get("type") == "audio":
                    processed_audio = self._process_audio_content(item)
                    if processed_audio:
                        gemini_content.append(processed_audio)
                elif item.get("type") == "video":
                    processed_video = self._process_video_content(item)
                    if processed_video:
                        gemini_content.append(processed_video)
                elif item.get("type") == "image_url":
                    # 处理OpenAI格式的图像URL
                    processed_image = self._process_image_url_content(item)
                    if processed_image:
                        gemini_content.append(processed_image)
                else:
                    # 尝试将其他类型转换为文本
                    gemini_content.append({
                        "text": str(item)
                    })
            else:
                gemini_content.append({
                    "text": str(item)
                })
        
        return gemini_content
    
    def _process_image_content(self, image_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理图像内容"""
        try:
            source = image_item.get("source", {})
            
            if not source:
                self.logger.warning("图像内容缺少source字段")
                return None
            
            # 检查图像格式
            mime_type = source.get("mime_type", "")
            if mime_type not in self.SUPPORTED_IMAGE_FORMATS:
                self.logger.warning(f"不支持的图像格式: {mime_type}")
                return None
            
            # 检查数据大小
            image_data = source.get("data", "")
            if isinstance(image_data, str):
                try:
                    decoded_data = base64.b64decode(image_data)
                    if len(decoded_data) > self.MAX_FILE_SIZE:
                        self.logger.warning(f"图像大小超过限制: {len(decoded_data)} bytes")
                        return None
                except Exception as e:
                    self.logger.error(f"图像数据解码失败: {e}")
                    return None
            
            return {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_data
                }
            }
        except Exception as e:
            self.logger.error(f"处理图像内容失败: {e}")
            return None
    
    def _process_image_url_content(self, image_url_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理OpenAI格式的图像URL内容"""
        try:
            image_url = image_url_item.get("image_url", {})
            url = image_url.get("url", "")
            
            if not url:
                self.logger.warning("图像URL内容缺少url字段")
                return None
            
            # 检查是否为base64格式
            if url.startswith("data:"):
                # 解析data URL格式: data:mime_type;base64,data
                try:
                    header, data = url.split(",", 1)
                    mime_type = header.split(":")[1].split(";")[0]
                    
                    if mime_type not in self.SUPPORTED_IMAGE_FORMATS:
                        self.logger.warning(f"不支持的图像格式: {mime_type}")
                        return None
                    
                    # 检查数据大小
                    try:
                        decoded_data = base64.b64decode(data)
                        if len(decoded_data) > self.MAX_FILE_SIZE:
                            self.logger.warning(f"图像大小超过限制: {len(decoded_data)} bytes")
                            return None
                    except Exception as e:
                        self.logger.error(f"图像数据解码失败: {e}")
                        return None
                    
                    return {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": data
                        }
                    }
                except Exception as e:
                    self.logger.error(f"解析图像URL失败: {e}")
                    return None
            else:
                self.logger.warning("Gemini只支持base64编码的图像数据，不支持外部URL")
                return None
        except Exception as e:
            self.logger.error(f"处理图像URL内容失败: {e}")
            return None
    
    def _process_audio_content(self, audio_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理音频内容"""
        try:
            source = audio_item.get("source", {})
            
            if not source:
                self.logger.warning("音频内容缺少source字段")
                return None
            
            # 检查音频格式
            mime_type = source.get("mime_type", "")
            if mime_type not in self.SUPPORTED_AUDIO_FORMATS:
                self.logger.warning(f"不支持的音频格式: {mime_type}")
                return None
            
            # 检查数据大小
            audio_data = source.get("data", "")
            if isinstance(audio_data, str):
                try:
                    decoded_data = base64.b64decode(audio_data)
                    if len(decoded_data) > self.MAX_FILE_SIZE:
                        self.logger.warning(f"音频大小超过限制: {len(decoded_data)} bytes")
                        return None
                except Exception as e:
                    self.logger.error(f"音频数据解码失败: {e}")
                    return None
            
            return {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": audio_data
                }
            }
        except Exception as e:
            self.logger.error(f"处理音频内容失败: {e}")
            return None
    
    def _process_video_content(self, video_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理视频内容"""
        try:
            source = video_item.get("source", {})
            
            if not source:
                self.logger.warning("视频内容缺少source字段")
                return None
            
            # 检查视频格式
            mime_type = source.get("mime_type", "")
            if mime_type not in self.SUPPORTED_VIDEO_FORMATS:
                self.logger.warning(f"不支持的视频格式: {mime_type}")
                return None
            
            # 检查数据大小
            video_data = source.get("data", "")
            if isinstance(video_data, str):
                try:
                    decoded_data = base64.b64decode(video_data)
                    if len(decoded_data) > self.MAX_FILE_SIZE:
                        self.logger.warning(f"视频大小超过限制: {len(decoded_data)} bytes")
                        return None
                except Exception as e:
                    self.logger.error(f"视频数据解码失败: {e}")
                    return None
            
            return {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": video_data
                }
            }
        except Exception as e:
            self.logger.error(f"处理视频内容失败: {e}")
            return None
    
    def extract_text_from_gemini_content(self, content: List[Dict[str, Any]]) -> str:
        """从Gemini格式内容中提取文本
        
        Args:
            content: Gemini格式的内容列表
            
        Returns:
            str: 提取的文本内容
        """
        text_parts = []
        
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    text_parts.append(item["text"])
                elif "inline_data" in item:
                    mime_type = item["inline_data"].get("mime_type", "")
                    if mime_type.startswith("image/"):
                        text_parts.append("[图像内容]")
                    elif mime_type.startswith("audio/"):
                        text_parts.append("[音频内容]")
                    elif mime_type.startswith("video/"):
                        text_parts.append("[视频内容]")
                    else:
                        text_parts.append("[多模态内容]")
        
        return " ".join(text_parts)
    
    def validate_gemini_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Gemini格式内容
        
        Args:
            content: Gemini格式的内容列表
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        media_count = 0
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"内容项 {i} 必须是字典")
                continue
            
            if "text" in item:
                text = item["text"]
                if not isinstance(text, str):
                    errors.append(f"文本内容项 {i} 的text字段必须是字符串")
            elif "inline_data" in item:
                media_count += 1
                media_errors = self._validate_inline_data(item["inline_data"], i)
                errors.extend(media_errors)
            else:
                errors.append(f"内容项 {i} 必须包含text或inline_data字段")
        
        # 检查媒体数量限制
        if media_count > 5:
            errors.append("每条消息最多支持5个媒体文件")
        
        return errors
    
    def _validate_inline_data(self, inline_data: Dict[str, Any], index: int) -> List[str]:
        """验证inline_data内容"""
        errors = []
        
        if not isinstance(inline_data, dict):
            errors.append(f"媒体项 {index} 的inline_data字段必须是字典")
            return errors
        
        # 检查媒体类型
        mime_type = inline_data.get("mime_type")
        if not isinstance(mime_type, str):
            errors.append(f"媒体项 {index} 缺少有效的mime_type")
        else:
            # 验证媒体类型
            if mime_type.startswith("image/"):
                if mime_type not in self.SUPPORTED_IMAGE_FORMATS:
                    errors.append(f"媒体项 {index} 有不支持的图像格式: {mime_type}")
            elif mime_type.startswith("audio/"):
                if mime_type not in self.SUPPORTED_AUDIO_FORMATS:
                    errors.append(f"媒体项 {index} 有不支持的音频格式: {mime_type}")
            elif mime_type.startswith("video/"):
                if mime_type not in self.SUPPORTED_VIDEO_FORMATS:
                    errors.append(f"媒体项 {index} 有不支持的视频格式: {mime_type}")
            else:
                errors.append(f"媒体项 {index} 有不支持的媒体类型: {mime_type}")
        
        # 检查数据
        data = inline_data.get("data")
        if not isinstance(data, str):
            errors.append(f"媒体项 {index} 的data字段必须是字符串")
        else:
            try:
                decoded_data = base64.b64decode(data)
                if len(decoded_data) > self.MAX_FILE_SIZE:
                    errors.append(f"媒体项 {index} 大小超过10MB限制")
            except Exception:
                errors.append(f"媒体项 {index} 的data字段不是有效的base64编码")
        
        return errors
    
    def create_image_content(
        self, 
        image_path: str, 
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件路径创建图像内容
        
        Args:
            image_path: 图像文件路径
            mime_type: 媒体类型，如果不提供则自动检测
            
        Returns:
            Dict[str, Any]: 图像内容字典
        """
        try:
            # 自动检测媒体类型
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = "image/jpeg"  # 默认
            
            # 读取并编码图像
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            if len(image_data) > self.MAX_FILE_SIZE:
                raise ValueError(f"图像大小超过限制: {len(image_data)} bytes")
            
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "mime_type": mime_type,
                    "data": encoded_data
                }
            }
        except Exception as e:
            self.logger.error(f"创建图像内容失败: {e}")
            raise
    
    def create_audio_content(
        self, 
        audio_path: str, 
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件路径创建音频内容
        
        Args:
            audio_path: 音频文件路径
            mime_type: 媒体类型，如果不提供则自动检测
            
        Returns:
            Dict[str, Any]: 音频内容字典
        """
        try:
            # 自动检测媒体类型
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(audio_path)
                if not mime_type:
                    mime_type = "audio/wav"  # 默认
            
            # 读取并编码音频
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            
            if len(audio_data) > self.MAX_FILE_SIZE:
                raise ValueError(f"音频大小超过限制: {len(audio_data)} bytes")
            
            encoded_data = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "type": "audio",
                "source": {
                    "type": "base64",
                    "mime_type": mime_type,
                    "data": encoded_data
                }
            }
        except Exception as e:
            self.logger.error(f"创建音频内容失败: {e}")
            raise
    
    def create_video_content(
        self, 
        video_path: str, 
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件路径创建视频内容
        
        Args:
            video_path: 视频文件路径
            mime_type: 媒体类型，如果不提供则自动检测
            
        Returns:
            Dict[str, Any]: 视频内容字典
        """
        try:
            # 自动检测媒体类型
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(video_path)
                if not mime_type:
                    mime_type = "video/mp4"  # 默认
            
            # 读取并编码视频
            with open(video_path, "rb") as f:
                video_data = f.read()
            
            if len(video_data) > self.MAX_FILE_SIZE:
                raise ValueError(f"视频大小超过限制: {len(video_data)} bytes")
            
            encoded_data = base64.b64encode(video_data).decode('utf-8')
            
            return {
                "type": "video",
                "source": {
                    "type": "base64",
                    "mime_type": mime_type,
                    "data": encoded_data
                }
            }
        except Exception as e:
            self.logger.error(f"创建视频内容失败: {e}")
            raise