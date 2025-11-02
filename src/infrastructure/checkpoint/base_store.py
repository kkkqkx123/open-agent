"""Checkpoint存储基类实现

定义所有checkpoint存储实现的通用基类。
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointSerializer
from .types import CheckpointError
from .performance import monitor_performance

logger = logging.getLogger(__name__)


class BaseCheckpointStore(ICheckpointStore, ABC):
    """Checkpoint存储的基类
    
    提供所有checkpoint存储实现的通用功能。
    """
    
    def __init__(self, serializer: Optional[ICheckpointSerializer] = None,
                 max_checkpoints_per_thread: int = 1000,
                 enable_performance_monitoring: bool = True):
        """初始化基类
        
        Args:
            serializer: 状态序列化器
            max_checkpoints_per_thread: 每个线程最大checkpoint数量
            enable_performance_monitoring: 是否启用性能监控
        """
        self.serializer = serializer
        self.max_checkpoints_per_thread = max_checkpoints_per_thread
        self.enable_performance_monitoring = enable_performance_monitoring
    
    @abstractmethod
    def _create_langgraph_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Any:
        """创建LangGraph标准配置
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            LangGraph配置对象
        """
        pass
    
    @abstractmethod
    def _create_langgraph_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Any:
        """创建LangGraph标准checkpoint
        
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
            
        Returns:
            LangGraph checkpoint对象
        """
        pass
    
    @abstractmethod
    def _extract_state_from_checkpoint(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            metadata: 可选的元数据
            
        Returns:
            提取的状态对象
        """
        pass
    
    @abstractmethod
    def _normalize_metadata(self, metadata: Any) -> Dict[str, Any]:
        """标准化metadata为字典格式
        
        Args:
            metadata: 原始metadata对象
            
        Returns:
            标准化的metadata字典
        """
        pass
    
    @monitor_performance("store.get_latest")
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        try:
            checkpoints = await self.list_by_thread(thread_id)
            return checkpoints[0] if checkpoints else None
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"获取最新checkpoint失败: {e}")
            raise
    
    @monitor_performance("store.get_checkpoints_by_workflow")
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            checkpoints = await self.list_by_thread(thread_id)
            return [cp for cp in checkpoints if cp.get('workflow_id') == workflow_id]
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"获取工作流checkpoint失败: {e}")
            raise
    
    @monitor_performance("store.get_checkpoint_count")
    async def get_checkpoint_count(self, thread_id: str) -> int:
        """获取thread的checkpoint数量
        
        Args:
            thread_id: thread ID
            
        Returns:
            int: checkpoint数量
        """
        try:
            checkpoints = await self.list_by_thread(thread_id)
            return len(checkpoints)
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"获取checkpoint数量失败: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            Dict[str, Any]: 性能指标
        """
        if not self.enable_performance_monitoring:
            return {"performance_monitoring": False}
        
        from .performance import get_performance_metrics
        return get_performance_metrics()
    
    def reset_performance_metrics(self) -> None:
        """重置性能指标"""
        if self.enable_performance_monitoring:
            from .performance import reset_performance_metrics
            reset_performance_metrics()