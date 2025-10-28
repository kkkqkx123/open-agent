"""API Token计算器"""

import hashlib
import logging
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage  # type: ignore

from .base import ITokenCalculator
from ..token_parsers.base import TokenUsage
from ..token_parsers import OpenAIParser, GeminiParser, AnthropicParser
from ..utils.encoding_protocol import extract_content_as_string

logger = logging.getLogger(__name__)


class ApiTokenCalculator(ITokenCalculator):
    """API Token计算器，基于API响应解析token使用信息"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", provider: str = "openai", 
                 supports_caching: bool = True):
        """
        初始化API Token计算器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
            supports_caching: 是否支持缓存
        """
        self.model_name = model_name
        self.provider = provider
        self.supports_caching = supports_caching
        self._last_usage: Optional[TokenUsage] = None
        self._usage_cache: Dict[str, TokenUsage] = {}
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "api_success": 0,
            "api_failed": 0,
            "fallback_to_local": 0
        }
        
        # 初始化解析器
        self._parsers = {
            "openai": OpenAIParser(),
            "gemini": GeminiParser(),
            "anthropic": AnthropicParser()
        }
        
        # 获取对应的解析器
        self._parser = self._parsers.get(provider)
        if not self._parser:
            logger.warning(f"未找到提供商 {provider} 的解析器，使用OpenAI解析器")
            self._parser = self._parsers["openai"]
    
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量（基于缓存的API响应）
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量，如果没有可用数据则返回None
        """
        self._stats["total_requests"] += 1
        
        if not self.supports_caching:
            # 如果不支持缓存，返回None
            self._stats["fallback_to_local"] += 1
            logger.warning(f"不支持缓存，返回None: {text[:50]}...")
            return None
        
        # 生成缓存key
        cache_key = self._generate_cache_key(text)
        
        # 检查缓存
        if cache_key in self._usage_cache:
            self._stats["api_success"] += 1
            return self._usage_cache[cache_key].total_tokens
        
        # 如果没有缓存数据，返回None
        self._stats["fallback_to_local"] += 1
        logger.warning(f"没有找到文本的API使用数据，返回None: {text[:50]}...")
        return None
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> Optional[int]:
        """
        计算消息列表的token数量（基于缓存的API响应）
        
        Args:
            messages: 消息列表
            
        Returns:
            Optional[int]: token数量，如果没有可用数据则返回None
        """
        self._stats["total_requests"] += 1
        
        if not self.supports_caching:
            # 如果不支持缓存，返回None
            self._stats["fallback_to_local"] += 1
            return None
        
        # 将消息转换为文本进行缓存查找
        text_context = self._messages_to_text(messages)
        return self.count_tokens(text_context)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "calculator_type": "api",
            "parser": self._parser.get_provider_name() if self._parser else "unknown",
            "supports_caching": self.supports_caching,
            "cache_size": len(self._usage_cache),
            "has_last_usage": self._last_usage is not None,
            "stats": self._stats
        }
    
    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        """
        从API响应更新token信息
        
        Args:
            response: API响应数据
            context: 上下文文本（可选）
            
        Returns:
            bool: 是否成功更新
        """
        self._stats["total_requests"] += 1
        
        try:
            # 使用对应的解析器解析响应
            if not self._parser:
                logger.warning(f"没有可用的解析器")
                self._stats["api_failed"] += 1
                return False
                
            usage = self._parser.parse_response(response)
            if not usage:
                logger.warning(f"无法解析 {self.provider} API响应")
                self._stats["api_failed"] += 1
                return False
            
            # 更新最后一次使用情况
            self._last_usage = usage
            self._stats["api_success"] += 1
            
            # 如果支持缓存且有上下文，更新缓存
            if self.supports_caching and context:
                cache_key = self._generate_cache_key(context)
                self._usage_cache[cache_key] = usage
                logger.debug(f"已缓存API使用数据，key: {cache_key}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新API响应失败: {e}")
            self._stats["api_failed"] += 1
            return False
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """
        获取最近的API使用情况
        
        Returns:
            TokenUsage: 最近的API使用情况，如果没有则返回None
        """
        return self._last_usage
    
    def is_api_usage_available(self) -> bool:
        """
        检查是否有可用的API使用数据
        
        Returns:
            bool: 是否有可用的API使用数据
        """
        return self._last_usage is not None
    
    def is_supported(self) -> bool:
        """
        检查是否支持API计算
        
        Returns:
            bool: 是否支持API计算
        """
        return self.supports_caching
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total = self._stats["total_requests"]
        success_rate = (
            self._stats["api_success"] / total * 100 
            if total > 0 else 0
        )
        
        return {
            **self._stats,
            "success_rate_percent": success_rate,
            "cache_size": len(self._usage_cache),
            "supports_caching": self.supports_caching
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "api_success": 0,
            "api_failed": 0,
            "fallback_to_local": 0
        }
        logger.debug("已重置API计算器统计信息")
    
    def _generate_cache_key(self, content: str) -> str:
        """
        生成缓存key
        
        Args:
            content: 内容文本
            
        Returns:
            str: 缓存key
        """
        # 使用内容的哈希值作为key
        return hashlib.md5(f"{self.provider}:{self.model_name}:{content}".encode()).hexdigest()
    
    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        """
        将消息列表转换为文本
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 转换后的文本
        """
        texts = []
        for message in messages:
            content = extract_content_as_string(message.content)
            texts.append(f"{message.type}:{content}")
        return "\n".join(texts)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._usage_cache.clear()
        self._last_usage = None
        logger.debug("已清空API使用缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        return {
            "cache_size": len(self._usage_cache),
            "has_last_usage": self._last_usage is not None,
            "provider": self.provider,
            "model_name": self.model_name,
            "supports_caching": self.supports_caching
        }