"""线程仓储实现"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.interfaces.threads.storage import IThreadRepository
from src.adapters.storage.backends.thread_base import IThreadStorageBackend
from src.core.threads.entities import Thread, ThreadStatus, ThreadType
from src.interfaces.storage.exceptions import StorageError

logger = get_logger(__name__)


class ThreadRepository(IThreadRepository):
    """线程仓储实现 - 协调多个存储后端"""
    
    def __init__(
        self, 
        primary_backend: IThreadStorageBackend,
        secondary_backends: Optional[List[IThreadStorageBackend]] = None
    ):
        """初始化线程仓储
        
        Args:
            primary_backend: 主存储后端（必须）
            secondary_backends: 辅助存储后端列表，用于冗余和查询扩展
        """
        self.primary_backend = primary_backend
        self.secondary_backends = secondary_backends or []
        logger.info(
            f"ThreadRepository initialized with {1 + len(self.secondary_backends)} backend(s)"
        )
    
    async def create(self, thread: Thread) -> bool:
        """创建线程 - 保存到所有后端
        
        Args:
            thread: 线程实体
            
        Returns:
            是否创建成功
        """
        try:
            # 将 Thread 实体转换为存储格式
            data = self._thread_to_dict(thread)
            
            # 保存到主后端
            if not await self.primary_backend.save(thread.id, data):
                raise StorageError("Failed to save to primary backend")
            
            # 保存到辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.save(thread.id, data)
                except Exception as e:
                    logger.warning(f"Failed to save to secondary backend: {e}")
            
            logger.info(f"Thread created: {thread.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise StorageError(f"Failed to create thread: {e}")
    
    async def get(self, thread_id: str) -> Optional[Thread]:
        """获取线程 - 优先从主后端读取
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程实体，不存在返回None
        """
        try:
            # 从主后端读取
            data = await self.primary_backend.load(thread_id)
            if data is None:
                # 尝试从辅助后端读取
                for backend in self.secondary_backends:
                    try:
                        data = await backend.load(thread_id)
                        if data:
                            break
                    except Exception:
                        continue
            
            if data:
                return self._dict_to_thread(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get thread {thread_id}: {e}")
            return None
    
    async def update(self, thread: Thread) -> bool:
        """更新线程 - 更新所有后端
        
        Args:
            thread: 线程实体
            
        Returns:
            是否更新成功
        """
        try:
            data = self._thread_to_dict(thread)
            
            # 更新主后端
            if not await self.primary_backend.save(thread.id, data):
                raise StorageError("Failed to update primary backend")
            
            # 更新辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.save(thread.id, data)
                except Exception as e:
                    logger.warning(f"Failed to update secondary backend: {e}")
            
            logger.debug(f"Thread updated: {thread.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update thread: {e}")
            raise StorageError(f"Failed to update thread: {e}")
    
    async def delete(self, thread_id: str) -> bool:
        """删除线程 - 删除所有后端
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        try:
            # 删除主后端
            primary_deleted = await self.primary_backend.delete(thread_id)
            
            # 删除辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.delete(thread_id)
                except Exception as e:
                    logger.warning(f"Failed to delete from secondary backend: {e}")
            
            logger.info(f"Thread deleted: {thread_id}")
            return primary_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete thread: {e}")
            raise StorageError(f"Failed to delete thread: {e}")
    
    async def list_by_session(self, session_id: str) -> List[Thread]:
        """按会话列线程
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            threads = []
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if thread and thread.graph_id == session_id:
                    threads.append(thread)
            
            # 按更新时间倒序
            threads.sort(key=lambda t: t.updated_at, reverse=True)
            logger.debug(f"Listed {len(threads)} threads for session {session_id}")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to list threads by session: {e}")
            raise StorageError(f"Failed to list threads by session: {e}")
    
    async def list_by_status(self, status: ThreadStatus) -> List[Thread]:
        """按状态列线程
        
        Args:
            status: 线程状态
            
        Returns:
            线程列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            threads = []
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if thread and thread.status == status:
                    threads.append(thread)
            
            # 按更新时间倒序
            threads.sort(key=lambda t: t.updated_at, reverse=True)
            logger.debug(f"Listed {len(threads)} threads with status {status}")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to list threads by status: {e}")
            raise StorageError(f"Failed to list threads by status: {e}")
    
    async def search(
        self, 
        query: str, 
        session_id: Optional[str] = None, 
        limit: int = 10
    ) -> List[Thread]:
        """搜索线程
        
        Args:
            query: 查询字符串
            session_id: 会话ID过滤（可选）
            limit: 返回数量限制
            
        Returns:
            线程列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            threads = []
            
            query_lower = query.lower()
            for thread_id in keys:
                if len(threads) >= limit:
                    break
                
                # 检查线程ID是否匹配
                if query_lower in thread_id.lower():
                    thread = await self.get(thread_id)
                    if thread and (session_id is None or thread.graph_id == session_id):
                        threads.append(thread)
                    continue
                
                # 检查元数据是否匹配
                thread = await self.get(thread_id)
                if thread:
                    if session_id and thread.graph_id != session_id:
                        continue
                    
                    metadata_str = str(thread.metadata).lower()
                    if query_lower in metadata_str:
                        threads.append(thread)
            
            # 按更新时间倒序
            threads.sort(key=lambda t: t.updated_at, reverse=True)
            logger.debug(f"Searched and found {len(threads)} threads matching '{query}'")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to search threads: {e}")
            raise StorageError(f"Failed to search threads: {e}")
    
    async def get_count_by_session(self, session_id: str) -> int:
        """获取会话的线程数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            线程数量
        """
        try:
            keys = await self.primary_backend.list_keys()
            count = 0
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if thread and thread.graph_id == session_id:
                    count += 1
            
            logger.debug(f"Session {session_id} has {count} threads")
            return count
            
        except Exception as e:
            logger.error(f"Failed to get thread count by session: {e}")
            raise StorageError(f"Failed to get thread count by session: {e}")
    
    async def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧线程
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的线程数量
        """
        try:
            keys = await self.primary_backend.list_keys()
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if thread:
                    # 只清理已完成或失败的旧线程
                    is_terminal = thread.status in ['completed', 'failed']
                    is_old = thread.updated_at < cutoff_date
                    
                    if is_terminal and is_old:
                        if await self.delete(thread_id):
                            deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old threads")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old threads: {e}")
            raise StorageError(f"Failed to cleanup old threads: {e}")
    
    async def exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        try:
            return await self.primary_backend.exists(thread_id)
        except Exception as e:
            logger.error(f"Failed to check thread existence: {e}")
            raise StorageError(f"Failed to check thread existence: {e}")
    
    async def list_by_type(self, thread_type: ThreadType) -> List[Thread]:
        """按类型列线程
        
        Args:
            thread_type: 线程类型
            
        Returns:
            线程列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            threads = []
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if thread and thread.type == thread_type:
                    threads.append(thread)
            
            # 按更新时间倒序
            threads.sort(key=lambda t: t.updated_at, reverse=True)
            logger.debug(f"Listed {len(threads)} threads of type {thread_type}")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to list threads by type: {e}")
            raise StorageError(f"Failed to list threads by type: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取线程统计信息
        
        Returns:
            统计信息字典
        """
        try:
            keys = await self.primary_backend.list_keys()
            
            stats = {
                "total_threads": len(keys),
                "by_status": {},
                "by_type": {},
                "total_messages": 0,
                "total_checkpoints": 0,
                "total_branches": 0,
                "active_threads": 0,
                "completed_threads": 0,
                "failed_threads": 0
            }
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if thread:
                    # 按状态统计
                    status_key = thread.status
                    stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
                    
                    # 按类型统计
                    type_key = thread.type
                    stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
                    
                    # 累计统计
                    stats["total_messages"] += thread.message_count
                    stats["total_checkpoints"] += thread.checkpoint_count
                    stats["total_branches"] += thread.branch_count
                    
                    # 活跃线程统计
                    if thread.status == ThreadStatus.ACTIVE:
                        stats["active_threads"] += 1
                    elif thread.status == ThreadStatus.COMPLETED:
                        stats["completed_threads"] += 1
                    elif thread.status == ThreadStatus.FAILED:
                        stats["failed_threads"] += 1
            
            logger.debug(f"Generated thread statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get thread statistics: {e}")
            raise StorageError(f"Failed to get thread statistics: {e}")
    
    async def search_with_filters(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Thread]:
        """根据过滤条件搜索线程
        
        Args:
            filters: 过滤条件
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            线程列表
        """
        try:
            keys = await self.primary_backend.list_keys()
            threads = []
            
            # 应用偏移量
            start_index = offset or 0
            current_index = 0
            
            for thread_id in keys:
                thread = await self.get(thread_id)
                if not thread:
                    continue
                
                # 检查是否匹配所有过滤条件
                matches = True
                
                # 状态过滤
                if "status" in filters:
                    if isinstance(filters["status"], str):
                        if thread.status != filters["status"]:
                            matches = False
                    elif isinstance(filters["status"], list):
                        if thread.status not in filters["status"]:
                            matches = False
                
                # 类型过滤
                if "type" in filters and matches:
                    if isinstance(filters["type"], str):
                        if thread.type != filters["type"]:
                            matches = False
                    elif isinstance(filters["type"], list):
                        if thread.type not in filters["type"]:
                            matches = False
                
                # 会话ID过滤
                if "session_id" in filters and matches:
                    if thread.graph_id != filters["session_id"]:
                        matches = False
                
                # 父线程ID过滤
                if "parent_thread_id" in filters and matches:
                    if thread.parent_thread_id != filters["parent_thread_id"]:
                        matches = False
                
                # 标签过滤
                if "tags" in filters and matches:
                    required_tags = filters["tags"]
                    if isinstance(required_tags, str):
                        required_tags = [required_tags]
                    
                    metadata = thread.metadata
                    thread_tags = metadata.get("tags", []) if isinstance(metadata, dict) else []
                    if not any(tag in thread_tags for tag in required_tags):
                        matches = False
                
                # 创建时间范围过滤
                if "created_after" in filters and matches:
                    created_after = filters["created_after"]
                    if isinstance(created_after, str):
                        created_after = datetime.fromisoformat(created_after)
                    if thread.created_at < created_after:
                        matches = False
                
                if "created_before" in filters and matches:
                    created_before = filters["created_before"]
                    if isinstance(created_before, str):
                        created_before = datetime.fromisoformat(created_before)
                    if thread.created_at > created_before:
                        matches = False
                
                # 更新时间范围过滤
                if "updated_after" in filters and matches:
                    updated_after = filters["updated_after"]
                    if isinstance(updated_after, str):
                        updated_after = datetime.fromisoformat(updated_after)
                    if thread.updated_at < updated_after:
                        matches = False
                
                if "updated_before" in filters and matches:
                    updated_before = filters["updated_before"]
                    if isinstance(updated_before, str):
                        updated_before = datetime.fromisoformat(updated_before)
                    if thread.updated_at > updated_before:
                        matches = False
                
                if matches:
                    current_index += 1
                    if current_index > start_index:
                        threads.append(thread)
                        if limit and len(threads) >= limit:
                            break
            
            # 按更新时间倒序
            threads.sort(key=lambda t: t.updated_at, reverse=True)
            logger.debug(f"Found {len(threads)} threads matching filters")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to search threads with filters: {e}")
            raise StorageError(f"Failed to search threads with filters: {e}")
    
    # === 私有方法 ===
    
    def _thread_to_dict(self, thread: Thread) -> Dict[str, Any]:
        """线程实体转为字典
        
        Args:
            thread: 线程实体
            
        Returns:
            线程数据字典
        """
        return {
            "id": thread.id,
            "status": thread.status,
            "type": thread.type,
            "graph_id": thread.graph_id,
            "parent_thread_id": thread.parent_thread_id,
            "source_checkpoint_id": thread.source_checkpoint_id,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "metadata": thread.metadata,
            "config": thread.config,
            "state": thread.state,
            "message_count": thread.message_count,
            "checkpoint_count": thread.checkpoint_count,
            "branch_count": thread.branch_count
        }
    
    def _dict_to_thread(self, data: Dict[str, Any]) -> Thread:
        """字典转为线程实体
        
        Args:
            data: 线程数据字典
            
        Returns:
            线程实体
        """
        from src.core.threads.entities import ThreadMetadata
        
        metadata_data = data.get("metadata", {})
        metadata = ThreadMetadata(**metadata_data) if isinstance(metadata_data, dict) else metadata_data
        
        return Thread(
            id=data["id"],
            status=ThreadStatus(data["status"]),
            type=data.get("type", "main"),
            graph_id=data.get("graph_id"),
            parent_thread_id=data.get("parent_thread_id"),
            source_checkpoint_id=data.get("source_checkpoint_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=metadata,
            config=data.get("config", {}),
            state=data.get("state", {}),
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            branch_count=data.get("branch_count", 0)
        )
