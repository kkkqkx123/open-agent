"""Thread分支数据存储"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.threads.models import ThreadBranch


class IThreadBranchStore(ABC):
    """Thread分支存储接口"""
    
    @abstractmethod
    async def save_branch(self, branch: ThreadBranch) -> bool:
        """保存分支信息"""
        pass
    
    @abstractmethod
    async def get_branch(self, branch_id: str) -> Optional[ThreadBranch]:
        """获取分支信息"""
        pass
    
    @abstractmethod
    async def get_branches_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """获取thread的所有分支"""
        pass
    
    @abstractmethod
    async def update_branch_status(self, branch_id: str, status: str) -> bool:
        """更新分支状态"""
        pass
    
    @abstractmethod
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        pass


class ThreadBranchStore(IThreadBranchStore):
    """Thread分支存储实现（基于内存）"""
    
    def __init__(self):
        """初始化分支存储"""
        self._branches: Dict[str, ThreadBranch] = {}
        self._thread_branches: Dict[str, List[str]] = {}  # thread_id -> [branch_id]
    
    async def save_branch(self, branch: ThreadBranch) -> bool:
        """保存分支信息"""
        try:
            self._branches[branch.branch_id] = branch
            
            # 更新thread到分支的映射
            if branch.source_thread_id not in self._thread_branches:
                self._thread_branches[branch.source_thread_id] = []
            if branch.branch_id not in self._thread_branches[branch.source_thread_id]:
                self._thread_branches[branch.source_thread_id].append(branch.branch_id)
            
            return True
        except Exception:
            return False
    
    async def get_branch(self, branch_id: str) -> Optional[ThreadBranch]:
        """获取分支信息"""
        return self._branches.get(branch_id)
    
    async def get_branches_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """获取thread的所有分支"""
        branch_ids = self._thread_branches.get(thread_id, [])
        branches = []
        for branch_id in branch_ids:
            branch = self._branches.get(branch_id)
            if branch:
                branches.append(branch)
        return branches
    
    async def update_branch_status(self, branch_id: str, status: str) -> bool:
        """更新分支状态"""
        branch = self._branches.get(branch_id)
        if branch:
            # 创建新的ThreadBranch实例（因为dataclass是不可变的）
            updated_branch = ThreadBranch(
                branch_id=branch.branch_id,
                source_thread_id=branch.source_thread_id,
                source_checkpoint_id=branch.source_checkpoint_id,
                branch_name=branch.branch_name,
                created_at=branch.created_at,
                metadata=branch.metadata,
                status=status
            )
            self._branches[branch_id] = updated_branch
            return True
        return False
    
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        if branch_id not in self._branches:
            return False
        
        branch = self._branches[branch_id]
        
        # 从thread映射中移除
        if branch.source_thread_id in self._thread_branches:
            if branch_id in self._thread_branches[branch.source_thread_id]:
                self._thread_branches[branch.source_thread_id].remove(branch_id)
        
        # 删除分支
        del self._branches[branch_id]
        return True