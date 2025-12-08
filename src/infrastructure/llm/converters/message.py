"""
统一消息转换器

提供所有消息格式转换的统一入口。
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base import ConversionContext, MessageRole
from .utils import (
    process_content_to_list,
    extract_text_from_content,
    create_timestamp,
    safe_get
)


class LLMMessage:
    """LLM消息类"""
    
    def __init__(
        self,
        role: MessageRole,
        content: str,
        name: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.role = role
        self.content = content
        self.name = name
        self.tool_calls = tool_calls or []
        self.metadata = metadata or {}
        self.timestamp = timestamp or create_timestamp()


class BaseMessage:
    """基础消息类"""
    
    def __init__(
        self,
        content: Union[str, List[Union[str, Dict[str, Any]]]],
        name: Optional[str] = None,
        additional_kwargs: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.content = content
        self.name = name
        self.additional_kwargs = additional_kwargs or {}
        self.timestamp = timestamp or create_timestamp()


class HumanMessage(BaseMessage):
    """人类消息"""
    pass


class AIMessage(BaseMessage):
    """AI消息"""
    
    def __init__(
        self,
        content: Union[str, List[Union[str, Dict[str, Any]]]],
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(content, **kwargs)
        self.tool_calls = tool_calls or []


class SystemMessage(BaseMessage):
    """系统消息"""
    pass


class ToolMessage(BaseMessage):
    """工具消息"""
    
    def __init__(
        self,
        content: Union[str, List[Union[str, Dict[str, Any]]]],
        tool_call_id: str,
        **kwargs
    ):
        super().__init__(content, **kwargs)
        self.tool_call_id = tool_call_id


class MessageConverter:
    """消息转换器"""
    
    def __init__(self):
        """初始化消息转换器"""
        self._providers = {}
        self._register_providers()
    
    def _register_providers(self):
        """注册所有提供商"""
        try:
            from .providers.openai import OpenAIProvider
            from .providers.anthropic import AnthropicProvider
            from .providers.gemini import GeminiProvider
            from .providers.openai_responses import OpenAIResponsesProvider
            
            self._providers["openai"] = OpenAIProvider()
            self._providers["anthropic"] = AnthropicProvider()
            self._providers["gemini"] = GeminiProvider()
            self._providers["openai-responses"] = OpenAIResponsesProvider()
        except ImportError as e:
            # 如果提供商模块不存在，跳过注册
            pass
    
    def to_base_message(self, message: Any, provider_hint: Optional[str] = None) -> BaseMessage:
        """将任意消息格式转换为基础消息
        
        Args:
            message: 输入消息
            provider_hint: 提供商提示（可选）
            
        Returns:
            BaseMessage: 基础消息
        """
        if isinstance(message, BaseMessage):
            return message
        
        if isinstance(message, LLMMessage):
            return self._llm_to_base(message)
        
        if isinstance(message, dict):
            return self._dict_to_base(message, provider_hint)
        
        if hasattr(message, 'content') and hasattr(message, 'role'):
            return self._object_to_base(message)
        
        # 默认转换为人类消息
        return HumanMessage(content=str(message))
    
    def from_base_message(self, message: BaseMessage, target_format: str = "llm", provider: Optional[str] = None) -> Any:
        """将基础消息转换为目标格式
        
        Args:
            message: 基础消息
            target_format: 目标格式 ("llm", "dict", "openai", "gemini", "anthropic")
            provider: 提供商名称（可选）
            
        Returns:
            Any: 转换后的消息
        """
        if target_format == "llm":
            return self._base_to_llm(message)
        
        if target_format == "dict":
            return self._base_to_dict(message)
        
        if target_format in self._providers:
            return self._base_to_provider(message, target_format)
        
        # 默认转换为字典格式
        return self._base_to_dict(message)
    
    def convert_message_list(self, messages: List[Any], provider_hint: Optional[str] = None) -> List[BaseMessage]:
        """批量转换消息列表为基础格式
        
        Args:
            messages: 消息列表
            provider_hint: 提供商提示（可选）
            
        Returns:
            List[BaseMessage]: 基础消息列表
        """
        return [self.to_base_message(msg, provider_hint) for msg in messages]
    
    def convert_from_base_list(self, messages: List[BaseMessage], target_format: str = "llm", provider: Optional[str] = None) -> List[Any]:
        """批量转换基础消息列表
        
        Args:
            messages: 基础消息列表
            target_format: 目标格式
            provider: 提供商名称（可选）
            
        Returns:
            List[Any]: 转换后的消息列表
        """
        return [self.from_base_message(msg, target_format, provider) for msg in messages]
    
    def _llm_to_base(self, message: LLMMessage) -> BaseMessage:
        """将LLM消息转换为基础消息"""
        if message.role == MessageRole.USER:
            return HumanMessage(
                content=message.content,
                name=message.name,
                additional_kwargs=message.metadata
            )
        elif message.role == MessageRole.ASSISTANT:
            return AIMessage(
                content=message.content,
                name=message.name,
                tool_calls=message.tool_calls,
                additional_kwargs=message.metadata
            )
        elif message.role == MessageRole.SYSTEM:
            return SystemMessage(
                content=message.content,
                name=message.name,
                additional_kwargs=message.metadata
            )
        elif message.role == MessageRole.TOOL:
            tool_call_id = message.metadata.get("tool_call_id", "")
            return ToolMessage(
                content=message.content,
                tool_call_id=tool_call_id,
                name=message.name,
                additional_kwargs=message.metadata
            )
        else:
            return HumanMessage(
                content=message.content,
                name=message.name,
                additional_kwargs=message.metadata
            )
    
    def _dict_to_base(self, message_dict: Dict[str, Any], provider_hint: Optional[str] = None) -> BaseMessage:
        """将字典转换为基础消息"""
        content = message_dict.get("content", "")
        role = message_dict.get("role", "user")
        
        # 处理工具调用
        tool_calls = message_dict.get("tool_calls")
        tool_call_id = message_dict.get("tool_call_id", "")
        
        # 处理额外参数
        additional_kwargs = {k: v for k, v in message_dict.items() 
                           if k not in ["content", "role", "tool_calls", "tool_call_id"]}
        
        name = additional_kwargs.pop("name", None)
        
        if role in ["user", "human"] or role == MessageRole.USER.value:
            return HumanMessage(
                content=content,
                name=name,
                additional_kwargs=additional_kwargs
            )
        elif role in ["assistant", "ai"] or role == MessageRole.ASSISTANT.value:
            return AIMessage(
                content=content,
                name=name,
                tool_calls=tool_calls,
                additional_kwargs=additional_kwargs
            )
        elif role == "system" or role == MessageRole.SYSTEM.value:
            return SystemMessage(
                content=content,
                name=name,
                additional_kwargs=additional_kwargs
            )
        elif role == "tool" or role == MessageRole.TOOL.value:
            return ToolMessage(
                content=content,
                tool_call_id=tool_call_id,
                name=name,
                additional_kwargs=additional_kwargs
            )
        else:
            # 默认为人类消息
            return HumanMessage(
                content=content,
                name=name,
                additional_kwargs=additional_kwargs
            )
    
    def _object_to_base(self, message_obj: Any) -> BaseMessage:
        """将对象转换为基础消息"""
        content = getattr(message_obj, 'content', '')
        role = getattr(message_obj, 'role', 'user')
        
        # 标准化role值
        if isinstance(role, MessageRole):
            role_str = role.value
        else:
            role_str = str(role)
        
        # 获取其他属性
        name = getattr(message_obj, 'name', None)
        tool_calls = getattr(message_obj, 'tool_calls', None)
        tool_call_id = getattr(message_obj, 'tool_call_id', None)
        
        # 构建额外参数
        additional_kwargs = {}
        for attr in dir(message_obj):
            if not attr.startswith('_') and attr not in ['content', 'role', 'name', 'tool_calls', 'tool_call_id']:
                value = getattr(message_obj, attr)
                if not callable(value):
                    additional_kwargs[attr] = value
        
        if role_str in ["user", "human"] or role_str == MessageRole.USER.value:
            return HumanMessage(
                content=content,
                name=name,
                additional_kwargs=additional_kwargs
            )
        elif role_str in ["assistant", "ai"] or role_str == MessageRole.ASSISTANT.value:
            return AIMessage(
                content=content,
                name=name,
                tool_calls=tool_calls,
                additional_kwargs=additional_kwargs
            )
        elif role_str == "system" or role_str == MessageRole.SYSTEM.value:
            return SystemMessage(
                content=content,
                name=name,
                additional_kwargs=additional_kwargs
            )
        elif role_str == "tool" or role_str == MessageRole.TOOL.value:
            return ToolMessage(
                content=content,
                tool_call_id=tool_call_id or "",
                name=name,
                additional_kwargs=additional_kwargs
            )
        else:
            # 默认为人类消息
            return HumanMessage(
                content=content,
                name=name,
                additional_kwargs=additional_kwargs
            )
    
    def _base_to_llm(self, message: BaseMessage) -> LLMMessage:
        """将基础消息转换为LLM消息"""
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
        
        # 处理内容
        content = extract_text_from_content(process_content_to_list(message.content))
        
        # 构建元数据
        metadata = message.additional_kwargs.copy()
        
        # 处理特殊字段
        if isinstance(message, ToolMessage):
            metadata["tool_call_id"] = message.tool_call_id
        elif isinstance(message, AIMessage) and message.tool_calls:
            metadata["tool_calls"] = message.tool_calls
        
        return LLMMessage(
            role=role,
            content=content,
            name=message.name,
            tool_calls=getattr(message, 'tool_calls', None),
            metadata=metadata,
            timestamp=message.timestamp
        )
    
    def _base_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """将基础消息转换为字典格式"""
        result = {
            "content": message.content,
            "type": self._get_message_type(message)
        }
        
        # 添加特定类型的额外信息
        if isinstance(message, ToolMessage):
            result["tool_call_id"] = message.tool_call_id
        
        # 添加额外属性
        if message.name:
            result["name"] = message.name
        
        if message.additional_kwargs:
            result["additional_kwargs"] = message.additional_kwargs
        
        if isinstance(message, AIMessage) and message.tool_calls:
            result["tool_calls"] = message.tool_calls
        
        return result
    
    def _base_to_provider(self, message: BaseMessage, provider: str) -> Dict[str, Any]:
        """将基础消息转换为提供商格式"""
        if provider not in self._providers:
            raise ValueError(f"不支持的提供商: {provider}")
        
        provider_instance = self._providers[provider]
        
        # 转换为提供商请求格式
        messages = [message]
        parameters = {}
        request_data = provider_instance.convert_request(messages, parameters)
        
        # 提取消息部分
        if "messages" in request_data and request_data["messages"]:
            return request_data["messages"][0]
        else:
            # 回退到基本处理
            return {
                "content": extract_text_from_content(process_content_to_list(message.content)),
                "role": "user"
            }
    
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
    
    # 便捷方法
    def create_system_message(self, content: str) -> LLMMessage:
        """创建系统消息"""
        return LLMMessage(
            role=MessageRole.SYSTEM,
            content=content
        )
    
    def create_user_message(self, content: str) -> LLMMessage:
        """创建用户消息"""
        return LLMMessage(
            role=MessageRole.USER,
            content=content
        )
    
    def create_assistant_message(self, content: str) -> LLMMessage:
        """创建助手消息"""
        return LLMMessage(
            role=MessageRole.ASSISTANT,
            content=content
        )
    
    def create_tool_message(self, content: str, tool_call_id: str) -> LLMMessage:
        """创建工具消息"""
        return LLMMessage(
            role=MessageRole.TOOL,
            content=content,
            metadata={"tool_call_id": tool_call_id}
        )
    
    def extract_tool_calls(self, message: Union[LLMMessage, BaseMessage]) -> List[Dict[str, Any]]:
        """提取工具调用信息"""
        if isinstance(message, LLMMessage):
            # 优先使用 tool_calls 属性
            if message.tool_calls:
                return message.tool_calls
            # 回退到 metadata
            tool_calls_meta = message.metadata.get("tool_calls", [])
            return tool_calls_meta if isinstance(tool_calls_meta, list) else []
        elif isinstance(message, AIMessage):
            # 从 AIMessage 提取 tool_calls
            if message.tool_calls:
                return message.tool_calls if isinstance(message.tool_calls, list) else []
            if message.additional_kwargs:
                tool_calls_kwargs = message.additional_kwargs.get("tool_calls", [])
                return tool_calls_kwargs if isinstance(tool_calls_kwargs, list) else []
            return []
        elif isinstance(message, BaseMessage):
            # 其他消息类型尝试从 additional_kwargs 提取
            if message.additional_kwargs:
                tool_calls_base = message.additional_kwargs.get("tool_calls", [])
                return tool_calls_base if isinstance(tool_calls_base, list) else []
            return []
        else:
            return []
    
    def add_tool_calls_to_message(self, message: LLMMessage, tool_calls: List[Dict[str, Any]]) -> LLMMessage:
        """添加工具调用到消息"""
        # 创建新消息，更新 tool_calls 和 metadata
        new_metadata = message.metadata.copy()
        new_metadata["tool_calls"] = tool_calls

        return LLMMessage(
            role=message.role,
            content=message.content,
            name=message.name,
            tool_calls=tool_calls,
            metadata=new_metadata,
            timestamp=message.timestamp
        )