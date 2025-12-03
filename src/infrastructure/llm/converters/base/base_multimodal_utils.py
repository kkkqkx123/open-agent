"""多模态基础工具类

定义所有LLM提供商的多模态内容处理通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
from src.services.logger import get_logger


class BaseMultimodalUtils(ABC):
    """多模态基础工具类
    
    定义多模态内容处理的通用接口和基础功能。
    """
    
    def __init__(self) -> None:
        """初始化多模态工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def process_content_to_provider_format(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """将内容转换为提供商特定格式
        
        Args:
            content: 输入内容，可以是字符串或列表
            
        Returns:
            List[Dict[str, Any]]: 提供商格式的内容列表
        """
        pass
    
    @abstractmethod
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从提供商格式内容中提取文本
        
        Args:
            content: 提供商格式的内容列表
            
        Returns:
            str: 提取的文本内容
        """
        pass
    
    @abstractmethod
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证提供商格式内容
        
        Args:
            content: 提供商格式的内容列表
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    def _process_content_list(self, content_list: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理内容列表（通用方法）"""
        processed_content = []
        
        for item in content_list:
            if isinstance(item, str):
                processed_content.append(self._create_text_content(item))
            elif isinstance(item, dict):
                processed_item = self._process_dict_content(item)
                if processed_item:
                    processed_content.append(processed_item)
            else:
                # 尝试将其他类型转换为文本
                processed_content.append(self._create_text_content(str(item)))
        
        return processed_content
    
    def _create_text_content(self, text: str) -> Dict[str, Any]:
        """创建文本内容（基础实现，子类可重写）"""
        return {"type": "text", "text": text}
    
    def _process_dict_content(self, content_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理字典内容（基础实现，子类可重写）"""
        content_type = content_dict.get("type")
        
        if content_type == "text":
            return {
                "type": "text",
                "text": content_dict.get("text", "")
            }
        elif content_type == "image":
            return self._process_image_content(content_dict)
        else:
            # 未知类型，转换为文本
            return self._create_text_content(str(content_dict))
    
    def _process_image_content(self, image_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理图像内容（基础实现，子类应重写）"""
        # 基础实现，子类应该根据具体API格式重写
        source = image_item.get("source", {})
        if not source:
            self.logger.warning("图像内容缺少source字段")
            return None
        
        return {
            "type": "image",
            "source": source
        }
    
    def _extract_text_from_content_list(self, content: List[Dict[str, Any]]) -> str:
        """从内容列表中提取文本（通用方法）"""
        text_parts = []
        
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "image":
                    text_parts.append("[图像内容]")
        
        return " ".join(text_parts)
    
    def _validate_content_structure(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证内容结构（通用方法）"""
        errors = []
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        if not content:
            errors.append("内容列表不能为空")
            return errors
        
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"内容项 {i} 必须是字典")
                continue
            
            content_type = item.get("type")
            if not content_type:
                errors.append(f"内容项 {i} 缺少type字段")
                continue
            
            # 验证特定类型的内容
            type_errors = self._validate_content_item(item, i)
            errors.extend(type_errors)
        
        return errors
    
    def _validate_content_item(self, item: Dict[str, Any], index: int) -> List[str]:
        """验证单个内容项（基础实现，子类可重写）"""
        errors = []
        content_type = item.get("type")
        
        if content_type == "text":
            text = item.get("text")
            if not isinstance(text, str):
                errors.append(f"文本内容项 {index} 的text字段必须是字符串")
        elif content_type == "image":
            image_errors = self._validate_image_item(item, index)
            errors.extend(image_errors)
        else:
            errors.append(f"内容项 {index} 有不支持的类型: {content_type}")
        
        return errors
    
    def _validate_image_item(self, image_item: Dict[str, Any], index: int) -> List[str]:
        """验证图像项（基础实现，子类可重写）"""
        errors = []
        
        source = image_item.get("source")
        if not isinstance(source, dict):
            errors.append(f"图像项 {index} 的source字段必须是字典")
            return errors
        
        # 基础验证，子类可以添加更多特定验证
        if not source.get("data"):
            errors.append(f"图像项 {index} 的source缺少data字段")
        
        return errors
    
    def create_image_content(
        self, 
        image_path: str, 
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """从文件路径创建图像内容（通用方法）"""
        import base64
        import mimetypes
        
        try:
            # 自动检测媒体类型
            if not media_type:
                media_type, _ = mimetypes.guess_type(image_path)
                if not media_type:
                    media_type = "image/jpeg"  # 默认
            
            # 读取并编码图像
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # 检查大小限制（基础实现，子类可以重写）
            max_size = self._get_max_image_size()
            if len(image_data) > max_size:
                raise ValueError(f"图像大小超过限制: {len(image_data)} bytes")
            
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            
            return self._create_image_content_dict(media_type, encoded_data)
        except Exception as e:
            self.logger.error(f"创建图像内容失败: {e}")
            raise
    
    def _create_image_content_dict(self, media_type: str, encoded_data: str) -> Dict[str, Any]:
        """创建图像内容字典（基础实现，子类可重写）"""
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded_data
            }
        }
    
    def _get_max_image_size(self) -> int:
        """获取最大图像大小限制（基础实现，子类可重写）"""
        return 5 * 1024 * 1024  # 默认5MB
    
    def _get_supported_image_formats(self) -> set:
        """获取支持的图像格式（基础实现，子类可重写）"""
        return {"image/jpeg", "image/png", "image/gif", "image/webp"}