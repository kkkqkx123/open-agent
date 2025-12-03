"""Anthropic多模态内容处理工具

专门处理Anthropic API的多模态内容，包括图像、文本等。
"""

from typing import Dict, Any, List, Union, Optional
import base64
import mimetypes
from src.services.logger import get_logger
from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils


class AnthropicMultimodalUtils(BaseMultimodalUtils):
    """Anthropic多模态内容处理工具类"""
    
    # 支持的图像格式
    SUPPORTED_IMAGE_FORMATS = {
        "image/jpeg",
        "image/png", 
        "image/gif",
        "image/webp"
    }
    
    # 图像大小限制（5MB）
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    
    def __init__(self) -> None:
        """初始化多模态工具"""
        super().__init__()
    
    def process_content_to_provider_format(
        self, 
        content: Union[str, List[Union[str, Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        """将内容转换为Anthropic格式
        
        Args:
            content: 输入内容，可以是字符串或列表
            
        Returns:
            List[Dict[str, Any]]: Anthropic格式的内容列表
        """
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        elif isinstance(content, list):
            return self._process_content_list(content)
        else:
            return [{"type": "text", "text": str(content)}]
    
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从Anthropic格式内容中提取文本
        
        Args:
            content: Anthropic格式的内容列表
            
        Returns:
            str: 提取的文本内容
        """
        return self._extract_text_from_content_list(content)
    
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Anthropic格式内容
        
        Args:
            content: Anthropic格式的内容列表
            
        Returns:
            List[str]: 验证错误列表
        """
        return self._validate_anthropic_content(content)
    
    def _process_content_list(self, content_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理内容列表"""
        anthropic_content = []
        
        for item in content_list:
            if isinstance(item, str):
                anthropic_content.append({"type": "text", "text": item})
            elif isinstance(item, dict):
                processed_item = self._process_dict_content(item)
                if processed_item:
                    anthropic_content.append(processed_item)
            else:
                anthropic_content.append({"type": "text", "text": str(item)})
        
        return anthropic_content
    
    def _process_dict_content(self, content_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理字典内容"""
        content_type = content_dict.get("type")
        
        if content_type == "text":
            return {
                "type": "text",
                "text": content_dict.get("text", "")
            }
        elif content_type == "image":
            return self._process_image_content(content_dict)
        else:
            # 尝试将其他类型转换为文本
            return {
                "type": "text", 
                "text": str(content_dict)
            }
    
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
                "type": "image",
                "source": {
                    "type": source.get("type", "base64"),
                    "media_type": media_type,
                    "data": image_data
                }
            }
        except Exception as e:
            self.logger.error(f"处理图像内容失败: {e}")
            return None
    
    def _validate_anthropic_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Anthropic格式内容"""
        errors = []
        image_count = 0
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"内容项 {i} 必须是字典")
                continue
            
            content_type = item.get("type")
            if not content_type:
                errors.append(f"内容项 {i} 缺少type字段")
                continue
            
            if content_type == "text":
                text = item.get("text")
                if not isinstance(text, str):
                    errors.append(f"文本内容项 {i} 的text字段必须是字符串")
            elif content_type == "image":
                image_count += 1
                image_errors = self._validate_image_content(item, i)
                errors.extend(image_errors)
            else:
                errors.append(f"内容项 {i} 有不支持的类型: {content_type}")
        
        # 检查图像数量限制
        if image_count > 5:
            errors.append("每条消息最多支持5张图像")
        
        return errors
    
    def _validate_image_content(self, image_item: Dict[str, Any], index: int) -> List[str]:
        """验证图像内容"""
        errors = []
        
        source = image_item.get("source")
        if not isinstance(source, dict):
            errors.append(f"图像项 {index} 的source字段必须是字典")
            return errors
        
        # 检查类型
        source_type = source.get("type")
        if source_type != "base64":
            errors.append(f"图像项 {index} 只支持base64类型")
        
        # 检查媒体类型
        media_type = source.get("media_type")
        if not media_type:
            errors.append(f"图像项 {index} 缺少media_type")
        elif media_type not in self.SUPPORTED_IMAGE_FORMATS:
            errors.append(f"图像项 {index} 有不支持的媒体类型: {media_type}")
        
        # 检查数据
        data = source.get("data")
        if not isinstance(data, str):
            errors.append(f"图像项 {index} 的data字段必须是字符串")
        else:
            try:
                decoded_data = base64.b64decode(data)
                if len(decoded_data) > self.MAX_IMAGE_SIZE:
                    errors.append(f"图像项 {index} 大小超过5MB限制")
            except Exception:
                errors.append(f"图像项 {index} 的data字段不是有效的base64编码")
        
        return errors
    
    def _create_text_content(self, text: str) -> Dict[str, Any]:
        """创建文本内容"""
        return {"type": "text", "text": text}
    
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
    
    def create_image_content(
        self, 
        image_path: str, 
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件路径创建图像内容
        
        Args:
            image_path: 图像文件路径
            media_type: 媒体类型，如果不提供则自动检测
            
        Returns:
            Dict[str, Any]: 图像内容字典
        """
        try:
            # 自动检测媒体类型
            if not media_type:
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
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": encoded_data
                }
            }
        except Exception as e:
            self.logger.error(f"创建图像内容失败: {e}")
            raise
    
    def extract_text_from_anthropic_content(self, content: List[Dict[str, Any]]) -> str:
        """从Anthropic格式内容中提取文本（兼容性方法）"""
        return self.extract_text_from_provider_content(content)
    
    def validate_anthropic_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证Anthropic格式内容（兼容性方法）"""
        return self.validate_provider_content(content)