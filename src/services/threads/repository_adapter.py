"""线程仓储适配器 - 桥接仓储接口与服务层"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.interfaces.threads import IThreadRepository, IThreadBranchRepository, IThreadSnapshotRepository
from src.core.threads.entities import Thread, ThreadBranch, ThreadSnapshot, ThreadMetadata


class ThreadRepositoryAdapter:
    """线程仓储适配器 - 将Dict数据转换为Thread实体"""
    
    def __init__(self, repository: IThreadRepository):
        self._repository = repository
    
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """获取Thread实体"""
        thread_data = await self._repository.find_by_id(thread_id)
        if not thread_data:
            return None
        
        # 转换Dict为Thread实体
        return Thread.from_dict(thread_data)
    
    async def save_thread(self, thread: Thread) -> bool:
        """保存Thread实体"""
        thread_data = thread.to_dict()
        return await self._repository.save(thread_data)
    
    async def update_thread(self, thread_id: str, thread: Thread) -> bool:
        """更新Thread实体"""
        thread_data = thread.to_dict()
        # 这里需要实现更新逻辑，当前仓储接口没有update方法
        # 先删除再保存作为临时方案
        await self._repository.delete(thread_id)
        return await self._repository.save(thread_data)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread"""
        return await self._repository.delete(thread_id)
    
    async def list_threads_by_type(self, thread_type: str) -> List[Thread]:
        """按类型列线程"""
        filters = {"type": thread_type}
        threads_data = await self._repository.find_all(filters)
        
        # 转换为Thread实体列表
        threads = []
        for thread_data in threads_data:
            try:
                thread = Thread.from_dict(thread_data)
                threads.append(thread)
            except Exception:
                # 跳过无效数据
                continue
        
        return threads
    
    async def associate_with_session(self, thread_id: str, session_id: str) -> bool:
        """关联会话（临时实现）"""
        # 获取现有线程数据
        thread_data = await self._repository.find_by_id(thread_id)
        if not thread_data:
            return False
        
        # 添加session_id
        thread_data["session_id"] = session_id
        
        # 保存更新
        return await self._repository.save(thread_data)


class ThreadBranchRepositoryAdapter:
    """线程分支仓储适配器"""
    
    def __init__(self, repository: IThreadBranchRepository):
        self._repository = repository
    
    async def get_branch(self, branch_id: str) -> Optional[ThreadBranch]:
        """获取ThreadBranch实体"""
        branch_data = await self._repository.find_branch_by_id(branch_id)
        if not branch_data:
            return None
        
        return ThreadBranch.from_dict(branch_data)
    
    async def save_branch(self, branch: ThreadBranch) -> bool:
        """保存ThreadBranch实体"""
        branch_data = branch.to_dict()
        return await self._repository.save_branch(branch_data)
    
    async def update_branch(self, branch_id: str, branch: ThreadBranch) -> bool:
        """更新ThreadBranch实体"""
        branch_data = branch.to_dict()
        # 临时实现：先删除再保存
        await self._repository.delete_branch(branch_id)
        return await self._repository.save_branch(branch_data)
    
    async def delete_branch(self, branch_id: str) -> bool:
        """删除分支"""
        return await self._repository.delete_branch(branch_id)
    
    async def list_branches_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """按线程列分支"""
        branches_data = await self._repository.find_branches_by_thread(thread_id)
        
        branches = []
        for branch_data in branches_data:
            try:
                branch = ThreadBranch.from_dict(branch_data)
                branches.append(branch)
            except Exception:
                continue
        
        return branches
    
    async def list_active_branches(self, thread_id: str) -> List[ThreadBranch]:
        """列活动分支"""
        all_branches = await self.list_branches_by_thread(thread_id)
        # 过滤活动分支（假设metadata中有is_active标记）
        return [b for b in all_branches if b.metadata.get("is_active", True)]
    
    async def get_branch_history(self, branch_id: str) -> List[Dict[str, Any]]:
        """获取分支历史（临时实现）"""
        # 这里应该从历史存储获取，暂时返回空列表
        return []


class ThreadSnapshotRepositoryAdapter:
    """线程快照仓储适配器"""
    
    def __init__(self, repository: IThreadSnapshotRepository):
        self._repository = repository
    
    async def get_snapshot(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """获取ThreadSnapshot实体"""
        snapshot_data = await self._repository.find_snapshot_by_id(snapshot_id)
        if not snapshot_data:
            return None
        
        return ThreadSnapshot.from_dict(snapshot_data)
    
    async def save_snapshot(self, snapshot: ThreadSnapshot) -> bool:
        """保存ThreadSnapshot实体"""
        snapshot_data = snapshot.to_dict()
        return await self._repository.save_snapshot(snapshot_data)
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        return await self._repository.delete_snapshot(snapshot_id)
    
    async def list_snapshots_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """按线程列快照"""
        snapshots_data = await self._repository.find_snapshots_by_thread(thread_id)
        
        snapshots = []
        for snapshot_data in snapshots_data:
            try:
                snapshot = ThreadSnapshot.from_dict(snapshot_data)
                snapshots.append(snapshot)
            except Exception:
                continue
        
        return snapshots