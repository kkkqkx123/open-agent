"""消息转换器

负责在不同消息格式之间进行转换，使用新的核心架构。
"""

from typing import Dict, Any, List, Optional, Union, Sequence
from src.services.logger.injection import get_logger
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
from ..models import LLMMessage, MessageRole
from src.infrastructure.llm.converters.core.conversion_context import ConversionContext
from src.infrastructure.llm.converters.core.conversion_pipeline import ConversionPipeline
from src.infrastructure.llm.converters.common.content_processors import TextProcessor
from src.infrastructure.llm.converters.common.error_handlers import ConversionErrorHandler

logger = get_logger(__name__)


class MessageConverter:
    """消息转换器 - 统一的消息格式转换门面
    
    这是消息转换系统的主入口，负责：
    1. 提供统一的消息格式转换API
    2. 支持多种消息格式之间的双向转换
    3. 委托给具体的转换器进行实际转换
    4. 提供便捷的消息创建和操作方法
    """
    
    def __init__(self) -> None:
        """初始化消息转换器"""
        self.logger = get_logger(__name__)
        
        # 初始化核心组件
        self.content_processor = TextProcessor()
        self.error_handler = ConversionErrorHandler()
        self.conversion_pipeline = ConversionPipeline("message_converter")
        
        # 初始化提供商处理器
        self._provider_handlers = {
            "openai": self._convert_from_openai_format,
            "openai-responses": self._convert_from_openai_responses_format,
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
        context = ConversionContext(
            provider_name="unknown",
            conversion_type="format",
            parameters={"input_message": message}
        )
        
        try:
            if isinstance(message, BaseMessage):
                # 已经是基础消息
                return message
            elif isinstance(message, LLMMessage):
                # LLMMessage格式
                return self._llm_message_to_base(message, context)
            elif isinstance(message, dict):
                # 检测是否为提供商特定格式
                provider_format = self._detect_provider_format(message)
                if provider_format in self._provider_handlers:
                    return self._provider_handlers[provider_format](message, context)
                else:
                    # 普通字典格式
                    return self._dict_to_base(message, context)
            elif hasattr(message, 'content') and hasattr(message, 'role'):
                # 对象格式
                return self._object_to_base(message, context)
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
        context = ConversionContext(
            provider_name="unknown",
            conversion_type="format",
            parameters={"target_format": target_format}
        )
        
        try:
            if target_format == "llm":
                return self._convert_to_llm_message(message, context)
            elif target_format == "dict":
                return self._convert_to_dict(message, context)
            else:
                # 提供商格式
                return self._convert_to_provider_format(message, target_format, context)
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
        context = ConversionContext(
            provider_name="unknown",
            conversion_type="format",
            parameters={}
        )
        
        try:
            return self._convert_to_dict(message, context)
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
        return [self.to_base_message(msg) for msg in messages]
    
    def convert_from_base_list(self, messages: List["IBaseMessage"]) -> List[LLMMessage]:
        """批量转换基础消息列表
        
        Args:
            messages: 基础消息列表
            
        Returns:
            List[LLMMessage]: LLM消息列表
        """
        return [self.from_base_message(msg) for msg in messages]
    
    def _llm_message_to_base(self, message: LLMMessage, context: ConversionContext) -> "IBaseMessage":
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
    
    def _dict_to_base(self, message_dict: Dict[str, Any], context: ConversionContext) -> "IBaseMessage":
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
    
    def _object_to_base(self, message_obj: Any, context: ConversionContext) -> "IBaseMessage":
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
    
    def _convert_to_llm_message(self, message: "IBaseMessage", context: ConversionContext) -> LLMMessage:
        """转换为基础LLM消息"""
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

        # 处理内容类型
        # TextProcessor.process返回ContentProcessingResult，需要提取processed_content
        result = self.content_processor.process(message.content)
        content = result.processed_content if result.is_successful() else str(message.content)

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
    
    def _convert_to_dict(self, message: "IBaseMessage", context: ConversionContext) -> Dict[str, Any]:
        """转换为字典格式"""
        result: Dict[str, Any] = {
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
    
    def _convert_to_provider_format(self, message: "IBaseMessage", provider: str, context: ConversionContext) -> Dict[str, Any]:
        """转换为提供商格式"""
        # 使用转换管道处理
        # 创建新的上下文而不是修改现有上下文
        context = ConversionContext(
            provider_name=provider,
            conversion_type="format",
            parameters=context.parameters
        )
        
        try:
            # 简化实现，直接使用提供商格式工具
            from .provider_format_utils import get_provider_format_utils_factory
            factory = get_provider_format_utils_factory()
            format_utils = factory.get_format_utils(provider)
            
            # 回退到基本处理
            return {
                "content": str(message.content),
                "role": "user"
            }
        except Exception as e:
            self.logger.error(f"转换为{provider}格式失败: {e}")
            # 回退到基本处理
            return {
                "content": str(message.content),
                "role": "user"
            }
    
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
    
    def _detect_provider_format(self, message_dict: Dict[str, Any]) -> str:
        """检测提供商格式"""
        if "role" in message_dict and "content" in message_dict:
            if "function_call" in message_dict or "tool_calls" in message_dict:
                return "openai"
            elif "author" in message_dict:
                return "anthropic"
            else:
                return "dict"
        elif "parts" in message_dict:
            return "gemini"
        elif "input" in message_dict and not "role" in message_dict:
            # Responses API格式：有input字段但没有role字段
            return "openai-responses"
        else:
            return "dict"
    
    def _convert_from_openai_format(self, message_dict: Dict[str, Any], context: ConversionContext) -> "IBaseMessage":
        """从OpenAI格式转换"""
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
    
    def _convert_from_openai_responses_format(self, message_dict: Dict[str, Any], context: ConversionContext) -> "IBaseMessage":
        """从OpenAI Responses API格式转换"""
        # 使用转换管道处理
        try:
            # 简化实现，直接使用提供商格式工具
            from .provider_format_utils import get_provider_format_utils_factory
            factory = get_provider_format_utils_factory()
            format_utils = factory.get_format_utils("openai-responses")
            # 回退到基本处理
            return HumanMessage(content=str(message_dict.get("content", "")))
        except Exception as e:
            self.logger.error(f"转换OpenAI Responses格式失败: {e}")
            # 回退到基本处理
            input_content = message_dict.get("input", "")
            return HumanMessage(content=str(input_content))
    
    def _convert_from_gemini_format(self, message_dict: Dict[str, Any], context: ConversionContext) -> "IBaseMessage":
        """从Gemini格式转换"""
        # 使用转换管道处理
        try:
            # 简化实现，直接使用提供商格式工具
            from .provider_format_utils import get_provider_format_utils_factory
            factory = get_provider_format_utils_factory()
            format_utils = factory.get_format_utils("gemini")
            # 回退到基本处理
            return HumanMessage(content=str(message_dict.get("content", "")))
        except Exception as e:
            self.logger.error(f"转换Gemini格式失败: {e}")
            # 回退到基本处理
            content = message_dict.get("content", "")
            return HumanMessage(content=str(content))
    
    def _convert_from_anthropic_format(self, message_dict: Dict[str, Any], context: ConversionContext) -> "IBaseMessage":
        """从Anthropic格式转换"""
        # 使用转换管道处理
        try:
            # 简化实现，直接使用提供商格式工具
            from .provider_format_utils import get_provider_format_utils_factory
            factory = get_provider_format_utils_factory()
            format_utils = factory.get_format_utils("anthropic")
            # 回退到基本处理
            return HumanMessage(content=str(message_dict.get("content", "")))
        except Exception as e:
            self.logger.error(f"转换Anthropic格式失败: {e}")
            # 回退到基本处理
            content = message_dict.get("content", "")
            return HumanMessage(content=str(content))
    
    # 便捷方法
    def create_system_message(self, content: str) -> LLMMessage:
        """创建系统消息"""
        return LLMMessage(
            role=MessageRole.SYSTEM,
            content=content,
            timestamp=datetime.now()
        )

    def create_user_message(self, content: str) -> LLMMessage:
        """创建用户消息"""
        return LLMMessage(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now()
        )

    def create_assistant_message(self, content: str) -> LLMMessage:
        """创建助手消息"""
        return LLMMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now()
        )

    def create_tool_message(self, content: str, tool_call_id: str) -> LLMMessage:
        """创建工具消息"""
        return LLMMessage(
            role=MessageRole.TOOL,
            content=content,
            metadata={"tool_call_id": tool_call_id},
            timestamp=datetime.now()
        )

    def extract_tool_calls(self, message: Union[LLMMessage, "IBaseMessage"]) -> List[Dict[str, Any]]:
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
            function_call=message.function_call,
            tool_calls=tool_calls,
            metadata=new_metadata,
            timestamp=message.timestamp
        )
    
    def convert_to_provider_format(self, message: "IBaseMessage", provider: str) -> Dict[str, Any]:
        """转换为基础消息为提供商格式"""
        context = ConversionContext(
            provider_name=provider,
            conversion_type="format",
            parameters={}
        )
        return self._convert_to_provider_format(message, provider, context)


# 为了向后兼容，保留其他类但简化实现
class RequestConverter:
    """请求转换器 - 统一的对外入口"""
    
    def __init__(self) -> None:
        """初始化请求转换器"""
        self.logger = get_logger(__name__)
        from .provider_format_utils import get_provider_format_utils_factory
        self.format_utils_factory = get_provider_format_utils_factory()
    
    def convert_to_provider_request(
        self,
        provider: str,
        messages: Sequence["IBaseMessage"],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换为提供商API请求格式"""
        format_utils = self.format_utils_factory.get_format_utils(provider)
        # 简化实现，直接返回基本格式
        return {
            "messages": [{"role": "user", "content": str(msg.content)} for msg in messages],
            "parameters": parameters
        }
    
    # 兼容性方法
    def convert_to_openai_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        return self.convert_to_provider_request("openai", messages, parameters)
    
    def convert_to_openai_responses_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        return self.convert_to_provider_request("openai-responses", messages, parameters)
    
    def convert_to_gemini_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        return self.convert_to_provider_request("gemini", messages, parameters)
    
    def convert_to_anthropic_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        return self.convert_to_provider_request("anthropic", messages, parameters)


class ResponseConverter:
    """响应转换器 - 统一的对外入口"""
    
    def __init__(self) -> None:
        """初始化响应转换器"""
        self.logger = get_logger(__name__)
        from .provider_format_utils import get_provider_format_utils_factory
        self.format_utils_factory = get_provider_format_utils_factory()
    
    def convert_from_provider_response(self, provider: str, response: Dict[str, Any]) -> "IBaseMessage":
         """从提供商API响应转换"""
         format_utils = self.format_utils_factory.get_format_utils(provider)
         try:
             # 简化实现，返回基本AI消息
             return AIMessage(content=str(response.get("content", "")))
         except Exception as e:
             self.logger.error(f"转换{provider}响应失败: {e}")
             return AIMessage(content="")
    
    def convert_from_provider_stream_response(self, provider: str, events: List[Dict[str, Any]]) -> "IBaseMessage":
         """从提供商流式响应转换"""
         format_utils = self.format_utils_factory.get_format_utils(provider)
         try:
             # 简化实现，返回基本AI消息
             content = " ".join(str(event.get("content", "")) for event in events)
             return AIMessage(content=content)
         except Exception as e:
             self.logger.error(f"转换{provider}流式响应失败: {e}")
             return AIMessage(content="")
    
    # 兼容性方法
    def convert_from_openai_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        return self.convert_from_provider_response("openai", response)
    
    def convert_from_gemini_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        return self.convert_from_provider_response("gemini", response)
    
    def convert_from_anthropic_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        return self.convert_from_provider_response("anthropic", response)


# 简化的工厂类
class MessageFactory:
    """消息工厂"""
    
    def __init__(self) -> None:
        """初始化消息工厂"""
        self.logger = get_logger(__name__)
    
    def create_human_message(self, content: str, **kwargs: Any) -> "IBaseMessage":
        """创建人类消息"""
        return HumanMessage(
            content=content,
            name=kwargs.get("name"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
    
    def create_ai_message(self, content: str, **kwargs: Any) -> "IBaseMessage":
        """创建AI消息"""
        return AIMessage(
            content=content,
            name=kwargs.get("name"),
            tool_calls=kwargs.get("tool_calls"),
            invalid_tool_calls=kwargs.get("invalid_tool_calls"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
    
    def create_system_message(self, content: str, **kwargs: Any) -> "IBaseMessage":
        """创建系统消息"""
        return SystemMessage(
            content=content,
            name=kwargs.get("name"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
    
    def create_tool_message(self, content: str, tool_call_id: str, **kwargs: Any) -> "IBaseMessage":
        """创建工具消息"""
        return ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=kwargs.get("name"),
            additional_kwargs=kwargs.get("additional_kwargs", {}),
            response_metadata=kwargs.get("response_metadata", {}),
            id=kwargs.get("id"),
            timestamp=kwargs.get("timestamp")
        )
    
    def create_from_dict(self, data: Dict[str, Any]) -> "IBaseMessage":
        """从字典创建消息"""
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
            tool_kwargs = {k: v for k, v in kwargs.items() if k != "tool_call_id"}
            return self.create_tool_message(content, tool_call_id, **tool_kwargs)
        else:
            self.logger.warning(f"未知消息类型: {message_type}，使用人类消息")
            return self.create_human_message(content, **kwargs)


class MessageSerializer:
    """消息序列化器"""
    
    def __init__(self) -> None:
        """初始化消息序列化器"""
        self.logger = get_logger(__name__)
    
    def serialize(self, message: "IBaseMessage") -> bytes:
        """序列化消息"""
        try:
            import json
            message_dict = message.to_dict()
            return json.dumps(message_dict, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            self.logger.error(f"消息序列化失败: {e}")
            raise
    
    def deserialize(self, data: bytes) -> "IBaseMessage":
        """反序列化消息"""
        try:
            import json
            message_dict = json.loads(data.decode('utf-8'))
            factory = MessageFactory()
            return factory.create_from_dict(message_dict)
        except Exception as e:
            self.logger.error(f"消息反序列化失败: {e}")
            raise
    
    def serialize_list(self, messages: List["IBaseMessage"]) -> bytes:
        """序列化消息列表"""
        try:
            import json
            messages_list = [message.to_dict() for message in messages]
            return json.dumps(messages_list, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            self.logger.error(f"消息列表序列化失败: {e}")
            raise
    
    def deserialize_list(self, data: bytes) -> List["IBaseMessage"]:
        """反序列化消息列表"""
        try:
            import json
            messages_list = json.loads(data.decode('utf-8'))
            factory = MessageFactory()
            return [factory.create_from_dict(message_dict) for message_dict in messages_list]
        except Exception as e:
            self.logger.error(f"消息列表反序列化失败: {e}")
            raise


class MessageValidator:
    """消息验证器"""
    
    def __init__(self) -> None:
        """初始化消息验证器"""
        self.logger = get_logger(__name__)
    
    def validate(self, message: "IBaseMessage") -> List[str]:
        """验证消息，返回错误列表"""
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
        """检查消息是否有效"""
        errors = self.validate(message)
        return len(errors) == 0
    
    def validate_content(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[str]:
        """验证消息内容"""
        errors = []
        
        if not isinstance(content, (str, list)):
            errors.append("消息内容必须是字符串或列表")
        
        return errors