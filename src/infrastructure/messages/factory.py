"""消息工厂实现

提供消息创建的统一接口。
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from src.interfaces.messages import IMessageFactory, IBaseMessage
from .types import HumanMessage, AIMessage, SystemMessage, ToolMessage


class MessageFactory(IMessageFactory):
    """消息工厂实现
    
    提供统一的消息创建接口，支持各种配置选项。
    """
    
    def __init__(self, default_metadata: Optional[Dict[str, Any]] = None):
        """初始化消息工厂
        
        Args:
            default_metadata: 默认元数据
        """
        self.default_metadata = default_metadata or {}
        self._message_counter = 0
    
    def create_human_message(self, content: str, **kwargs) -> IBaseMessage:
        """创建人类消息"""
        return self._create_message(HumanMessage, content, **kwargs)
    
    def create_ai_message(self, content: str, **kwargs) -> IBaseMessage:
        """创建AI消息"""
        return self._create_message(AIMessage, content, **kwargs)
    
    def create_system_message(self, content: str, **kwargs) -> IBaseMessage:
        """创建系统消息"""
        return self._create_message(SystemMessage, content, **kwargs)
    
    def create_tool_message(self, content: str, tool_call_id: str, **kwargs) -> IBaseMessage:
        """创建工具消息"""
        return self._create_message(ToolMessage, content, tool_call_id=tool_call_id, **kwargs)
    
    def create_message_from_type(self, message_type: str, content: str, **kwargs) -> IBaseMessage:
        """根据类型创建消息"""
        type_map = {
            "human": self.create_human_message,
            "user": self.create_human_message,
            "ai": self.create_ai_message,
            "assistant": self.create_ai_message,
            "system": self.create_system_message,
            "tool": self.create_tool_message
        }
        
        creator = type_map.get(message_type.lower())
        if not creator:
            raise ValueError(f"Unknown message type: {message_type}")
        
        if message_type.lower() == "tool":
            tool_call_id = kwargs.get("tool_call_id")
            if not tool_call_id:
                raise ValueError("Tool message requires tool_call_id")
            return creator(content, tool_call_id=tool_call_id, **kwargs)
        else:
            return creator(content, **kwargs)
    
    def create_message_with_id(self, message_type: str, content: str, message_id: str, **kwargs) -> IBaseMessage:
        """创建带ID的消息"""
        kwargs["id"] = message_id
        return self.create_message_from_type(message_type, content, **kwargs)
    
    def create_message_with_timestamp(self, message_type: str, content: str, timestamp: datetime, **kwargs) -> IBaseMessage:
        """创建带时间戳的消息"""
        kwargs["timestamp"] = timestamp
        return self.create_message_from_type(message_type, content, **kwargs)
    
    def create_conversation_pair(self, user_input: str, ai_response: str, **kwargs) -> tuple[IBaseMessage, IBaseMessage]:
        """创建对话消息对"""
        human_msg = self.create_human_message(user_input, **kwargs)
        ai_msg = self.create_ai_message(ai_response, **kwargs)
        return human_msg, ai_msg
    
    def create_conversation_thread(self, messages: List[Dict[str, Any]]) -> List[IBaseMessage]:
        """创建对话线程"""
        thread = []
        for msg_data in messages:
            content = msg_data.get("content", "")
            msg_type = msg_data.get("type", "human")
            
            # 移除type和content，其他参数传递给创建方法
            kwargs = {k: v for k, v in msg_data.items() if k not in ["type", "content"]}
            
            message = self.create_message_from_type(msg_type, content, **kwargs)
            thread.append(message)
        
        return thread
    
    def clone_message(self, message: IBaseMessage, **overrides) -> IBaseMessage:
        """克隆消息并允许覆盖属性"""
        if isinstance(message, HumanMessage):
            return self._clone_message_type(HumanMessage, message, **overrides)
        elif isinstance(message, AIMessage):
            return self._clone_message_type(AIMessage, message, **overrides)
        elif isinstance(message, SystemMessage):
            return self._clone_message_type(SystemMessage, message, **overrides)
        elif isinstance(message, ToolMessage):
            return self._clone_message_type(ToolMessage, message, **overrides)
        else:
            # 默认克隆为人类消息
            return self._clone_message_type(HumanMessage, message, **overrides)
    
    def _create_message(self, message_class: type, content: str, **kwargs) -> IBaseMessage:
        """创建消息的通用方法"""
        # 合并默认元数据
        merged_metadata = self.default_metadata.copy()
        if "additional_kwargs" in kwargs:
            merged_metadata.update(kwargs["additional_kwargs"])
            kwargs["additional_kwargs"] = merged_metadata
        else:
            kwargs["additional_kwargs"] = merged_metadata
        
        # 自动生成ID（如果没有提供）
        if "id" not in kwargs:
            kwargs["id"] = self._generate_message_id()
        
        # 增加计数器
        self._message_counter += 1
        
        # 创建消息
        if message_class == ToolMessage:
            tool_call_id = kwargs.pop("tool_call_id", None)
            if not tool_call_id:
                raise ValueError("Tool message requires tool_call_id")
            return message_class(content, tool_call_id, **kwargs)
        else:
            return message_class(content, **kwargs)
    
    def _clone_message_type(self, message_class: type, message: IBaseMessage, **overrides) -> IBaseMessage:
        """克隆特定类型的消息"""
        # 获取原始消息的数据
        original_data = message.to_dict()
        
        # 应用覆盖
        original_data.update(overrides)
        
        # 重新创建消息
        if message_class == ToolMessage:
            return message_class.from_dict(original_data)
        else:
            return message_class.from_dict(original_data)
    
    def _generate_message_id(self) -> str:
        """生成消息ID"""
        return f"msg_{self._message_counter}_{uuid.uuid4().hex[:8]}"
    
    def set_default_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置默认元数据"""
        self.default_metadata = metadata.copy()
    
    def add_default_metadata(self, key: str, value: Any) -> None:
        """添加默认元数据项"""
        self.default_metadata[key] = value
    
    def remove_default_metadata(self, key: str) -> None:
        """移除默认元数据项"""
        self.default_metadata.pop(key, None)
    
    def get_default_metadata(self) -> Dict[str, Any]:
        """获取默认元数据的副本"""
        return self.default_metadata.copy()
    
    def reset_counter(self) -> None:
        """重置消息计数器"""
        self._message_counter = 0
    
    def get_message_count(self) -> int:
        """获取已创建的消息数量"""
        return self._message_counter


# 全局消息工厂实例
_global_factory: Optional[MessageFactory] = None


def get_message_factory() -> MessageFactory:
    """获取全局消息工厂实例
    
    Returns:
        MessageFactory: 消息工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = MessageFactory()
    return _global_factory


def create_human_message(content: str, **kwargs) -> IBaseMessage:
    """便捷函数：创建人类消息"""
    return get_message_factory().create_human_message(content, **kwargs)


def create_ai_message(content: str, **kwargs) -> IBaseMessage:
    """便捷函数：创建AI消息"""
    return get_message_factory().create_ai_message(content, **kwargs)


def create_system_message(content: str, **kwargs) -> IBaseMessage:
    """便捷函数：创建系统消息"""
    return get_message_factory().create_system_message(content, **kwargs)


def create_tool_message(content: str, tool_call_id: str, **kwargs) -> IBaseMessage:
    """便捷函数：创建工具消息"""
    return get_message_factory().create_tool_message(content, tool_call_id, **kwargs)


def create_message_from_type(message_type: str, content: str, **kwargs) -> IBaseMessage:
    """便捷函数：根据类型创建消息"""
    return get_message_factory().create_message_from_type(message_type, content, **kwargs)