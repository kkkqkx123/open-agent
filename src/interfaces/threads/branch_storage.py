"""线程分支存储适配器接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.entities import ThreadBranch


class IThreadBranchStore(ABC):
    """线程分支存储适配器接口"""
    
    @abstractmethod
    async def get_branch(self, branch_id: str) -> Optional[ThreadBranch]:
        """获取分支"""
        pass
    
    @abstractmethod
    async def create_branch(self, branch: ThreadBranch) -> bool:
        """创建分支"""
        pass
    
    @abstractmethod
    async def update_branch(self, branch_id: str, branch: ThreadBranch) -> bool:
        """更新分支"""
        pass
    
    @abstractmethod
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        pass
    
    @abstractmethod
    async def list_branches_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """按线程列分支"""
        pass
    
    @abstractmethod
    async def get_branch_by_checkpoint(self, checkpoint_id: str) -> Optional[ThreadBranch]:
        """按检查点获取分支"""
        pass
    
    @abstractmethod
    async def get_main_branch(self, thread_id: str) -> Optional[ThreadBranch]:
        """获取主分支"""
        pass
    
    @abstractmethod
    async def merge_branch(self, source_branch_id: str, target_branch_id: str) -> bool:
        """合并分支"""
        pass
    
    @abstractmethod
    async def get_branch_history(self, branch_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取分支历史"""
        pass
    
    @abstractmethod
    async def cleanup_old_branches(self, max_age_days: int = 30) -> int:
        """清理旧分支"""
        pass