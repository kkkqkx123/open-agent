"""具体消息类型实现

实现 HumanMessage, AIMessage, SystemMessage, ToolMessage 等具体类型。
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base import BaseMessage
from src.interfaces.messages import IBaseMessage


class HumanMessage(BaseMessage):
    """人类消息
    
    表示来自用户的消息。
    """
    
    @property
    def type(self) -> str:
        """获取消息类型"""
        return "human"
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs: Any) -> None:
        """初始化人类消息"""
        super().__init__(content=content, **kwargs)
    
    def has_tool_calls(self) -> bool:
        """检查是否包含工具调用"""
        # HumanMessage 不包含工具调用
        return False
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """获取所有工具调用（包括无效的）"""
        # HumanMessage 不包含工具调用
        return []
    
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取有效的工具调用"""
        # HumanMessage 不包含工具调用
        return []
    
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取无效的工具调用"""
        # HumanMessage 不包含工具调用
        return []
    
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """添加工具调用"""
        # HumanMessage 不能添加工具调用
        raise NotImplementedError("HumanMessage cannot add tool calls")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanMessage":
        """从字典创建实例"""
        # 处理时间戳
        timestamp = datetime.now()
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        return cls(
            content=data["content"],
            additional_kwargs=data.get("additional_kwargs", {}),
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id"),
            timestamp=timestamp
        )


class AIMessage(BaseMessage):
    """AI消息
    
    表示来自AI助手的消息。
    """
    
    @property
    def type(self) -> str:
        """获取消息类型"""
        return "ai"
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs: Any) -> None:
        """初始化AI消息"""
        self.tool_calls = kwargs.pop("tool_calls", None)
        self.invalid_tool_calls = kwargs.pop("invalid_tool_calls", None)
        
        super().__init__(content=content, **kwargs)
        
        # 不再同步到 additional_kwargs，使用统一的接口方法访问
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIMessage":
        """从字典创建实例"""
        # 处理时间戳
        timestamp = datetime.now()
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        # 提取工具调用信息
        # 直接从字典中提取工具调用信息
        tool_calls = data.get("tool_calls", None)
        invalid_tool_calls = data.get("invalid_tool_calls", None)
        additional_kwargs = data.get("additional_kwargs", {})
        
        return cls(
            content=data["content"],
            additional_kwargs=additional_kwargs,
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id"),
            timestamp=timestamp,
            tool_calls=tool_calls,
            invalid_tool_calls=invalid_tool_calls
        )
    
    def has_tool_calls(self) -> bool:
        """检查是否包含工具调用"""
        return bool(self.tool_calls or self.invalid_tool_calls)
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """获取所有工具调用（包括无效的）"""
        all_calls = []
        if self.tool_calls:
            all_calls.extend(self.tool_calls)
        if self.invalid_tool_calls:
            all_calls.extend(self.invalid_tool_calls)
        return all_calls
    
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取有效的工具调用"""
        return self.tool_calls or []
    
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取无效的工具调用"""
        return self.invalid_tool_calls or []
    
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """添加工具调用"""
        if not self.tool_calls:
            self.tool_calls = []
        self.tool_calls.append(tool_call)


class SystemMessage(BaseMessage):
    """系统消息
    
    表示系统级别的消息，通常用于设置AI行为。
    """
    
    @property
    def type(self) -> str:
        """获取消息类型"""
        return "system"
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs: Any) -> None:
        """初始化系统消息"""
        super().__init__(content=content, **kwargs)
    
    def has_tool_calls(self) -> bool:
        """检查是否包含工具调用"""
        # SystemMessage 不包含工具调用
        return False
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """获取所有工具调用（包括无效的）"""
        # SystemMessage 不包含工具调用
        return []
    
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取有效的工具调用"""
        # SystemMessage 不包含工具调用
        return []
    
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取无效的工具调用"""
        # SystemMessage 不包含工具调用
        return []
    
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """添加工具调用"""
        # SystemMessage 不能添加工具调用
        raise NotImplementedError("SystemMessage cannot add tool calls")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemMessage":
        """从字典创建实例"""
        # 处理时间戳
        timestamp = datetime.now()
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        return cls(
            content=data["content"],
            additional_kwargs=data.get("additional_kwargs", {}),
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id"),
            timestamp=timestamp
        )


class ToolMessage(BaseMessage):
    """工具消息
    
    表示工具执行结果的消息。
    """
    
    @property
    def type(self) -> str:
        """获取消息类型"""
        return "tool"
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], tool_call_id: str, **kwargs: Any) -> None:
        """初始化工具消息"""
        self.tool_call_id = tool_call_id
        super().__init__(content=content, **kwargs)
    
    def has_tool_calls(self) -> bool:
        """检查是否包含工具调用"""
        # ToolMessage 是工具执行结果，不包含工具调用
        return False
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """获取所有工具调用（包括无效的）"""
        # ToolMessage 是工具执行结果，不包含工具调用
        return []
    
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取有效的工具调用"""
        # ToolMessage 是工具执行结果，不包含工具调用
        return []
    
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        """获取无效的工具调用"""
        # ToolMessage 是工具执行结果，不包含工具调用
        return []
    
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """添加工具调用"""
        # ToolMessage 是工具执行结果，不能添加工具调用
        raise NotImplementedError("ToolMessage cannot add tool calls")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolMessage":
        """从字典创建实例"""
        # 处理时间戳
        timestamp = datetime.now()
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        # 提取 tool_call_id
        tool_call_id = data.get("tool_call_id")
        if not tool_call_id:
            # 尝试从 additional_kwargs 中获取
            tool_call_id = data.get("additional_kwargs", {}).get("tool_call_id")
        
        if not tool_call_id:
            raise ValueError("ToolMessage requires tool_call_id")
        
        # 获取 additional_kwargs
        additional_kwargs = data.get("additional_kwargs", {})
        
        return cls(
            content=data["content"],
            tool_call_id=tool_call_id,
            additional_kwargs=additional_kwargs,
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id"),
            timestamp=timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        result = super().to_dict()
        result["tool_call_id"] = self.tool_call_id
        return result
    
    def copy(self, **kwargs: Any) -> "ToolMessage":
        """创建消息副本，允许覆盖属性"""
        current_data = self.to_dict()
        current_data.update(kwargs)
        return self.from_dict(current_data)


# 消息类型映射
MESSAGE_TYPE_MAP = {
    "human": HumanMessage,
    "ai": AIMessage,
    "system": SystemMessage,
    "tool": ToolMessage
}


def create_message_from_dict(data: Dict[str, Any]) -> BaseMessage:
    """从字典创建适当类型的消息"""
    message_type = data.get("type", "human")
    message_class = MESSAGE_TYPE_MAP.get(message_type, HumanMessage)
    
    if message_class is ToolMessage:
        # ToolMessage 需要特殊处理
        return ToolMessage.from_dict(data)
    elif message_class is HumanMessage:
        return HumanMessage.from_dict(data)
    elif message_class is AIMessage:
        return AIMessage.from_dict(data)
    elif message_class is SystemMessage:
        return SystemMessage.from_dict(data)
    else:
        return HumanMessage.from_dict(data)


def get_message_type(message: BaseMessage) -> str:
    """获取消息类型"""
    return message.type


def is_human_message(message: Union[BaseMessage, IBaseMessage]) -> bool:
    """检查是否为人类消息"""
    return isinstance(message, HumanMessage)


def is_ai_message(message: Union[BaseMessage, IBaseMessage]) -> bool:
    """检查是否为AI消息"""
    return isinstance(message, AIMessage)


def is_system_message(message: Union[BaseMessage, IBaseMessage]) -> bool:
    """检查是否为系统消息"""
    return isinstance(message, SystemMessage)


def is_tool_message(message: Union[BaseMessage, IBaseMessage]) -> bool:
    """检查是否为工具消息"""
    return isinstance(message, ToolMessage)
