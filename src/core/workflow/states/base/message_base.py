"""消息基类

提供消息管理的基础接口和实现。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Union

# Import LangChain message types - core dependency
from langchain_core.messages import (
    BaseMessage as LCBaseMessage,
    HumanMessage as LCHumanMessage,
    AIMessage as LCAIMessage,
    SystemMessage as LCSystemMessage,
    ToolMessage as LCToolMessage,
)


class MessageRole:
    """消息角色常量"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
    UNKNOWN = "unknown"


@dataclass
class BaseMessage:
    """消息基类"""
    content: str
    role: str = MessageRole.UNKNOWN
    
    def to_langchain(self) -> LCBaseMessage:
        """转换为LangChain消息格式
        
        Returns:
            LCBaseMessage: LangChain消息
        """
        if self.role == MessageRole.HUMAN:
            return LCHumanMessage(content=self.content)
        elif self.role == MessageRole.AI:
            return LCAIMessage(content=self.content)
        elif self.role == MessageRole.SYSTEM:
            return LCSystemMessage(content=self.content)
        elif self.role == MessageRole.TOOL:
            return LCToolMessage(content=self.content, tool_call_id="")
        else:
            return LCBaseMessage(content=self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "content": self.content,
            "role": self.role
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMessage":
        """从字典创建消息
        
        Args:
            data: 字典数据
            
        Returns:
            BaseMessage: 消息实例
        """
        return cls(
            content=data.get("content", ""),
            role=data.get("role", MessageRole.UNKNOWN)
        )


@dataclass
class HumanMessage(BaseMessage):
    """人类消息"""
    role: str = MessageRole.HUMAN

    def to_langchain(self) -> LCHumanMessage:
        """转换为LangChain HumanMessage格式
        
        Returns:
            LCHumanMessage: LangChain人类消息
        """
        return LCHumanMessage(content=self.content)


@dataclass
class AIMessage(BaseMessage):
    """AI消息"""
    role: str = MessageRole.AI

    def to_langchain(self) -> LCAIMessage:
        """转换为LangChain AIMessage格式
        
        Returns:
            LCAIMessage: LangChain AI消息
        """
        return LCAIMessage(content=self.content)


@dataclass
class SystemMessage(BaseMessage):
    """系统消息"""
    role: str = MessageRole.SYSTEM

    def to_langchain(self) -> LCSystemMessage:
        """转换为LangChain SystemMessage格式
        
        Returns:
            LCSystemMessage: LangChain系统消息
        """
        return LCSystemMessage(content=self.content)


@dataclass
class ToolMessage(BaseMessage):
    """工具消息"""
    role: str = MessageRole.TOOL
    tool_call_id: str = ""

    def to_langchain(self) -> LCToolMessage:
        """转换为LangChain ToolMessage格式
        
        Returns:
            LCToolMessage: LangChain工具消息
        """
        return LCToolMessage(content=self.content, tool_call_id=self.tool_call_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "content": self.content,
            "role": self.role,
            "tool_call_id": self.tool_call_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolMessage":
        """从字典创建消息
        
        Args:
            data: 字典数据
            
        Returns:
            ToolMessage: 工具消息实例
        """
        return cls(
            content=data.get("content", ""),
            tool_call_id=data.get("tool_call_id", "")
        )


class MessageManager:
    """消息管理器
    
    负责管理消息列表和相关操作。
    """
    
    def __init__(self) -> None:
        """初始化消息管理器"""
        self._messages: List[Union[BaseMessage, LCBaseMessage]] = []
    
    def add_message(self, message: Union[BaseMessage, LCBaseMessage]) -> None:
        """添加消息
        
        Args:
            message: 消息
        """
        self._messages.append(message)
    
    def get_messages(self) -> List[Union[BaseMessage, LCBaseMessage]]:
        """获取所有消息
        
        Returns:
            List[Union[BaseMessage, LCBaseMessage]]: 消息列表
        """
        return self._messages.copy()
    
    def get_last_message(self) -> Union[BaseMessage, LCBaseMessage, None]:
        """获取最后一条消息
        
        Returns:
            Union[BaseMessage, LCBaseMessage, None]: 最后一条消息
        """
        return self._messages[-1] if self._messages else None
    
    def clear_messages(self) -> None:
        """清除所有消息"""
        self._messages.clear()
    
    def get_messages_by_role(self, role: str) -> List[Union[BaseMessage, LCBaseMessage]]:
        """根据角色获取消息
        
        Args:
            role: 消息角色
            
        Returns:
            List[Union[BaseMessage, LCBaseMessage]]: 消息列表
        """
        filtered_messages: List[Union[BaseMessage, LCBaseMessage]] = []
        for message in self._messages:
            if isinstance(message, BaseMessage):
                if message.role == role:
                    filtered_messages.append(message)
            elif hasattr(message, 'type'):
                if message.type == role:
                    filtered_messages.append(message)
        return filtered_messages
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典
        
        Returns:
            List[Dict[str, Any]]: 消息字典列表
        """
        messages_data = []
        for msg in self._messages:
            if isinstance(msg, BaseMessage):
                # 自定义消息类型
                messages_data.append(msg.to_dict())
            elif hasattr(msg, 'content'):
                # LangChain消息类型
                messages_data.append({
                    "content": msg.content,
                    "role": getattr(msg, 'type', 'unknown')
                })
            else:
                # 未知消息类型
                messages_data.append({
                    "content": str(msg),
                    "role": "unknown"
                })
        return messages_data
    
    def from_dict(self, messages_data: List[Dict[str, Any]]) -> None:
        """从字典加载消息
        
        Args:
            messages_data: 消息字典列表
        """
        self._messages.clear()
        for msg_data in messages_data:
            role = msg_data.get("role", "unknown")
            content = msg_data.get("content", "")
            
            if role == MessageRole.HUMAN:
                self._messages.append(HumanMessage(content=content))
            elif role == MessageRole.AI:
                self._messages.append(AIMessage(content=content))
            elif role == MessageRole.SYSTEM:
                self._messages.append(SystemMessage(content=content))
            elif role == MessageRole.TOOL:
                tool_call_id = msg_data.get("tool_call_id", "")
                self._messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
            else:
                self._messages.append(BaseMessage(content=content, role=role))