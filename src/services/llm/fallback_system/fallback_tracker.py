"""降级跟踪器

整合了统计信息和会话管理功能，提供统一的降级跟踪和统计。
"""

from typing import Any, Dict, List, Optional, Tuple
from .fallback_config import FallbackSession


class FallbackTracker:
    """降级跟踪器
    
    整合了统计信息和会话管理功能，包括：
    1. 会话的创建、跟踪和管理
    2. 统计信息的收集和管理
    3. Core 层和 Services 层的统计数据
    4. 统计数据的计算和查询
    """
    
    def __init__(self, max_sessions: int = 1000):
        """
        初始化降级跟踪器
        
        Args:
            max_sessions: 最大会话数量，超过后会清理旧会话
        """
        self._sessions: List[FallbackSession] = []
        self._max_sessions = max_sessions
        
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
    
    # === 会话管理方法 ===
    
    def add_session(self, session: FallbackSession) -> None:
        """
        添加会话记录
        
        Args:
            session: 会话记录
        """
        self._sessions.append(session)
        
        # 如果超过最大会话数量，清理旧会话
        if len(self._sessions) > self._max_sessions:
            # 保留最新的会话
            self._sessions = self._sessions[-self._max_sessions:]
        
        # 更新统计信息
        self._update_core_stats()
    
    def get_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取降级会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            会话记录列表
        """
        sessions = self._sessions.copy()
        if limit:
            sessions = sessions[-limit:]
        return sessions
    
    def get_successful_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取成功的会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            成功的会话记录列表
        """
        sessions = [s for s in self._sessions if s.success]
        if limit:
            sessions = sessions[-limit:]
        return sessions
    
    def get_failed_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取失败的会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            失败的会话记录列表
        """
        sessions = [s for s in self._sessions if not s.success]
        if limit:
            sessions = sessions[-limit:]
        return sessions
    
    def get_sessions_by_model(self, model_name: str, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        根据模型名称获取会话记录
        
        Args:
            model_name: 模型名称
            limit: 限制返回数量
            
        Returns:
            指定模型的会话记录列表
        """
        sessions = [s for s in self._sessions if s.primary_model == model_name]
        if limit:
            sessions = sessions[-limit:]
        return sessions
    
    def clear_sessions(self) -> None:
        """清空会话记录"""
        self._sessions.clear()
        self._reset_stats()
    
    def clear_old_sessions(self, keep_count: int) -> None:
        """
        清理旧会话，保留指定数量的最新会话
        
        Args:
            keep_count: 保留的会话数量
        """
        if keep_count < 0:
            return
        
        if len(self._sessions) > keep_count:
            self._sessions = self._sessions[-keep_count:]
            self._update_core_stats()
    
    # === 统计信息方法 ===
    
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
    
    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self._reset_stats()
    
    # === 分析方法 ===
    
    def get_session_count(self) -> int:
        """
        获取会话总数
        
        Returns:
            会话总数
        """
        return len(self._sessions)
    
    def get_successful_session_count(self) -> int:
        """
        获取成功会话数
        
        Returns:
            成功会话数
        """
        return sum(1 for s in self._sessions if s.success)
    
    def get_failed_session_count(self) -> int:
        """
        获取失败会话数
        
        Returns:
            失败会话数
        """
        return sum(1 for s in self._sessions if not s.success)
    
    def get_average_attempts(self) -> float:
        """
        获取平均尝试次数
        
        Returns:
            平均尝试次数
        """
        if not self._sessions:
            return 0.0
        
        total_attempts = sum(s.get_total_attempts() for s in self._sessions)
        return total_attempts / len(self._sessions)
    
    def get_fallback_rate(self) -> float:
        """
        获取降级使用率
        
        Returns:
            降级使用率（0-1之间的浮点数）
        """
        if not self._sessions:
            return 0.0
        
        fallback_usage = sum(1 for s in self._sessions if s.get_total_attempts() > 1)
        return fallback_usage / len(self._sessions)
    
    def get_most_used_models(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        获取最常用的模型列表
        
        Args:
            limit: 返回的模型数量限制
            
        Returns:
            按使用次数排序的模型列表，每个元素为 (model_name, count) 元组
        """
        model_counts = {}
        for session in self._sessions:
            model_name = session.primary_model
            model_counts[model_name] = model_counts.get(model_name, 0) + 1
        
        # 按使用次数排序
        sorted_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_models[:limit]
    
    def get_error_summary(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        获取错误摘要
        
        Args:
            limit: 返回的错误类型数量限制
            
        Returns:
            按出现次数排序的错误类型列表，每个元素为 (error_type, count) 元组
        """
        error_counts = {}
        for session in self._sessions:
            if not session.success and session.final_error:
                error_type = type(session.final_error).__name__
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # 按出现次数排序
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_errors[:limit]
    
    # === 内部方法 ===
    
    def _update_core_stats(self) -> None:
        """
        更新 Core 层统计信息
        """
        total_sessions = len(self._sessions)
        successful_sessions = sum(1 for s in self._sessions if s.success)
        failed_sessions = total_sessions - successful_sessions
        
        total_attempts = sum(s.get_total_attempts() for s in self._sessions)
        
        # 计算平均尝试次数
        avg_attempts = total_attempts / total_sessions if total_sessions > 0 else 0
        
        # 计算降级使用率
        fallback_usage = sum(1 for s in self._sessions if s.get_total_attempts() > 1)
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
    
    def _reset_stats(self) -> None:
        """重置统计信息"""
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