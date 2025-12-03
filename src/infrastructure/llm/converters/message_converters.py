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
        
        # 提取文本内容、工具调用和思考过程
        content_parts = []
        tool_calls = []
        thoughts = []
        
        for part in parts:
            if isinstance(part, dict):
                if "text" in part:
                    content_parts.append(part["text"])
                elif "inline_data" in part:
                    # 处理多模态内容
                    mime_type = part['inline_data'].get('mime_type', 'unknown')
                    if mime_type.startswith("image/"):
                        content_parts.append("[图像内容]")
                    elif mime_type.startswith("audio/"):
                        content_parts.append("[音频内容]")
                    elif mime_type.startswith("video/"):
                        content_parts.append("[视频内容]")
                    else:
                        content_parts.append(f"[多模态内容: {mime_type}]")
                elif "functionCall" in part:
                    # 处理工具调用
                    function_call = part["functionCall"]
                    tool_call = {
                        "id": f"call_{hash(str(function_call))}",  # Gemini不提供ID，生成一个
                        "type": "function",
                        "function": {
                            "name": function_call.get("name", ""),
                            "arguments": function_call.get("args", {})
                        }
                    }
                    tool_calls.append(tool_call)
                elif "thought" in part:
                    # 处理思考过程
                    thoughts.append(part["thought"])
            else:
                content_parts.append(str(part))
        
        content = " ".join(content_parts)
        
        # 构建额外参数
        additional_kwargs = {
            "role": role,
            "original_parts": parts
        }
        
        # 添加工具调用信息
        if tool_calls:
            additional_kwargs["tool_calls"] = tool_calls
        
        # 添加思考过程
        if thoughts:
            additional_kwargs["thoughts"] = thoughts
        
        if role == "user":
            return HumanMessage(
                content=content,
                additional_kwargs=additional_kwargs
            )
        elif role == "model":
            return AIMessage(
                content=content,
                tool_calls=tool_calls if tool_calls else None,
                additional_kwargs=additional_kwargs
            )
        else:
            return HumanMessage(
                content=content,
                additional_kwargs=additional_kwargs
            )
    
    def _convert_from_anthropic_format(self, message_dict: Dict[str, Any]) -> "IBaseMessage":
        """从Anthropic格式转换
        
        Args:
            message_dict: Anthropic格式消息
            
        Returns:
            IBaseMessage: 基础消息
        """
        role = message_dict.get("role", "user")
        content = message_dict.get("content", "")
        name = message_dict.get("name")
        
        # 处理内容
        text_content = ""
        tool_calls = []
        additional_kwargs = {}
        
        if isinstance(content, list):
            # 处理多模态内容和工具使用
            text_parts = []
            tool_use_blocks = []
            
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    
                    if item_type == "text":
                        text_parts.append(item.get("text", ""))
                    elif item_type == "image":
                        text_parts.append("[图像内容]")
                    elif item_type == "tool_use":
                        # 处理工具使用
                        tool_call = self._extract_tool_call_from_anthropic(item)
                        if tool_call:
                            tool_calls.append(tool_call)
                            tool_use_blocks.append(item)
                    else:
                        text_parts.append(f"[{item_type} content]")
            
            text_content = " ".join(text_parts)
            
            # 保存工具使用块到额外参数
            if tool_use_blocks:
                additional_kwargs["tool_use_blocks"] = tool_use_blocks
        else:
            text_content = str(content)
        
        # 构建额外参数
        additional_kwargs.update({
            "role": role,
            "original_content": content
        })
        
        # 创建消息
        if role == "user":
            return HumanMessage(
                content=text_content,
                name=name,
                additional_kwargs=additional_kwargs
            )
        elif role == "assistant":
            return AIMessage(
                content=text_content,
                name=name,
                tool_calls=tool_calls if tool_calls else None,
                additional_kwargs=additional_kwargs
            )
        elif role == "system":
            return SystemMessage(
                content=text_content,
                name=name,
                additional_kwargs=additional_kwargs
            )
        else:
            # 默认为用户消息
            return HumanMessage(
                content=text_content,
                name=name,
                additional_kwargs=additional_kwargs
            )
    
    def _extract_tool_call_from_anthropic(self, tool_use_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从Anthropic工具使用项中提取工具调用
        
        Args:
            tool_use_item: Anthropic工具使用项
            
        Returns:
            Optional[Dict[str, Any]]: 标准格式的工具调用
        """
        try:
            tool_call = {
                "id": tool_use_item.get("id", ""),
                "type": "function",
                "function": {
                    "name": tool_use_item.get("name", ""),
                    "arguments": tool_use_item.get("input", {})
                }
            }
            
            # 验证必需字段
            if not tool_call["id"] or not tool_call["function"]["name"]:
                return None
            
            return tool_call
        except Exception:
            return None
    
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
        
        # 使用Gemini多模态工具处理内容
        from .gemini_multimodal_utils import GeminiMultimodalUtils
        multimodal_utils = GeminiMultimodalUtils()
        
        # 处理内容
        if isinstance(message.content, str):
            parts = [{"text": message.content}]
        elif isinstance(message.content, list):
            parts = multimodal_utils.process_content_to_gemini_format(message.content)
        else:
            parts = [{"text": str(message.content)}]
        
        # 处理工具调用
        if isinstance(message, AIMessage) and message.tool_calls:
            # 替换内容为工具调用
            tool_parts = []
            for tool_call in message.tool_calls:
                function_call = {
                    "name": tool_call.get("function", {}).get("name", ""),
                    "args": tool_call.get("function", {}).get("arguments", {})
                }
                tool_parts.append({
                    "functionCall": function_call
                })
            
            # 如果有文本内容，保留
            if message.content and isinstance(message.content, str) and message.content.strip():
                tool_parts.insert(0, {"text": message.content})
            
            parts = tool_parts
        
        # 处理工具消息
        elif isinstance(message, ToolMessage):
            from .gemini_tools_utils import GeminiToolsUtils
            tools_utils = GeminiToolsUtils()
            
            # 确保工具结果是字符串或字典格式
            tool_result_content = message.content
            if isinstance(tool_result_content, list):
                # 如果是列表，手动提取文本内容
                text_parts = []
                for item in tool_result_content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                    else:
                        text_parts.append(str(item))
                tool_result_content = " ".join(text_parts)
            elif not isinstance(tool_result_content, (str, dict)):
                tool_result_content = str(tool_result_content)
            
            tool_response = tools_utils.create_tool_response_content(
                message.tool_call_id,
                tool_result_content  # type: ignore
            )
            parts = [tool_response]
        
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
        elif isinstance(message.content, list):
            # 确保列表中的元素都是正确的格式
            content = []
            for item in message.content:
                if isinstance(item, dict):
                    content.append(item)
                else:
                    content.append({"type": "text", "text": str(item)})
        else:
            content = [{"type": "text", "text": str(message.content)}]
        
        # 处理工具调用
        if isinstance(message, AIMessage) and message.tool_calls:
            # 替换内容为工具使用块
            tool_content = []
            for tool_call in message.tool_calls:
                tool_use_block = {
                    "type": "tool_use",
                    "id": tool_call.get("id", ""),
                    "name": tool_call.get("function", {}).get("name", ""),
                    "input": tool_call.get("function", {}).get("arguments", {})
                }
                tool_content.append(tool_use_block)
            
            # 如果有文本内容，保留
            if message.content and isinstance(message.content, str) and message.content.strip():
                tool_content.insert(0, {"type": "text", "text": message.content})
            
            content = tool_content
        
        # 处理工具消息
        elif isinstance(message, ToolMessage):
            content = [{
                "type": "tool_result",
                "tool_use_id": message.tool_call_id,
                "content": message.content if isinstance(message.content, str) else str(message.content)
            }]
        
        result = {
            "role": role,
            "content": content
        }
        
        # 添加名称（如果有）
        if message.name:
            result["name"] = message.name
        
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
    
    def convert_from_gemini_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从Gemini流式响应转换"""
        try:
            format_utils = self.format_utils_factory.get_format_utils("gemini")
            return format_utils.convert_stream_response(events)
        except Exception as e:
            self.logger.error(f"转换Gemini流式响应失败: {e}")
            # 回退到基本处理
            try:
                from .gemini_stream_utils import GeminiStreamUtils
                stream_utils = GeminiStreamUtils()
                text_content = stream_utils.extract_text_from_stream_events(events)
                return AIMessage(content=text_content)
            except:
                return AIMessage(content="")
    
    def convert_from_anthropic_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从Anthropic API响应转换（兼容性方法）"""
        return self.convert_from_provider_response("anthropic", response)
    
    def convert_from_anthropic_stream_events(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从Anthropic流式事件转换
        
        Args:
            events: Anthropic流式事件列表
            
        Returns:
            IBaseMessage: 基础消息
        """
        try:
            from .anthropic_stream_utils import AnthropicStreamUtils
            stream_utils = AnthropicStreamUtils()
            
            # 处理流式事件
            response = stream_utils.process_stream_events(events)
            
            # 转换为标准消息
            return self.convert_from_provider_response("anthropic", response)
        except Exception as e:
            self.logger.error(f"转换Anthropic流式事件失败: {e}")
            # 回退到基本处理
            try:
                from .anthropic_stream_utils import AnthropicStreamUtils
                stream_utils = AnthropicStreamUtils()
                text_content = stream_utils.extract_text_from_stream_events(events)
                return AIMessage(content=text_content)
            except:
                return AIMessage(content="")
    
    def extract_text_from_anthropic_stream(self, events: List[Dict[str, Any]]) -> str:
        """从Anthropic流式事件中提取文本内容
        
        Args:
            events: Anthropic流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        try:
            from .anthropic_stream_utils import AnthropicStreamUtils
            stream_utils = AnthropicStreamUtils()
            return stream_utils.extract_text_from_stream_events(events)
        except Exception as e:
            self.logger.error(f"提取Anthropic流式文本失败: {e}")
            return ""
    
    def extract_tool_calls_from_anthropic_stream(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从Anthropic流式事件中提取工具调用
        
        Args:
            events: Anthropic流式事件列表
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        try:
            from .anthropic_stream_utils import AnthropicStreamUtils
            stream_utils = AnthropicStreamUtils()
            return stream_utils.extract_tool_calls_from_stream_events(events)
        except Exception as e:
            self.logger.error(f"提取Anthropic流式工具调用失败: {e}")
            return []
    
    def extract_text_from_gemini_stream(self, events: List[Dict[str, Any]]) -> str:
        """从Gemini流式事件中提取文本内容"""
        try:
            from .gemini_stream_utils import GeminiStreamUtils
            stream_utils = GeminiStreamUtils()
            return stream_utils.extract_text_from_stream_events(events)
        except Exception as e:
            self.logger.error(f"提取Gemini流式文本失败: {e}")
            return ""
    
    def extract_tool_calls_from_gemini_stream(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从Gemini流式事件中提取工具调用"""
        try:
            from .gemini_stream_utils import GeminiStreamUtils
            stream_utils = GeminiStreamUtils()
            return stream_utils.extract_tool_calls_from_stream_events(events)
        except Exception as e:
            self.logger.error(f"提取Gemini流式工具调用失败: {e}")
            return []
    
    def extract_thoughts_from_gemini_stream(self, events: List[Dict[str, Any]]) -> List[str]:
        """从Gemini流式事件中提取思考过程"""
        try:
            from .gemini_stream_utils import GeminiStreamUtils
            stream_utils = GeminiStreamUtils()
            return stream_utils.extract_thoughts_from_stream_events(events)
        except Exception as e:
            self.logger.error(f"提取Gemini流式思考过程失败: {e}")
            return []
    
    def parse_anthropic_stream_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析Anthropic流式响应行
        
        Args:
            line: 流式响应行
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件
        """
        try:
            from .anthropic_stream_utils import AnthropicStreamUtils
            stream_utils = AnthropicStreamUtils()
            return stream_utils.parse_stream_event(line)
        except Exception as e:
            self.logger.error(f"解析Anthropic流式行失败: {e}")
            return None


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