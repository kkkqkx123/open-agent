"""Gemini专用缓存管理器"""

from typing import Any, Optional, Sequence, Dict
from src.interfaces.messages import IBaseMessage

from ...core.cache_manager import CacheManager
from ...config.cache_config import BaseCacheConfig
from ...core.key_generator import LLMCacheKeyGenerator


class GeminiCacheManager(CacheManager):
    """Gemini专用缓存管理器（专注于客户端缓存）"""
    
    def __init__(self, config: BaseCacheConfig):
        """
        初始化Gemini缓存管理器
        
        Args:
            config: 缓存配置
        """
        super().__init__(config)
        # 使用Gemini专用的键生成器
        self._key_generator = GeminiCacheKeyGenerator()
    
    def generate_gemini_key(self, messages: Sequence[IBaseMessage], model: str = "",
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
    
    def get_gemini_response(self, messages: Sequence[IBaseMessage], model: str = "",
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
    
    def set_gemini_response(self, messages: Sequence[IBaseMessage], response: Any,
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


class GeminiCacheKeyGenerator(LLMCacheKeyGenerator):
    """Gemini专用缓存键生成器"""
    
    def generate_key(self, messages: Sequence[IBaseMessage], model: str = "",
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
        # 委托给统一的Gemini键生成器
        from ...core.key_generator import GeminiCacheKeyGenerator
        gemini_generator = GeminiCacheKeyGenerator(
            include_model=self.include_model,
            include_parameters=self.include_parameters
        )
        return gemini_generator.generate_key(messages, model, parameters, **kwargs)