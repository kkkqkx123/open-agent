"""
内存检查点存储后端

提供基于内存的checkpoint存储实现。
"""

import time
from typing import Dict, Any, Optional, List
from collections import defaultdict

from src.interfaces.dependency_injection import get_logger
from src.core.threads.checkpoints.models import ThreadCheckpoint as Checkpoint, CheckpointStatus, CheckpointType
from src.infrastructure.threads.checkpoint_repository import ThreadCheckpointRepository
from .base import BaseCheckpointBackend


logger = get_logger(__name__)


class MemoryCheckpointBackend(BaseCheckpointBackend):
    """内存检查点存储后端"""
    
    def __init__(self, **config: Any) -> None:
        """初始化内存存储后端"""
        super().__init__(**config)
        
        # 内存存储
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._thread_index: Dict[str, List[str]] = defaultdict(list)
        self._status_index: Dict[CheckpointStatus, List[str]] = defaultdict(list)
        self._type_index: Dict[CheckpointType, List[str]] = defaultdict(list)
        
        # 配置
        self.max_checkpoints = config.get("max_checkpoints", 1000)
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
    
    async def _do_connect(self) -> None:
        """连接到内存存储"""
        # 内存存储不需要连接操作
        logger.info("Connected to memory checkpoint storage")
    
    async def _do_disconnect(self) -> None:
        """断开内存存储连接"""
        # 清理所有数据
        self._checkpoints.clear()
        self._thread_index.clear()
        self._status_index.clear()
        self._type_index.clear()
        logger.info("Disconnected from memory checkpoint storage")
    
    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点"""
        self._check_connection()
        
        try:
            # 检查容量限制
            if len(self._checkpoints) >= self.max_checkpoints:
                await self._cleanup_oldest_checkpoints()
            
            # 更新索引
            self._update_indexes(checkpoint)
            
            # 保存检查点
            self._checkpoints[checkpoint.id] = checkpoint
            
            logger.debug(f"Saved checkpoint {checkpoint.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint.id}: {e}")
            return False
    
    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        self._check_connection()
        
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint:
            # 检查是否过期
            if self.enable_ttl and checkpoint.is_expired():
                await self.delete(checkpoint_id)
                logger.debug(f"Checkpoint {checkpoint_id} expired and removed")
                return None
            
            logger.debug(f"Loaded checkpoint {checkpoint_id}")
            return checkpoint
        
        logger.debug(f"Checkpoint {checkpoint_id} not found")
        return None
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        self._check_connection()
        
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint:
            # 从索引中删除
            self._remove_from_indexes(checkpoint)
            
            # 从存储中删除
            del self._checkpoints[checkpoint_id]
            logger.debug(f"Deleted checkpoint {checkpoint_id}")
            return True
        
        logger.debug(f"Checkpoint {checkpoint_id} not found for deletion")
        return False
    
    async def list(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None,
        limit: Optional[int] = None
    ) -> List[Checkpoint]:
        """列出检查点"""
        self._check_connection()
        
        # 获取候选检查点ID
        candidate_ids = None
        
        if thread_id:
            candidate_ids = set(self._thread_index.get(thread_id, []))
        
        if status:
            status_ids = set(self._status_index.get(status, []))
            candidate_ids = status_ids if candidate_ids is None else candidate_ids & status_ids
        
        if checkpoint_type:
            type_ids = set(self._type_index.get(checkpoint_type, []))
            candidate_ids = type_ids if candidate_ids is None else candidate_ids & type_ids
        
        if candidate_ids is None:
            candidate_ids = set(self._checkpoints.keys())
        
        # 获取检查点并过滤
        checkpoints = []
        for checkpoint_id in candidate_ids:
            checkpoint = self._checkpoints.get(checkpoint_id)
            if checkpoint:
                # 检查是否过期
                if self.enable_ttl and checkpoint.is_expired():
                    continue
                
                checkpoints.append(checkpoint)
        
        # 按创建时间排序
        checkpoints.sort(key=lambda c: c.created_at, reverse=True)
        
        # 应用限制
        if limit:
            checkpoints = checkpoints[:limit]
        
        logger.debug(f"Listed {len(checkpoints)} checkpoints")
        return checkpoints
    
    async def count(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None
    ) -> int:
        """统计检查点数量"""
        checkpoints = await self.list(thread_id, status, checkpoint_type)
        count = len(checkpoints)
        logger.debug(f"Counted {count} checkpoints")
        return count
    
    async def cleanup_expired(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点"""
        self._check_connection()
        
        if not self.enable_ttl:
            logger.debug("TTL disabled, no cleanup needed")
            return 0
        
        expired_count = 0
        expired_checkpoints = []
        
        for checkpoint in self._checkpoints.values():
            if thread_id and checkpoint.thread_id != thread_id:
                continue
            
            if checkpoint.is_expired():
                expired_checkpoints.append(checkpoint)
        
        for checkpoint in expired_checkpoints:
            if await self.delete(checkpoint.id):
                expired_count += 1
        
        logger.info(f"Cleaned up {expired_count} expired checkpoints")
        return expired_count
    
    async def get_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息"""
        self._check_connection()
        
        checkpoints = await self.list(thread_id)
        
        # 基础统计
        total_count = len(checkpoints)
        status_counts = {}
        type_counts = {}
        total_size = 0
        total_restores = 0
        
        oldest_age = 0.0
        newest_age = float('inf')
        total_age = 0.0
        
        for checkpoint in checkpoints:
            # 状态统计
            status = checkpoint.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 类型统计
            cp_type = checkpoint.checkpoint_type.value
            type_counts[cp_type] = type_counts.get(cp_type, 0) + 1
            
            # 大小和恢复统计
            total_size += checkpoint.size_bytes
            total_restores += checkpoint.restore_count
            
            # 年龄统计
            age_hours = checkpoint.get_age_hours()
            total_age += age_hours
            oldest_age = max(oldest_age, age_hours)
            newest_age = min(newest_age, age_hours)
        
        # 修正newest_age（如果没有检查点）
        if newest_age == float('inf'):
            newest_age = 0.0
        
        return {
            "total_checkpoints": total_count,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "total_size_bytes": total_size,
            "average_size_bytes": total_size / total_count if total_count > 0 else 0,
            "total_restores": total_restores,
            "average_restores": total_restores / total_count if total_count > 0 else 0,
            "oldest_checkpoint_age_hours": oldest_age,
            "newest_checkpoint_age_hours": newest_age,
            "average_age_hours": total_age / total_count if total_count > 0 else 0,
        }
    
    def _update_indexes(self, checkpoint: Checkpoint) -> None:
        """更新索引"""
        # Thread索引
        if checkpoint.thread_id:
            if checkpoint.id not in self._thread_index[checkpoint.thread_id]:
                self._thread_index[checkpoint.thread_id].append(checkpoint.id)
        
        # 状态索引
        if checkpoint.id not in self._status_index[checkpoint.status]:
            self._status_index[checkpoint.status].append(checkpoint.id)
        
        # 类型索引
        if checkpoint.id not in self._type_index[checkpoint.checkpoint_type]:
            self._type_index[checkpoint.checkpoint_type].append(checkpoint.id)
    
    def _remove_from_indexes(self, checkpoint: Checkpoint) -> None:
        """从索引中删除"""
        # Thread索引
        if checkpoint.thread_id and checkpoint.id in self._thread_index[checkpoint.thread_id]:
            self._thread_index[checkpoint.thread_id].remove(checkpoint.id)
        
        # 状态索引
        if checkpoint.id in self._status_index[checkpoint.status]:
            self._status_index[checkpoint.status].remove(checkpoint.id)
        
        # 类型索引
        if checkpoint.id in self._type_index[checkpoint.checkpoint_type]:
            self._type_index[checkpoint.checkpoint_type].remove(checkpoint.id)
    
    async def _cleanup_oldest_checkpoints(self) -> None:
        """清理最旧的检查点"""
        if len(self._checkpoints) < self.max_checkpoints:
            return
        
        # 按创建时间排序
        sorted_checkpoints = sorted(
            self._checkpoints.values(),
            key=lambda c: c.created_at
        )
        
        # 删除最旧的10%
        cleanup_count = max(1, self.max_checkpoints // 10)
        for checkpoint in sorted_checkpoints[:cleanup_count]:
            await self.delete(checkpoint.id)
            logger.debug(f"Cleaned up old checkpoint {checkpoint.id}")