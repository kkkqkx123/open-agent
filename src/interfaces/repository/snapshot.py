"""快照Repository接口

定义快照数据的存储和检索接口，实现数据访问层的抽象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ISnapshotRepository(ABC):
    """快照仓库接口
    
    专注于快照数据的存储和检索，不包含业务逻辑。
    支持通用快照操作和线程特定的快照操作。
    """
    
    @abstractmethod
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """保存快照
        
        Args:
            snapshot: 快照数据，包含agent_id、state_data、metadata等字段
            
        Returns:
            保存的快照ID
        """
        pass
    
    @abstractmethod
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def get_snapshots(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取代理的快照列表
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            快照列表，按创建时间倒序排列
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def delete_snapshots_by_agent(self, agent_id: str) -> int:
        """删除代理的所有快照
        
        Args:
            agent_id: 代理ID
            
        Returns:
            删除的快照数量
        """
        pass
    
    @abstractmethod
    async def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息
        
        Returns:
            统计信息字典，包含总快照数、代理数量等
        """
        pass
    
    @abstractmethod
    async def get_latest_snapshot(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取代理的最新快照
        
        Args:
            agent_id: 代理ID
            
        Returns:
            最新快照，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def cleanup_old_snapshots(self, agent_id: str, max_count: int) -> int:
        """清理旧的快照，保留最新的max_count个
        
        Args:
            agent_id: 代理ID
            max_count: 保留的最大数量
            
        Returns:
            删除的快照数量
        """
        pass
    
    @abstractmethod
    async def get_snapshot_comparison(
        self,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较两个快照
        
        Args:
            snapshot_id1: 第一个快照ID
            snapshot_id2: 第二个快照ID
            
        Returns:
            比较结果字典
        """
        pass
    
    @abstractmethod
    async def validate_snapshot_integrity(self, snapshot_id: str) -> bool:
        """验证快照完整性
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照完整返回True，否则返回False
        """
        pass