"""通用内容处理器

提供各种内容类型的处理功能，包括文本、图像和混合内容。
"""

import base64
import mimetypes
from typing import Dict, Any, List, Union, Optional
from src.services.logger.injection import get_logger


class TextProcessor:
    """文本内容处理器"""
    
    def __init__(self) -> None:
        """初始化文本处理器"""
        self.logger = get_logger(__name__)
    
    @staticmethod
    def extract_text(content: Any) -> str:
        """提取文本内容
        
        Args:
            content: 输入内容，可以是字符串、列表或字典
            
        Returns:
            str: 提取的文本内容
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        text_parts.append(item["text"])
                    else:
                        # 尝试转换为字符串
                        text_parts.append(str(item))
            return " ".join(text_parts)
        elif isinstance(content, dict):
            if "text" in content:
                return content["text"]
            else:
                return str(content)
        else:
            return str(content)
    
    @staticmethod
    def validate_text(text: str) -> List[str]:
        """验证文本内容
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(text, str):
            errors.append("文本内容必须是字符串")
        
        return errors
    
    def clean_text(self, text: str) -> str:
        """清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not isinstance(text, str):
            return str(text)
        
        # 移除多余的空白字符
        cleaned = " ".join(text.split())
        
        return cleaned
    
    def truncate_text(self, text: str, max_length: int, suffix: str = "...") -> str:
        """截断文本
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后缀
            
        Returns:
            str: 截断后的文本
        """
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix


class ImageProcessor:
    """图像内容处理器"""
    
    # 支持的图像格式
    SUPPORTED_FORMATS = {
        "image/jpeg",
        "image/png", 
        "image/gif",
        "image/webp"
    }
    
    # 默认大小限制（5MB）
    DEFAULT_MAX_SIZE = 5 * 1024 * 1024
    
    def __init__(self, max_size: Optional[int] = None) -> None:
        """初始化图像处理器
        
        Args:
            max_size: 最大图像大小限制（字节）
        """
        self.logger = get_logger(__name__)
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
    
    def process_image(self, image_data: Union[str, bytes, Dict[str, Any]]) -> Dict[str, Any]:
        """处理图像数据
        
        Args:
            image_data: 图像数据，可以是base64字符串、字节数组或字典
            
        Returns:
            Dict[str, Any]: 处理后的图像数据
        """
        if isinstance(image_data, dict):
            return self._process_image_dict(image_data)
        elif isinstance(image_data, str):
            return self._process_base64_image(image_data)
        elif isinstance(image_data, bytes):
            return self._process_bytes_image(image_data)
        else:
            raise ValueError(f"不支持的图像数据类型: {type(image_data)}")
    
    def _process_image_dict(self, image_dict: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典格式的图像数据"""
        source = image_dict.get("source", {})
        
        if not source:
            raise ValueError("图像字典缺少source字段")
        
        # 验证媒体类型
        media_type = source.get("media_type", "")
        if media_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的图像格式: {media_type}")
        
        # 验证数据大小
        image_data = source.get("data", "")
        if isinstance(image_data, str):
            try:
                decoded_data = base64.b64decode(image_data)
                if len(decoded_data) > self.max_size:
                    raise ValueError(f"图像大小超过限制: {len(decoded_data)} bytes")
            except Exception as e:
                raise ValueError(f"图像数据解码失败: {e}")
        
        return {
            "type": "image",
            "source": {
                "type": source.get("type", "base64"),
                "media_type": media_type,
                "data": image_data
            }
        }
    
    def _process_base64_image(self, base64_data: str) -> Dict[str, Any]:
        """处理base64格式的图像数据"""
        try:
            decoded_data = base64.b64decode(base64_data)
            if len(decoded_data) > self.max_size:
                raise ValueError(f"图像大小超过限制: {len(decoded_data)} bytes")
            
            # 尝试检测图像格式
            media_type = self._detect_image_format(decoded_data)
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data
                }
            }
        except Exception as e:
            raise ValueError(f"处理base64图像失败: {e}")
    
    def _process_bytes_image(self, byte_data: bytes) -> Dict[str, Any]:
        """处理字节数组格式的图像数据"""
        if len(byte_data) > self.max_size:
            raise ValueError(f"图像大小超过限制: {len(byte_data)} bytes")
        
        try:
            # 检测图像格式
            media_type = self._detect_image_format(byte_data)
            
            # 编码为base64
            base64_data = base64.b64encode(byte_data).decode('utf-8')
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data
                }
            }
        except Exception as e:
            raise ValueError(f"处理字节数组图像失败: {e}")
    
    def _detect_image_format(self, byte_data: bytes) -> str:
        """检测图像格式"""
        # 简单的格式检测
        if byte_data.startswith(b'\xFF\xD8\xFF'):
            return "image/jpeg"
        elif byte_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        elif byte_data.startswith(b'GIF87a') or byte_data.startswith(b'GIF89a'):
            return "image/gif"
        elif byte_data.startswith(b'RIFF') and b'WEBP' in byte_data[:12]:
            return "image/webp"
        else:
            # 默认返回JPEG
            return "image/jpeg"
    
    def validate_image(self, image_data: Dict[str, Any]) -> List[str]:
        """验证图像数据
        
        Args:
            image_data: 图像数据字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(image_data, dict):
            errors.append("图像数据必须是字典")
            return errors
        
        if image_data.get("type") != "image":
            errors.append("图像数据type字段必须是'image'")
        
        source = image_data.get("source")
        if not isinstance(source, dict):
            errors.append("图像source字段必须是字典")
            return errors
        
        # 验证媒体类型
        media_type = source.get("media_type")
        if not media_type:
            errors.append("图像缺少media_type字段")
        elif media_type not in self.SUPPORTED_FORMATS:
            errors.append(f"不支持的图像格式: {media_type}")
        
        # 验证数据
        data = source.get("data")
        if not isinstance(data, str):
            errors.append("图像data字段必须是字符串")
        else:
            try:
                decoded_data = base64.b64decode(data)
                if len(decoded_data) > self.max_size:
                    errors.append(f"图像大小超过限制: {len(decoded_data)} bytes")
            except Exception:
                errors.append("图像data字段不是有效的base64编码")
        
        return errors
    
    def create_image_from_file(self, file_path: str) -> Dict[str, Any]:
        """从文件路径创建图像数据
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            Dict[str, Any]: 图像数据字典
        """
        try:
            # 自动检测媒体类型
            media_type, _ = mimetypes.guess_type(file_path)
            if not media_type or media_type not in self.SUPPORTED_FORMATS:
                media_type = "image/jpeg"  # 默认
            
            # 读取文件
            with open(file_path, "rb") as f:
                image_data = f.read()
            
            return self._process_bytes_image(image_data)
        except Exception as e:
            self.logger.error(f"从文件创建图像失败: {e}")
            raise


class MixedContentProcessor:
    """混合内容处理器"""
    
    def __init__(self) -> None:
        """初始化混合内容处理器"""
        self.logger = get_logger(__name__)
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
    
    def process_mixed_content(self, content: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理混合内容
        
        Args:
            content: 混合内容列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的内容列表
        """
        processed_content = []
        
        for item in content:
            if isinstance(item, str):
                processed_content.append({
                    "type": "text",
                    "text": self.text_processor.clean_text(item)
                })
            elif isinstance(item, dict):
                processed_item = self._process_content_item(item)
                if processed_item:
                    processed_content.append(processed_item)
            else:
                # 转换为文本
                processed_content.append({
                    "type": "text",
                    "text": str(item)
                })
        
        return processed_content
    
    def _process_content_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个内容项"""
        content_type = item.get("type")
        
        if content_type == "text":
            return {
                "type": "text",
                "text": self.text_processor.clean_text(item.get("text", ""))
            }
        elif content_type == "image":
            try:
                return self.image_processor.process_image(item)
            except Exception as e:
                self.logger.warning(f"处理图像内容失败: {e}")
                return None
        else:
            # 未知类型，转换为文本
            return {
                "type": "text",
                "text": str(item)
            }
    
    def validate_mixed_content(self, content: List[Union[str, Dict[str, Any]]]) -> List[str]:
        """验证混合内容
        
        Args:
            content: 混合内容列表
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(content, list):
            errors.append("混合内容必须是列表格式")
            return errors
        
        if not content:
            errors.append("混合内容列表不能为空")
            return errors
        
        image_count = 0
        
        for i, item in enumerate(content):
            if isinstance(item, str):
                # 验证文本
                text_errors = self.text_processor.validate_text(item)
                for error in text_errors:
                    errors.append(f"内容项 {i}: {error}")
            elif isinstance(item, dict):
                content_type = item.get("type")
                if content_type == "text":
                    text_errors = self.text_processor.validate_text(item.get("text", ""))
                    for error in text_errors:
                        errors.append(f"内容项 {i}: {error}")
                elif content_type == "image":
                    image_count += 1
                    image_errors = self.image_processor.validate_image(item)
                    for error in image_errors:
                        errors.append(f"内容项 {i}: {error}")
                else:
                    errors.append(f"内容项 {i} 有不支持的类型: {content_type}")
            else:
                errors.append(f"内容项 {i} 必须是字符串或字典")
        
        # 检查图像数量限制
        if image_count > 5:
            errors.append("每条消息最多支持5张图像")
        
        return errors
    
    def extract_text_from_mixed_content(self, content: List[Dict[str, Any]]) -> str:
        """从混合内容中提取文本
        
        Args:
            content: 混合内容列表
            
        Returns:
            str: 提取的文本内容
        """
        text_parts = []
        
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "image":
                    text_parts.append("[图像内容]")
        
        return " ".join(text_parts)