"""消息转换器实现

提供不同消息格式之间的转换功能。
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime

from src.interfaces.messages import IMessageConverter, IBaseMessage
# 不导入特定的异常类，使用通用的Exception
from src.infrastructure.llm.models import LLMMessage, MessageRole
from .types import HumanMessage, AIMessage, SystemMessage, ToolMessage, create_message_from_dict

if TYPE_CHECKING:
    # 避免运行时循环依赖
    pass


class MessageConverter(IMessageConverter):
    """消息转换器实现
    
    提供内部消息格式与外部格式之间的转换。
    """
    
    def __init__(self) -> None:
        """初始化消息转换器"""
        self._conversion_cache: Dict[str, IBaseMessage] = {}  # 简单的转换缓存
    
    def to_base_message(self, message: Any) -> IBaseMessage:
        """转换为标准消息格式"""
        try:
            # 如果已经是标准格式，直接返回
            if isinstance(message, IBaseMessage):
                return message
            
            # 检查缓存
            cache_key = self._get_cache_key(message)
            cached_result = self._conversion_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 根据类型进行转换
            if isinstance(message, LLMMessage):
                result: IBaseMessage = self._from_llm_message(message)
            elif isinstance(message, dict):
                result = self._from_dict(message)
            elif hasattr(message, 'content') and hasattr(message, 'role'):
                # 对象格式（类似LLMMessage）
                result = self._from_object(message)
            else:
                # 默认转换为人类消息
                result = HumanMessage(content=str(message))
            
            # 缓存结果
            self._conversion_cache[cache_key] = result
            return result
            
        except Exception as e:
            # 转换失败时直接抛异常，让上层处理
            raise Exception(
                f"消息转换失败 - 目标类型: IBaseMessage, 源消息: {message}, 原始错误: {e}"
            ) from e
    
    def from_base_message(self, message: IBaseMessage) -> Any:
        """从标准消息格式转换"""
        try:
            if isinstance(message, LLMMessage):
                return message
            else:
                return self._to_llm_message(message)
        except Exception as e:
            # 转换失败时直接抛异常，让上层处理
            raise Exception(
                f"消息转换失败 - 目标类型: LLMMessage, 源消息: {message}, 原始错误: {e}"
            ) from e
    
    def convert_message_list(self, messages: List[Any]) -> List[IBaseMessage]:
        """批量转换消息列表为标准格式"""
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.to_base_message(msg))
        return converted_messages
    
    def convert_from_base_list(self, messages: List[IBaseMessage]) -> List[Any]:
        """批量转换标准消息列表"""
        converted_messages = []
        for msg in messages:
            converted_messages.append(self.from_base_message(msg))
        return converted_messages
    
    def _from_llm_message(self, llm_message: LLMMessage) -> IBaseMessage:
        """从LLMMessage转换"""
        if llm_message.role == MessageRole.USER:
            return HumanMessage(
                content=llm_message.content,
                name=llm_message.name,
                id=llm_message.metadata.get("id"),
                additional_kwargs=llm_message.metadata
            )
        elif llm_message.role == MessageRole.ASSISTANT:
            return AIMessage(
                content=llm_message.content,
                name=llm_message.name,
                id=llm_message.metadata.get("id"),
                tool_calls=llm_message.tool_calls,
                additional_kwargs=llm_message.metadata
            )
        elif llm_message.role == MessageRole.SYSTEM:
            return SystemMessage(
                content=llm_message.content,
                name=llm_message.name,
                id=llm_message.metadata.get("id"),
                additional_kwargs=llm_message.metadata
            )
        elif llm_message.role == MessageRole.TOOL:
            tool_call_id = llm_message.metadata.get("tool_call_id", "")
            return ToolMessage(
                content=llm_message.content,
                tool_call_id=tool_call_id,
                name=llm_message.name,
                id=llm_message.metadata.get("id"),
                additional_kwargs=llm_message.metadata
            )
        else:
            return HumanMessage(
                content=llm_message.content,
                name=llm_message.name,
                id=llm_message.metadata.get("id"),
                additional_kwargs=llm_message.metadata
            )
    
    def _to_llm_message(self, base_message: IBaseMessage) -> LLMMessage:
        """转换为LLMMessage"""
        if isinstance(base_message, HumanMessage):
            role = MessageRole.USER
        elif isinstance(base_message, AIMessage):
            role = MessageRole.ASSISTANT
        elif isinstance(base_message, SystemMessage):
            role = MessageRole.SYSTEM
        elif isinstance(base_message, ToolMessage):
            role = MessageRole.TOOL
        else:
            role = MessageRole.USER
        
        # 构建元数据
        metadata = base_message.additional_kwargs.copy()
        
        # 处理特殊字段
        if isinstance(base_message, ToolMessage):
            metadata["tool_call_id"] = base_message.tool_call_id
        elif isinstance(base_message, AIMessage) and base_message.tool_calls:
            metadata["tool_calls"] = base_message.tool_calls
        
        # 添加通用字段
        if base_message.id:
            metadata["id"] = base_message.id
        if base_message.name:
            metadata["name"] = base_message.name
        
        # 处理内容
        content = base_message.content
        if isinstance(content, list):
            # 将列表内容转换为字符串
            content = " ".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
                if isinstance(item, (dict, str))
            )
        elif not isinstance(content, str):
            content = str(content)
        
        # 获取时间戳
        timestamp = datetime.now()
        if hasattr(base_message, 'timestamp'):
            ts = base_message.timestamp
            timestamp = ts if isinstance(ts, datetime) else datetime.now()
        
        return LLMMessage(
            role=role,
            content=content,
            name=base_message.name,
            metadata=metadata,
            timestamp=timestamp
        )
    
    def _from_dict(self, message_dict: Dict[str, Any]) -> IBaseMessage:
        """从字典转换"""
        try:
            return create_message_from_dict(message_dict)
        except Exception as e:
            # 字典转换失败时直接抛异常
            raise Exception(
                f"字典消息转换失败 - 目标类型: IBaseMessage, 源数据: {message_dict}, 原始错误: {e}"
            ) from e
    
    def _from_object(self, message_obj: Any) -> IBaseMessage:
        """从对象转换"""
        try:
            content = getattr(message_obj, 'content', '')
            role = getattr(message_obj, 'role', 'human')
            name = getattr(message_obj, 'name', None)
            
            # 标准化role值
            if hasattr(role, 'value') and not isinstance(role, str):  # 枚举类型
                role_str = role.value
            else:
                role_str = str(role)
            
            kwargs = {}
            if name:
                kwargs['name'] = name
            
            # 尝试获取其他属性
            for attr in ['id', 'tool_call_id', 'tool_calls']:
                if hasattr(message_obj, attr):
                    kwargs[attr] = getattr(message_obj, attr)
            
            if role_str in ["human", "user"]:
                return HumanMessage(content=content, **kwargs)
            elif role_str in ["ai", "assistant"]:
                return AIMessage(content=content, **kwargs)
            elif role_str == "system":
                return SystemMessage(content=content, **kwargs)
            elif role_str == "tool":
                tool_call_id = kwargs.get("tool_call_id", "")
                return ToolMessage(content=content, tool_call_id=tool_call_id, **kwargs)
            else:
                return HumanMessage(content=content, **kwargs)
                
        except Exception as e:
            # 对象转换失败时直接抛异常
            raise Exception(
                f"对象消息转换失败 - 目标类型: IBaseMessage, 源对象: {message_obj}, 原始错误: {e}"
            ) from e
    
    def _get_cache_key(self, message: Any) -> str:
        """生成缓存键"""
        try:
            if isinstance(message, IBaseMessage):
                # 对于IBaseMessage对象，使用类型和内容生成键
                content = str(message.content) if hasattr(message, 'content') else ""
                msg_type = message.type
                return f"{msg_type}:{hash(content)}"
            elif isinstance(message, LLMMessage):
                # 对于LLMMessage对象
                content = str(message.content) if hasattr(message, 'content') else ""
                msg_type = message.role.value if hasattr(message.role, 'value') else str(message.role)
                return f"{msg_type}:{hash(content)}"
            elif isinstance(message, dict):
                # 对于字典，使用排序后的JSON字符串
                import json
                return f"dict:{hash(json.dumps(message, sort_keys=True))}"
            else:
                # 对于其他对象，使用字符串表示
                return f"other:{hash(str(message))}"
        except Exception:
            # 生成缓存键失败时使用默认值
            return f"fallback:{id(message)}"
    
    def clear_cache(self) -> None:
        """清空转换缓存"""
        self._conversion_cache.clear()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._conversion_cache)


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


def convert_to_base_message(message: Any) -> IBaseMessage:
    """便捷函数：转换为标准消息格式"""
    return get_message_converter().to_base_message(message)


def convert_from_base_message(message: IBaseMessage) -> Any:
    """便捷函数：从标准消息格式转换"""
    return get_message_converter().from_base_message(message)


def convert_message_list(messages: List[Any]) -> List[IBaseMessage]:
    """便捷函数：批量转换消息列表为标准格式"""
    return get_message_converter().convert_message_list(messages)


def convert_from_base_list(messages: List[IBaseMessage]) -> List[Any]:
    """便捷函数：批量转换标准消息列表"""
    return get_message_converter().convert_from_base_list(messages)