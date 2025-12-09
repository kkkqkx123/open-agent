"""会话和线程存储接口定义

定义会话和线程专用的存储接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator
from .base import IStorage


class ISessionStorage(IStorage):
    """会话存储接口
    
    专门用于会话数据的存储，继承通用存储接口并添加会话特定方法。
    """
    
    # === 会话特定方法 ===
    
    @abstractmethod
    async def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，不存在返回None
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_sessions(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def get_session_threads(self, session_id: str) -> List[str]:
        """获取会话关联的线程ID列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程ID列表
        """
        pass
    
    @abstractmethod
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态
        
        Args:
            session_id: 会话ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        pass


class IThreadStorage(IStorage):
    """线程存储接口
    
    专门用于线程数据的存储，继承通用存储接口并添加线程特定方法。
    """
    
    # === 线程特定方法 ===
    
    @abstractmethod
    async def save_thread(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据
        
        Args:
            thread_id: 线程ID
            data: 线程数据
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程数据，不存在返回None
        """
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_threads(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出线程
        
        Args:
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            线程列表
        """
        pass
    
    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def get_threads_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取线程列表
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程列表
        """
        pass
    
    @abstractmethod
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新线程状态
        
        Args:
            thread_id: 线程ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def get_thread_branches(self, thread_id: str) -> List[str]:
        """获取线程关联的分支ID列表
        
        Args:
            thread_id: 线程ID
            
        Returns:
            分支ID列表
        """
        pass