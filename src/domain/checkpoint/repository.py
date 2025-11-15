"""检查点仓储接口定义

定义检查点仓储的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .interfaces import ICheckpointStore


class ICheckpointRepository(ABC):
    """检查点仓储接口
    
    负责检查点数据的存储和检索。
    """
    
    @abstractmethod
    async def save_checkpoint(self, thread_id: str, workflow_id: str, state_data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """保存检查点"""
        pass
    
    @abstractmethod
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取检查点"""
        pass
    
    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出检查点"""
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除检查点"""
        pass


class CheckpointRepository(ICheckpointRepository):
    """检查点仓储实现
    
    使用ICheckpointStore作为底层存储。
    """
    
    def __init__(self, checkpoint_store: Optional[ICheckpointStore] = None):
        """初始化检查点仓储
        
        Args:
            checkpoint_store: 检查点存储实例
        """
        self.checkpoint_store = checkpoint_store
    
    async def save_checkpoint(self, thread_id: str, workflow_id: str, state_data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """保存检查点"""
        if not self.checkpoint_store:
            return False
            
        checkpoint_data = {
            'thread_id': thread_id,
            'workflow_id': workflow_id,
            'state_data': state_data,
            'metadata': metadata or {}
        }
        
        return await self.checkpoint_store.save(checkpoint_data)
    
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取检查点"""
        if not self.checkpoint_store:
            return None
            
        return await self.checkpoint_store.load_by_thread(thread_id, checkpoint_id)
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出检查点"""
        if not self.checkpoint_store:
            return []
            
        return await self.checkpoint_store.list_by_thread(thread_id)
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除检查点"""
        if not self.checkpoint_store:
            return False
            
        return await self.checkpoint_store.delete_by_thread(thread_id, checkpoint_id)