"""线程分支服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IThreadBranchService(ABC):
    """线程分支业务服务接口 - 定义线程分支相关的业务逻辑"""
    
    @abstractmethod
    async def create_branch_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建分支
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新分支的ID
        """
        pass
    
    @abstractmethod
    async def merge_branch_to_main(
        self,
        thread_id: str,
        branch_id: str,
        merge_strategy: str = "overwrite"
    ) -> bool:
        """将分支合并到主线
        
        Args:
            thread_id: 线程ID
            branch_id: 分支ID
            merge_strategy: 合并策略
            
        Returns:
            合并成功返回True
        """
        pass
    
    @abstractmethod
    async def get_branch_history(self, thread_id: str, branch_id: str) -> List[Dict[str, Any]]:
        """获取分支历史
        
        Args:
            thread_id: 线程ID
            branch_id: 分支ID
            
        Returns:
            分支历史列表
        """
        pass
    
    @abstractmethod
    async def list_active_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """列活动分支
        
        Args:
            thread_id: 线程ID
            
        Returns:
            活动分支列表
        """
        pass
    
    @abstractmethod
    async def validate_branch_integrity(self, thread_id: str, branch_id: str) -> bool:
        """验证分支完整性
        
        Args:
            thread_id: 线程ID
            branch_id: 分支ID
            
        Returns:
            分支完整返回True，否则返回False
        """
        pass
    
    @abstractmethod
    async def cleanup_orphaned_branches(self, thread_id: str) -> int:
        """清理孤立分支
        
        Args:
            thread_id: 线程ID
            
        Returns:
            清理的分支数量
        """
        pass