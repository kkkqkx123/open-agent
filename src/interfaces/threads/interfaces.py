"""线程仓储层接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadRepository(ABC):
    """Thread仓储接口 - 负责Thread的持久化"""
    
    @abstractmethod
    async def save(self, thread: Dict[str, Any]) -> bool:
        """保存Thread实体
        
        Args:
            thread: Thread实体数据
            
        Returns:
            保存是否成功
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread实体数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, thread_id: str) -> bool:
        """删除Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """查找所有Thread
        
        Args:
            filters: 过滤条件
            
        Returns:
            Thread实体数据列表
        """
        pass
    
    @abstractmethod
    async def exists(self, thread_id: str) -> bool:
        """检查Thread是否存在
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread是否存在
        """
        pass


class IThreadBranchRepository(ABC):
    """Thread分支仓储接口"""
    
    @abstractmethod
    async def save_branch(self, branch: Dict[str, Any]) -> bool:
        """保存分支信息"""
        pass
    
    @abstractmethod
    async def find_branch_by_id(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找分支"""
        pass
    
    @abstractmethod
    async def find_branches_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """查找指定Thread的所有分支"""
        pass
    
    @abstractmethod
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        pass


class IThreadSnapshotRepository(ABC):
    """Thread快照仓储接口"""
    
    @abstractmethod
    async def save_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """保存快照"""
        pass
    
    @abstractmethod
    async def find_snapshot_by_id(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找快照"""
        pass
    
    @abstractmethod
    async def find_snapshots_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """查找指定Thread的所有快照"""
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        pass


class IThreadDomainService(ABC):
    """Thread领域服务接口 - 负责核心业务逻辑"""
    
    @abstractmethod
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建新的Thread实体
        
        Args:
            graph_id: 关联的图ID
            metadata: Thread元数据
            
        Returns:
            创建的Thread实体数据
        """
        pass
    
    @abstractmethod
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从配置文件创建Thread
        
        Args:
            config_path: 配置文件路径
            metadata: Thread元数据
            
        Returns:
            创建的Thread实体数据
        """
        pass
    
    @abstractmethod
    async def fork_thread(
        self, 
        source_thread_id: str, 
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支
        
        Args:
            source_thread_id: 源Thread ID
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新分支的Thread ID
        """
        pass
    
    @abstractmethod
    async def validate_thread_state(self, thread: Dict[str, Any]) -> bool:
        """验证Thread状态
        
        Args:
            thread: Thread实体数据
            
        Returns:
            状态有效返回True，无效返回False
        """
        pass
    
    @abstractmethod
    async def can_transition_to_status(self, thread: Dict[str, Any], new_status: str) -> bool:
        """检查是否可以转换到指定状态
        
        Args:
            thread: 当前Thread
            new_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        pass