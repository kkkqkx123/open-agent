"""
通用内容处理器

提供各种内容类型的处理功能，包括文本、图像和混合内容。
"""

import base64
import mimetypes
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional, Protocol
from dataclasses import dataclass

from src.services.logger.injection import get_logger


@dataclass
class ContentProcessingResult:
    """内容处理结果"""
    
    processed_content: Any
    metadata: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    
    def is_successful(self) -> bool:
        """检查处理是否成功"""
        return len(self.errors) == 0
    
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return len(self.warnings) > 0


class IContentProcessor(Protocol):
    """内容处理器接口"""
    
    def process(self, content: Any, **kwargs: Any) -> ContentProcessingResult:
        """处理内容"""
        ...
    
    def validate(self, content: Any, **kwargs: Any) -> List[str]:
        """验证内容"""
        ...
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型"""
        ...


class BaseContentProcessor(ABC):
    """基础内容处理器
    
    提供内容处理的通用基础实现。
    """
    
    def __init__(self, name: str):
        """初始化基础内容处理器
        
        Args:
            name: 处理器名称
        """
        self.name = name
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def process(self, content: Any, **kwargs: Any) -> ContentProcessingResult:
        """处理内容
        
        Args:
            content: 输入内容
            **kwargs: 处理参数
            
        Returns:
            ContentProcessingResult: 处理结果
        """
        pass
    
    @abstractmethod
    def validate(self, content: Any, **kwargs: Any) -> List[str]:
        """验证内容
        
        Args:
            content: 输入内容
            **kwargs: 验证参数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型
        
        Returns:
            List[str]: 支持的内容类型列表
        """
        pass
    
    def _create_result(self, processed_content: Any, metadata: Optional[Dict[str, Any]] = None,
                      errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None) -> ContentProcessingResult:
        """创建处理结果
        
        Args:
            processed_content: 处理后的内容
            metadata: 元数据
            errors: 错误列表
            warnings: 警告列表
            
        Returns:
            ContentProcessingResult: 处理结果
        """
        return ContentProcessingResult(
            processed_content=processed_content,
            metadata=metadata or {},
            errors=errors or [],
            warnings=warnings or []
        )


class TextProcessor(BaseContentProcessor):
    """文本内容处理器"""
    
    def __init__(self):
        """初始化文本处理器"""
        super().__init__("TextProcessor")
    
    def process(self, content: Any, **kwargs: Any) -> ContentProcessingResult:
        """处理文本内容
        
        Args:
            content: 输入内容
            **kwargs: 处理参数
                - clean: 是否清理文本（默认True）
                - truncate: 是否截断文本（默认False）
                - max_length: 最大长度（默认1000）
                - suffix: 截断后缀（默认"..."）
                
        Returns:
            ContentProcessingResult: 处理结果
        """
        errors = self.validate(content, **kwargs)
        warnings = []
        
        if errors:
            return self._create_result(None, errors=errors)
        
        try:
            # 提取文本
            text = self._extract_text(content)
            
            # 清理文本
            clean = kwargs.get("clean", True)
            if clean:
                text = self._clean_text(text)
            
            # 截断文本
            truncate = kwargs.get("truncate", False)
            if truncate:
                max_length = kwargs.get("max_length", 1000)
                suffix = kwargs.get("suffix", "...")
                text = self._truncate_text(text, max_length, suffix)
            
            # 创建元数据
            metadata = {
                "original_type": type(content).__name__,
                "processed_length": len(text),
                "cleaned": clean,
                "truncated": truncate
            }
            
            return self._create_result(text, metadata=metadata, warnings=warnings)
            
        except Exception as e:
            error_msg = f"文本处理失败: {e}"
            self.logger.error(error_msg)
            return self._create_result(None, errors=[error_msg])
    
    def validate(self, content: Any, **kwargs: Any) -> List[str]:
        """验证文本内容
        
        Args:
            content: 输入内容
            **kwargs: 验证参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if content is None:
            errors.append("内容不能为None")
            return errors
        
        # 检查是否可以转换为文本
        try:
            text = self._extract_text(content)
            if not isinstance(text, str):
                errors.append("内容无法转换为文本")
        except Exception as e:
            errors.append(f"内容转换失败: {e}")
        
        return errors
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型
        
        Returns:
            List[str]: 支持的内容类型列表
        """
        return ["str", "dict", "list", "int", "float", "bool"]
    
    def _extract_text(self, content: Any) -> str:
        """提取文本内容
        
        Args:
            content: 输入内容
            
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
                        text_parts.append(str(item))
                else:
                    text_parts.append(str(item))
            return " ".join(text_parts)
        elif isinstance(content, dict):
            if "text" in content:
                return content["text"]
            else:
                return str(content)
        else:
            return str(content)
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not isinstance(text, str):
            text = str(text)
        
        # 移除多余的空白字符
        cleaned = " ".join(text.split())
        
        return cleaned
    
    def _truncate_text(self, text: str, max_length: int, suffix: str) -> str:
        """截断文本
        
        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后缀
            
        Returns:
            str: 截断后的文本
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix


class ImageProcessor(BaseContentProcessor):
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
    
    def __init__(self, max_size: Optional[int] = None):
        """初始化图像处理器
        
        Args:
            max_size: 最大图像大小限制（字节）
        """
        super().__init__("ImageProcessor")
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
    
    def process(self, content: Any, **kwargs: Any) -> ContentProcessingResult:
        """处理图像数据
        
        Args:
            content: 输入内容
            **kwargs: 处理参数
                - target_format: 目标格式（默认保持原格式）
                - quality: 图像质量（0-100，默认85）
                - resize: 是否调整大小（默认False）
                - max_width: 最大宽度（默认1024）
                - max_height: 最大高度（默认1024）
                
        Returns:
            ContentProcessingResult: 处理结果
        """
        errors = self.validate(content, **kwargs)
        warnings = []
        
        if errors:
            return self._create_result(None, errors=errors)
        
        try:
            # 处理图像数据
            if isinstance(content, dict):
                processed_image = self._process_image_dict(content, **kwargs)
            elif isinstance(content, str):
                processed_image = self._process_base64_image(content, **kwargs)
            elif isinstance(content, bytes):
                processed_image = self._process_bytes_image(content, **kwargs)
            else:
                raise ValueError(f"不支持的图像数据类型: {type(content)}")
            
            # 创建元数据
            metadata = {
                "original_type": type(content).__name__,
                "processed_format": processed_image["source"]["media_type"],
                "size_bytes": len(base64.b64decode(processed_image["source"]["data"]))
            }
            
            return self._create_result(processed_image, metadata=metadata, warnings=warnings)
            
        except Exception as e:
            error_msg = f"图像处理失败: {e}"
            self.logger.error(error_msg)
            return self._create_result(None, errors=[error_msg])
    
    def validate(self, content: Any, **kwargs: Any) -> List[str]:
        """验证图像数据
        
        Args:
            content: 输入内容
            **kwargs: 验证参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if content is None:
            errors.append("图像内容不能为None")
            return errors
        
        try:
            if isinstance(content, dict):
                errors.extend(self._validate_image_dict(content))
            elif isinstance(content, str):
                errors.extend(self._validate_base64_image(content))
            elif isinstance(content, bytes):
                errors.extend(self._validate_bytes_image(content))
            else:
                errors.append(f"不支持的图像数据类型: {type(content)}")
        except Exception as e:
            errors.append(f"图像验证失败: {e}")
        
        return errors
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型
        
        Returns:
            List[str]: 支持的内容类型列表
        """
        return ["dict", "str", "bytes"]
    
    def _process_image_dict(self, image_dict: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """处理字典格式的图像数据
        
        Args:
            image_dict: 图像字典
            **kwargs: 处理参数
            
        Returns:
            Dict[str, Any]: 处理后的图像数据
        """
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
    
    def _process_base64_image(self, base64_data: str, **kwargs: Any) -> Dict[str, Any]:
        """处理base64格式的图像数据
        
        Args:
            base64_data: base64数据
            **kwargs: 处理参数
            
        Returns:
            Dict[str, Any]: 处理后的图像数据
        """
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
    
    def _process_bytes_image(self, byte_data: bytes, **kwargs: Any) -> Dict[str, Any]:
        """处理字节数组格式的图像数据
        
        Args:
            byte_data: 字节数据
            **kwargs: 处理参数
            
        Returns:
            Dict[str, Any]: 处理后的图像数据
        """
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
        """检测图像格式
        
        Args:
            byte_data: 字节数据
            
        Returns:
            str: 图像格式
        """
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
    
    def _validate_image_dict(self, image_dict: Dict[str, Any]) -> List[str]:
        """验证图像字典
        
        Args:
            image_dict: 图像字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(image_dict, dict):
            errors.append("图像数据必须是字典")
            return errors
        
        if image_dict.get("type") != "image":
            errors.append("图像数据type字段必须是'image'")
        
        source = image_dict.get("source")
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
    
    def _validate_base64_image(self, base64_data: str) -> List[str]:
        """验证base64图像数据
        
        Args:
            base64_data: base64数据
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(base64_data, str):
            errors.append("base64数据必须是字符串")
            return errors
        
        try:
            decoded_data = base64.b64decode(base64_data)
            if len(decoded_data) > self.max_size:
                errors.append(f"图像大小超过限制: {len(decoded_data)} bytes")
        except Exception:
            errors.append("无效的base64编码")
        
        return errors
    
    def _validate_bytes_image(self, byte_data: bytes) -> List[str]:
        """验证字节数组图像数据
        
        Args:
            byte_data: 字节数据
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(byte_data, bytes):
            errors.append("图像数据必须是字节数组")
            return errors
        
        if len(byte_data) > self.max_size:
            errors.append(f"图像大小超过限制: {len(byte_data)} bytes")
        
        return errors


class MixedContentProcessor(BaseContentProcessor):
    """混合内容处理器"""
    
    def __init__(self):
        """初始化混合内容处理器"""
        super().__init__("MixedContentProcessor")
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
    
    def process(self, content: Any, **kwargs: Any) -> ContentProcessingResult:
        """处理混合内容
        
        Args:
            content: 输入内容
            **kwargs: 处理参数
                
        Returns:
            ContentProcessingResult: 处理结果
        """
        errors = self.validate(content, **kwargs)
        warnings = []
        
        if errors:
            return self._create_result(None, errors=errors)
        
        try:
            if not isinstance(content, list):
                # 将非列表内容转换为列表
                content = [content]
            
            processed_content = []
            metadata = {
                "original_type": type(content).__name__,
                "item_count": len(content),
                "processed_items": 0
            }
            
            for i, item in enumerate(content):
                if isinstance(item, str):
                    # 处理文本
                    result = self.text_processor.process(item, **kwargs)
                    if result.is_successful():
                        processed_content.append({
                            "type": "text",
                            "text": result.processed_content
                        })
                        metadata["processed_items"] += 1
                    else:
                        errors.extend([f"项目 {i}: {error}" for error in result.errors])
                        
                elif isinstance(item, dict):
                    # 处理字典内容
                    processed_item = self._process_dict_item(item, i, **kwargs)
                    if processed_item:
                        processed_content.append(processed_item)
                        metadata["processed_items"] += 1
                        
                else:
                    # 转换为文本
                    result = self.text_processor.process(str(item), **kwargs)
                    if result.is_successful():
                        processed_content.append({
                            "type": "text",
                            "text": result.processed_content
                        })
                        metadata["processed_items"] += 1
                    else:
                        errors.extend([f"项目 {i}: {error}" for error in result.errors])
            
            # 验证图像数量
            image_count = len([item for item in processed_content if item.get("type") == "image"])
            if image_count > 5:
                warnings.append(f"图像数量较多({image_count})，可能影响处理性能")
            
            return self._create_result(processed_content, metadata=metadata, warnings=warnings, errors=errors)
            
        except Exception as e:
            error_msg = f"混合内容处理失败: {e}"
            self.logger.error(error_msg)
            return self._create_result(None, errors=[error_msg])
    
    def validate(self, content: Any, **kwargs: Any) -> List[str]:
        """验证混合内容
        
        Args:
            content: 输入内容
            **kwargs: 验证参数
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if content is None:
            errors.append("内容不能为None")
            return errors
        
        if not isinstance(content, list):
            # 非列表内容可以转换为列表处理
            return errors
        
        if not content:
            errors.append("内容列表不能为空")
            return errors
        
        # 验证列表中的每个项目
        for i, item in enumerate(content):
            if isinstance(item, str):
                # 文本内容验证
                text_errors = self.text_processor.validate(item, **kwargs)
                for error in text_errors:
                    errors.append(f"项目 {i}: {error}")
            elif isinstance(item, dict):
                # 字典内容验证
                dict_errors = self._validate_dict_item(item, i)
                for error in dict_errors:
                    errors.append(f"项目 {i}: {error}")
            else:
                # 其他类型转换为文本
                text_errors = self.text_processor.validate(str(item), **kwargs)
                for error in text_errors:
                    errors.append(f"项目 {i}: {error}")
        
        return errors
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型
        
        Returns:
            List[str]: 支持的内容类型列表
        """
        return ["list", "str", "dict", "int", "float", "bool"]
    
    def _process_dict_item(self, item: Dict[str, Any], index: int, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """处理字典内容项
        
        Args:
            item: 字典项
            index: 项目索引
            **kwargs: 处理参数
            
        Returns:
            Optional[Dict[str, Any]]: 处理后的项目
        """
        content_type = item.get("type")
        
        if content_type == "text":
            result = self.text_processor.process(item.get("text", ""), **kwargs)
            if result.is_successful():
                return {
                    "type": "text",
                    "text": result.processed_content
                }
            else:
                self.logger.warning(f"处理文本项 {index} 失败: {result.errors}")
                return None
                
        elif content_type == "image":
            result = self.image_processor.process(item, **kwargs)
            if result.is_successful():
                return result.processed_content
            else:
                self.logger.warning(f"处理图像项 {index} 失败: {result.errors}")
                return None
        else:
            # 未知类型，转换为文本
            result = self.text_processor.process(str(item), **kwargs)
            if result.is_successful():
                return {
                    "type": "text",
                    "text": result.processed_content
                }
            else:
                self.logger.warning(f"处理未知类型项 {index} 失败: {result.errors}")
                return None
    
    def _validate_dict_item(self, item: Dict[str, Any], index: int) -> List[str]:
        """验证字典内容项
        
        Args:
            item: 字典项
            index: 项目索引
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(item, dict):
            errors.append(f"项目 {index} 必须是字典")
            return errors
        
        content_type = item.get("type")
        if not content_type:
            errors.append(f"项目 {index} 缺少type字段")
            return errors
        
        if content_type == "text":
            text_errors = self.text_processor.validate(item.get("text", ""))
            for error in text_errors:
                errors.append(f"项目 {index} 文本: {error}")
        elif content_type == "image":
            image_errors = self.image_processor.validate(item)
            for error in image_errors:
                errors.append(f"项目 {index} 图像: {error}")
        else:
            errors.append(f"项目 {index} 有不支持的类型: {content_type}")
        
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