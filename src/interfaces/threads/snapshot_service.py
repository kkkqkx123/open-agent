"""线程快照服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadSnapshotService(ABC):
    """线程快照业务服务接口 - 定义线程快照相关的业务逻辑"""
    
    @abstractmethod
    async def create_snapshot_from_thread(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """从线程创建快照
        
        Args:
            thread_id: 线程ID
            snapshot_name: 快照名称
            description: 快照描述
            include_metadata: 是否包含元数据
            
        Returns:
            快照ID
        """
        pass
    
    @abstractmethod
    async def restore_thread_from_snapshot(
        self,
        thread_id: str,
        snapshot_id: str,
        restore_strategy: str = "full"
    ) -> bool:
        """从快照恢复线程
        
        Args:
            thread_id: 线程ID
            snapshot_id: 快照ID
            restore_strategy: 恢复策略
            
        Returns:
            恢复成功返回True
        """
        pass
    
    @abstractmethod
    async def get_snapshot_comparison(
        self,
        thread_id: str,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较两个快照
        
        Args:
            thread_id: 线程ID
            snapshot_id1: 第一个快照ID
            snapshot_id2: 第二个快照ID
            
        Returns:
            比较结果
        """
        pass
    
    @abstractmethod
    async def list_thread_snapshots(self, thread_id: str) -> List[Dict[str, Any]]:
        """列线程快照
        
        Args:
            thread_id: 线程ID
            
        Returns:
            快照列表
        """
        pass
    
    @abstractmethod
    async def validate_snapshot_integrity(self, thread_id: str, snapshot_id: str) -> bool:
        """验证快照完整性
        
        Args:
            thread_id: 线程ID
            snapshot_id: 快照ID
            
        Returns:
            快照完整返回True，否则返回False
        """
        pass
    
    @abstractmethod
    async def cleanup_old_snapshots(self, thread_id: str, max_age_days: int = 30) -> int:
        """清理旧快照
        
        Args:
            thread_id: 线程ID
            max_age_days: 最大存活天数
            
        Returns:
            清理的快照数量
        """
        pass