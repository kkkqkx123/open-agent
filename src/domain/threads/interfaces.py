"""Thread管理器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IThreadManager(ABC):
    """Thread管理器接口"""
    
    @abstractmethod
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread
        
        Args:
            graph_id: 关联的图ID
            metadata: Thread元数据
            
        Returns:
            创建的Thread ID
        """
        pass
    
    @abstractmethod
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread信息，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据
        
        Args:
            thread_id: Thread ID
            metadata: 要更新的元数据
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads
        
        Args:
            filters: 过滤条件
            limit: 返回结果数量限制
            
        Returns:
            Thread信息列表
        """
        pass
    
    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread是否存在
        """
        pass
    
    @abstractmethod
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread状态，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            state: 新状态
            
        Returns:
            更新是否成功
        """
        pass