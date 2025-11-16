"""Checkpoint存储基类实现

实现ICheckpointStore接口，提供通用的checkpoint存储功能。
"""

import logging
from abc import ABC
from typing import Dict, Any, Optional, List

from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointSerializer
from ..common.temporal.temporal_manager import TemporalManager
from ..common.metadata.metadata_manager import MetadataManager
from ..common.cache.cache_manager import CacheManager
from ..common.monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class CheckpointBaseStorage(ICheckpointStore, ABC):
    """Checkpoint存储基类，实现ICheckpointStore接口

    提供所有checkpoint存储实现的通用功能，包括序列化、缓存、性能监控等。
    """

    def __init__(
        self,
        serializer: Optional[ICheckpointSerializer] = None,
        temporal_manager=None,
        metadata_manager=None,
        cache_manager=None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        max_checkpoints_per_thread: int = 1000,
        enable_performance_monitoring: bool = True
    ):
        """初始化checkpoint存储基类
        
        Args:
            serializer: 状态序列化器
            temporal_manager: 时间管理器
            metadata_manager: 元数据管理器
            cache_manager: 缓存管理器
            performance_monitor: 性能监控器
            max_checkpoints_per_thread: 每个线程最大checkpoint数量
            enable_performance_monitoring: 是否启用性能监控
        """
        self.serializer = serializer
        self.temporal = temporal_manager or TemporalManager()
        self.metadata = metadata_manager or MetadataManager()
        self.cache = cache_manager
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.max_checkpoints_per_thread = max_checkpoints_per_thread
        self.enable_performance_monitoring = enable_performance_monitoring

    # ICheckpointStore接口实现
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        raise NotImplementedError

    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        raise NotImplementedError

    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        raise NotImplementedError

    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint"""
        raise NotImplementedError

    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            checkpoints = await self.list_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
        except Exception as e:
            logger.error(f"获取最新checkpoint失败: {e}")
            raise

    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            checkpoints = await self.list_by_thread(thread_id)
            return [cp for cp in checkpoints if cp.get('workflow_id') == workflow_id]
        except Exception as e:
            logger.error(f"获取工作流checkpoint失败: {e}")
            raise

    async def get_checkpoint_count(self, thread_id: str) -> int:
        """获取thread的checkpoint数量"""
        try:
            checkpoints = await self.list_by_thread(thread_id)
            return len(checkpoints)
        except Exception as e:
            logger.error(f"获取checkpoint数量失败: {e}")
            raise

    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        raise NotImplementedError

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {"performance_monitoring": self.enable_performance_monitoring}

    def reset_performance_metrics(self) -> None:
        """重置性能指标"""
        pass