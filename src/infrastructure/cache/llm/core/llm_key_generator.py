"""LLM缓存键生成器

提供LLM专用的缓存键生成功能，支持多种LLM提供商。
"""

import hashlib
import json
from typing import Any, Dict, Optional, Sequence, List, Set
from src.interfaces.messages import IBaseMessage
from src.interfaces.llm import ICacheKeyGenerator


class BaseKeySerializer:
    """基础键序列化器，提供通用的序列化功能"""
    
    @staticmethod
    def serialize_value(value: Any) -> str:
        """
        序列化值为字符串
        
        Args:
            value: 要序列化的值
            
        Returns:
            序列化后的字符串
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return f"[{','.join(BaseKeySerializer.serialize_value(v) for v in value)}]"
        elif isinstance(value, dict):
            items = []
            for k, v in sorted(value.items()):
                items.append(f"{k}:{BaseKeySerializer.serialize_value(v)}")
            return f"{{{','.join(items)}}}"
        elif isinstance(value, Sequence) and not isinstance(value, str):
            return f"[{','.join(BaseKeySerializer.serialize_value(v) for v in value)}]"
        else:
            # 对于复杂对象，使用JSON序列化
            try:
                return json.dumps(value, sort_keys=True, default=str)
            except (TypeError, ValueError):
                return str(value)
    
    @staticmethod
    def hash_string(text: str) -> str:
        """生成字符串哈希"""
        return hashlib.md5(text.encode()).hexdigest()
    
    @staticmethod
    def json_dumps(obj: Any) -> str:
        """JSON序列化"""
        return json.dumps(obj, sort_keys=True)


class MessageSerializer:
    """消息序列化器"""
    
    @staticmethod
    def serialize_messages_json(messages: Sequence[IBaseMessage]) -> str:
        """
        使用JSON格式序列化消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            序列化后的字符串
        """
        serialized: List[str] = []
        for message in messages:
            message_dict: Dict[str, Any] = {
                "type": message.type,
                "content": str(message.content),
            }
            
            # 添加额外的消息属性
            if hasattr(message, "additional_kwargs") and message.additional_kwargs:
                message_dict["additional_kwargs"] = message.additional_kwargs
            
            serialized.append(json.dumps(message_dict, sort_keys=True))
        
        return f"[{','.join(serialized)}]"
    
    @staticmethod
    def serialize_messages_kv(messages: Sequence[IBaseMessage]) -> str:
        """
        使用键值对格式序列化消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            序列化后的字符串
        """
        serialized = []
        for message in messages:
            message_parts = []
            message_parts.append(f"type:{message.type}")
            message_parts.append(f"content:{str(message.content)}")
            
            # 添加额外的消息属性
            if hasattr(message, "additional_kwargs") and message.additional_kwargs:
                for key, value in message.additional_kwargs.items():
                    message_parts.append(f"{key}:{BaseKeySerializer.serialize_value(value)}")
            
            serialized.append(f"{{{','.join(message_parts)}}}")
        
        return f"[{','.join(serialized)}]"


class ParameterFilter:
    """参数过滤器"""
    
    # Anthropic支持的参数
    ANTHROPIC_PARAMS: Set[str] = {
        "temperature", "max_tokens", "top_p", "top_k", "stop_sequences",
        "tool_choice", "tools", "system", "thinking_config", "response_format",
        "metadata", "user"
    }
    
    # Gemini支持的参数
    GEMINI_PARAMS: Set[str] = {
        "temperature", "max_tokens", "max_output_tokens", "top_p", "top_k",
        "stop_sequences", "candidate_count", "system_instruction",
        "response_mime_type", "thinking_config", "safety_settings",
        "tool_choice", "tools", "user"
    }
    
    @staticmethod
    def filter_parameters(parameters: Dict[str, Any],
                         allowed_params: Set[str],
                         filter_none: bool = True,
                         filter_empty: bool = True) -> Dict[str, Any]:
        """
        过滤参数字典
        
        Args:
            parameters: 原始参数字典
            allowed_params: 允许的参数集合
            filter_none: 是否过滤None值
            filter_empty: 是否过滤空字符串值
            
        Returns:
            过滤后的参数字典
        """
        filtered_params = {}
        for key, value in parameters.items():
            if key not in allowed_params:
                continue
            
            if filter_none and value is None:
                continue
                
            if filter_empty and value == "":
                continue
            
            filtered_params[key] = value
        
        return filtered_params
    
    @staticmethod
    def serialize_parameters_json(parameters: Dict[str, Any]) -> str:
        """使用JSON格式序列化参数"""
        return json.dumps(parameters, sort_keys=True)
    
    @staticmethod
    def serialize_parameters_kv(parameters: Dict[str, Any]) -> str:
        """使用键值对格式序列化参数"""
        items = []
        for key, value in sorted(parameters.items()):
            items.append(f"{key}:{BaseKeySerializer.serialize_value(value)}")
        return f"{{{','.join(items)}}}"


class LLMCacheKeyGenerator(ICacheKeyGenerator):
    """LLM专用缓存键生成器"""
    
    def __init__(self,
                 include_model: bool = True,
                 include_parameters: bool = True,
                 provider_prefix: str = ""):
        """
        初始化LLM缓存键生成器
        
        Args:
            include_model: 是否包含模型名称
            include_parameters: 是否包含生成参数
            provider_prefix: 提供商前缀
        """
        self.include_model = include_model
        self.include_parameters = include_parameters
        self.provider_prefix = provider_prefix

    def generate_key(self, messages: Sequence[IBaseMessage], model: str = "",
                    parameters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        生成LLM缓存键
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        key_parts = []
        
        # 添加提供商前缀
        if self.provider_prefix:
            key_parts.append(self.provider_prefix)
        
        # 添加模型名称
        if self.include_model and model:
            key_parts.append(f"model:{model}")
        
        # 序列化消息
        serialized_messages = self._serialize_messages(messages)
        key_parts.append(f"messages:{serialized_messages}")
        
        # 添加参数
        if self.include_parameters and parameters:
            serialized_params = self._serialize_parameters(parameters)
            key_parts.append(f"params:{serialized_params}")
        
        # 添加其他参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{BaseKeySerializer.serialize_value(value)}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return BaseKeySerializer.hash_string(key_string)
    
    def _serialize_messages(self, messages: Sequence[IBaseMessage]) -> str:
        """序列化消息列表（子类可重写）"""
        return MessageSerializer.serialize_messages_json(messages)
    
    def _serialize_parameters(self, parameters: Dict[str, Any]) -> str:
        """序列化参数字典（子类可重写）"""
        # 默认过滤掉None值和空值
        filtered_params = ParameterFilter.filter_parameters(
            parameters,
            set(parameters.keys()),  # 允许所有参数
            filter_none=True,
            filter_empty=True
        )
        return ParameterFilter.serialize_parameters_json(filtered_params)


class AnthropicCacheKeyGenerator(LLMCacheKeyGenerator):
    """Anthropic专用缓存键生成器"""
    
    def __init__(self, include_model: bool = True, include_parameters: bool = True):
        super().__init__(
            include_model=include_model,
            include_parameters=include_parameters,
            provider_prefix="anthropic"
        )
    
    def _serialize_parameters(self, parameters: Dict[str, Any]) -> str:
        """序列化Anthropic参数"""
        filtered_params = ParameterFilter.filter_parameters(
            parameters,
            ParameterFilter.ANTHROPIC_PARAMS
        )
        return ParameterFilter.serialize_parameters_json(filtered_params)


class GeminiCacheKeyGenerator(LLMCacheKeyGenerator):
    """Gemini专用缓存键生成器"""
    
    def __init__(self, include_model: bool = True, include_parameters: bool = True):
        super().__init__(
            include_model=include_model,
            include_parameters=include_parameters,
            provider_prefix="gemini"
        )
    
    def _serialize_messages(self, messages: Sequence[IBaseMessage]) -> str:
        """序列化Gemini消息（使用键值对格式）"""
        return MessageSerializer.serialize_messages_kv(messages)
    
    def _serialize_parameters(self, parameters: Dict[str, Any]) -> str:
        """序列化Gemini参数（使用键值对格式）"""
        filtered_params = ParameterFilter.filter_parameters(
            parameters,
            ParameterFilter.GEMINI_PARAMS
        )
        return ParameterFilter.serialize_parameters_kv(filtered_params)