"""状态快照管理接口定义

定义状态快照管理相关的接口，包括创建、恢复和清理功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# 使用接口定义，遵循分层架构
from .entities import IStateSnapshot


# 状态快照管理器接口定义
class IStateSnapshotManager(ABC):
    """状态快照管理器接口
    
    负责管理状态快照，包括创建、恢复和清理功能。
    """
    
    @abstractmethod
    def create_snapshot(self, thread_id: str, state_data: Dict[str, Any], snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建状态快照
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            snapshot_name: 快照名称
            metadata: 元数据
            
        Returns:
            快照ID
        """
        pass
    
    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> Optional[IStateSnapshot]:
        """恢复状态快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的快照，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_snapshots_by_thread(self, thread_id: str) -> List[IStateSnapshot]:
        """获取指定线程的快照列表
        
        Args:
            thread_id: 线程ID
            limit: 返回快照数限制
            
        Returns:
            快照列表
        """
        pass
    
    @abstractmethod
    def cleanup_old_snapshots(self, thread_id: str, max_snapshots: int = 50) -> int:
        """清理旧快照
        
        Args:
            thread_id: 线程ID
            max_snapshots: 保留的最大快照数
            
        Returns:
            清理的快照数量
        """
        pass