"""Gemini专用缓存管理器"""

from typing import Any, Optional, Sequence, Dict
from langchain_core.messages import BaseMessage

from .cache_manager import CacheManager
from .cache_config import CacheConfig
from .key_generator import LLMCacheKeyGenerator


class GeminiCacheManager(CacheManager):
    """Gemini专用缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        """
        初始化Gemini缓存管理器
        
        Args:
            config: 缓存配置
        """
        super().__init__(config)
        # 使用Gemini专用的键生成器
        self._key_generator = GeminiCacheKeyGenerator()
    
    def generate_gemini_key(self, messages: Sequence[BaseMessage], model: str = "",
    parameters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        生成Gemini缓存键
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        return self._key_generator.generate_key(messages, model, parameters, **kwargs)
    
    def get_gemini_response(self, messages: Sequence[BaseMessage], model: str = "",
    parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Any]:
        """
        获取Gemini响应缓存
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存的响应，如果不存在则返回None
        """
        key = self.generate_gemini_key(messages, model, parameters, **kwargs)
        return self.get(key)
    
    def set_gemini_response(self, messages: Sequence[BaseMessage], response: Any,
    model: str = "", parameters: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None,
    **kwargs) -> None:
        """
        设置Gemini响应缓存
        
        Args:
            messages: 消息列表
            response: 响应内容
            model: 模型名称
            parameters: 生成参数
            ttl: 生存时间（秒）
            **kwargs: 其他参数
        """
        key = self.generate_gemini_key(messages, model, parameters, **kwargs)
        self.set(key, response, ttl)
    
    def get_gemini_cache_params(self) -> Dict[str, Any]:
        """
        获取Gemini缓存参数
        
        Returns:
            Gemini缓存参数字典
        """
        if not self.config.content_cache_enabled:
            return {}
        
        cache_params = {}
        
        if self.config.content_cache_display_name:
            cache_params["cached_content"] = self.config.content_cache_display_name
        
        return cache_params


class GeminiCacheKeyGenerator(LLMCacheKeyGenerator):
    """Gemini专用缓存键生成器"""
    
    def generate_key(self, messages: Sequence[BaseMessage], model: str = "",
                    parameters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        生成Gemini缓存键
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        # Gemini特定的键前缀
        key_parts = ["gemini"]
        
        # 添加模型名称
        if self.include_model and model:
            key_parts.append(f"model:{model}")
        
        # 序列化消息
        serialized_messages = self._serialize_messages_gemini(messages)
        key_parts.append(f"messages:{serialized_messages}")
        
        # 添加参数
        if self.include_parameters and parameters:
            serialized_params = self._serialize_parameters_gemini(parameters)
            key_parts.append(f"params:{serialized_params}")
        
        # 添加其他参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{self._serialize_value(value)}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return self._hash_string(key_string)
    
    def _serialize_messages_gemini(self, messages: Sequence[BaseMessage]) -> str:
        """
        序列化Gemini消息列表
        
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
            
            # Gemini特定的额外属性
            if hasattr(message, "additional_kwargs") and message.additional_kwargs:
                for key, value in message.additional_kwargs.items():
                    message_parts.append(f"{key}:{value}")
            
            serialized.append(f"{{{','.join(message_parts)}}}")
        
        return f"[{','.join(serialized)}]"
    
    def _serialize_parameters_gemini(self, parameters: dict) -> str:
        """
        序列化Gemini参数字典
        
        Args:
            parameters: 参数字典
            
        Returns:
            序列化后的字符串
        """
        # Gemini特定的参数过滤
        filtered_params = {}
        gemini_params = [
            "temperature", "max_tokens", "max_output_tokens", "top_p", "top_k",
            "stop_sequences", "candidate_count", "system_instruction",
            "response_mime_type", "thinking_config", "safety_settings",
            "tool_choice", "tools", "user"
        ]
        
        for key, value in parameters.items():
            if key in gemini_params and value is not None and value != "":
                filtered_params[key] = value
        
        # 返回键值对格式，而不是JSON
        items = []
        for key, value in sorted(filtered_params.items()):
            items.append(f"{key}:{self._serialize_value(value)}")
        
        return f"{{{','.join(items)}}}"
    
    def _json_dumps(self, obj: Any) -> str:
        """JSON序列化"""
        import json
        return json.dumps(obj, sort_keys=True)
    
    def _hash_string(self, text: str) -> str:
        """生成字符串哈希"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值为字符串"""
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
        else:
            # 对于复杂对象，使用JSON序列化
            try:
                return self._json_dumps(value)
            except (TypeError, ValueError):
                return str(value)