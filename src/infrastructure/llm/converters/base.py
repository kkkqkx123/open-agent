"""
基础类和接口定义

提供转换器系统的核心抽象和基础实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Sequence
from dataclasses import dataclass
from enum import Enum
from src.interfaces.messages import IBaseMessage


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ConversionContext:
    """转换上下文"""
    provider_name: str
    conversion_type: str
    parameters: Dict[str, Any]
    errors: List[str] = None  # type: ignore
    warnings: List[str] = None  # type: ignore
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数"""
        return self.parameters.get(key, default)


class IProvider(ABC):
    """提供商接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取提供商名称"""
        pass
    
    @abstractmethod
    def convert_request(self, messages: Sequence[Union[Any, "IBaseMessage"]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求格式"""
        pass
    
    @abstractmethod
    def convert_response(self, response: Dict[str, Any]) -> Any:
        """转换响应格式"""
        pass
    
    @abstractmethod
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> Any:
        """转换流式响应格式"""
        pass
    
    @abstractmethod
    def validate_request(self, messages: Sequence[Union[Any, "IBaseMessage"]], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass


class IConverter(ABC):
    """转换器接口"""
    
    @abstractmethod
    def can_convert(self, source_type: type, target_type: type) -> bool:
        """检查是否可以转换"""
        pass
    
    @abstractmethod
    def convert(self, source: Any, context: ConversionContext) -> Any:
        """执行转换"""
        pass


class BaseProvider(IProvider):
    """提供商基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = self._get_logger()
    
    def _get_logger(self):
        """获取日志器"""
        try:
            from src.interfaces.dependency_injection import get_logger
            return get_logger(__name__)
        except ImportError:
            import logging
            return logging.getLogger(__name__)
    
    def get_name(self) -> str:
        """获取提供商名称"""
        return self.name
    
    def validate_request(self, messages: Sequence[Union[Any, "IBaseMessage"]], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        errors = []
        
        if not messages:
            errors.append("消息列表不能为空")
        
        if not isinstance(parameters, dict):
            errors.append("参数必须是字典格式")
        
        return errors
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [self.get_default_model()]
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return "default"
    
    def _create_context(self, conversion_type: str, parameters: Dict[str, Any]) -> ConversionContext:
        """创建转换上下文"""
        return ConversionContext(
            provider_name=self.name,
            conversion_type=conversion_type,
            parameters=parameters
        )
    
    def _process_content(self, content: Union[str, List[Union[str, Dict[str, Any]]]], context: Optional["ConversionContext"]) -> List[Dict[str, Any]]:
        """处理内容为统一格式"""
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        elif isinstance(content, list):
            processed = []
            for item in content:
                if isinstance(item, str):
                    processed.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    processed.append(item)
            return processed
        else:
            return [{"type": "text", "text": str(content)}]
    
    def _extract_text_from_content(self, content: List[Dict[str, Any]]) -> str:
        """从内容中提取文本"""
        text_parts = []
        for item in content:
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return " ".join(text_parts)
    
    def _validate_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证内容格式"""
        errors = []
        
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
            
            if content_type == "text" and "text" not in item:
                errors.append(f"文本内容项 {i} 缺少text字段")
            elif content_type == "image" and "source" not in item:
                errors.append(f"图像内容项 {i} 缺少source字段")
        
        return errors