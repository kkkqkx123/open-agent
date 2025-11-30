"""Checkpoint内存存储后端

提供基于内存的checkpoint存储实现，实现ICheckpointStore和IThreadCheckpointStorage接口。
"""

import time
import uuid
import threading
import logging
from typing import Dict, Any, Optional, List, Union, cast

from src.interfaces.checkpoint import ICheckpointStore
from src.interfaces.threads.checkpoint import IThreadCheckpointStorage
from src.adapters.storage.adapters.base import StorageBackend
from src.core.common.exceptions import (
    CheckpointNotFoundError,
    CheckpointStorageError
)
from src.adapters.storage.utils.common_utils import StorageCommonUtils
from src.core.threads.checkpoints.storage.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointStatistics
)


logger = logging.getLogger(__name__)


class CheckpointMemoryBackend(StorageBackend, ICheckpointStore, IThreadCheckpointStorage):
    """Checkpoint内存存储后端实现
    
    提供基于内存的checkpoint存储功能，实现ICheckpointStore和IThreadCheckpointStorage接口。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化checkpoint内存存储
        """
        super().__init__(**config)
        
        # 存储checkpoint数据
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        
        # 线程安全锁
        self._storage_lock = threading.RLock()
        
        logger.info("CheckpointMemoryBackend initialized")
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存checkpoint数据
        
        Args:
            data: checkpoint数据字典
            
        Returns:
            str: 保存的数据ID
        """
        try:
            # 生成ID（如果没有）
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            checkpoint_id: str = data["id"]
            thread_id = data.get("thread_id", "")
            
            if not thread_id:
                raise CheckpointStorageError("checkpoint_data必须包含'thread_id'")
            
            # 添加时间戳
            current_time = time.time()
            data["created_at"] = data.get("created_at", current_time)
            data["updated_at"] = current_time
            
            # 保存到内存
            with self._storage_lock:
                self._checkpoints[checkpoint_id] = data
            
            logger.debug(f"Saved checkpoint {checkpoint_id} for thread {thread_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise CheckpointStorageError(f"保存checkpoint失败: {e}") from e
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            checkpoints = []
            
            with self._storage_lock:
                # 筛选指定thread的checkpoint
                for checkpoint_data in self._checkpoints.values():
                    if checkpoint_data.get("thread_id") == thread_id:
                        # 检查是否过期
                        if self._is_expired(checkpoint_data):
                            continue
                        checkpoints.append(checkpoint_data)
            
            # 按创建时间倒序排列
            checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
            
            logger.debug(f"Listed {len(checkpoints)} checkpoints for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}") from e
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        try:
            if checkpoint_id:
                # 根据ID加载特定checkpoint
                with self._storage_lock:
                    checkpoint_data = self._checkpoints.get(checkpoint_id)
                
                if checkpoint_data and checkpoint_data.get("thread_id") == thread_id:
                    # 检查是否过期
                    if self._is_expired(checkpoint_data):
                        await self.delete_by_thread(thread_id, checkpoint_id)
                        return None
                    return checkpoint_data
                else:
                    return None
            else:
                # 加载最新checkpoint
                return await self.get_latest(thread_id)
                
        except Exception as e:
            logger.error(f"Failed to load checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"加载checkpoint失败: {e}") from e
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID，如果为None则删除所有
            
        Returns:
            bool: 是否删除成功
        """
        try:
            deleted_count = 0
            
            with self._storage_lock:
                if checkpoint_id:
                    # 删除特定checkpoint
                    if (checkpoint_id in self._checkpoints and 
                        self._checkpoints[checkpoint_id].get("thread_id") == thread_id):
                        del self._checkpoints[checkpoint_id]
                        deleted_count = 1
                else:
                    # 删除thread的所有checkpoint
                    ids_to_delete = [
                        cp_id for cp_id, cp_data in self._checkpoints.items()
                        if cp_data.get("thread_id") == thread_id
                    ]
                    for cp_id in ids_to_delete:
                        del self._checkpoints[cp_id]
                        deleted_count += 1
            
            logger.debug(f"Deleted {deleted_count} checkpoints for thread {thread_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoints for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"删除checkpoint失败: {e}") from e
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        try:
            # 获取thread的所有checkpoint
            all_checkpoints = await self.list_by_thread(thread_id)
            
            if all_checkpoints:
                # 返回第一个（最新的）
                return all_checkpoints[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for thread {thread_id}: {e}")
            raise CheckpointStorageError(f"获取最新checkpoint失败: {e}") from e
    
    async def _cleanup_old_checkpoints_impl(self, thread_id: str, max_count: int) -> int:
         """清理旧的checkpoint，保留最新的max_count个（内部实现）
         
         Args:
             thread_id: thread ID
             max_count: 保留的最大数量
             
         Returns:
             int: 删除的checkpoint数量
         """
         try:
             # 获取thread的所有checkpoint（已按时间倒序排列）
             all_checkpoints = await self.list_by_thread(thread_id)
             
             if len(all_checkpoints) <= max_count:
                 # 不需要清理
                 return 0
             
             # 需要删除的checkpoint（保留最新的max_count个）
             checkpoints_to_delete = all_checkpoints[max_count:]
             
             # 删除旧的checkpoint
             deleted_count = 0
             for checkpoint_data in checkpoints_to_delete:
                 checkpoint_id = checkpoint_data.get("id")
                 if checkpoint_id:
                     success = await self.delete_by_thread(thread_id, checkpoint_id)
                     if success:
                         deleted_count += 1
             
             logger.debug(f"Cleaned up {deleted_count} old checkpoints for thread {thread_id}")
             return deleted_count
             
         except Exception as e:
             logger.error(f"Failed to cleanup old checkpoints for thread {thread_id}: {e}")
             raise CheckpointStorageError(f"清理旧checkpoint失败: {e}") from e
    
    def _is_expired(self, checkpoint_data: Dict[str, Any]) -> bool:
        """检查checkpoint是否过期
        
        Args:
            checkpoint_data: checkpoint数据
            
        Returns:
            bool: 是否过期
        """
        if not self.enable_ttl:
            return False
        
        expires_at = checkpoint_data.get("expires_at")
        if expires_at and isinstance(expires_at, (int, float)):
            return bool(expires_at < time.time())
        
        return False
    
    # 实现StorageBackend的抽象方法
    async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
        """实际保存实现"""
        # 如果数据是字节类型，需要反序列化
        if isinstance(data, bytes):
            data_dict = StorageCommonUtils.deserialize_data(data.decode('utf-8'))
        else:
            data_dict: Dict[str, Any] = data  # type: ignore
        
        # 生成ID
        item_id: str = cast(str, data_dict.get("id", str(uuid.uuid4())))
        data_dict["id"] = item_id
        
        # 保存到内存
        with self._storage_lock:
            self._checkpoints[item_id] = data_dict
        
        return item_id
    
    async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        with self._storage_lock:
            return self._checkpoints.get(id)
    
    async def delete_impl(self, id: str) -> bool:
        """实际删除实现"""
        with self._storage_lock:
            if id in self._checkpoints:
                del self._checkpoints[id]
                return True
            return False
    
    async def list_impl(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """实际列表实现"""
        results = []
        
        with self._storage_lock:
            for data in self._checkpoints.values():
                # 检查过滤器
                if StorageCommonUtils.matches_filters(data, filters):
                    results.append(data)
                    
                    # 检查限制
                    if limit and len(results) >= limit:
                        break
        
        return results
    
    async def health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        return {
            "status": "healthy",
            "backend_type": "checkpoint_memory",
            "total_checkpoints": len(self._checkpoints),
            "thread_count": len(set(cp.get("thread_id") for cp in self._checkpoints.values() if cp.get("thread_id"))),
            "memory_usage_approx": len(str(self._checkpoints)),  # 近似内存使用量
        }
    
    async def cleanup_old_data_impl(self, retention_days: int) -> int:
        """实际清理旧数据实现"""
        cutoff_time = StorageCommonUtils.calculate_cutoff_time(retention_days)
        count = 0
        
        with self._storage_lock:
            ids_to_delete = [
                cp_id for cp_id, cp_data in self._checkpoints.items()
                if cp_data.get("created_at", 0) < cutoff_time
            ]
            
            for cp_id in ids_to_delete:
                del self._checkpoints[cp_id]
                count += 1
        
        return count
    
    # === IThreadCheckpointStorage 接口实现 ===
    
    async def save_checkpoint(self, thread_id: str, checkpoint: ThreadCheckpoint) -> str:
        """保存Thread检查点"""
        try:
            # 确保thread_id匹配
            checkpoint.thread_id = thread_id
            
            # 转换为字典格式保存
            checkpoint_data = checkpoint.to_dict()
            return await self.save(checkpoint_data)
            
        except Exception as e:
            logger.error(f"Failed to save thread checkpoint: {e}")
            raise CheckpointStorageError(f"保存Thread检查点失败: {e}") from e
    
    async def load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载Thread检查点"""
        try:
            checkpoint_data = await self.load_by_thread(thread_id, checkpoint_id)
            if checkpoint_data:
                return ThreadCheckpoint.from_dict(checkpoint_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to load thread checkpoint: {e}")
            raise CheckpointStorageError(f"加载Thread检查点失败: {e}") from e
    
    async def list_checkpoints(self, thread_id: str, status: Optional[CheckpointStatus] = None) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点"""
        try:
            checkpoint_list = await self.list_by_thread(thread_id)
            
            # 转换为ThreadCheckpoint对象并过滤状态
            checkpoints = []
            for checkpoint_data in checkpoint_list:
                checkpoint = ThreadCheckpoint.from_dict(checkpoint_data)
                if status is None or checkpoint.status == status:
                    checkpoints.append(checkpoint)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list thread checkpoints: {e}")
            raise CheckpointStorageError(f"列出Thread检查点失败: {e}") from e
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点"""
        try:
            return await self.delete_by_thread(thread_id, checkpoint_id)
            
        except Exception as e:
            logger.error(f"Failed to delete thread checkpoint: {e}")
            raise CheckpointStorageError(f"删除Thread检查点失败: {e}") from e
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点"""
        try:
            checkpoint_data = await self.get_latest(thread_id)
            if checkpoint_data:
                return ThreadCheckpoint.from_dict(checkpoint_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest thread checkpoint: {e}")
            raise CheckpointStorageError(f"获取最新Thread检查点失败: {e}") from e
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点"""
        try:
            return await self._cleanup_old_checkpoints_impl(thread_id, max_count)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old thread checkpoints: {e}")
            raise CheckpointStorageError(f"清理旧Thread检查点失败: {e}") from e
    
    async def get_checkpoint_statistics(self, thread_id: str) -> CheckpointStatistics:
        """获取Thread检查点统计信息"""
        try:
            # 获取所有检查点
            checkpoints = await self.list_checkpoints(thread_id)
            
            # 计算统计信息
            stats = CheckpointStatistics()
            stats.total_checkpoints = len(checkpoints)
            
            for checkpoint in checkpoints:
                # 状态统计
                if checkpoint.status == CheckpointStatus.ACTIVE:
                    stats.active_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.EXPIRED:
                    stats.expired_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.CORRUPTED:
                    stats.corrupted_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.ARCHIVED:
                    stats.archived_checkpoints += 1
                
                # 大小统计
                stats.total_size_bytes += checkpoint.size_bytes
                if checkpoint.size_bytes > stats.largest_checkpoint_bytes:
                    stats.largest_checkpoint_bytes = checkpoint.size_bytes
                if stats.smallest_checkpoint_bytes == 0 or checkpoint.size_bytes < stats.smallest_checkpoint_bytes:
                    stats.smallest_checkpoint_bytes = checkpoint.size_bytes
                
                # 恢复统计
                stats.total_restores += checkpoint.restore_count
                
                # 年龄统计
                age_hours = checkpoint.get_age_hours()
                if stats.oldest_checkpoint_age_hours == 0 or age_hours > stats.oldest_checkpoint_age_hours:
                    stats.oldest_checkpoint_age_hours = age_hours
                if stats.newest_checkpoint_age_hours == 0 or age_hours < stats.newest_checkpoint_age_hours:
                    stats.newest_checkpoint_age_hours = age_hours
            
            # 计算平均值
            if stats.total_checkpoints > 0:
                stats.average_size_bytes = stats.total_size_bytes / stats.total_checkpoints
                stats.average_restores = stats.total_restores / stats.total_checkpoints
                stats.average_age_hours = (stats.oldest_checkpoint_age_hours + stats.newest_checkpoint_age_hours) / 2
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get thread checkpoint statistics: {e}")
            raise CheckpointStorageError(f"获取Thread检查点统计失败: {e}") from e