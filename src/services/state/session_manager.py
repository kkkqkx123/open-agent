"""会话状态管理服务实现

提供会话状态的创建、管理和清理功能，使用简化的架构。
"""

import asyncio
import time
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.interfaces.state.session import ISessionState, ISessionStateManager
from src.core.state.implementations.session_state import SessionStateImpl
from src.infrastructure.common.serialization import Serializer
from src.core.sessions.entities import SessionStatus


logger = get_logger(__name__)


class SessionStateManager(ISessionStateManager):
    """会话状态管理器实现
    
    使用简化的架构提供完整的会话状态管理功能。
    """
    
    def __init__(self,
                 serializer: Optional[Serializer] = None,
                 session_timeout_minutes: int = 30,
                 cleanup_interval_minutes: int = 60,
                 cache_size: int = 1000):
        """初始化会话状态管理器
        
        Args:
            serializer: 状态序列化器
            session_timeout_minutes: 会话超时时间（分钟）
            cleanup_interval_minutes: 清理间隔（分钟）
            cache_size: 缓存大小
        """
        self._serializer = serializer
        self._session_timeout_minutes = session_timeout_minutes
        self._cleanup_interval_minutes = cleanup_interval_minutes
        
        # 简单的内存缓存
        self._session_cache: Dict[str, ISessionState] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_size = cache_size
        
        self._last_cleanup_time = datetime.now()
        
        # 统计信息
        self._statistics: Dict[str, Any] = {
            "total_sessions_created": 0,
            "total_sessions_deleted": 0,
            "total_sessions_loaded": 0,
            "total_sessions_saved": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cleanup_runs": 0,
            "sessions_cleaned": 0
        }
        
        logger.info("会话状态管理器初始化完成（简化版本）")
    
    def create_session_state(self, session_id: str, user_id: Optional[str] = None,
                           config: Optional[Dict[str, Any]] = None) -> ISessionState:
        """创建会话状态"""
        try:
            # 检查是否已存在
            existing_session = self.get_session_state(session_id)
            if existing_session:
                logger.warning(f"会话 {session_id} 已存在")
                return existing_session
            
            # 创建新的会话状态
            session_state = SessionStateImpl(
                session_id=session_id,
                user_id=user_id,
                session_config=config or {}
            )
            
            # 更新缓存
            self._set_cache(session_id, session_state)
            
            # 更新统计
            self._statistics["total_sessions_created"] += 1
            
            logger.info(f"创建会话状态成功: {session_id}")
            return session_state
            
        except Exception as e:
            logger.error(f"创建会话状态失败: {e}")
            raise
    
    def get_session_state(self, session_id: str) -> Optional[ISessionState]:
        """获取会话状态"""
        try:
            # 先从缓存获取
            session_state = self._get_cache(session_id)
            if session_state:
                self._statistics["cache_hits"] += 1
                logger.debug(f"会话缓存命中: {session_id}")
                return session_state
            
            self._statistics["cache_misses"] += 1
            logger.debug(f"会话不存在: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return None
    
    def save_session_state(self, session_state: ISessionState) -> None:
        """保存会话状态"""
        try:
            # 更新缓存
            self._set_cache(session_state.session_id, session_state)
            
            # 更新统计
            self._statistics["total_sessions_saved"] += 1
            
            logger.debug(f"保存会话状态成功: {session_state.session_id}")
            
        except Exception as e:
            logger.error(f"保存会话状态失败: {e}")
            raise
    
    def delete_session_state(self, session_id: str) -> bool:
        """删除会话状态"""
        try:
            # 从缓存删除
            deleted = self._delete_cache(session_id)
            
            if deleted:
                # 更新统计
                self._statistics["total_sessions_deleted"] += 1
                
                logger.info(f"删除会话状态成功: {session_id}")
                return True
            
            logger.warning(f"会话不存在，无法删除: {session_id}")
            return False
            
        except Exception as e:
            logger.error(f"删除会话状态失败: {e}")
            return False
    
    def get_active_sessions(self, timeout_minutes: int = 30) -> List[ISessionState]:
        """获取活跃会话列表"""
        try:
            active_sessions = []
            
            # 检查缓存中的会话
            for session_state in self._session_cache.values():
                if session_state.is_active(timeout_minutes):
                    active_sessions.append(session_state)
            
            logger.debug(f"获取到 {len(active_sessions)} 个活跃会话")
            return active_sessions
            
        except Exception as e:
            logger.error(f"获取活跃会话失败: {e}")
            return []
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """清理非活跃会话"""
        try:
            # 检查是否需要清理
            now = datetime.now()
            if (now - self._last_cleanup_time).total_seconds() < self._cleanup_interval_minutes * 60:
                return 0
            
            cleaned_count = 0
            
            # 获取所有会话
            session_ids = list(self._session_cache.keys())
            
            for session_id in session_ids:
                session_state = self.get_session_state(session_id)
                if session_state and not session_state.is_active(timeout_minutes):
                    if self.delete_session_state(session_id):
                        cleaned_count += 1
            
            # 更新清理时间和统计
            self._last_cleanup_time = now
            self._statistics["cleanup_runs"] += 1
            self._statistics["sessions_cleaned"] += cleaned_count
            
            logger.info(f"清理了 {cleaned_count} 个非活跃会话")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理非活跃会话失败: {e}")
            return 0
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        try:
            # 基础统计
            stats = self._statistics.copy()
            
            # 当前状态统计
            stats["cached_sessions"] = len(self._session_cache)
            stats["active_sessions"] = len(self.get_active_sessions(self._session_timeout_minutes))
            stats["last_cleanup_time"] = self._last_cleanup_time.isoformat()
            stats["session_timeout_minutes"] = self._session_timeout_minutes
            stats["cleanup_interval_minutes"] = self._cleanup_interval_minutes
            
            total_requests = stats["cache_hits"] + stats["cache_misses"]
            if total_requests > 0:
                stats["cache_hit_rate"] = stats["cache_hits"] / total_requests
            else:
                stats["cache_hit_rate"] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取会话统计信息失败: {e}")
            return self._statistics
    
    def get_sessions_by_user(self, user_id: str) -> List[ISessionState]:
        """获取指定用户的会话列表"""
        try:
            user_sessions = []
            
            for session_state in self._session_cache.values():
                if session_state.user_id == user_id:
                    user_sessions.append(session_state)
            
            return user_sessions
            
        except Exception as e:
            logger.error(f"获取用户会话失败: {e}")
            return []
    
    def get_sessions_with_thread(self, thread_id: str) -> List[ISessionState]:
        """获取包含指定线程的会话列表"""
        try:
            sessions_with_thread = []
            
            for session_state in self._session_cache.values():
                if thread_id in session_state.thread_ids:
                    sessions_with_thread.append(session_state)
            
            return sessions_with_thread
            
        except Exception as e:
            logger.error(f"获取包含线程的会话失败: {e}")
            return []
    
    def archive_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """归档会话"""
        try:
            session_state = self.get_session_state(session_id)
            if not session_state:
                return None
            
            # 归档数据
            archive_data = session_state.get_session_summary()
            archive_data["archived_at"] = datetime.now().isoformat()
            
            # 删除原会话
            self.delete_session_state(session_id)
            
            logger.info(f"会话 {session_id} 已归档")
            return archive_data
            
        except Exception as e:
            logger.error(f"归档会话失败: {e}")
            return None
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._session_cache.clear()
        self._cache_timestamps.clear()
        logger.info("会话缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cached_sessions": len(self._session_cache),
            "cache_hits": self._statistics["cache_hits"],
            "cache_misses": self._statistics["cache_misses"],
            "hit_rate": (
                self._statistics["cache_hits"] / 
                (self._statistics["cache_hits"] + self._statistics["cache_misses"])
                if (self._statistics["cache_hits"] + self._statistics["cache_misses"]) > 0 
                else 0
            ),
            "cache_size": self._cache_size
        }
    
    # 缓存方法
    def _get_cache(self, session_id: str) -> Optional[ISessionState]:
        """获取缓存"""
        if session_id not in self._session_cache:
            return None
        
        # 检查是否过期
        if session_id in self._cache_timestamps:
            if time.time() - self._cache_timestamps[session_id] > self._session_timeout_minutes * 60:
                self._delete_cache(session_id)
                return None
        
        return self._session_cache.get(session_id)
    
    def _set_cache(self, session_id: str, session_state: ISessionState) -> None:
        """设置缓存"""
        import time
        
        # 检查缓存大小限制
        if len(self._session_cache) >= self._cache_size:
            # 删除最旧的缓存项
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            self._delete_cache(oldest_key)
        
        self._session_cache[session_id] = session_state
        self._cache_timestamps[session_id] = time.time()
    
    def _delete_cache(self, session_id: str) -> bool:
        """删除缓存"""
        deleted = False
        if session_id in self._session_cache:
            del self._session_cache[session_id]
            deleted = True
        if session_id in self._cache_timestamps:
            del self._cache_timestamps[session_id]
            deleted = True
        return deleted