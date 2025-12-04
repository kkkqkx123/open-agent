"""降级跟踪器基础设施模块

提供统一的降级跟踪和统计功能。
"""

from typing import Any, Dict, List, Optional, Tuple
from .fallback_config import FallbackSession, FallbackStats


class FallbackTracker:
    """降级跟踪器
    
    提供统一的降级跟踪和统计功能，包括会话管理和统计分析。
    """
    
    def __init__(self, max_sessions: int = 1000):
        """
        初始化降级跟踪器
        
        Args:
            max_sessions: 最大会话数量，超过后会清理旧会话
        """
        self._sessions: List[FallbackSession] = []
        self._max_sessions = max_sessions
        self._stats = FallbackStats()
    
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
        self._stats.update(session)
    
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
    
    def get_fallback_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取使用了降级的会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            使用了降级的会话记录列表
        """
        sessions = [s for s in self._sessions if s.get_fallback_usage()]
        if limit:
            sessions = sessions[-limit:]
        return sessions
    
    def clear_sessions(self) -> None:
        """清空会话记录"""
        self._sessions.clear()
        self._stats = FallbackStats()
    
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
            # 重新计算统计信息
            self._recalculate_stats()
    
    # === 统计信息方法 ===
    
    def get_stats(self) -> FallbackStats:
        """
        获取降级统计信息
        
        Returns:
            统计信息对象
        """
        return self._stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = FallbackStats()
    
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
    
    def get_fallback_usage_count(self) -> int:
        """
        获取降级使用次数
        
        Returns:
            降级使用次数
        """
        return sum(1 for s in self._sessions if s.get_fallback_usage())
    
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
        
        fallback_usage = sum(1 for s in self._sessions if s.get_fallback_usage())
        return fallback_usage / len(self._sessions)
    
    def get_success_rate(self) -> float:
        """
        获取成功率
        
        Returns:
            成功率（0-1之间的浮点数）
        """
        if not self._sessions:
            return 0.0
        
        successful_count = sum(1 for s in self._sessions if s.success)
        return successful_count / len(self._sessions)
    
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
    
    def get_most_used_fallback_models(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        获取最常用的降级模型列表
        
        Args:
            limit: 返回的模型数量限制
            
        Returns:
            按使用次数排序的降级模型列表，每个元素为 (model_name, count) 元组
        """
        model_counts = {}
        for session in self._sessions:
            for attempt in session.attempts:
                if attempt.fallback_model and attempt.success:
                    model_name = attempt.fallback_model
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
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要字典
        """
        if not self._sessions:
            return {
                "average_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "total_duration": 0.0,
            }
        
        durations = []
        for session in self._sessions:
            duration = session.get_total_duration()
            if duration is not None:
                durations.append(duration)
        
        if not durations:
            return {
                "average_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "total_duration": 0.0,
            }
        
        return {
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations),
        }
    
    def get_recent_activity(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取最近活动统计
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            最近活动统计字典
        """
        import time
        cutoff_time = time.time() - (hours * 3600)
        
        recent_sessions = [s for s in self._sessions if s.start_time >= cutoff_time]
        
        if not recent_sessions:
            return {
                "total_sessions": 0,
                "successful_sessions": 0,
                "failed_sessions": 0,
                "fallback_usage": 0,
                "success_rate": 0.0,
                "fallback_rate": 0.0,
            }
        
        successful_count = sum(1 for s in recent_sessions if s.success)
        fallback_usage = sum(1 for s in recent_sessions if s.get_fallback_usage())
        
        return {
            "total_sessions": len(recent_sessions),
            "successful_sessions": successful_count,
            "failed_sessions": len(recent_sessions) - successful_count,
            "fallback_usage": fallback_usage,
            "success_rate": successful_count / len(recent_sessions),
            "fallback_rate": fallback_usage / len(recent_sessions),
        }
    
    # === 内部方法 ===
    
    def _recalculate_stats(self) -> None:
        """重新计算统计信息"""
        self._stats = FallbackStats()
        for session in self._sessions:
            self._stats.update(session)


class FallbackTrackerFactory:
    """降级跟踪器工厂"""
    
    @staticmethod
    def create_default() -> FallbackTracker:
        """创建默认降级跟踪器"""
        return FallbackTracker()
    
    @staticmethod
    def create_with_max_sessions(max_sessions: int) -> FallbackTracker:
        """创建指定最大会话数的降级跟踪器"""
        return FallbackTracker(max_sessions)