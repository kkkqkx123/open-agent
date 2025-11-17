"""降级会话管理器

负责会话的创建、跟踪和管理，包括会话的生命周期管理。
"""

from typing import List, Optional
from .fallback_config import FallbackSession


class FallbackSessionManager:
    """降级会话管理器
    
    负责会话的创建、跟踪和管理，包括：
    1. 会话的创建和存储
    2. 会话的查询和过滤
    3. 会话的清理和重置
    4. 会话的生命周期管理
    """
    
    def __init__(self, max_sessions: int = 1000):
        """
        初始化降级会话管理器
        
        Args:
            max_sessions: 最大会话数量，超过后会清理旧会话
        """
        self._sessions: List[FallbackSession] = []
        self._max_sessions = max_sessions
    
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
    
    def clear_sessions(self) -> None:
        """清空会话记录"""
        self._sessions.clear()
    
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
    
    def get_most_used_models(self, limit: int = 10) -> List[tuple]:
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
    
    def get_error_summary(self, limit: int = 10) -> List[tuple]:
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