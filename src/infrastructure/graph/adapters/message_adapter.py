"""消息适配器

负责在不同层级消息对象之间进行转换。
"""

from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

from src.infrastructure.llm.models import LLMMessage, MessageRole

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

    def to_graph_message(self, domain_message: LLMMessage) -> BaseMessage:
        """将域层消息转换为图系统消息

        Args:
            domain_message: 域层消息

        Returns:
            BaseMessage: 图系统消息
        """
        if domain_message.role == MessageRole.USER:
            return HumanMessage(content=domain_message.content)
        elif domain_message.role == MessageRole.ASSISTANT:
            return AIMessage(content=domain_message.content)
        elif domain_message.role == MessageRole.SYSTEM:
            return SystemMessage(content=domain_message.content)
        elif domain_message.role == MessageRole.TOOL:
            tool_call_id = domain_message.metadata.get("tool_call_id", "")
            return ToolMessage(content=domain_message.content, tool_call_id=tool_call_id)
        else:
            return HumanMessage(content=domain_message.content)

    def from_graph_message(self, graph_message: BaseMessage) -> LLMMessage:
        """将图系统消息转换为域层消息

        Args:
            graph_message: 图系统消息

        Returns:
            LLMMessage: 域层消息
        """
        if isinstance(graph_message, HumanMessage):
            role = MessageRole.USER
        elif isinstance(graph_message, AIMessage):
            role = MessageRole.ASSISTANT
        elif isinstance(graph_message, SystemMessage):
            role = MessageRole.SYSTEM
        elif isinstance(graph_message, ToolMessage):
            role = MessageRole.TOOL
        else:
            role = MessageRole.USER

        # 处理内容类型 - LangChain消息内容可以是字符串或列表
        content = graph_message.content
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
            metadata=getattr(graph_message, "additional_kwargs", {}),
            timestamp=datetime.now()
        )

    def to_graph_messages(self, domain_messages: List[LLMMessage]) -> List[BaseMessage]:
        """批量转换域层消息为图系统消息

        Args:
            domain_messages: 域层消息列表

        Returns:
            List[BaseMessage]: 图系统消息列表
        """
        return [self.to_graph_message(msg) for msg in domain_messages]

    def from_graph_messages(self, graph_messages: List[BaseMessage]) -> List[LLMMessage]:
        """批量转换图系统消息为域层消息

        Args:
            graph_messages: 图系统消息列表

        Returns:
            List[LLMMessage]: 域层消息列表
        """
        return [self.from_graph_message(msg) for msg in graph_messages]

    def extract_tool_calls(self, domain_message: LLMMessage) -> List[Dict[str, Any]]:
        """提取工具调用信息

        Args:
            domain_message: 域层消息

        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        # 优先使用 tool_calls 属性
        if hasattr(domain_message, 'tool_calls') and domain_message.tool_calls:
            return domain_message.tool_calls

        # 回退到 metadata
        tool_calls = domain_message.metadata.get("tool_calls", [])
        return tool_calls

    def add_tool_calls_to_message(self, domain_message: LLMMessage, tool_calls: List[Dict[str, Any]]) -> LLMMessage:
        """添加工具调用到消息

        Args:
            domain_message: 域层消息
            tool_calls: 工具调用列表

        Returns:
            LLMMessage: 更新后的消息
        """
        # 创建新消息，更新 tool_calls 和 metadata
        new_metadata = domain_message.metadata.copy()
        new_metadata["tool_calls"] = tool_calls

        return LLMMessage(
            role=domain_message.role,
            content=domain_message.content,
            name=domain_message.name,
            function_call=domain_message.function_call,
            tool_calls=tool_calls,
            metadata=new_metadata,
            timestamp=domain_message.timestamp
        )

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