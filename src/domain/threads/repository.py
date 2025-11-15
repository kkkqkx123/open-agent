"""Thread领域仓储实现

提供Thread实体的持久化功能，遵循DDD仓储模式。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .interfaces import IThreadRepository, IThreadBranchRepository, IThreadSnapshotRepository
from .models import Thread, ThreadBranch, ThreadSnapshot
from ...infrastructure.threads.metadata_store import IThreadMetadataStore
from ...infrastructure.threads.branch_store import IThreadBranchStore
from ...infrastructure.threads.snapshot_store import IThreadSnapshotStore

logger = logging.getLogger(__name__)


class ThreadRepository(IThreadRepository):
    """Thread仓储实现
    
    使用IThreadMetadataStore作为底层存储，提供Thread实体的持久化功能。
    """
    
    def __init__(self, metadata_store: IThreadMetadataStore):
        """初始化Thread仓储
        
        Args:
            metadata_store: 元数据存储
        """
        self.metadata_store = metadata_store
    
    async def save(self, thread: Thread) -> bool:
        """保存Thread实体
        
        Args:
            thread: Thread实体
            
        Returns:
            保存是否成功
        """
        try:
            # 将Thread实体转换为元数据格式
            thread_metadata = {
                "thread_id": thread.thread_id,
                "graph_id": thread.graph_id,
                "status": thread.status,
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "metadata": thread.metadata
            }
            
            # 保存到元数据存储
            success = await self.metadata_store.save_metadata(thread.thread_id, thread_metadata)
            
            if success:
                logger.debug(f"Thread保存成功: {thread.thread_id}")
            else:
                logger.error(f"Thread保存失败: {thread.thread_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存Thread失败: {thread.thread_id}, error: {e}")
            return False
    
    async def find_by_id(self, thread_id: str) -> Optional[Thread]:
        """根据ID查找Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread实体，如果不存在则返回None
        """
        try:
            # 从元数据存储获取
            metadata = await self.metadata_store.get_metadata(thread_id)
            if not metadata:
                logger.debug(f"Thread不存在: {thread_id}")
                return None
            
            # 转换为Thread实体
            thread = Thread(
                thread_id=metadata["thread_id"],
                graph_id=metadata["graph_id"],
                status=metadata.get("status", "active"),
                created_at=datetime.fromisoformat(metadata["created_at"]),
                updated_at=datetime.fromisoformat(metadata["updated_at"]),
                metadata=metadata.get("metadata", {})
            )
            
            logger.debug(f"Thread查找成功: {thread_id}")
            return thread
            
        except Exception as e:
            logger.error(f"查找Thread失败: {thread_id}, error: {e}")
            return None
    
    async def delete(self, thread_id: str) -> bool:
        """删除Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        try:
            success = await self.metadata_store.delete_metadata(thread_id)
            
            if success:
                logger.debug(f"Thread删除成功: {thread_id}")
            else:
                logger.warning(f"Thread删除失败: {thread_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除Thread失败: {thread_id}, error: {e}")
            return False
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Thread]:
        """查找所有Thread
        
        Args:
            filters: 过滤条件
            
        Returns:
            Thread实体列表
        """
        try:
            # 获取所有元数据
            all_metadata = await self.metadata_store.list_threads()
            
            threads = []
            for metadata in all_metadata:
                # 应用过滤条件
                if self._matches_filters(metadata, filters):
                    # 转换为Thread实体
                    thread = Thread(
                        thread_id=metadata["thread_id"],
                        graph_id=metadata["graph_id"],
                        status=metadata.get("status", "active"),
                        created_at=datetime.fromisoformat(metadata["created_at"]),
                        updated_at=datetime.fromisoformat(metadata["updated_at"]),
                        metadata=metadata.get("metadata", {})
                    )
                    threads.append(thread)
            
            logger.debug(f"查找所有Thread完成，共{len(threads)}个")
            return threads
            
        except Exception as e:
            logger.error(f"查找所有Thread失败, error: {e}")
            return []
    
    async def exists(self, thread_id: str) -> bool:
        """检查Thread是否存在
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread是否存在
        """
        try:
            return await self.metadata_store.thread_exists(thread_id)
        except Exception as e:
            logger.error(f"检查Thread存在性失败: {thread_id}, error: {e}")
            return False
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        """检查元数据是否匹配过滤条件
        
        Args:
            metadata: 元数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        if not filters:
            return True
        
        for key, value in filters.items():
            if key == "status":
                if metadata.get("status") != value:
                    return False
            elif key == "graph_id":
                if metadata.get("graph_id") != value:
                    return False
            elif key == "metadata":
                for metadata_key, expected_value in value.items():
                    if metadata.get("metadata", {}).get(metadata_key) != expected_value:
                        return False
            elif key == "created_after":
                if isinstance(value, datetime):
                    created_at_str = metadata.get("created_at")
                    if created_at_str and isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < value:
                            return False
            elif key == "created_before":
                if isinstance(value, datetime):
                    created_at_str = metadata.get("created_at")
                    if created_at_str and isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at > value:
                            return False
        
        return True


class ThreadBranchRepository(IThreadBranchRepository):
    """Thread分支仓储实现"""
    
    def __init__(self, branch_store: IThreadBranchStore):
        """初始化分支仓储
        
        Args:
            branch_store: 分支存储
        """
        self.branch_store = branch_store
    
    async def save(self, branch: ThreadBranch) -> bool:
        """保存分支信息"""
        try:
            success = await self.branch_store.save_branch(branch)
            
            if success:
                logger.debug(f"分支保存成功: {branch.branch_id}")
            else:
                logger.error(f"分支保存失败: {branch.branch_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存分支失败: {branch.branch_id}, error: {e}")
            return False
    
    async def find_by_id(self, branch_id: str) -> Optional[ThreadBranch]:
        """根据ID查找分支"""
        try:
            branch = await self.branch_store.get_branch(branch_id)
            
            if branch:
                logger.debug(f"分支查找成功: {branch_id}")
            else:
                logger.debug(f"分支不存在: {branch_id}")
            
            return branch
            
        except Exception as e:
            logger.error(f"查找分支失败: {branch_id}, error: {e}")
            return None
    
    async def find_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """查找Thread的所有分支"""
        try:
            branches = await self.branch_store.get_branches_by_thread(thread_id)
            logger.debug(f"查找Thread分支完成: {thread_id}, 共{len(branches)}个")
            return branches
            
        except Exception as e:
            logger.error(f"查找Thread分支失败: {thread_id}, error: {e}")
            return []
    
    async def delete(self, branch_id: str) -> bool:
        """删除分支"""
        try:
            success = await self.branch_store.delete_branch(branch_id)
            
            if success:
                logger.debug(f"分支删除成功: {branch_id}")
            else:
                logger.warning(f"分支删除失败: {branch_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除分支失败: {branch_id}, error: {e}")
            return False


class ThreadSnapshotRepository(IThreadSnapshotRepository):
    """Thread快照仓储实现"""
    
    def __init__(self, snapshot_store: IThreadSnapshotStore):
        """初始化快照仓储
        
        Args:
            snapshot_store: 快照存储
        """
        self.snapshot_store = snapshot_store
    
    async def save(self, snapshot: ThreadSnapshot) -> bool:
        """保存快照信息"""
        try:
            success = await self.snapshot_store.save_snapshot(snapshot)
            
            if success:
                logger.debug(f"快照保存成功: {snapshot.snapshot_id}")
            else:
                logger.error(f"快照保存失败: {snapshot.snapshot_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存快照失败: {snapshot.snapshot_id}, error: {e}")
            return False
    
    async def find_by_id(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """根据ID查找快照"""
        try:
            snapshot = await self.snapshot_store.get_snapshot(snapshot_id)
            
            if snapshot:
                logger.debug(f"快照查找成功: {snapshot_id}")
            else:
                logger.debug(f"快照不存在: {snapshot_id}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"查找快照失败: {snapshot_id}, error: {e}")
            return None
    
    async def find_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """查找Thread的所有快照"""
        try:
            snapshots = await self.snapshot_store.get_snapshots_by_thread(thread_id)
            logger.debug(f"查找Thread快照完成: {thread_id}, 共{len(snapshots)}个")
            return snapshots
            
        except Exception as e:
            logger.error(f"查找Thread快照失败: {thread_id}, error: {e}")
            return []
    
    async def delete(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            success = await self.snapshot_store.delete_snapshot(snapshot_id)
            
            if success:
                logger.debug(f"快照删除成功: {snapshot_id}")
            else:
                logger.warning(f"快照删除失败: {snapshot_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除快照失败: {snapshot_id}, error: {e}")
            return False