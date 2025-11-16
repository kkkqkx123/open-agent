"""基于LangGraph标准的内存checkpoint存储实现 - 重构版本

使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
"""

import logging
from typing import Dict, Any, Optional, List

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import CheckpointTuple

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ..common.serialization.serializer import Serializer
from ..common.cache.cache_manager import CacheManager
from ..common.temporal.temporal_manager import TemporalManager
from ..common.metadata.metadata_manager import MetadataManager
from ..common.monitoring.performance_monitor import PerformanceMonitor
from .types import CheckpointStorageError
from .checkpoint_base_storage import CheckpointBaseStorage
from .langgraph_adapter import LangGraphAdapter

logger = logging.getLogger(__name__)


class MemoryCheckpointStore(CheckpointBaseStorage):
    """基于LangGraph标准的内存checkpoint存储实现 - 重构版本
    
    使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
    仅支持内存存储。
    """
    
    def __init__(
        self,
        serializer: Optional[ICheckpointSerializer] = None,
        max_checkpoints_per_thread: int = 1000,
        enable_performance_monitoring: bool = True,
        universal_serializer: Optional[Serializer] = None,
        cache_manager: Optional[CacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化内存存储"""
        # 初始化基类
        super().__init__(
            serializer=serializer,
            temporal_manager=TemporalManager(),
            metadata_manager=MetadataManager(),
            cache_manager=cache_manager,
            performance_monitor=performance_monitor,
            max_checkpoints_per_thread=max_checkpoints_per_thread,
            enable_performance_monitoring=enable_performance_monitoring
        )
        
        # 使用公用组件
        self.universal_serializer = universal_serializer or Serializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        
        # 使用内存存储，适合开发和测试环境
        self._checkpointer = InMemorySaver()
        logger.info("使用内存存储")
        
        # 使用LangGraph适配器
        self.langgraph_adapter = LangGraphAdapter(
            serializer=serializer,
            universal_serializer=self.universal_serializer
        )
        
        logger.debug("checkpoint存储初始化完成")
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        operation_id = self.performance_monitor.start_operation("save_checkpoint")
        
        try:
            thread_id = checkpoint_data.get('thread_id')
            if not thread_id:
                raise ValueError("checkpoint_data必须包含'thread_id'")
            
            # 检查checkpoint数量限制
            current_count = await self.get_checkpoint_count(thread_id)
            if current_count >= self.max_checkpoints_per_thread:
                logger.warning(f"线程 {thread_id} 的checkpoint数量已达到最大限制 {self.max_checkpoints_per_thread}")
                # 清理旧的checkpoint
                await self.cleanup_old_checkpoints(thread_id, self.max_checkpoints_per_thread - 1)
            
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 使用LangGraph配置
            config = self.langgraph_adapter.create_config(thread_id)
            
            # 创建LangGraph checkpoint - 这里需要创建符合LangGraph格式的checkpoint
            # 但实际我们只需要正确的结构，langgraph会处理格式
            langgraph_checkpoint = self.langgraph_adapter.create_checkpoint(
                state, workflow_id, metadata
            )
            
            # 保存到LangGraph checkpointer
            # 注意：LangGraph的put方法需要特定的checkpoint格式
            self._checkpointer.put(config, langgraph_checkpoint, metadata, {})
            
            # 缓存checkpoint
            checkpoint_id = langgraph_checkpoint.get('id')
            if self.cache and checkpoint_id:
                await self.cache.delete(checkpoint_id)
                await self.cache.set(checkpoint_id, checkpoint_data, ttl=3600)
            
            logger.debug(f"成功保存checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
            
            # 记录性能指标
            self.performance_monitor.end_operation(
                operation_id, "save_checkpoint", True,
                {"thread_id": thread_id, "workflow_id": workflow_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            
            self.performance_monitor.end_operation(
                operation_id, "save_checkpoint", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"保存checkpoint失败: {e}")
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        operation_id = self.performance_monitor.start_operation("load_by_thread")
        
        try:
            # 先从缓存获取
            if self.cache and checkpoint_id:
                cached_checkpoint = await self.cache.get(checkpoint_id)
                if cached_checkpoint:
                    self.performance_monitor.end_operation(
                        operation_id, "load_by_thread", True,
                        {"cache_hit": True}
                    )
                    return cached_checkpoint
            
            # 创建LangGraph配置
            config = self.langgraph_adapter.create_config(thread_id, checkpoint_id)
            
            # 从LangGraph checkpointer获取
            result = self._checkpointer.get(config)
            if result:
                # 检查result是否为CheckpointTuple
                if isinstance(result, CheckpointTuple):
                    # 是CheckpointTuple对象
                    langgraph_checkpoint = result.checkpoint
                    metadata = result.metadata
                else:
                    # 是字典格式或其他格式
                    langgraph_checkpoint = result
                    metadata = {}
                
                # 提取状态
                state_data = self.langgraph_adapter.extract_state(langgraph_checkpoint, metadata)
                
                # 从LangGraph checkpoint获取workflow_id
                workflow_id = 'unknown'
                if isinstance(langgraph_checkpoint, dict):
                    channel_values = langgraph_checkpoint.get('channel_values', {})
                    workflow_id = channel_values.get('workflow_id', 'unknown')
                
                checkpoint_data = {
                    'id': langgraph_checkpoint.get('id') if isinstance(langgraph_checkpoint, dict) else None,
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': state_data,
                    'metadata': self.metadata.normalize_metadata(metadata),
                    'created_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None,
                    'updated_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None
                }
                
                # 缓存结果
                result_checkpoint_id = checkpoint_data.get('id')
                if self.cache and result_checkpoint_id:
                    await self.cache.delete(result_checkpoint_id)
                    await self.cache.set(result_checkpoint_id, checkpoint_data, ttl=3600)
                
                self.performance_monitor.end_operation(
                    operation_id, "load_by_thread", True,
                    {"cache_hit": False}
                )
                
                return checkpoint_data
            
            return None
        except Exception as e:
            logger.error(f"加载checkpoint失败: {e}")
            
            self.performance_monitor.end_operation(
                operation_id, "load_by_thread", False,
                {"error": str(e)}
            )
            
            raise
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        operation_id = self.performance_monitor.start_operation("list_by_thread")
        
        try:
            # 创建LangGraph配置
            config = self.langgraph_adapter.create_config(thread_id)
            
            # 从LangGraph checkpointer列出
            checkpoint_tuples = list(self._checkpointer.list(config))
            
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                # 检查是否为CheckpointTuple
                if isinstance(checkpoint_tuple, CheckpointTuple):
                    langgraph_checkpoint = checkpoint_tuple.checkpoint
                    metadata = checkpoint_tuple.metadata
                else:
                    langgraph_checkpoint = checkpoint_tuple
                    metadata = {}
                
                # 提取状态
                state_data = self.langgraph_adapter.extract_state(langgraph_checkpoint, metadata)
                
                # 从LangGraph checkpoint获取workflow_id
                workflow_id = 'unknown'
                if isinstance(langgraph_checkpoint, dict):
                    channel_values = langgraph_checkpoint.get('channel_values', {})
                    workflow_id = channel_values.get('workflow_id', 'unknown')
                
                result.append({
                    'id': langgraph_checkpoint.get('id') if isinstance(langgraph_checkpoint, dict) else None,
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': state_data,
                    'metadata': self.metadata.normalize_metadata(metadata),
                    'created_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None,
                    'updated_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None
                })
            
            # 按创建时间倒序排列
            result.sort(key=lambda x: x.get('created_at', '') or '', reverse=True)
            
            self.performance_monitor.end_operation(
                operation_id, "list_by_thread", True,
                {"thread_id": thread_id, "count": len(result)}
            )
            
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            
            self.performance_monitor.end_operation(
                operation_id, "list_by_thread", False,
                {"error": str(e)}
            )
            
            raise
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint"""
        operation_id = self.performance_monitor.start_operation("delete_by_thread")
        
        try:
            if checkpoint_id:
                # LangGraph的InMemorySaver不支持删除单个checkpoint，只能删除整个thread
                # 我们需要获取所有checkpoint，删除指定的，然后重新保存其他checkpoint
                all_checkpoints = await self.list_by_thread(thread_id)
                
                # 找到要保留的checkpoint（除要删除的之外）
                checkpoints_to_keep = [cp for cp in all_checkpoints if cp.get('id') != checkpoint_id]
                
                # 删除整个thread
                self._checkpointer.delete_thread(thread_id)
                
                # 清理缓存
                if self.cache:
                    await self.cache.delete(checkpoint_id)
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                self.performance_monitor.end_operation(
                    operation_id, "delete_by_thread", True,
                    {"thread_id": thread_id, "checkpoint_id": checkpoint_id}
                )
                
                return True
            else:
                # 删除整个thread的所有checkpoint
                self._checkpointer.delete_thread(thread_id)
                
                # 清理缓存中该thread的所有checkpoint
                if self.cache:
                    # 获取该thread的所有checkpoint并删除它们的缓存
                    all_checkpoints = await self.list_by_thread(thread_id)
                    for cp in all_checkpoints:
                        cp_id = cp.get('id')
                        if cp_id:
                            await self.cache.delete(cp_id)
                
                self.performance_monitor.end_operation(
                    operation_id, "delete_by_thread", True,
                    {"thread_id": thread_id, "all": True}
                )
                
                return True
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            
            self.performance_monitor.end_operation(
                operation_id, "delete_by_thread", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"删除checkpoint失败: {e}")
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        operation_id = self.performance_monitor.start_operation("cleanup_old_checkpoints")
        
        try:
            all_checkpoints = await self.list_by_thread(thread_id)
            if len(all_checkpoints) <= max_count:
                self.performance_monitor.end_operation(
                    operation_id, "cleanup_old_checkpoints", True,
                    {"thread_id": thread_id, "cleaned": 0}
                )
                return 0
            
            # 保留最新的max_count个checkpoint
            checkpoints_to_keep = all_checkpoints[:max_count]  # 按时间倒序排列，所以前max_count个是最新的
            checkpoints_to_delete = all_checkpoints[max_count:]
            
            # 删除整个thread
            self._checkpointer.delete_thread(thread_id)
            
            # 清理缓存
            if self.cache:
                for cp in checkpoints_to_delete:
                    cp_id = cp.get('id')
                    if cp_id:
                        await self.cache.delete(cp_id)
            
            # 重新保存需要保留的checkpoint
            for checkpoint_data in checkpoints_to_keep:
                await self.save(checkpoint_data)
            
            deleted_count = len(checkpoints_to_delete)
            
            self.performance_monitor.end_operation(
                operation_id, "cleanup_old_checkpoints", True,
                {"thread_id": thread_id, "cleaned": deleted_count}
            )
            
            return deleted_count
        except Exception as e:
            logger.error(f"清理旧checkpoint失败: {e}")
            
            self.performance_monitor.end_operation(
                operation_id, "cleanup_old_checkpoints", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"清理旧checkpoint失败: {e}")
    
    def clear(self):
        """清除所有checkpoint（仅用于测试）"""
        try:
            # 创建新的InMemorySaver实例来清除所有数据
            self._checkpointer = InMemorySaver()
            logger.debug("内存checkpoint存储已清空")
        except Exception as e:
            logger.error(f"清空内存checkpoint存储失败: {e}")
            raise CheckpointStorageError(f"清空内存checkpoint存储失败: {e}")
    
    def get_langgraph_checkpointer(self):
        """获取LangGraph原生的checkpointer"""
        return self._checkpointer