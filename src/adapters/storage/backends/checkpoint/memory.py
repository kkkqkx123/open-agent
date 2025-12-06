"""Checkpoint内存存储后端

提供基于内存的checkpoint存储实现，实现ICheckpointStore和IThreadCheckpointStorage接口。
"""

import time
import uuid
import threading
from src.services.logger.injection import get_logger
from typing import Dict, Any, Optional, List, Union, cast

from src.interfaces.checkpoint.saver import ICheckpointSaver
from src.interfaces.threads.checkpoint import IThreadCheckpointStorage
from src.adapters.storage.adapters.base import StorageBackend
from src.core.checkpoint.validators import CheckpointValidationError
from src.adapters.storage.utils.common_utils import StorageCommonUtils
from src.core.threads.checkpoints.storage.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointStatistics
)
# 新增导入
from src.interfaces.checkpoint.saver import ICheckpointSaver
from src.core.checkpoint.models import Checkpoint, CheckpointMetadata, CheckpointTuple
from src.core.checkpoint.factory import CheckpointFactory


logger = get_logger(__name__)


class CheckpointMemoryBackend(StorageBackend, IThreadCheckpointStorage, ICheckpointSaver):
    """Checkpoint内存存储后端实现
    
    提供基于内存的checkpoint存储功能，实现ICheckpointStore和IThreadCheckpointStorage接口。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化checkpoint内存存储
        """
        super().__init__(**config)
        
        # 存储checkpoint数据
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        
        # 存储写入数据
        self._writes: Dict[tuple[str, str, str], Dict[str, Any]] = {}
        
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
                raise CheckpointValidationError("checkpoint_data必须包含'thread_id'")
            
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
            raise CheckpointValidationError(f"保存checkpoint失败: {e}") from e
    
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
            raise CheckpointValidationError(f"列出checkpoint失败: {e}") from e
    
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
            raise CheckpointValidationError(f"加载checkpoint失败: {e}") from e
    
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
            raise CheckpointValidationError(f"删除checkpoint失败: {e}") from e
    
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
            raise CheckpointValidationError(f"获取最新checkpoint失败: {e}") from e
    
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
             raise CheckpointValidationError(f"清理旧checkpoint失败: {e}") from e
    
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
            raise CheckpointValidationError(f"保存Thread检查点失败: {e}") from e
    
    async def load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载Thread检查点"""
        try:
            checkpoint_data = await self.load_by_thread(thread_id, checkpoint_id)
            if checkpoint_data:
                return ThreadCheckpoint.from_dict(checkpoint_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to load thread checkpoint: {e}")
            raise CheckpointValidationError(f"加载Thread检查点失败: {e}") from e
    
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
            raise CheckpointValidationError(f"列出Thread检查点失败: {e}") from e
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点"""
        try:
            return await self.delete_by_thread(thread_id, checkpoint_id)
            
        except Exception as e:
            logger.error(f"Failed to delete thread checkpoint: {e}")
            raise CheckpointValidationError(f"删除Thread检查点失败: {e}") from e
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点"""
        try:
            checkpoint_data = await self.get_latest(thread_id)
            if checkpoint_data:
                return ThreadCheckpoint.from_dict(checkpoint_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest thread checkpoint: {e}")
            raise CheckpointValidationError(f"获取最新Thread检查点失败: {e}") from e
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点"""
        try:
            return await self._cleanup_old_checkpoints_impl(thread_id, max_count)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old thread checkpoints: {e}")
            raise CheckpointValidationError(f"清理旧Thread检查点失败: {e}") from e
    
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
            raise CheckpointValidationError(f"获取Thread检查点统计失败: {e}") from e
    
    # === ICheckpointSaver 接口实现 ===
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点"""
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            checkpoint_id = config["configurable"].get("checkpoint_id")
            
            with self._storage_lock:
                if checkpoint_id:
                    # 获取特定检查点
                    checkpoint_data = self._checkpoints.get(checkpoint_id)
                    if checkpoint_data and checkpoint_data.get("thread_id") == thread_id:
                        return checkpoint_data
                else:
                    # 获取最新检查点
                    checkpoints = [
                        cp for cp in self._checkpoints.values()
                        if cp.get("thread_id") == thread_id and cp.get("checkpoint_ns") == checkpoint_ns
                    ]
                    if checkpoints:
                        # 按时间排序，返回最新的
                        checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
                        return checkpoints[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
            return None
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组"""
        try:
            checkpoint_data = self.get(config)
            if not checkpoint_data:
                return None
            
            # 获取写入数据
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            checkpoint_id = checkpoint_data.get("id")
            
            with self._storage_lock:
                writes = self._writes.get((thread_id, checkpoint_ns, checkpoint_id or ""), {})
                pending_writes = list(writes.items())
            
            # 创建检查点元组
            checkpoint = Checkpoint.from_dict(checkpoint_data)
            metadata = CheckpointMetadata(**checkpoint_data.get("metadata", {}))
            
            tuple_obj = CheckpointFactory.create_tuple(
                config=config,
                checkpoint=checkpoint,
                metadata=metadata,
                pending_writes=pending_writes
            )
            
            return tuple_obj.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint tuple: {e}")
            return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ):
        """列出匹配给定条件的检查点"""
        try:
            checkpoints = []
            
            with self._storage_lock:
                for checkpoint_data in self._checkpoints.values():
                    # 应用过滤条件
                    if config:
                        thread_id = config.get("configurable", {}).get("thread_id")
                        if thread_id and checkpoint_data.get("thread_id") != thread_id:
                            continue
                    
                    if filter:
                        match = True
                        for key, value in filter.items():
                            if checkpoint_data.get(key) != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    checkpoints.append(checkpoint_data)
                    
                    if limit and len(checkpoints) >= limit:
                        break
            
            # 按时间倒序排序
            checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
            
            # 转换为元组格式
            result = []
            for checkpoint_data in checkpoints:
                checkpoint = Checkpoint.from_dict(checkpoint_data)
                metadata = CheckpointMetadata(**checkpoint_data.get("metadata", {}))
                
                tuple_config = CheckpointFactory.create_config(
                    thread_id=checkpoint_data.get("thread_id", ""),
                    checkpoint_ns=checkpoint_data.get("checkpoint_ns", ""),
                    checkpoint_id=checkpoint_data.get("id")
                )
                
                tuple_obj = CheckpointFactory.create_tuple(
                    config=tuple_config,
                    checkpoint=checkpoint,
                    metadata=metadata
                )
                
                result.append(tuple_obj.to_dict())
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点"""
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = checkpoint.get("id", str(uuid.uuid4()))
            
            # 准备检查点数据
            checkpoint_data = {
                "id": checkpoint_id,
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "channel_values": checkpoint.get("channel_values", {}),
                "channel_versions": checkpoint.get("channel_versions", {}),
                "versions_seen": checkpoint.get("versions_seen", {}),
                "ts": checkpoint.get("ts", time.time()),
                "metadata": metadata,
                "created_at": time.time(),
                "updated_at": time.time()
            }
            
            # 保存检查点
            with self._storage_lock:
                self._checkpoints[checkpoint_id] = checkpoint_data
            
            # 返回更新后的配置
            updated_config = config.copy()
            updated_config["configurable"] = updated_config["configurable"].copy()
            updated_config["configurable"]["checkpoint_id"] = checkpoint_id
            
            return updated_config
            
        except Exception as e:
            logger.error(f"Failed to put checkpoint: {e}")
            raise CheckpointValidationError(f"保存检查点失败: {e}") from e
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: List[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入"""
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = config["configurable"]["checkpoint_id"]
            
            with self._storage_lock:
                key = (thread_id, checkpoint_ns, checkpoint_id or "")
                if key not in self._writes:
                    self._writes[key] = {}
                
                for channel, value in writes:
                    self._writes[key][channel] = value
            
        except Exception as e:
            logger.error(f"Failed to put writes: {e}")
            raise CheckpointValidationError(f"保存写入失败: {e}") from e