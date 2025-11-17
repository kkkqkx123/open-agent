"""缓存键生成器"""

import hashlib
import json
from typing import Any, Dict, Optional, Sequence
from langchain_core.messages import BaseMessage

from .interfaces import ICacheKeyGenerator


class DefaultCacheKeyGenerator(ICacheKeyGenerator):
    """默认缓存键生成器"""
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        # 将所有参数序列化为字符串
        key_parts = []
        
        # 处理位置参数
        for arg in args:
            key_parts.append(self._serialize_value(arg))
        
        # 处理关键字参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{self._serialize_value(value)}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _serialize_value(self, value: Any) -> str:
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
            return f"[{','.join(self._serialize_value(v) for v in value)}]"
        elif isinstance(value, dict):
            items = []
            for k, v in sorted(value.items()):
                items.append(f"{k}:{self._serialize_value(v)}")
            return f"{{{','.join(items)}}}"
        elif isinstance(value, Sequence) and not isinstance(value, str):
            return f"[{','.join(self._serialize_value(v) for v in value)}]"
        else:
            # 对于复杂对象，使用JSON序列化
            try:
                return json.dumps(value, sort_keys=True, default=str)
            except (TypeError, ValueError):
                return str(value)


class LLMCacheKeyGenerator(ICacheKeyGenerator):
    """LLM专用缓存键生成器"""
    
    def __init__(self, include_model: bool = True, include_parameters: bool = True):
        """
        初始化LLM缓存键生成器
        
        Args:
            include_model: 是否包含模型名称
            include_parameters: 是否包含生成参数
        """
        self.include_model = include_model
        self.include_parameters = include_parameters
        self._default_generator = DefaultCacheKeyGenerator()

    def generate_key(self, messages: Sequence[BaseMessage], model: str = "",
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
            key_parts.append(f"{key}:{self._default_generator._serialize_value(value)}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _serialize_messages(self, messages: Sequence[BaseMessage]) -> str:
        """
        序列化消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            序列化后的字符串
        """
        serialized = []
        for message in messages:
            message_dict = {
                "type": message.type,
                "content": str(message.content),
            }
            
            # 添加额外的消息属性
            if hasattr(message, "additional_kwargs") and message.additional_kwargs:
                message_dict["additional_kwargs"] = message.additional_kwargs  # type: ignore
            
            serialized.append(json.dumps(message_dict, sort_keys=True))
        
        return f"[{','.join(serialized)}]"
    
    def _serialize_parameters(self, parameters: dict) -> str:
        """
        序列化参数字典
        
        Args:
            parameters: 参数字典
            
        Returns:
            序列化后的字符串
        """
        # 过滤掉None值和空值
        filtered_params = {}
        for key, value in parameters.items():
            if value is not None and value != "":
                filtered_params[key] = value
        
        return json.dumps(filtered_params, sort_keys=True)


class AnthropicCacheKeyGenerator(LLMCacheKeyGenerator):
    """Anthropic专用缓存键生成器"""
    
    def generate_key(self, messages: Sequence[BaseMessage], model: str = "",
                    parameters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        生成Anthropic缓存键
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        # Anthropic特定的键前缀
        key_parts = ["anthropic"]
        
        # 添加模型名称
        if self.include_model and model:
            key_parts.append(f"model:{model}")
        
        # 序列化消息（Anthropic对系统消息有特殊处理）
        serialized_messages = self._serialize_messages_anthropic(messages)
        key_parts.append(f"messages:{serialized_messages}")
        
        # 添加参数
        if self.include_parameters and parameters:
            serialized_params = self._serialize_parameters_anthropic(parameters)
            key_parts.append(f"params:{serialized_params}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _serialize_messages_anthropic(self, messages: Sequence[BaseMessage]) -> str:
        """
        序列化Anthropic消息列表
        
        Args:
            messages: 消息列表
            
        Returns:
            序列化后的字符串
        """
        serialized = []
        for message in messages:
            message_dict = {
                "type": message.type,
                "content": str(message.content),
            }
            
            # Anthropic特定的额外属性
            if hasattr(message, "additional_kwargs") and message.additional_kwargs:
                message_dict["additional_kwargs"] = message.additional_kwargs  # type: ignore
            
            serialized.append(json.dumps(message_dict, sort_keys=True))
        
        return f"[{','.join(serialized)}]"
    
    def _serialize_parameters_anthropic(self, parameters: dict) -> str:
        """
        序列化Anthropic参数字典
        
        Args:
            parameters: 参数字典
            
        Returns:
            序列化后的字符串
        """
        # Anthropic特定的参数过滤
        filtered_params = {}
        anthropic_params = [
            "temperature", "max_tokens", "top_p", "top_k", "stop_sequences",
            "tool_choice", "tools", "system", "thinking_config", "response_format",
            "metadata", "user"
        ]
        
        for key, value in parameters.items():
            if key in anthropic_params and value is not None and value != "":
                filtered_params[key] = value
        
        return json.dumps(filtered_params, sort_keys=True)