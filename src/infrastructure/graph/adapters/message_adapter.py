"""消息适配器

负责在不同层级消息对象之间进行转换。
"""

from typing import Dict, Any, List, Optional, Union
import logging

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

logger = logging.getLogger(__name__)


class MessageAdapter:
    """消息适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def to_langchain_message(self, message: Any) -> BaseMessage:
        """将任意消息格式转换为LangChain消息
        
        Args:
            message: 输入消息
            
        Returns:
            BaseMessage: LangChain消息
        """
        try:
            if isinstance(message, BaseMessage):
                # 已经是LangChain消息
                return message
            elif isinstance(message, dict):
                # 字典格式
                return self._dict_to_langchain(message)
            elif hasattr(message, 'content') and hasattr(message, 'role'):
                # 对象格式
                return self._object_to_langchain(message)
            else:
                # 其他格式，转换为人类消息
                return HumanMessage(content=str(message))
        except Exception as e:
            self.logger.error(f"消息转换失败: {e}")
            return HumanMessage(content=str(message))
    
    def from_langchain_message(self, message: BaseMessage) -> Dict[str, Any]:
        """将LangChain消息转换为字典格式
        
        Args:
            message: LangChain消息
            
        Returns:
            Dict[str, Any]: 字典格式消息
        """
        try:
            result = {
                "content": message.content,
                "type": self._get_message_type(message)
            }
            
            # 添加特定类型的额外信息
            if isinstance(message, ToolMessage):
                result["tool_call_id"] = message.tool_call_id
            
            # 添加额外属性
            if hasattr(message, 'additional_kwargs'):
                result["additional_kwargs"] = message.additional_kwargs
            
            return result
        except Exception as e:
            self.logger.error(f"消息转换失败: {e}")
            return {
                "content": str(message),
                "type": "human"
            }
    
    def convert_message_list(self, messages: List[Any]) -> List[BaseMessage]:
        """批量转换消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            List[BaseMessage]: LangChain消息列表
        """
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.to_langchain_message(msg))
        return converted_messages
    
    def _dict_to_langchain(self, message_dict: Dict[str, Any]) -> BaseMessage:
        """将字典转换为LangChain消息"""
        content = message_dict.get("content", "")
        role = message_dict.get("role", "human")
        
        if role == "human":
            return HumanMessage(content=content)
        elif role == "ai":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        elif role == "tool":
            tool_call_id = message_dict.get("tool_call_id", "")
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            # 默认为人类消息
            return HumanMessage(content=content)
    
    def _object_to_langchain(self, message_obj: Any) -> BaseMessage:
        """将对象转换为LangChain消息"""
        content = getattr(message_obj, 'content', '')
        role = getattr(message_obj, 'role', 'human')
        
        if role == "human":
            return HumanMessage(content=content)
        elif role == "ai":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        elif role == "tool":
            tool_call_id = getattr(message_obj, 'tool_call_id', '')
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            # 默认为人类消息
            return HumanMessage(content=content)
    
    def _get_message_type(self, message: BaseMessage) -> str:
        """获取消息类型"""
        if isinstance(message, HumanMessage):
            return "human"
        elif isinstance(message, AIMessage):
            return "ai"
        elif isinstance(message, SystemMessage):
            return "system"
        elif isinstance(message, ToolMessage):
            return "tool"
        else:
            return "unknown"


# 全局消息适配器实例
_global_adapter: Optional[MessageAdapter] = None


def get_message_adapter() -> MessageAdapter:
    """获取全局消息适配器实例
    
    Returns:
        MessageAdapter: 消息适配器实例
    """
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = MessageAdapter()
    return _global_adapter