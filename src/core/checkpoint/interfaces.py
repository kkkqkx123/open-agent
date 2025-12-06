"""
检查点核心接口定义

定义检查点的核心操作接口，提供统一的检查点管理抽象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from .models import Checkpoint, CheckpointStatus, CheckpointType


class ICheckpointRepository(ABC):
    """检查点仓储接口"""
    
    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None,
        limit: Optional[int] = None
    ) -> List[Checkpoint]:
        """列出检查点
        
        Args:
            thread_id: Thread ID过滤
            status: 状态过滤
            checkpoint_type: 类型过滤
            limit: 返回数量限制
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None
    ) -> int:
        """统计检查点数量
        
        Args:
            thread_id: Thread ID过滤
            status: 状态过滤
            checkpoint_type: 类型过滤
            
        Returns:
            检查点数量
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点
        
        Args:
            thread_id: Thread ID，None表示清理所有
            
        Returns:
            清理的检查点数量
        """
        pass
    
    @abstractmethod
    async def get_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            thread_id: Thread ID，None表示全局统计
            
        Returns:
            统计信息字典
        """
        pass