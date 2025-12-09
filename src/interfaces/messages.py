"""消息系统接口定义

定义消息系统的核心抽象，遵循领域层接口设计原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

class IBaseMessage(ABC):
    """基础消息接口
    
    定义所有消息类型的核心契约，这是领域层的核心抽象。
    """
    
    @property
    @abstractmethod
    def content(self) -> Union[str, List[Union[str, Dict[str, Any]]]]:
        """获取消息内容"""
        pass
    
    @property
    @abstractmethod
    def type(self) -> str:
        """获取消息类型"""
        pass
    
    @property
    @abstractmethod
    def additional_kwargs(self) -> Dict[str, Any]:
        """获取额外参数"""
        pass
    
    @property
    @abstractmethod
    def response_metadata(self) -> Dict[str, Any]:
        """获取响应元数据"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> Optional[str]:
        """获取消息名称"""
        pass
    
    @property
    @abstractmethod
    def id(self) -> Optional[str]:
        """获取消息ID"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """获取消息时间戳"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        pass
    
    @abstractmethod
    def get_text_content(self) -> str:
        """获取纯文本内容"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IBaseMessage":
        """从字典创建实例"""
        pass
    
    @abstractmethod
    def has_tool_calls(self) -> bool:
        """检查是否包含工具调用"""
        pass
    
    @abstractmethod
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """获取所有工具调用（包括无效的）"""
        pass
    
    @abstractmethod
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取有效的工具调用"""
        pass
    
    @abstractmethod
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取无效的工具调用"""
        pass
    
    @abstractmethod
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """添加工具调用"""
        pass


class IMessageConverter(ABC):
    """消息转换器接口
    
    定义不同消息格式之间的转换契约。
    """
    
    @abstractmethod
    def to_base_message(self, message: Any) -> IBaseMessage:
        """转换为标准消息格式"""
        pass
    
    @abstractmethod
    def from_base_message(self, message: IBaseMessage) -> Any:
        """从标准消息格式转换"""
        pass
    
    @abstractmethod
    def convert_message_list(self, messages: List[Any]) -> List[IBaseMessage]:
        """批量转换消息列表为标准格式"""
        pass
    
    @abstractmethod
    def convert_from_base_list(self, messages: List[IBaseMessage]) -> List[Any]:
        """批量转换标准消息列表"""
        pass


class IMessageFactory(ABC):
    """消息工厂接口
    
    定义消息创建的契约。
    """
    
    @abstractmethod
    def create_human_message(self, content: str, **kwargs: Any) -> IBaseMessage:
        """创建人类消息"""
        pass
    
    @abstractmethod
    def create_ai_message(self, content: str, **kwargs: Any) -> IBaseMessage:
        """创建AI消息"""
        pass
    
    @abstractmethod
    def create_system_message(self, content: str, **kwargs: Any) -> IBaseMessage:
        """创建系统消息"""
        pass
    
    @abstractmethod
    def create_tool_message(self, content: str, tool_call_id: str, **kwargs: Any) -> IBaseMessage:
        """创建工具消息"""
        pass


class IMessageSerializer(ABC):
    """消息序列化接口
    
    定义消息序列化和反序列化的契约。
    """
    
    @abstractmethod
    def serialize(self, message: IBaseMessage) -> bytes:
        """序列化消息"""
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes) -> IBaseMessage:
        """反序列化消息"""
        pass
    
    @abstractmethod
    def serialize_list(self, messages: List[IBaseMessage]) -> bytes:
        """序列化消息列表"""
        pass
    
    @abstractmethod
    def deserialize_list(self, data: bytes) -> List[IBaseMessage]:
        """反序列化消息列表"""
        pass


class IMessageValidator(ABC):
    """消息验证器接口
    
    定义消息验证的契约。
    """
    
    @abstractmethod
    def validate(self, message: IBaseMessage) -> List[str]:
        """验证消息，返回错误列表"""
        pass
    
    @abstractmethod
    def is_valid(self, message: IBaseMessage) -> bool:
        """检查消息是否有效"""
        pass
    
    @abstractmethod
    def validate_content(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[str]:
        """验证消息内容"""
        pass