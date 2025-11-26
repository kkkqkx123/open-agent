"""消息转换器

负责在不同消息格式之间进行转换：
- LLMMessage <-> LangChain BaseMessage
- 字典格式消息 <-> LangChain BaseMessage
- 对象格式消息 <-> LangChain BaseMessage
"""

from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

from ..models import LLMMessage, MessageRole

logger = logging.getLogger(__name__)


class MessageConverter:
    """消息转换器
    
    提供在不同消息格式之间的双向转换。
    """
    
    def __init__(self):
        """初始化消息转换器"""
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
            elif isinstance(message, LLMMessage):
                # LLMMessage格式
                return self._llm_message_to_langchain(message)
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
    
    def from_langchain_message(self, message: BaseMessage) -> LLMMessage:
        """将LangChain消息转换为LLMMessage格式
        
        Args:
            message: LangChain消息
            
        Returns:
            LLMMessage: LLM消息
        """
        try:
            if isinstance(message, HumanMessage):
                role = MessageRole.USER
            elif isinstance(message, AIMessage):
                role = MessageRole.ASSISTANT
            elif isinstance(message, SystemMessage):
                role = MessageRole.SYSTEM
            elif isinstance(message, ToolMessage):
                role = MessageRole.TOOL
            else:
                role = MessageRole.USER

            # 处理内容类型 - LangChain消息内容可以是字符串或列表
            content = message.content
            if isinstance(content, list):
                # 如果是列表，提取文本内容
                content = " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                    if isinstance(item, (dict, str))
                )
            elif not isinstance(content, str):
                content = str(content)

            return LLMMessage(
                role=role,
                content=content,
                metadata=getattr(message, "additional_kwargs", {}),
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"消息转换失败: {e}")
            return LLMMessage(
                role=MessageRole.USER,
                content=str(message),
                timestamp=datetime.now()
            )
    
    def from_langchain_message_dict(self, message: BaseMessage) -> Dict[str, Any]:
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
        """批量转换消息列表为LangChain格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List[BaseMessage]: LangChain消息列表
        """
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.to_langchain_message(msg))
        return converted_messages
    
    def convert_from_langchain_list(self, messages: List[BaseMessage]) -> List[LLMMessage]:
        """批量转换LangChain消息列表
        
        Args:
            messages: LangChain消息列表
            
        Returns:
            List[LLMMessage]: LLM消息列表
        """
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.from_langchain_message(msg))
        return converted_messages
    
    def _llm_message_to_langchain(self, message: LLMMessage) -> BaseMessage:
        """将LLMMessage转换为LangChain消息"""
        if message.role == MessageRole.USER:
            return HumanMessage(content=message.content)
        elif message.role == MessageRole.ASSISTANT:
            return AIMessage(content=message.content)
        elif message.role == MessageRole.SYSTEM:
            return SystemMessage(content=message.content)
        elif message.role == MessageRole.TOOL:
            tool_call_id = message.metadata.get("tool_call_id", "")
            return ToolMessage(content=message.content, tool_call_id=tool_call_id)
        else:
            return HumanMessage(content=message.content)
    
    def _dict_to_langchain(self, message_dict: Dict[str, Any]) -> BaseMessage:
        """将字典转换为LangChain消息"""
        content = message_dict.get("content", "")
        role = message_dict.get("role", "human")
        
        if role == "human" or role == MessageRole.USER.value:
            return HumanMessage(content=content)
        elif role == "ai" or role == MessageRole.ASSISTANT.value:
            return AIMessage(content=content)
        elif role == "system" or role == MessageRole.SYSTEM.value:
            return SystemMessage(content=content)
        elif role == "tool" or role == MessageRole.TOOL.value:
            tool_call_id = message_dict.get("tool_call_id", "")
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        else:
            # 默认为人类消息
            return HumanMessage(content=content)
    
    def _object_to_langchain(self, message_obj: Any) -> BaseMessage:
        """将对象转换为LangChain消息"""
        content = getattr(message_obj, 'content', '')
        role = getattr(message_obj, 'role', 'human')
        
        # 标准化role值
        if isinstance(role, MessageRole):
            role_str = role.value
        else:
            role_str = str(role)
        
        if role_str == "human" or role_str == MessageRole.USER.value:
            return HumanMessage(content=content)
        elif role_str == "ai" or role_str == MessageRole.ASSISTANT.value:
            return AIMessage(content=content)
        elif role_str == "system" or role_str == MessageRole.SYSTEM.value:
            return SystemMessage(content=content)
        elif role_str == "tool" or role_str == MessageRole.TOOL.value:
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

    def create_system_message(self, content: str) -> LLMMessage:
        """创建系统消息
        
        Args:
            content: 消息内容
            
        Returns:
            LLMMessage: 系统消息
        """
        return LLMMessage(
            role=MessageRole.SYSTEM,
            content=content,
            timestamp=datetime.now()
        )

    def create_user_message(self, content: str) -> LLMMessage:
        """创建用户消息
        
        Args:
            content: 消息内容
            
        Returns:
            LLMMessage: 用户消息
        """
        return LLMMessage(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now()
        )

    def create_assistant_message(self, content: str) -> LLMMessage:
        """创建助手消息
        
        Args:
            content: 消息内容
            
        Returns:
            LLMMessage: 助手消息
        """
        return LLMMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now()
        )

    def create_tool_message(self, content: str, tool_call_id: str) -> LLMMessage:
        """创建工具消息
        
        Args:
            content: 消息内容
            tool_call_id: 工具调用ID
            
        Returns:
            LLMMessage: 工具消息
        """
        return LLMMessage(
            role=MessageRole.TOOL,
            content=content,
            metadata={"tool_call_id": tool_call_id},
            timestamp=datetime.now()
        )

    def extract_tool_calls(self, message: Union[LLMMessage, BaseMessage]) -> List[Dict[str, Any]]:
        """提取工具调用信息
        
        Args:
            message: LLM消息或LangChain消息
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        if isinstance(message, LLMMessage):
            # 优先使用 tool_calls 属性
            if message.tool_calls:
                return message.tool_calls
            # 回退到 metadata
            return message.metadata.get("tool_calls", [])
        elif isinstance(message, AIMessage):
            # 从 AIMessage 提取 tool_calls (仅 AIMessage 具有此属性)
            tool_calls = getattr(message, 'tool_calls', None)
            if tool_calls:
                # 将 ToolCall 对象转换为字典格式
                return [
                    {
                        "id": tc.id,
                        "name": tc.type if hasattr(tc, 'type') else "function",
                        "args": tc.args if hasattr(tc, 'args') else {}
                    }
                    for tc in tool_calls
                ] if isinstance(tool_calls, list) else []
            if hasattr(message, 'additional_kwargs'):
                return message.additional_kwargs.get("tool_calls", [])
            return []
        elif isinstance(message, BaseMessage):
            # 其他消息类型尝试从 additional_kwargs 提取
            if hasattr(message, 'additional_kwargs'):
                return message.additional_kwargs.get("tool_calls", [])
            return []
        else:
            return []

    def add_tool_calls_to_message(self, message: LLMMessage, tool_calls: List[Dict[str, Any]]) -> LLMMessage:
        """添加工具调用到消息
        
        Args:
            message: 域层消息
            tool_calls: 工具调用列表
            
        Returns:
            LLMMessage: 更新后的消息
        """
        # 创建新消息，更新 tool_calls 和 metadata
        new_metadata = message.metadata.copy()
        new_metadata["tool_calls"] = tool_calls

        return LLMMessage(
            role=message.role,
            content=message.content,
            name=message.name,
            function_call=message.function_call,
            tool_calls=tool_calls,
            metadata=new_metadata,
            timestamp=message.timestamp
        )


# 全局消息转换器实例
_global_converter: Optional[MessageConverter] = None


def get_message_converter() -> MessageConverter:
    """获取全局消息转换器实例
    
    Returns:
        MessageConverter: 消息转换器实例
    """
    global _global_converter
    if _global_converter is None:
        _global_converter = MessageConverter()
    return _global_converter
