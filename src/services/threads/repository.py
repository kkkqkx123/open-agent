"""线程仓储实现"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.interfaces.threads.storage import IThreadRepository
from src.adapters.storage.backends.thread_base import IThreadStorageBackend
from src.core.threads.entities import Thread, ThreadStatus
from src.core.common.exceptions import StorageError

logger = logging.getLogger(__name__)


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
                    is_terminal = thread.status.value in ['completed', 'failed']
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
            "status": thread.status.value,
            "type": thread.type.value,
            "graph_id": thread.graph_id,
            "parent_thread_id": thread.parent_thread_id,
            "source_checkpoint_id": thread.source_checkpoint_id,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "metadata": thread.metadata.model_dump() if hasattr(thread.metadata, 'model_dump') else thread.metadata,
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
