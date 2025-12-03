"""兼容性适配器

提供与 LangChain 消息系统的兼容性支持。
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
import warnings

from ...interfaces.messages import IBaseMessage
from .types import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

if TYPE_CHECKING:
    # 避免运行时导入 LangChain
    try:
        from langchain_core.messages import BaseMessage as LCBaseMessage
        from langchain_core.messages import HumanMessage as LCHumanMessage
        from langchain_core.messages import AIMessage as LCAIMessage
        from langchain_core.messages import SystemMessage as LCSystemMessage
        from langchain_core.messages import ToolMessage as LCToolMessage
    except ImportError:
        LCBaseMessage = None
        LCHumanMessage = None
        LCAIMessage = None
        LCSystemMessage = None
        LCToolMessage = None


class LangChainCompatibilityAdapter:
    """LangChain兼容性适配器
    
    提供与LangChain消息系统的兼容性，确保现有代码无缝迁移。
    """
    
    @staticmethod
    def create_human_message(content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs) -> HumanMessage:
        """创建人类消息（兼容LangChain接口）"""
        return HumanMessage(content=content, **kwargs)
    
    @staticmethod
    def create_ai_message(content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs) -> AIMessage:
        """创建AI消息（兼容LangChain接口）"""
        return AIMessage(content=content, **kwargs)
    
    @staticmethod
    def create_system_message(content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs) -> SystemMessage:
        """创建系统消息（兼容LangChain接口）"""
        return SystemMessage(content=content, **kwargs)
    
    @staticmethod
    def create_tool_message(content: Union[str, List[Union[str, Dict[str, Any]]]], tool_call_id: str, **kwargs) -> ToolMessage:
        """创建工具消息（兼容LangChain接口）"""
        return ToolMessage(content=content, tool_call_id=tool_call_id, **kwargs)
    
    @classmethod
    def convert_from_langchain(cls, langchain_message: Any) -> BaseMessage:
        """从LangChain消息转换
        
        Args:
            langchain_message: LangChain消息对象
            
        Returns:
            BaseMessage: 转换后的消息对象
        """
        try:
            # 尝试导入LangChain
            from langchain_core.messages import BaseMessage as LCBaseMessage
            from langchain_core.messages import HumanMessage as LCHumanMessage
            from langchain_core.messages import AIMessage as LCAIMessage
            from langchain_core.messages import SystemMessage as LCSystemMessage
            from langchain_core.messages import ToolMessage as LCToolMessage
        except ImportError:
            warnings.warn("LangChain not available, returning original message")
            return langchain_message
        
        if not isinstance(langchain_message, LCBaseMessage):
            raise ValueError("Expected LangChain BaseMessage")
        
        # 提取通用属性
        content = langchain_message.content
        additional_kwargs = getattr(langchain_message, 'additional_kwargs', {})
        response_metadata = getattr(langchain_message, 'response_metadata', {})
        name = getattr(langchain_message, 'name', None)
        message_id = getattr(langchain_message, 'id', None)
        
        # 根据类型创建对应的消息
        if isinstance(langchain_message, LCHumanMessage):
            return HumanMessage(
                content=content,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
                name=name,
                id=message_id
            )
        elif isinstance(langchain_message, LCAIMessage):
            # 处理AI消息的特殊属性
            tool_calls = getattr(langchain_message, 'tool_calls', None)
            invalid_tool_calls = getattr(langchain_message, 'invalid_tool_calls', None)
            
            return AIMessage(
                content=content,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
                name=name,
                id=message_id,
                tool_calls=tool_calls,
                invalid_tool_calls=invalid_tool_calls
            )
        elif isinstance(langchain_message, LCSystemMessage):
            return SystemMessage(
                content=content,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
                name=name,
                id=message_id
            )
        elif isinstance(langchain_message, LCToolMessage):
            tool_call_id = getattr(langchain_message, 'tool_call_id', '')
            return ToolMessage(
                content=content,
                tool_call_id=tool_call_id,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
                name=name,
                id=message_id
            )
        else:
            # 未知类型，默认为人类消息
            return HumanMessage(
                content=content,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
                name=name,
                id=message_id
            )
    
    @classmethod
    def convert_to_langchain(cls, base_message: BaseMessage) -> Any:
        """转换为LangChain消息
        
        Args:
            base_message: 基础消息对象
            
        Returns:
            LangChain消息对象
        """
        try:
            # 尝试导入LangChain
            from langchain_core.messages import HumanMessage as LCHumanMessage
            from langchain_core.messages import AIMessage as LCAIMessage
            from langchain_core.messages import SystemMessage as LCSystemMessage
            from langchain_core.messages import ToolMessage as LCToolMessage
        except ImportError:
            warnings.warn("LangChain not available, returning original message")
            return base_message
        
        # 准备通用参数
        common_kwargs = {
            'content': base_message.content,
            'additional_kwargs': base_message.additional_kwargs,
            'response_metadata': base_message.response_metadata
        }
        
        if base_message.name:
            common_kwargs['name'] = base_message.name
        if base_message.id:
            common_kwargs['id'] = base_message.id
        
        # 根据类型创建对应的LangChain消息
        if isinstance(base_message, HumanMessage):
            return LCHumanMessage(**common_kwargs)
        elif isinstance(base_message, AIMessage):
            # 处理AI消息的特殊属性
            if base_message.tool_calls:
                common_kwargs['tool_calls'] = base_message.tool_calls
            if base_message.invalid_tool_calls:
                common_kwargs['invalid_tool_calls'] = base_message.invalid_tool_calls
            
            return LCAIMessage(**common_kwargs)
        elif isinstance(base_message, SystemMessage):
            return LCSystemMessage(**common_kwargs)
        elif isinstance(base_message, ToolMessage):
            common_kwargs['tool_call_id'] = base_message.tool_call_id
            return LCToolMessage(**common_kwargs)
        else:
            # 未知类型，默认为人类消息
            return LCHumanMessage(**common_kwargs)
    
    @classmethod
    def convert_list_from_langchain(cls, langchain_messages: List[Any]) -> List[BaseMessage]:
        """批量转换LangChain消息列表
        
        Args:
            langchain_messages: LangChain消息列表
            
        Returns:
            List[BaseMessage]: 转换后的消息列表
        """
        return [cls.convert_from_langchain(msg) for msg in langchain_messages]
    
    @classmethod
    def convert_list_to_langchain(cls, base_messages: List[BaseMessage]) -> List[Any]:
        """批量转换为LangChain消息列表
        
        Args:
            base_messages: 基础消息列表
            
        Returns:
            List[LangChain消息]: 转换后的消息列表
        """
        return [cls.convert_to_langchain(msg) for msg in base_messages]
    
    @staticmethod
    def is_langchain_available() -> bool:
        """检查LangChain是否可用
        
        Returns:
            bool: LangChain是否可用
        """
        try:
            import langchain_core.messages
            return True
        except ImportError:
            return False
    
    @staticmethod
    def is_langchain_message(message: Any) -> bool:
        """检查是否为LangChain消息
        
        Args:
            message: 消息对象
            
        Returns:
            bool: 是否为LangChain消息
        """
        try:
            from langchain_core.messages import BaseMessage as LCBaseMessage
            return isinstance(message, LCBaseMessage)
        except ImportError:
            return False
    
    @staticmethod
    def is_base_message(message: Any) -> bool:
        """检查是否为基础消息
        
        Args:
            message: 消息对象
            
        Returns:
            bool: 是否为基础消息
        """
        return isinstance(message, BaseMessage)
    
    @classmethod
    def auto_convert(cls, message: Any) -> Union[BaseMessage, Any]:
        """自动转换消息格式
        
        如果是LangChain消息则转换为基础消息，否则返回原消息。
        
        Args:
            message: 消息对象
            
        Returns:
            Union[BaseMessage, Any]: 转换后的消息或原消息
        """
        if cls.is_langchain_message(message):
            return cls.convert_from_langchain(message)
        else:
            return message
    
    @classmethod
    def auto_convert_list(cls, messages: List[Any]) -> List[Union[BaseMessage, Any]]:
        """自动转换消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            List[Union[BaseMessage, Any]]: 转换后的消息列表
        """
        return [cls.auto_convert(msg) for msg in messages]


# 便捷函数
def convert_from_langchain(langchain_message: Any) -> BaseMessage:
    """便捷函数：从LangChain消息转换"""
    return LangChainCompatibilityAdapter.convert_from_langchain(langchain_message)


def convert_to_langchain(base_message: BaseMessage) -> Any:
    """便捷函数：转换为LangChain消息"""
    return LangChainCompatibilityAdapter.convert_to_langchain(base_message)


def auto_convert_message(message: Any) -> Union[BaseMessage, Any]:
    """便捷函数：自动转换消息格式"""
    return LangChainCompatibilityAdapter.auto_convert(message)


def is_langchain_available() -> bool:
    """检查LangChain是否可用
    
    Returns:
        bool: LangChain是否可用
    """
    try:
        import langchain_core.messages
        return True
    except ImportError:
        return False