"""基础消息实现

实现 BaseMessage 类，提供消息的核心功能。
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from src.interfaces.messages import IBaseMessage


class BaseMessage(IBaseMessage):
    """基础消息实现
    
    提供消息的核心功能，支持序列化和反序列化。
    """
    
    def __init__(
        self,
        content: Union[str, List[Union[str, Dict[str, Any]]]],
        name: Optional[str] = None,
        id: Optional[str] = None,
        additional_kwargs: Optional[Dict[str, Any]] = None,
        response_metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """初始化基础消息"""
        self._content = content
        self._name = name
        self._id = id
        self._additional_kwargs = additional_kwargs or {}
        self._response_metadata = response_metadata or {}
        self._timestamp = timestamp or datetime.now()
        
        # 确保content是有效类型
        if not isinstance(self._content, (str, list)):
            self._content = str(self._content)
        
        # 如果是列表，确保元素类型正确
        if isinstance(self._content, list):
            validated_content = []
            for item in self._content:
                if isinstance(item, (str, dict)):
                    validated_content.append(item)
                else:
                    validated_content.append(str(item))
            self._content = validated_content
    
    @property
    def content(self) -> Union[str, List[Union[str, Dict[str, Any]]]]:
        """获取消息内容"""
        return self._content
    
    @property
    def name(self) -> Optional[str]:
        """获取消息名称"""
        return self._name
    
    @property
    def id(self) -> Optional[str]:
        """获取消息ID"""
        return self._id
    
    @property
    def additional_kwargs(self) -> Dict[str, Any]:
        """获取额外参数"""
        return self._additional_kwargs
    
    @property
    def response_metadata(self) -> Dict[str, Any]:
        """获取响应元数据"""
        return self._response_metadata
    
    @property
    def timestamp(self) -> datetime:
        """获取消息时间戳"""
        return self._timestamp
    
    @property
    def type(self) -> str:
        """获取消息类型（由子类实现）"""
        raise NotImplementedError("Subclasses must implement type property")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        result = {
            "content": self.content,
            "type": self.type,
            "additional_kwargs": self.additional_kwargs,
            "response_metadata": self.response_metadata,
            "name": self.name,
            "id": self.id,
            "timestamp": self.timestamp.isoformat()
        }
        
        # 移除None值
        return {k: v for k, v in result.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMessage":
        """从字典创建实例"""
        # 子类必须实现具体的 from_dict 逻辑
        raise NotImplementedError("Subclasses must implement from_dict")
    
    def copy(self, **kwargs: Any) -> "BaseMessage":
        """创建消息副本，允许覆盖属性"""
        # 获取当前实例的所有字段
        current_data = self.to_dict()
        
        # 更新字段
        current_data.update(kwargs)
        
        # 从字典创建新实例
        return self.from_dict(current_data)
    
    def get_text_content(self) -> str:
        """获取纯文本内容"""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            text_parts = []
            for item in self.content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    # 提取字典中的文本内容
                    if "text" in item:
                        text_parts.append(item["text"])
                    else:
                        text_parts.append(json.dumps(item))
            return " ".join(text_parts)
        else:
            return str(self.content)
    
    def has_tool_calls(self) -> bool:
        """检查是否包含工具调用"""
        # 基础实现：子类可以重写
        return False
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """获取所有工具调用（包括无效的）"""
        # 基础实现：子类可以重写
        return []
    
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取有效的工具调用"""
        # 基础实现：子类可以重写
        return []
    
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取无效的工具调用"""
        # 基础实现：子类可以重写
        return []
    
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """添加工具调用"""
        # 基础实现：子类可以重写
        pass
    
    def get_additional_kwarg(self, key: str, default: Any = None) -> Any:
        """获取额外参数"""
        return self.additional_kwargs.get(key, default)
    
    def set_additional_kwarg(self, key: str, value: Any) -> None:
        """设置额外参数"""
        self.additional_kwargs[key] = value
    
    def get_response_metadata(self, key: str, default: Any = None) -> Any:
        """获取响应元数据"""
        return self.response_metadata.get(key, default)
    
    def set_response_metadata(self, key: str, value: Any) -> None:
        """设置响应元数据"""
        self.response_metadata[key] = value
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(content={self.get_text_content()[:100]}...)"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (
            f"{self.__class__.__name__}("
            f"type={self.type}, "
            f"content={self.get_text_content()[:50]}..., "
            f"id={self.id}, "
            f"name={self.name}"
            f")"
        )
    
    def __eq__(self, other: object) -> bool:
        """相等性比较"""
        if not isinstance(other, BaseMessage):
            return False
        
        return (
            self.content == other.content and
            self.type == other.type and
            self.additional_kwargs == other.additional_kwargs and
            self.name == other.name and
            self.id == other.id
        )
    
    def __hash__(self) -> int:
        """哈希值计算"""
        # 使用内容的哈希值
        content_str = json.dumps(self.content, sort_keys=True) if isinstance(self.content, list) else self.content
        kwargs_str = json.dumps(self.additional_kwargs, sort_keys=True)
        
        return hash((
            content_str,
            self.type,
            kwargs_str,
            self.name,
            self.id
        ))
