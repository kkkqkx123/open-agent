"""Gemini多模态内容处理工具

专门处理Gemini API的多模态内容，包括图像、文本等。
"""

from typing import Dict, Any, List, Union, Optional
import base64
import mimetypes
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils


class GeminiMultimodalUtils(BaseMultimodalUtils):
    """Gemini多模态内容处理工具类"""
    
    # 支持的图像格式
    SUPPORTED_IMAGE_FORMATS = {
        "image/jpeg",
        "image/png", 
        "image/gif",
        "image/webp",
        "image/heic",
        "image/heif"
    }
    
    # 图像大小限制（10MB）
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    
    def __init__(self) -> None:
        """初始化多模态工具"""
        super().__init__()
    
    def process_content_to_provider_format(
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
    
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从Gemini格式内容中提取文本
        
        Args:
            content: Gemini格式的内容列表
            
        Returns:
            str: 提取的文本内容
        """
        return self._extract_text_from_content_list(content)
    
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Gemini格式内容
        
        Args:
            content: Gemini格式的内容列表
            
        Returns:
            List[str]: 验证错误列表
        """
        return self._validate_gemini_content(content)
    
    def _process_content_list(self, content_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理内容列表"""
        gemini_content = []
        
        for item in content_list:
            if isinstance(item, str):
                gemini_content.append({"text": item})
            elif isinstance(item, dict):
                processed_item = self._process_dict_content(item)
                if processed_item:
                    gemini_content.append(processed_item)
            else:
                gemini_content.append({"text": str(item)})
        
        return gemini_content
    
    def _process_dict_content(self, content_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理字典内容"""
        content_type = content_dict.get("type")
        
        if content_type == "text":
            return {"text": content_dict.get("text", "")}
        elif content_type == "image":
            return self._process_image_content(content_dict)
        else:
            # 未知类型，转换为文本
            return {"text": str(content_dict)}
    
    def _process_image_content(self, image_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理图像内容"""
        try:
            source = image_item.get("source", {})
            
            if not source:
                self.logger.warning("图像内容缺少source字段")
                return None
            
            # 检查图像格式
            media_type = source.get("media_type", "")
            if media_type not in self.SUPPORTED_IMAGE_FORMATS:
                self.logger.warning(f"不支持的图像格式: {media_type}")
                return None
            
            # 检查数据大小
            image_data = source.get("data", "")
            if isinstance(image_data, str):
                try:
                    decoded_data = base64.b64decode(image_data)
                    if len(decoded_data) > self.MAX_IMAGE_SIZE:
                        self.logger.warning(f"图像大小超过限制: {len(decoded_data)} bytes")
                        return None
                except Exception as e:
                    self.logger.error(f"图像数据解码失败: {e}")
                    return None
            
            return {
                "inline_data": {
                    "mime_type": media_type,
                    "data": image_data
                }
            }
        except Exception as e:
            self.logger.error(f"处理图像内容失败: {e}")
            return None
    
    def _validate_gemini_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Gemini格式内容"""
        errors = []
        image_count = 0
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"内容项 {i} 必须是字典")
                continue
            
            if "text" in item:
                # 验证文本内容
                text = item["text"]
                if not isinstance(text, str):
                    errors.append(f"内容项 {i} 的text字段必须是字符串")
            elif "inline_data" in item:
                # 验证图像内容
                image_count += 1
                image_errors = self._validate_inline_data(item["inline_data"], i)
                errors.extend(image_errors)
            else:
                errors.append(f"内容项 {i} 必须包含text或inline_data字段")
        
        # Gemini对图像数量没有严格限制，但建议合理使用
        if image_count > 10:
            self.logger.warning(f"图像数量较多: {image_count}，可能影响性能")
        
        return errors
    
    def _validate_inline_data(self, inline_data: Dict[str, Any], index: int) -> List[str]:
        """验证inline_data字段"""
        errors = []
        
        if not isinstance(inline_data, dict):
            errors.append(f"内容项 {index} 的inline_data字段必须是字典")
            return errors
        
        # 检查mime_type
        mime_type = inline_data.get("mime_type")
        if not isinstance(mime_type, str):
            errors.append(f"内容项 {index} 的mime_type字段必须是字符串")
        elif mime_type not in self.SUPPORTED_IMAGE_FORMATS:
            errors.append(f"内容项 {index} 有不支持的mime_type: {mime_type}")
        
        # 检查data
        data = inline_data.get("data")
        if not isinstance(data, str):
            errors.append(f"内容项 {index} 的data字段必须是字符串")
        else:
            try:
                decoded_data = base64.b64decode(data)
                if len(decoded_data) > self.MAX_IMAGE_SIZE:
                    errors.append(f"内容项 {index} 的图像大小超过10MB限制")
            except Exception:
                errors.append(f"内容项 {index} 的data字段不是有效的base64编码")
        
        return errors
    
    def _create_text_content(self, text: str) -> Dict[str, Any]:
        """创建文本内容"""
        return {"text": text}
    
    def _create_image_content_dict(self, media_type: str, encoded_data: str) -> Dict[str, Any]:
        """创建图像内容字典"""
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded_data
            }
        }
    
    def _get_max_image_size(self) -> int:
        """获取最大图像大小限制"""
        return self.MAX_IMAGE_SIZE
    
    def _get_supported_image_formats(self) -> set:
        """获取支持的图像格式"""
        return self.SUPPORTED_IMAGE_FORMATS
    
    def create_gemini_part_from_image(self, image_path: str) -> Dict[str, Any]:
        """从图像文件路径创建Gemini part
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            Dict[str, Any]: Gemini格式的图像part
        """
        try:
            # 自动检测媒体类型
            media_type, _ = mimetypes.guess_type(image_path)
            if not media_type:
                media_type = "image/jpeg"  # 默认
            
            # 读取并编码图像
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            if len(image_data) > self.MAX_IMAGE_SIZE:
                raise ValueError(f"图像大小超过限制: {len(image_data)} bytes")
            
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            
            return {
                "inline_data": {
                    "mime_type": media_type,
                    "data": encoded_data
                }
            }
        except Exception as e:
            self.logger.error(f"创建Gemini图像part失败: {e}")
            raise
    
    def process_video_content(self, video_path: str) -> Dict[str, Any]:
        """处理视频内容（Gemini支持视频）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: Gemini格式的视频part
        """
        try:
            # 自动检测媒体类型
            media_type, _ = mimetypes.guess_type(video_path)
            if not media_type or not media_type.startswith("video/"):
                media_type = "video/mp4"  # 默认
            
            # 读取并编码视频
            with open(video_path, "rb") as f:
                video_data = f.read()
            
            # 视频大小限制（100MB）
            max_video_size = 100 * 1024 * 1024
            if len(video_data) > max_video_size:
                raise ValueError(f"视频大小超过限制: {len(video_data)} bytes")
            
            encoded_data = base64.b64encode(video_data).decode('utf-8')
            
            return {
                "inline_data": {
                    "mime_type": media_type,
                    "data": encoded_data
                }
            }
        except Exception as e:
            self.logger.error(f"处理视频内容失败: {e}")
            raise
    
    def extract_text_from_gemini_content(self, content: List[Dict[str, Any]]) -> str:
        """从Gemini格式内容中提取文本（兼容性方法）"""
        return self.extract_text_from_provider_content(content)
    
    def validate_gemini_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Gemini格式内容（兼容性方法）"""
        return self.validate_provider_content(content)