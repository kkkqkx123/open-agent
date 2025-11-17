"""Token处理器基础实现

为ITokenProcessor提供默认实现。
"""

import logging
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage  # type: ignore

from .base_processor import ITokenProcessor
from .token_types import TokenUsage

logger = logging.getLogger(__name__)


class BaseTokenProcessor(ITokenProcessor):
    """Token处理器基础实现类
    
    提供新方法的默认实现，现有processor可以继承此类。
    """
    
    def __init__(self, model_name: str, provider: str):
        """
        初始化基础Token处理器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
        """
        self.model_name = model_name
        self.provider = provider
        self._last_usage: Optional[TokenUsage] = None
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "degradation_events": 0
        }
    
    # 缓存相关方法的默认实现
    def supports_caching(self) -> bool:
        """默认不支持缓存"""
        return False
    
    def clear_cache(self) -> None:
        """默认空实现"""
        logger.debug("缓存功能未启用")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """默认返回空缓存统计"""
        return {
            "supports_caching": False,
            "cache_size": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    # 降级策略相关方法的默认实现
    def supports_degradation(self) -> bool:
        """默认不支持降级策略"""
        return False
    
    def set_degradation_enabled(self, enabled: bool) -> None:
        """默认空实现"""
        logger.debug(f"降级策略功能未启用，设置: {enabled}")
    
    def is_degradation_enabled(self) -> bool:
        """默认返回False"""
        return False
    
    # 统计功能的默认实现
    def get_stats(self) -> Dict[str, Any]:
        """获取基础统计信息"""
        total = self._stats["total_requests"]
        success_rate = (
            self._stats["successful_calculations"] / total * 100 
            if total > 0 else 0
        )
        
        return {
            **self._stats,
            "success_rate_percent": success_rate,
            "model_name": self.model_name,
            "provider": self.provider,
            "supports_caching": self.supports_caching(),
            "supports_degradation": self.supports_degradation(),
            "supports_conversation_tracking": self.supports_conversation_tracking()
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "degradation_events": 0
        }
        logger.debug("已重置统计信息")
    
    # 对话跟踪相关方法的默认实现
    def supports_conversation_tracking(self) -> bool:
        """默认不支持对话跟踪"""
        return False
    
    def set_conversation_tracking_enabled(self, enabled: bool) -> None:
        """默认空实现"""
        logger.debug(f"对话跟踪功能未启用，设置: {enabled}")
    
    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """默认返回None"""
        return None
    
    def clear_conversation_history(self) -> None:
        """默认空实现"""
        logger.debug("对话跟踪功能未启用")
    
    # 辅助方法
    def _update_stats_on_success(self) -> None:
        """更新成功统计"""
        self._stats["total_requests"] += 1
        self._stats["successful_calculations"] += 1
    
    def _update_stats_on_failure(self) -> None:
        """更新失败统计"""
        self._stats["total_requests"] += 1
        self._stats["failed_calculations"] += 1
    
    def _update_cache_hit(self) -> None:
        """更新缓存命中统计"""
        self._stats["cache_hits"] += 1
    
    def _update_cache_miss(self) -> None:
        """更新缓存未命中统计"""
        self._stats["cache_misses"] += 1
    
    def _update_degradation_event(self) -> None:
        """更新降级事件统计"""
        self._stats["degradation_events"] += 1
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.provider
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """获取最近的API使用情况"""
        return self._last_usage
    
    def is_api_usage_available(self) -> bool:
        """检查是否有可用的API使用数据"""
        return self._last_usage is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取基础模型信息"""
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "processor_type": self.__class__.__name__,
            "supports_caching": self.supports_caching(),
            "supports_degradation": self.supports_degradation(),
            "supports_conversation_tracking": self.supports_conversation_tracking(),
            "stats": self.get_stats()
        }
    
    # 核心方法的默认实现
    def count_tokens(self, text: str) -> Optional[int]:
        """默认不支持token计数"""
        logger.debug(f"Token计数功能未实现 (model={self.model_name}, provider={self.provider})")
        return None
    
    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """默认不支持消息token计数"""
        logger.debug(f"消息Token计数功能未实现 (model={self.model_name}, provider={self.provider})")
        return None
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """默认不支持解析响应"""
        logger.debug(f"响应解析功能未实现 (model={self.model_name}, provider={self.provider})")
        return None
    
    def update_from_api_response(self, response: Dict[str, Any], context: Optional[str] = None) -> bool:
        """默认不支持从API响应更新"""
        logger.debug(f"API响应更新功能未实现 (model={self.model_name}, provider={self.provider})")
        return False
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """默认不支持任何响应"""
        return False


class CachedTokenProcessor(BaseTokenProcessor):
    """支持缓存的Token处理器基础实现"""
    
    def __init__(self, model_name: str, provider: str, cache_size: int = 1000):
        """
        初始化缓存Token处理器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
            cache_size: 缓存大小
        """
        super().__init__(model_name, provider)
        self.cache_size = cache_size
        self._usage_cache: Dict[str, TokenUsage] = {}
    
    def supports_caching(self) -> bool:
        """支持缓存"""
        return True
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._usage_cache.clear()
        logger.debug("已清空缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "supports_caching": True,
            "cache_size": len(self._usage_cache),
            "max_cache_size": self.cache_size,
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"]
        }
    
    def _get_from_cache(self, cache_key: str) -> Optional[TokenUsage]:
        """从缓存获取数据"""
        if cache_key in self._usage_cache:
            self._update_cache_hit()
            return self._usage_cache[cache_key]
        self._update_cache_miss()
        return None
    
    def _add_to_cache(self, cache_key: str, usage: TokenUsage) -> None:
        """添加数据到缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self._usage_cache) >= self.cache_size:
            # 简单的FIFO策略，删除第一个条目
            oldest_key = next(iter(self._usage_cache))
            del self._usage_cache[oldest_key]
        
        self._usage_cache[cache_key] = usage
    
    def _generate_cache_key(self, content: str) -> str:
        """生成缓存key"""
        import hashlib
        return hashlib.md5(f"{self.provider}:{self.model_name}:{content}".encode()).hexdigest()


class DegradationTokenProcessor(BaseTokenProcessor):
    """支持降级策略的Token处理器基础实现"""
    
    def __init__(self, model_name: str, provider: str, degradation_enabled: bool = True):
        """
        初始化降级Token处理器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
            degradation_enabled: 是否启用降级策略
        """
        super().__init__(model_name, provider)
        self._degradation_enabled = degradation_enabled
    
    def supports_degradation(self) -> bool:
        """支持降级策略"""
        return True
    
    def set_degradation_enabled(self, enabled: bool) -> None:
        """设置是否启用降级策略"""
        self._degradation_enabled = enabled
        logger.debug(f"设置降级策略: {enabled}")
    
    def is_degradation_enabled(self) -> bool:
        """检查降级策略是否启用"""
        return self._degradation_enabled
    
    def _should_degrade(self, api_count: int, local_count: int, threshold: float = 0.25) -> bool:
        """
        判断是否应该降级
        
        Args:
            api_count: API计算的token数
            local_count: 本地计算的token数
            threshold: 降级阈值（API token数与本地token数的比例）
            
        Returns:
            bool: 是否应该降级
        """
        if not self._degradation_enabled:
            return False
        
        if api_count < local_count * threshold:
            self._update_degradation_event()
            logger.warning(
                f"API token count ({api_count}) is less than {threshold * 100}% of "
                f"local estimate ({local_count}), triggering degradation"
            )
            return True
        
        return False