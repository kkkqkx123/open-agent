"""混合Token计算器"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage  # type: ignore

from .base import ITokenCalculator
from ..token_parsers.base import TokenUsage
from .local_calculator import LocalTokenCalculator
from .api_calculator import ApiTokenCalculator

logger = logging.getLogger(__name__)


class HybridTokenCalculator(ITokenCalculator):
    """混合Token计算器，实现降级策略"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", provider: str = "openai", 
                 prefer_api: bool = True):
        """
        初始化混合Token计算器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
            prefer_api: 是否优先使用API计算器
        """
        self.model_name = model_name
        self.provider = provider
        self.prefer_api = prefer_api
        
        # 初始化本地和API计算器
        self._local_calculator = LocalTokenCalculator(model_name, provider)
        self._api_calculator = ApiTokenCalculator(model_name, provider)
        
        # 统计信息
        self._stats = {
            "local_count": 0,
            "api_count": 0,
            "fallback_count": 0
        }
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        if self.prefer_api:
            # 优先使用API计算器
            if self._api_calculator.is_api_usage_available():
                self._stats["api_count"] += 1
                return self._api_calculator.count_tokens(text)
            else:
                # 降级到本地计算器
                self._stats["fallback_count"] += 1
                self._stats["local_count"] += 1
                return self._local_calculator.count_tokens(text)
        else:
            # 优先使用本地计算器
            self._stats["local_count"] += 1
            return self._local_calculator.count_tokens(text)
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        if self.prefer_api:
            # 优先使用API计算器
            if self._api_calculator.is_api_usage_available():
                self._stats["api_count"] += 1
                return self._api_calculator.count_messages_tokens(messages)
            else:
                # 降级到本地计算器
                self._stats["fallback_count"] += 1
                self._stats["local_count"] += 1
                return self._local_calculator.count_messages_tokens(messages)
        else:
            # 优先使用本地计算器
            self._stats["local_count"] += 1
            return self._local_calculator.count_messages_tokens(messages)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        local_info = self._local_calculator.get_model_info()
        api_info = self._api_calculator.get_model_info()
        
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "calculator_type": "hybrid",
            "prefer_api": self.prefer_api,
            "local_calculator": local_info,
            "api_calculator": api_info,
            "stats": self._stats,
            "api_available": self._api_calculator.is_api_usage_available()
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
        return self._api_calculator.update_from_api_response(response, context)
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """
        获取最近的API使用情况
        
        Returns:
            TokenUsage: 最近的API使用情况，如果没有则返回None
        """
        return self._api_calculator.get_last_api_usage()
    
    def is_api_usage_available(self) -> bool:
        """
        检查是否有可用的API使用数据
        
        Returns:
            bool: 是否有可用的API使用数据
        """
        return self._api_calculator.is_api_usage_available()
    
    def set_prefer_api(self, prefer_api: bool) -> None:
        """
        设置是否优先使用API计算器
        
        Args:
            prefer_api: 是否优先使用API计算器
        """
        self.prefer_api = prefer_api
        logger.debug(f"设置优先使用API计算器: {prefer_api}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total = self._stats["local_count"] + self._stats["api_count"]
        fallback_rate = (
            self._stats["fallback_count"] / total * 100 
            if total > 0 else 0
        )
        
        return {
            **self._stats,
            "total_requests": total,
            "fallback_rate_percent": fallback_rate,
            "api_available": self.is_api_usage_available()
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "local_count": 0,
            "api_count": 0,
            "fallback_count": 0
        }
        logger.debug("已重置混合计算器统计信息")
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._api_calculator.clear_cache()
        logger.debug("已清空混合计算器缓存")
    
    def force_local_calculation(self, text: str) -> int:
        """
        强制使用本地计算器计算token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        self._stats["local_count"] += 1
        return self._local_calculator.count_tokens(text)
    
    def force_api_calculation(self, text: str) -> int:
        """
        强制使用API计算器计算token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        if self._api_calculator.is_api_usage_available():
            self._stats["api_count"] += 1
            return self._api_calculator.count_tokens(text)
        else:
            logger.warning("API计算器不可用，降级到本地计算器")
            self._stats["fallback_count"] += 1
            self._stats["local_count"] += 1
            return self._local_calculator.count_tokens(text)