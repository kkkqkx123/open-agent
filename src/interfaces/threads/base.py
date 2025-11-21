"""线程管理基础接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadManager(ABC):
    """线程管理器接口 - 负责线程的生命周期管理"""

    @abstractmethod
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新线程
        
        Args:
            graph_id: 关联的图ID
            metadata: 可选的线程元数据
            
        Returns:
            新创建的线程ID
        """
        pass

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程信息
        
        Args:
            thread_id: 线程唯一标识
            
        Returns:
            线程详细信息字典，不存在时返回None
        """
        pass

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程
        
        Args:
            thread_id: 线程唯一标识
            
        Returns:
            删除成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出线程
        
        Args:
            filters: 可选的过滤条件
            
        Returns:
            线程列表
        """
        pass

    @abstractmethod
    async def fork_thread(self, source_thread_id: str, checkpoint_id: str, branch_name: str) -> str:
        """创建线程分支
        
        Args:
            source_thread_id: 源线程ID
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            
        Returns:
            新分支的线程ID
        """
        pass

    @abstractmethod
    async def create_snapshot(self, thread_id: str, snapshot_name: str, description: Optional[str] = None) -> str:
        """创建线程快照
        
        Args:
            thread_id: 线程唯一标识
            snapshot_name: 快照名称
            description: 快照描述
            
        Returns:
            新创建的快照ID
        """
        pass

    @abstractmethod
    async def restore_snapshot(self, thread_id: str, snapshot_id: str) -> bool:
        """恢复线程快照
        
        Args:
            thread_id: 线程唯一标识
            snapshot_id: 快照ID
            
        Returns:
            恢复成功返回True，失败返回False
        """
        pass