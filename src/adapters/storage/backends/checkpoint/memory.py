"""Checkpoint内存存储后端

提供基于内存的checkpoint存储实现，实现IThreadCheckpointStorage接口。
"""

import time
import uuid
from typing import Dict, Any, Optional, List, Union, cast, Sequence, Iterator
from datetime import datetime
from collections import defaultdict

from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointMetadata
from src.core.threads.checkpoints.extensions import ThreadCheckpointExtension
from src.interfaces.threads.checkpoint import IThreadCheckpointStorage
from src.services.logger.injection import get_logger
from src.interfaces.threads.checkpoint import (
    CheckpointValidationError,
    CheckpointNotFoundError,
    CheckpointStorageError,
)

from src.core.threads.checkpoints.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointStatistics
)


logger = get_logger(__name__)


class CheckpointMemoryBackend(IThreadCheckpointStorage):
    """Checkpoint内存存储后端实现

    提供基于内存的checkpoint存储功能，实现IThreadCheckpointStorage接口。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化checkpoint内存存储
        """
        # 内存存储
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._thread_checkpoints: Dict[str, ThreadCheckpoint] = {}
        self._writes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 配置
        self.max_checkpoints = config.get("max_checkpoints", 1000)
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
        
        # 统计信息
        self._stats: Dict[str, Any] = {
            "total_checkpoints": 0,
            "total_thread_checkpoints": 0,
            "total_writes": 0,
            "memory_usage_bytes": 0,
        }
        
        # 连接状态
        self._connected = False
        self._config = config
    
    async def connect(self) -> None:
        """连接到内存存储"""
        try:
            if self._connected:
                return
            
            self._connected = True
            logger.info("Connected to memory checkpoint storage")
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to connect to memory storage: {e}")
    
    async def disconnect(self) -> None:
        """断开与内存存储的连接"""
        try:
            if not self._connected:
                return
            
            # 清理所有数据
            self._checkpoints.clear()
            self._thread_checkpoints.clear()
            self._writes.clear()
            
            self._connected = False
            logger.info("Disconnected from memory checkpoint storage")
            
        except Exception as e:
            raise CheckpointStorageError(f"Failed to disconnect from memory storage: {e}")
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点"""
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = config["configurable"].get("checkpoint_id")
            
            # 构建键
            if checkpoint_id:
                key = f"{thread_id}:{checkpoint_ns}:{checkpoint_id}"
            else:
                # 获取最新的检查点
                key_prefix = f"{thread_id}:{checkpoint_ns}:"
                matching_keys = [k for k in self._checkpoints.keys() if k.startswith(key_prefix)]
                if not matching_keys:
                    return None
                
                # 按创建时间排序，获取最新的
                latest_key = max(matching_keys, 
                               key=lambda k: self._checkpoints[k].get("created_at", 0))
                key = latest_key
            
            checkpoint_data = self._checkpoints.get(key)
            if checkpoint_data:
                # 检查是否过期
                if self.enable_ttl:
                    created_at = checkpoint_data.get("created_at", 0)
                    if time.time() - created_at > self.default_ttl_seconds:
                        del self._checkpoints[key]
                        return None
                
                return checkpoint_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
            raise CheckpointStorageError(f"获取checkpoint失败: {e}")
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组"""
        try:
            checkpoint = self.get(config)
            if checkpoint:
                return {
                    "config": config,
                    "checkpoint": checkpoint,
                    "metadata": checkpoint.get("metadata", {}),
                    "parent_config": None
                }
            return None
            
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
    ) -> Iterator[Dict[str, Any]]:
        """列出匹配给定条件的检查点"""
        try:
            # 构建键前缀
            key_prefix = ""
            if config:
                thread_id = config.get("configurable", {}).get("thread_id")
                checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns")
                
                if thread_id:
                    key_prefix = f"{thread_id}:"
                if checkpoint_ns:
                    key_prefix += f"{checkpoint_ns}:"
            
            # 过滤检查点
            filtered_checkpoints = []
            for key, checkpoint_data in self._checkpoints.items():
                # 检查键前缀
                if key_prefix and not key.startswith(key_prefix):
                    continue
                
                # 检查是否过期
                if self.enable_ttl:
                    created_at = checkpoint_data.get("created_at", 0)
                    if time.time() - created_at > self.default_ttl_seconds:
                        continue
                
                # 应用过滤器
                if filter:
                    metadata = checkpoint_data.get("metadata", {})
                    match = True
                    for f_key, f_value in filter.items():
                        if metadata.get(f_key) != f_value:
                            match = False
                            break
                    if not match:
                        continue
                
                # 应用before条件
                if before:
                    before_time = before.get("step", 0)
                    created_at = checkpoint_data.get("created_at", 0)
                    if created_at >= before_time:
                        continue
                
                filtered_checkpoints.append((key, checkpoint_data))
            
            # 按创建时间排序
            filtered_checkpoints.sort(key=lambda x: x[1].get("created_at", 0), reverse=True)
            
            # 应用限制
            if limit:
                filtered_checkpoints = filtered_checkpoints[:limit]
            
            # 生成结果
            for key, checkpoint_data in filtered_checkpoints:
                # 解析键
                parts = key.split(":")
                thread_id = parts[0] if len(parts) > 0 else ""
                checkpoint_ns = parts[1] if len(parts) > 1 else ""
                checkpoint_id = parts[2] if len(parts) > 2 else ""
                
                yield {
                    "config": {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": checkpoint_id
                        }
                    },
                    "checkpoint": checkpoint_data,
                    "metadata": checkpoint_data.get("metadata", {}),
                    "parent_config": None
                }
                
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}")
    
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
            checkpoint_id = config["configurable"].get("checkpoint_id", str(uuid.uuid4()))
            
            # 构建键
            key = f"{thread_id}:{checkpoint_ns}:{checkpoint_id}"
            
            # 准备检查点数据
            current_time = time.time()
            checkpoint_data = {
                "id": checkpoint_id,
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "checkpoint_data": checkpoint,
                "metadata": metadata,
                "channel_values": checkpoint.get("channel_values", {}),
                "channel_versions": checkpoint.get("channel_versions", {}),
                "versions_seen": checkpoint.get("versions_seen", {}),
                "created_at": current_time,
                "updated_at": current_time,
                "expires_at": current_time + self.default_ttl_seconds if self.enable_ttl else None
            }
            
            # 检查容量限制
            if len(self._checkpoints) >= self.max_checkpoints:
                # 删除最旧的检查点
                oldest_key = min(self._checkpoints.keys(), 
                               key=lambda k: self._checkpoints[k].get("created_at", 0))
                del self._checkpoints[oldest_key]
            
            # 存储检查点
            self._checkpoints[key] = checkpoint_data
            self._stats["total_checkpoints"] += 1
            
            # 更新配置中的checkpoint_id
            updated_config = config.copy()
            updated_config["configurable"]["checkpoint_id"] = checkpoint_id
            
            return updated_config
            
        except Exception as e:
            logger.error(f"Failed to put checkpoint: {e}")
            raise CheckpointValidationError(f"保存checkpoint失败: {e}")
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入"""
        try:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"]["checkpoint_ns"]
            checkpoint_id = config["configurable"]["checkpoint_id"]
            
            # 构建键
            key = f"{thread_id}:{checkpoint_ns}:{checkpoint_id}"
            
            # 存储写入记录
            current_time = time.time()
            for channel, value in writes:
                write_record = {
                    "id": str(uuid.uuid4()),
                    "checkpoint_id": checkpoint_id,
                    "task_id": task_id,
                    "task_path": task_path,
                    "channel_name": channel,
                    "channel_value": value,
                    "created_at": current_time
                }
                self._writes[key].append(write_record)
                self._stats["total_writes"] += 1
            
        except Exception as e:
            logger.error(f"Failed to put writes: {e}")
            raise CheckpointStorageError(f"保存写入记录失败: {e}")
    
    # 实现IThreadCheckpointStorage接口
    async def save_thread_checkpoint(self, checkpoint: ThreadCheckpoint) -> str:
        """保存线程检查点"""
        try:
            self._thread_checkpoints[checkpoint.id] = checkpoint
            self._stats["total_thread_checkpoints"] += 1
            return checkpoint.id
            
        except Exception as e:
            raise CheckpointStorageError(f"保存线程检查点失败: {e}")
    
    async def load_thread_checkpoint(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载线程检查点"""
        try:
            checkpoint = self._thread_checkpoints.get(checkpoint_id)
            if checkpoint:
                # 检查是否过期
                if self.enable_ttl and checkpoint.is_expired():
                    del self._thread_checkpoints[checkpoint_id]
                    return None
            return checkpoint
            
        except Exception as e:
            raise CheckpointStorageError(f"加载线程检查点失败: {e}")
    
    async def list_thread_checkpoints(
        self, 
        thread_id: str, 
        status: Optional[CheckpointStatus] = None,
        limit: Optional[int] = None
    ) -> List[ThreadCheckpoint]:
        """列出线程检查点"""
        try:
            checkpoints = []
            
            for checkpoint in self._thread_checkpoints.values():
                # 过滤线程ID
                if checkpoint.thread_id != thread_id:
                    continue
                
                # 检查是否过期
                if self.enable_ttl and checkpoint.is_expired():
                    continue
                
                # 过滤状态
                if status and checkpoint.status != status:
                    continue
                
                checkpoints.append(checkpoint)
            
            # 按创建时间排序
            checkpoints.sort(key=lambda c: c.created_at, reverse=True)
            
            # 应用限制
            if limit:
                checkpoints = checkpoints[:limit]
            
            return checkpoints
            
        except Exception as e:
            raise CheckpointStorageError(f"列出线程检查点失败: {e}")
    
    async def delete_thread_checkpoint(self, checkpoint_id: str) -> bool:
        """删除线程检查点"""
        try:
            if checkpoint_id in self._thread_checkpoints:
                del self._thread_checkpoints[checkpoint_id]
                return True
            return False
            
        except Exception as e:
            raise CheckpointStorageError(f"删除线程检查点失败: {e}")
    
    async def get_thread_checkpoint_statistics(self, thread_id: str) -> CheckpointStatistics:
        """获取线程检查点统计信息"""
        try:
            stats = CheckpointStatistics()
            
            for checkpoint in self._thread_checkpoints.values():
                # 过滤线程ID
                if checkpoint.thread_id != thread_id:
                    continue
                
                # 检查是否过期
                if self.enable_ttl and checkpoint.is_expired():
                    continue
                
                # 更新统计
                stats.total_checkpoints += 1
                
                if checkpoint.status == CheckpointStatus.ACTIVE:
                    stats.active_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.EXPIRED:
                    stats.expired_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.CORRUPTED:
                    stats.corrupted_checkpoints += 1
                elif checkpoint.status == CheckpointStatus.ARCHIVED:
                    stats.archived_checkpoints += 1
                
                stats.total_size_bytes += checkpoint.size_bytes
                stats.total_restores += checkpoint.restore_count
                
                # 更新最值
                if not stats.largest_checkpoint_bytes or checkpoint.size_bytes > stats.largest_checkpoint_bytes:
                    stats.largest_checkpoint_bytes = checkpoint.size_bytes
                
                if not stats.smallest_checkpoint_bytes or checkpoint.size_bytes < stats.smallest_checkpoint_bytes:
                    stats.smallest_checkpoint_bytes = checkpoint.size_bytes
            
            # 计算平均值
            if stats.total_checkpoints > 0:
                stats.average_size_bytes = stats.total_size_bytes / stats.total_checkpoints
                stats.average_restores = stats.total_restores / stats.total_checkpoints
            
            return stats
            
        except Exception as e:
            raise CheckpointStorageError(f"获取线程检查点统计失败: {e}")
    
    async def cleanup_old_thread_checkpoints(self, thread_id: str, retention_days: int) -> int:
        """清理旧的线程检查点"""
        try:
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
            count = 0
            
            to_delete = []
            for checkpoint_id, checkpoint in self._thread_checkpoints.items():
                if checkpoint.thread_id != thread_id:
                    continue
                
                if checkpoint.created_at.timestamp() < cutoff_time:
                    to_delete.append(checkpoint_id)
            
            for checkpoint_id in to_delete:
                del self._thread_checkpoints[checkpoint_id]
                count += 1
            
            return count
            
        except Exception as e:
            raise CheckpointStorageError(f"清理旧线程检查点失败: {e}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        import sys
        
        total_size = 0
        for checkpoint_data in self._checkpoints.values():
            total_size += sys.getsizeof(checkpoint_data)
        
        for checkpoint in self._thread_checkpoints.values():
            total_size += sys.getsizeof(checkpoint)
        
        for writes_list in self._writes.values():
            for write_record in writes_list:
                total_size += sys.getsizeof(write_record)
        
        return {
            "total_checkpoints": len(self._checkpoints),
            "total_thread_checkpoints": len(self._thread_checkpoints),
            "total_writes": sum(len(writes) for writes in self._writes.values()),
            "memory_usage_bytes": total_size,
            "max_checkpoints": self.max_checkpoints,
        }