"""Thread领域接口定义

包含Thread核心业务概念和仓储接口，遵循DDD原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import Thread, ThreadBranch, ThreadSnapshot


class IThreadRepository(ABC):
    """Thread仓储接口 - 负责Thread的持久化"""
    
    @abstractmethod
    async def save(self, thread: Thread) -> bool:
        """保存Thread实体
        
        Args:
            thread: Thread实体
            
        Returns:
            保存是否成功
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, thread_id: str) -> Optional[Thread]:
        """根据ID查找Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread实体，如果不存在则返回None
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
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Thread]:
        """查找所有Thread
        
        Args:
            filters: 过滤条件
            
        Returns:
            Thread实体列表
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


class IThreadDomainService(ABC):
    """Thread领域服务接口 - 负责核心业务逻辑"""
    
    @abstractmethod
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> Thread:
        """创建新的Thread实体
        
        Args:
            graph_id: 关联的图ID
            metadata: Thread元数据
            
        Returns:
            创建的Thread实体
        """
        pass
    
    @abstractmethod
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> Thread:
        """从配置文件创建Thread实体
        
        Args:
            config_path: 配置文件路径
            metadata: Thread元数据
            
        Returns:
            创建的Thread实体
        """
        pass
    
    @abstractmethod
    async def fork_thread(
        self, 
        source_thread: Thread, 
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Thread:
        """从指定checkpoint创建thread分支
        
        Args:
            source_thread: 源Thread实体
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新的Thread实体
        """
        pass
    
    @abstractmethod
    async def validate_thread_state(self, thread: Thread, state: Dict[str, Any]) -> bool:
        """验证Thread状态的有效性
        
        Args:
            thread: Thread实体
            state: 状态数据
            
        Returns:
            状态是否有效
        """
        pass


class IThreadBranchRepository(ABC):
    """Thread分支仓储接口"""
    
    @abstractmethod
    async def save(self, branch: ThreadBranch) -> bool:
        """保存分支信息"""
        pass
    
    @abstractmethod
    async def find_by_id(self, branch_id: str) -> Optional[ThreadBranch]:
        """根据ID查找分支"""
        pass
    
    @abstractmethod
    async def find_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """查找Thread的所有分支"""
        pass
    
    @abstractmethod
    async def delete(self, branch_id: str) -> bool:
        """删除分支"""
        pass


class IThreadSnapshotRepository(ABC):
    """Thread快照仓储接口"""
    
    @abstractmethod
    async def save(self, snapshot: ThreadSnapshot) -> bool:
        """保存快照信息"""
        pass
    
    @abstractmethod
    async def find_by_id(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """根据ID查找快照"""
        pass
    
    @abstractmethod
    async def find_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """查找Thread的所有快照"""
        pass
    
    @abstractmethod
    async def delete(self, snapshot_id: str) -> bool:
        """删除快照"""
        pass


# 为了向后兼容，保留IThreadManager接口，但标记为废弃
# 实际使用中应该使用IThreadRepository和IThreadDomainService
class IThreadManager(ABC):
    """Thread管理器接口 - 已废弃，请使用IThreadRepository和IThreadDomainService
    
    此接口保留仅为了向后兼容，新代码应该使用更具体的接口。
    """
    
    @abstractmethod
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread"""
        pass
    
    @abstractmethod
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        pass
    
    @abstractmethod
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态"""
        pass
    
    @abstractmethod
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        pass
    
    @abstractmethod
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads"""
        pass
    
    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        pass
    
    @abstractmethod
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
        pass
    
    @abstractmethod
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        pass
    
    @abstractmethod
    async def fork_thread(
        self, 
        source_thread_id: str, 
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支"""
        pass

    @abstractmethod
    async def create_thread_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建thread状态快照"""
        pass

    @abstractmethod
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚thread到指定checkpoint"""
        pass

    @abstractmethod
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread"""
        pass

    @abstractmethod
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        pass

    @abstractmethod
    async def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ):
        """流式执行工作流"""
        pass

    @abstractmethod
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取thread历史记录"""
        pass