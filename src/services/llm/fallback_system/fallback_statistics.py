"""降级统计管理器

负责统计信息的收集和管理，包括 Core 层和 Services 层的统计数据。
"""

from typing import Any, Dict, List
from .fallback_config import FallbackSession


class FallbackStatistics:
    """降级统计管理器
    
    负责统计信息的收集和管理，包括：
    1. Core 层统计信息（会话、尝试次数、成功率等）
    2. Services 层统计信息（请求、降级次数等）
    3. 统计数据的计算和更新
    4. 统计数据的查询和重置
    """
    
    def __init__(self):
        """初始化降级统计管理器"""
        # 统计信息（整合 Core 和 Services 层）
        self._stats = {
            # Core 层统计
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_attempts": 0,
            "average_attempts": 0.0,
            "fallback_usage": 0,
            "fallback_rate": 0.0,
            # Services 层统计
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }
    
    def update_core_stats(self, sessions: List[FallbackSession]) -> None:
        """
        更新 Core 层统计信息
        
        Args:
            sessions: 会话列表
        """
        total_sessions = len(sessions)
        successful_sessions = sum(1 for s in sessions if s.success)
        failed_sessions = total_sessions - successful_sessions
        
        total_attempts = sum(s.get_total_attempts() for s in sessions)
        
        # 计算平均尝试次数
        avg_attempts = total_attempts / total_sessions if total_sessions > 0 else 0
        
        # 计算降级使用率
        fallback_usage = sum(1 for s in sessions if s.get_total_attempts() > 1)
        fallback_rate = fallback_usage / total_sessions if total_sessions > 0 else 0
        
        self._stats.update({
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": failed_sessions,
            "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
            "total_attempts": total_attempts,
            "average_attempts": avg_attempts,
            "fallback_usage": fallback_usage,
            "fallback_rate": fallback_rate,
        })
    
    def increment_total_requests(self) -> None:
        """增加总请求数"""
        self._stats["total_requests"] += 1
    
    def increment_successful_requests(self) -> None:
        """增加成功请求数"""
        self._stats["successful_requests"] += 1
    
    def increment_failed_requests(self) -> None:
        """增加失败请求数"""
        self._stats["failed_requests"] += 1
    
    def increment_group_fallbacks(self) -> None:
        """增加任务组降级次数"""
        self._stats["group_fallbacks"] += 1
    
    def increment_pool_fallbacks(self) -> None:
        """增加轮询池降级次数"""
        self._stats["pool_fallbacks"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取降级统计信息（整合 Core 和 Services 层）
        
        Returns:
            统计信息字典
        """
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self._stats = {
            # Core 层统计
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_attempts": 0,
            "average_attempts": 0.0,
            "fallback_usage": 0,
            "fallback_rate": 0.0,
            # Services 层统计
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }
    
    def get_core_stats(self) -> Dict[str, Any]:
        """
        获取 Core 层统计信息
        
        Returns:
            Core 层统计信息字典
        """
        return {
            "total_sessions": self._stats["total_sessions"],
            "successful_sessions": self._stats["successful_sessions"],
            "failed_sessions": self._stats["failed_sessions"],
            "success_rate": self._stats.get("success_rate", 0),
            "total_attempts": self._stats["total_attempts"],
            "average_attempts": self._stats["average_attempts"],
            "fallback_usage": self._stats["fallback_usage"],
            "fallback_rate": self._stats["fallback_rate"],
        }
    
    def get_services_stats(self) -> Dict[str, Any]:
        """
        获取 Services 层统计信息
        
        Returns:
            Services 层统计信息字典
        """
        return {
            "total_requests": self._stats["total_requests"],
            "successful_requests": self._stats["successful_requests"],
            "failed_requests": self._stats["failed_requests"],
            "group_fallbacks": self._stats["group_fallbacks"],
            "pool_fallbacks": self._stats["pool_fallbacks"],
        }