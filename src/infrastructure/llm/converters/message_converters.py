"""消息转换器

负责在不同消息格式之间进行转换：
- LLMMessage <-> 基础消息格式
- 字典格式消息 <-> 基础消息格式
- 对象格式消息 <-> 基础消息格式
- 提供商特定格式 <-> 基础消息格式
"""

from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger
from datetime import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

from src.infrastructure.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from src.infrastructure.messages.converters import MessageConverter as InfraMessageConverter
from ..models import LLMMessage, MessageRole

logger = get_logger(__name__)


class MessageConverter:
    """消息转换器
    
    提供在不同消息格式之间的双向转换，支持提供商特定格式。
    """
    
    def __init__(self) -> None:
        """初始化消息转换器"""
        self.logger = get_logger(__name__)
        self._provider_handlers = {
            "openai": self._convert_from_openai_format,
            "gemini": self._convert_from_gemini_format,
            "anthropic": self._convert_from_anthropic_format,
        }
    
    def to_base_message(self, message: Any) -> "IBaseMessage":
        """将任意消息格式转换为基础消息
        
        Args:
            message: 输入消息
            
        Returns:
            IBaseMessage: 基础消息
        """
        try:
            if isinstance(message, BaseMessage):
                # 已经是基础消息
                return message
            elif isinstance(message, LLMMessage):
                # LLMMessage格式
                return self._llm_message_to_base(message)
            elif isinstance(message, dict):
                # 检测是否为提供商特定格式
                provider_format = self._detect_provider_format(message)
                if provider_format in self._provider_handlers:
                    return self._provider_handlers[provider_format](message)
                else:
                    # 普通字典格式
                    return self._dict_to_base(message)
            elif hasattr(message, 'content') and hasattr(message, 'role'):
                # 对象格式
                return self._object_to_base(message)
            else:
                # 其他格式，转换为人类消息
                return HumanMessage(content=str(message))
        except Exception as e:
            self.logger.error(f"消息转换失败: {e}")
            return HumanMessage(content=str(message))
    
    def from_base_message(self, message: "IBaseMessage", target_format: str = "llm") -> Any:
        """将基础消息转换为目标格式
        
        Args:
            message: 基础消息
            target_format: 目标格式 ("llm", "dict", "openai", "gemini", "anthropic")
            
        Returns:
            Any: 转换后的消息
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

            # 处理内容类型 - 基础消息内容可以是字符串或列表
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

            # 构建元数据
            metadata = getattr(message, "additional_kwargs", {}).copy()
            
            # 处理特殊字段
            if isinstance(message, ToolMessage):
                metadata["tool_call_id"] = message.tool_call_id
            elif isinstance(message, AIMessage) and hasattr(message, 'tool_calls') and message.tool_calls:
                metadata["tool_calls"] = message.tool_calls

            return LLMMessage(
                role=role,
                content=content,
                name=message.name,
                metadata=metadata,
                timestamp=message.timestamp if hasattr(message, 'timestamp') else datetime.now()
            )
        except Exception as e:
            self.logger.error(f"消息转换失败: {e}")
            return LLMMessage(
                role=MessageRole.USER,
                content=str(message),
                timestamp=datetime.now()
            )
    
    def from_base_message_dict(self, message: "IBaseMessage") -> Dict[str, Any]:
        """将基础消息转换为字典格式
        
        Args:
            message: 基础消息
            
        Returns:
            Dict[str, Any]: 字典格式消息
        """
        try:
            content: Union[str, List[Union[str, Dict[str, Any]]]]
            if isinstance(message.content, str):
                content = message.content
            else:
                content = message.content
            
            result: Dict[str, Any] = {
                "content": content,
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
    
    def convert_message_list(self, messages: List[Any]) -> List["IBaseMessage"]:
        """批量转换消息列表为基础格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List[IBaseMessage]: 基础消息列表
        """
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.to_base_message(msg))
        return converted_messages
    
    def convert_from_base_list(self, messages: List["IBaseMessage"]) -> List[LLMMessage]:
        """批量转换基础消息列表
        
        Args:
            messages: 基础消息列表
            
        Returns:
            List[LLMMessage]: LLM消息列表
        """
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.from_base_message(msg))
        return converted_messages
    
    def _llm_message_to_base(self, message: LLMMessage) -> "IBaseMessage":
        """将LLMMessage转换为基础消息"""
        if message.role == MessageRole.USER:
            return HumanMessage(content=message.content, name=message.name, additional_kwargs=message.metadata)
        elif message.role == MessageRole.ASSISTANT:
            return AIMessage(
                content=message.content,
                name=message.name,
                tool_calls=message.tool_calls,
                additional_kwargs=message.metadata
            )
        elif message.role == MessageRole.SYSTEM:
            return SystemMessage(content=message.content, name=message.name, additional_kwargs=message.metadata)
        elif message.role == MessageRole.TOOL:
            tool_call_id = message.metadata.get("tool_call_id", "")
            return ToolMessage(content=message.content, tool_call_id=tool_call_id, name=message.name, additional_kwargs=message.metadata)
        else:
            return HumanMessage(content=message.content, name=message.name, additional_kwargs=message.metadata)
    
    def _dict_to_base(self, message_dict: Dict[str, Any]) -> "IBaseMessage":
        """将字典转换为基础消息"""
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
    
    def _object_to_base(self, message_obj: Any) -> "IBaseMessage":
        """将对象转换为基础消息"""
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
    
    def _get_message_type(self, message: "IBaseMessage") -> str:
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

    def extract_tool_calls(self, message: Union[LLMMessage, "IBaseMessage"]) -> List[Dict[str, Any]]:
        """提取工具调用信息
         
        Args:
             message: LLM消息或基础消息
             
        Returns:
             List[Dict[str, Any]]: 工具调用列表
        """
        if isinstance(message, LLMMessage):
            # 优先使用 tool_calls 属性
            if message.tool_calls:
                return message.tool_calls
            # 回退到 metadata
            tool_calls_meta = message.metadata.get("tool_calls", [])
            return tool_calls_meta if isinstance(tool_calls_meta, list) else []
        elif isinstance(message, AIMessage):
            # 从 AIMessage 提取 tool_calls - AIMessage有tool_calls属性
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
    
    def _detect_provider_format(self, message_dict: Dict[str, Any]) -> str:
        """检测提供商格式
        
        Args:
            message_dict: 消息字典
            
        Returns:
            str: 提供商名称
        """
        if "role" in message_dict and "content" in message_dict:
            if "function_call" in message_dict or "tool_calls" in message_dict:
                return "openai"
            elif "author" in message_dict:
                return "anthropic"
            else:
                return "dict"
        elif "parts" in message_dict:
            return "gemini"
        else:
            return "dict"
    
    def _convert_from_openai_format(self, message_dict: Dict[str, Any]) -> "IBaseMessage":
        """从OpenAI格式转换
        
        Args:
            message_dict: OpenAI格式消息
            
        Returns:
            IBaseMessage: 基础消息
        """
        role = message_dict.get("role", "user")
        content = message_dict.get("content", "")
        
        if role == "user":
            return HumanMessage(
                content=content,
                name=message_dict.get("name"),
                additional_kwargs=message_dict.get("additional_kwargs", {})
            )
        elif role == "assistant":
            return AIMessage(
                content=content,
                name=message_dict.get("name"),
                tool_calls=message_dict.get("tool_calls"),
                additional_kwargs=message_dict.get("additional_kwargs", {})
            )
        elif role == "system":
            return SystemMessage(
                content=content,
                name=message_dict.get("name"),
                additional_kwargs=message_dict.get("additional_kwargs", {})
            )
        elif role == "tool":
            return ToolMessage(
                content=content,
                tool_call_id=message_dict.get("tool_call_id", ""),
                name=message_dict.get("name"),
                additional_kwargs=message_dict.get("additional_kwargs", {})
            )
        else:
            return HumanMessage(content=content)
    
    def _convert_from_gemini_format(self, message_dict: Dict[str, Any]) -> "IBaseMessage":
        """从Gemini格式转换
        
        Args:
            message_dict: Gemini格式消息
            
        Returns:
            IBaseMessage: 基础消息
        """
        role = message_dict.get("role", "user")
        parts = message_dict.get("parts", [])
        
        # 提取文本内容
        content_parts = []
        for part in parts:
            if isinstance(part, dict):
                if "text" in part:
                    content_parts.append(part["text"])
                elif "inline_data" in part:
                    # 处理多模态内容
                    content_parts.append(f"[ multimodal content: {part['inline_data'].get('mime_type', 'unknown')} ]")
            else:
                content_parts.append(str(part))
        
        content = " ".join(content_parts)
        
        if role == "user":
            return HumanMessage(content=content)
        elif role == "model":
            return AIMessage(content=content)
        else:
            return HumanMessage(content=content)
    
    def _convert_from_anthropic_format(self, message_dict: Dict[str, Any]) -> "IBaseMessage":
        """从Anthropic格式转换
        
        Args:
            message_dict: Anthropic格式消息
            
        Returns:
            IBaseMessage: 基础消息
        """
        role = message_dict.get("role", "user")
        content = message_dict.get("content", "")
        
        if isinstance(content, list):
            # 处理多模态内容
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, dict) and item.get("type") == "image":
                    text_parts.append("[ image content ]")
            content = " ".join(text_parts)
        
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        else:
            return HumanMessage(content=content)
    
    def convert_to_provider_format(self, message: "IBaseMessage", provider: str) -> Dict[str, Any]:
        """转换为基础消息为提供商格式
        
        Args:
            message: 基础消息
            provider: 提供商名称 ("openai", "gemini", "anthropic")
            
        Returns:
            Dict[str, Any]: 提供商格式消息
        """
        if provider == "openai":
            return self._convert_to_openai_format(message)
        elif provider == "gemini":
            return self._convert_to_gemini_format(message)
        elif provider == "anthropic":
            return self._convert_to_anthropic_format(message)
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    def _convert_to_openai_format(self, message: "IBaseMessage") -> Dict[str, Any]:
        """转换为OpenAI格式"""
        result = {
            "role": "user" if message.type == "human" else message.type,
            "content": message.content
        }
        
        if message.name:
            result["name"] = message.name
        
        if isinstance(message, AIMessage) and message.tool_calls:
            result["tool_calls"] = message.tool_calls
        
        if isinstance(message, ToolMessage):
            result["tool_call_id"] = message.tool_call_id
        
        return result
    
    def _convert_to_gemini_format(self, message: "IBaseMessage") -> Dict[str, Any]:
        """转换为Gemini格式"""
        role = "user" if message.type == "human" else "model"
        
        # 处理内容
        if isinstance(message.content, str):
            parts = [{"text": message.content}]
        else:
            parts = message.content  # type: ignore
        
        result = {
            "role": role,
            "parts": parts
        }
        
        return result
    
    def _convert_to_anthropic_format(self, message: "IBaseMessage") -> Dict[str, Any]:
        """转换为Anthropic格式"""
        role = "user" if message.type == "human" else "assistant"
        
        # 处理内容
        if isinstance(message.content, str):
            content = [{"type": "text", "text": message.content}]
        else:
            content = message.content  # type: ignore
        
        result = {
            "role": role,
            "content": content
        }
        
        return result


class ProviderRequestConverter:
    """提供商请求转换器
    
    使用提供商格式工具类处理向LLM提供商发送请求时的格式转换。
    """
    
    def __init__(self) -> None:
        """初始化提供商请求转换器"""
        self.logger = get_logger(__name__)
        from .provider_format_utils import get_provider_format_utils_factory
        self.format_utils_factory = get_provider_format_utils_factory()
    
    def convert_to_provider_request(self, provider: str, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为提供商API请求格式
        
        Args:
            provider: 提供商名称
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            Dict[str, Any]: 提供商API请求格式
        """
        format_utils = self.format_utils_factory.get_format_utils(provider)
        return format_utils.convert_request(messages, parameters)
    
    def convert_to_openai_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为OpenAI API请求格式（兼容性方法）"""
        return self.convert_to_provider_request("openai", messages, parameters)
    
    def convert_to_gemini_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Gemini API请求格式（兼容性方法）"""
        return self.convert_to_provider_request("gemini", messages, parameters)
    
    def convert_to_anthropic_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为Anthropic API请求格式（兼容性方法）"""
        return self.convert_to_provider_request("anthropic", messages, parameters)


class ProviderResponseConverter:
    """提供商响应转换器
    
    使用提供商格式工具类处理从LLM提供商接收响应时的格式转换。
    """
    
    def __init__(self) -> None:
        """初始化提供商响应转换器"""
        self.logger = get_logger(__name__)
        from .provider_format_utils import get_provider_format_utils_factory
        self.format_utils_factory = get_provider_format_utils_factory()
    
    def convert_from_provider_response(self, provider: str, response: Dict[str, Any]) -> "IBaseMessage":
        """从提供商API响应转换
        
        Args:
            provider: 提供商名称
            response: 提供商API响应
            
        Returns:
            IBaseMessage: 基础消息
        """
        format_utils = self.format_utils_factory.get_format_utils(provider)
        return format_utils.convert_response(response)
    
    def convert_from_openai_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从OpenAI API响应转换（兼容性方法）"""
        return self.convert_from_provider_response("openai", response)
    
    def convert_from_gemini_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Gemini API响应转换（兼容性方法）"""
        return self.convert_from_provider_response("gemini", response)
    
    def convert_from_anthropic_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Anthropic API响应转换（兼容性方法）"""
        return self.convert_from_provider_response("anthropic", response)


class MessageFactory:
    """消息工厂
    
    提供创建各种类型消息的统一接口。
    """
    
    def __init__(self) -> None:
        """初始化消息工厂"""
        self.logger = get_logger(__name__)
    
    def create_human_message(self, content: str, **kwargs: Any) -> "IBaseMessage":
        """创建人类消息
        
        Args:
            content: 消息内容
            **kwargs: 额外参数
            
        Returns:
            IBaseMessage: 人类消息
        """
        self._validate_content(content)
        
        message = HumanMessage(
            content=content,
            name=kwargs.get("name"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
        
        self._validate_message("human", message)
        return message
    
    def create_ai_message(self, content: str, **kwargs: Any) -> "IBaseMessage":
        """创建AI消息
        
        Args:
            content: 消息内容
            **kwargs: 额外参数
            
        Returns:
            IBaseMessage: AI消息
        """
        self._validate_content(content)
        
        message = AIMessage(
            content=content,
            name=kwargs.get("name"),
            tool_calls=kwargs.get("tool_calls"),
            invalid_tool_calls=kwargs.get("invalid_tool_calls"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
        
        self._validate_message("ai", message)
        return message
    
    def create_system_message(self, content: str, **kwargs: Any) -> "IBaseMessage":
        """创建系统消息
        
        Args:
            content: 消息内容
            **kwargs: 额外参数
            
        Returns:
            IBaseMessage: 系统消息
        """
        self._validate_content(content)
        
        message = SystemMessage(
            content=content,
            name=kwargs.get("name"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
        
        self._validate_message("system", message)
        return message
    
    def create_tool_message(self, content: str, tool_call_id: str, **kwargs: Any) -> "IBaseMessage":
        """创建工具消息
        
        Args:
            content: 消息内容
            tool_call_id: 工具调用ID
            **kwargs: 额外参数
            
        Returns:
            IBaseMessage: 工具消息
        """
        self._validate_content(content)
        self._validate_tool_call_id(tool_call_id)
        
        message = ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=kwargs.get("name"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
        
        self._validate_message("tool", message)
        return message
    
    def create_from_dict(self, data: Dict[str, Any]) -> "IBaseMessage":
        """从字典创建消息
        
        Args:
            data: 消息数据
            
        Returns:
            IBaseMessage: 基础消息
        """
        message_type = data.get("type", "human")
        content = data.get("content", "")
        
        kwargs = {
            "name": data.get("name"),
            "additional_kwargs": data.get("additional_kwargs", {}),
            "response_metadata": data.get("response_metadata", {}),
            "id": data.get("id"),
            "timestamp": data.get("timestamp")
        }
        
        if message_type == "human":
            return self.create_human_message(content, **kwargs)
        elif message_type == "ai":
            kwargs.update({
                "tool_calls": data.get("tool_calls"),
                "invalid_tool_calls": data.get("invalid_tool_calls")
            })
            return self.create_ai_message(content, **kwargs)
        elif message_type == "system":
            return self.create_system_message(content, **kwargs)
        elif message_type == "tool":
            tool_call_id = data.get("tool_call_id", "")
            # 移除tool_call_id从kwargs，因为它需要作为位置参数传递
            tool_kwargs = {k: v for k, v in kwargs.items() if k != "tool_call_id"}
            return self.create_tool_message(content, tool_call_id, **tool_kwargs)
        else:
            self.logger.warning(f"未知消息类型: {message_type}，使用人类消息")
            return self.create_human_message(content, **kwargs)
    
    def _validate_content(self, content: str) -> None:
        """验证内容
        
        Args:
            content: 消息内容
            
        Raises:
            ValueError: 内容无效时
        """
        if not isinstance(content, (str, list)):
            raise ValueError("消息内容必须是字符串或列表")
        
        if isinstance(content, str) and len(content.strip()) == 0:
            self.logger.warning("消息内容为空")
    
    def _validate_tool_call_id(self, tool_call_id: str) -> None:
        """验证工具调用ID
        
        Args:
            tool_call_id: 工具调用ID
            
        Raises:
            ValueError: ID无效时
        """
        if not isinstance(tool_call_id, str) or len(tool_call_id.strip()) == 0:
            raise ValueError("工具调用ID不能为空")
    
    def _validate_message(self, message_type: str, message: "IBaseMessage") -> None:
        """验证消息
        
        Args:
            message_type: 消息类型
            message: 消息对象
        """
        if message_type == "human" and not message.content:
            raise ValueError("人类消息内容不能为空")
        elif message_type == "ai" and not message.content and not getattr(message, 'tool_calls', None):
            raise ValueError("AI消息必须包含内容或工具调用")
        elif message_type == "system" and not message.content:
            raise ValueError("系统消息内容不能为空")
        elif message_type == "tool":
            if not message.content:
                raise ValueError("工具消息内容不能为空")
            if not getattr(message, 'tool_call_id', None):
                raise ValueError("工具消息必须包含工具调用ID")


class MessageSerializer:
    """消息序列化器
    
    提供消息的序列化和反序列化功能。
    """
    
    def __init__(self) -> None:
        """初始化消息序列化器"""
        self.logger = get_logger(__name__)
    
    def serialize(self, message: "IBaseMessage") -> bytes:
        """序列化消息
        
        Args:
            message: 基础消息
            
        Returns:
            bytes: 序列化后的数据
        """
        try:
            import json
            message_dict = message.to_dict()
            return json.dumps(message_dict, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            self.logger.error(f"消息序列化失败: {e}")
            raise
    
    def deserialize(self, data: bytes) -> "IBaseMessage":
        """反序列化消息
        
        Args:
            data: 序列化数据
            
        Returns:
            IBaseMessage: 基础消息
        """
        try:
            import json
            message_dict = json.loads(data.decode('utf-8'))
            factory = MessageFactory()
            return factory.create_from_dict(message_dict)
        except Exception as e:
            self.logger.error(f"消息反序列化失败: {e}")
            raise
    
    def serialize_list(self, messages: List["IBaseMessage"]) -> bytes:
        """序列化消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            bytes: 序列化后的数据
        """
        try:
            import json
            messages_list = [message.to_dict() for message in messages]
            return json.dumps(messages_list, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            self.logger.error(f"消息列表序列化失败: {e}")
            raise
    
    def deserialize_list(self, data: bytes) -> List["IBaseMessage"]:
        """反序列化消息列表
        
        Args:
            data: 序列化数据
            
        Returns:
            List[IBaseMessage]: 消息列表
        """
        try:
            import json
            messages_list = json.loads(data.decode('utf-8'))
            factory = MessageFactory()
            return [factory.create_from_dict(message_dict) for message_dict in messages_list]
        except Exception as e:
            self.logger.error(f"消息列表反序列化失败: {e}")
            raise


class MessageValidator:
    """消息验证器
    
    提供消息验证功能。
    """
    
    def __init__(self) -> None:
        """初始化消息验证器"""
        self.logger = get_logger(__name__)
    
    def validate(self, message: "IBaseMessage") -> List[str]:
        """验证消息，返回错误列表
        
        Args:
            message: 基础消息
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        # 验证内容
        content_errors = self.validate_content(message.content)
        errors.extend(content_errors)
        
        # 验证类型特定字段
        if isinstance(message, ToolMessage):
            if not message.tool_call_id:
                errors.append("工具消息必须包含工具调用ID")
        elif isinstance(message, AIMessage):
            if not message.content and not message.tool_calls:
                errors.append("AI消息必须包含内容或工具调用")
        
        return errors
    
    def is_valid(self, message: "IBaseMessage") -> bool:
        """检查消息是否有效
        
        Args:
            message: 基础消息
            
        Returns:
            bool: 是否有效
        """
        errors = self.validate(message)
        return len(errors) == 0
    
    def validate_content(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[str]:
        """验证消息内容
        
        Args:
            content: 消息内容
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        if not isinstance(content, (str, list)):
            errors.append("消息内容必须是字符串或列表")
            return errors
        
        if isinstance(content, str):
            if len(content.strip()) == 0:
                errors.append("字符串内容不能为空")
        elif isinstance(content, list):
            if len(content) == 0:
                errors.append("列表内容不能为空")
            
            for i, item in enumerate(content):
                if not isinstance(item, (str, dict)):
                    errors.append(f"列表项 {i} 必须是字符串或字典")
        
        return errors


# 全局消息转换器实例
_global_converter: Optional[MessageConverter] = None
_global_request_converter: Optional[ProviderRequestConverter] = None
_global_response_converter: Optional[ProviderResponseConverter] = None
_global_message_factory: Optional[MessageFactory] = None
_global_message_serializer: Optional[MessageSerializer] = None
_global_message_validator: Optional[MessageValidator] = None


def get_message_converter() -> MessageConverter:
    """获取全局消息转换器实例
    
    Returns:
        MessageConverter: 消息转换器实例
    """
    global _global_converter
    if _global_converter is None:
        _global_converter = MessageConverter()
    return _global_converter


def get_provider_request_converter() -> ProviderRequestConverter:
    """获取全局提供商请求转换器实例
    
    Returns:
        ProviderRequestConverter: 提供商请求转换器实例
    """
    global _global_request_converter
    if _global_request_converter is None:
        _global_request_converter = ProviderRequestConverter()
    return _global_request_converter


def get_provider_response_converter() -> ProviderResponseConverter:
    """获取全局提供商响应转换器实例
    
    Returns:
        ProviderResponseConverter: 提供商响应转换器实例
    """
    global _global_response_converter
    if _global_response_converter is None:
        _global_response_converter = ProviderResponseConverter()
    return _global_response_converter


def get_message_factory() -> MessageFactory:
    """获取全局消息工厂实例
    
    Returns:
        MessageFactory: 消息工厂实例
    """
    global _global_message_factory
    if _global_message_factory is None:
        _global_message_factory = MessageFactory()
    return _global_message_factory


def get_message_serializer() -> MessageSerializer:
    """获取全局消息序列化器实例
    
    Returns:
        MessageSerializer: 消息序列化器实例
    """
    global _global_message_serializer
    if _global_message_serializer is None:
        _global_message_serializer = MessageSerializer()
    return _global_message_serializer


def get_message_validator() -> MessageValidator:
    """获取全局消息验证器实例
    
    Returns:
        MessageValidator: 消息验证器实例
    """
    global _global_message_validator
    if _global_message_validator is None:
        _global_message_validator = MessageValidator()
    return _global_message_validator