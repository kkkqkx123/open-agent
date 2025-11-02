"""会话上下文管理模块

提供会话上下文管理功能，用于在应用程序中获取当前会话ID，
替代历史记录模块中的硬编码默认会话ID。
"""

from typing import Optional, Dict, Any
from threading import local
import contextlib
import uuid


class SessionContext:
    """会话上下文管理器
    
    提供线程本地存储的会话上下文，支持嵌套上下文管理。
    """
    
    def __init__(self):
        self._local = local()
        self._local.session_stack = []
    
    def set_current_session(self, session_id: str) -> None:
        """设置当前会话ID
        
        Args:
            session_id: 会话ID
        """
        if not hasattr(self._local, 'session_stack'):
            self._local.session_stack = []
        
        # 如果会话ID已经在栈中，先移除
        if session_id in self._local.session_stack:
            self._local.session_stack.remove(session_id)
        
        # 添加到栈顶
        self._local.session_stack.append(session_id)
    
    def get_current_session(self) -> Optional[str]:
        """获取当前会话ID
        
        Returns:
            Optional[str]: 当前会话ID，如果没有设置则返回None
        """
        if not hasattr(self._local, 'session_stack') or not self._local.session_stack:
            return None
        return self._local.session_stack[-1]
    
    def clear_current_session(self) -> None:
        """清除当前会话ID"""
        if hasattr(self._local, 'session_stack') and self._local.session_stack:
            self._local.session_stack.pop()
    
    @contextlib.contextmanager
    def session_context(self, session_id: str):
        """会话上下文管理器
        
        Args:
            session_id: 会话ID
            
        Yields:
            None
        """
        old_session_id = self.get_current_session()
        self.set_current_session(session_id)
        try:
            yield
        finally:
            self.clear_current_session()
            if old_session_id:
                self.set_current_session(old_session_id)
    
    def generate_session_id(self) -> str:
        """生成新的会话ID
        
        Returns:
            str: 新生成的会话ID
        """
        return str(uuid.uuid4())


# 全局会话上下文实例
_session_context = SessionContext()


def get_current_session() -> Optional[str]:
    """获取当前会话ID
    
    Returns:
        Optional[str]: 当前会话ID，如果没有设置则返回None
    """
    return _session_context.get_current_session()


def set_current_session(session_id: str) -> None:
    """设置当前会话ID
    
    Args:
        session_id: 会话ID
    """
    _session_context.set_current_session(session_id)


def clear_current_session() -> None:
    """清除当前会话ID"""
    _session_context.clear_current_session()


@contextlib.contextmanager
def session_context(session_id: str):
    """会话上下文管理器
    
    Args:
        session_id: 会话ID
        
    Yields:
        None
    """
    with _session_context.session_context(session_id):
        yield


def generate_session_id() -> str:
    """生成新的会话ID
    
    Returns:
        str: 新生成的会话ID
    """
    return _session_context.generate_session_id()


class SessionContextManager:
    """会话上下文管理器类
    
    提供更高级的会话上下文管理功能，包括会话元数据管理。
    """
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新会话
        
        Args:
            metadata: 会话元数据
            
        Returns:
            str: 新创建的会话ID
        """
        session_id = generate_session_id()
        self._sessions[session_id] = {
            "created_at": None,  # 将在实际创建时设置
            "metadata": metadata or {},
            "active": True
        }
        return session_id
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话元数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话元数据，如果会话不存在则返回None
        """
        return self._sessions.get(session_id, {}).get("metadata")
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """更新会话元数据
        
        Args:
            session_id: 会话ID
            metadata: 新的元数据
            
        Returns:
            bool: 更新是否成功
        """
        if session_id not in self._sessions:
            return False
        
        self._sessions[session_id]["metadata"].update(metadata)
        return True
    
    def deactivate_session(self, session_id: str) -> bool:
        """停用会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 停用是否成功
        """
        if session_id not in self._sessions:
            return False
        
        self._sessions[session_id]["active"] = False
        return True
    
    def is_session_active(self, session_id: str) -> bool:
        """检查会话是否活跃
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 会话是否活跃
        """
        return self._sessions.get(session_id, {}).get("active", False)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃会话
        
        Returns:
            Dict[str, Dict[str, Any]]: 活跃会话字典
        """
        return {
            session_id: session_data
            for session_id, session_data in self._sessions.items()
            if session_data.get("active", False)
        }


# 全局会话上下文管理器实例
_session_context_manager = SessionContextManager()


def get_session_context_manager() -> SessionContextManager:
    """获取全局会话上下文管理器实例
    
    Returns:
        SessionContextManager: 会话上下文管理器实例
    """
    return _session_context_manager