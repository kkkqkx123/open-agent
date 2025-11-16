"""Checkpoint管理器实现 - 重构版本

提供checkpoint的创建、保存、恢复和管理功能。
"""

import uuid
import logging
from typing import Dict, Any, Optional, List, cast
from datetime import datetime

from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointManager, ICheckpointPolicy
from ...domain.checkpoint.config import CheckpointConfig
from ...infrastructure.common.serialization.serializer import Serializer
from src.infrastructure.common.cache.cache_manager import CacheManager
from ...infrastructure.common.temporal.temporal_manager import TemporalManager
from ...infrastructure.common.metadata.metadata_manager import MetadataManager
from ...infrastructure.common.id_generator.id_generator import IDGenerator
from ...infrastructure.common.monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class DefaultCheckpointPolicy(ICheckpointPolicy):
    """默认checkpoint策略
    
    基于配置和触发条件决定何时保存checkpoint。
    """
    
    def __init__(self, config: CheckpointConfig):
        """初始化策略
        
        Args:
            config: checkpoint配置
        """
        self.config = config
        self._step_counters: Dict[str, int] = {}
    
    def should_save_checkpoint(self, thread_id: str, workflow_id: str,
                              state: Any, context: Dict[str, Any]) -> bool:
        """判断是否应该保存checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该保存checkpoint
        """
        if not self.config.enabled:
            return False
        
        # 检查触发条件
        trigger_reason = context.get('trigger_reason', '')
        if trigger_reason in self.config.trigger_conditions:
            return True
        
        # 检查步数间隔
        if self.config.auto_save and self.config.save_interval > 0:
            thread_key = f"{thread_id}_{workflow_id}"
            step_count = self._step_counters.get(thread_key, 0) + 1
            self._step_counters[thread_key] = step_count
            
            if step_count % self.config.save_interval == 0:
                return True
        
        return False
    
    def get_checkpoint_metadata(self, thread_id: str, workflow_id: str,
                               state: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取checkpoint元数据
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: checkpoint元数据
        """
        thread_key = f"{thread_id}_{workflow_id}"
        step_count = self._step_counters.get(thread_key, 0)
        
        return {
            'checkpoint_id': str(uuid.uuid4()),
            'thread_id': thread_id,
            'workflow_id': workflow_id,
            'step_count': step_count,
            'node_name': context.get('node_name'),
            'trigger_reason': context.get('trigger_reason', 'auto_save'),
            'tags': context.get('tags', []),
            'custom_data': context.get('custom_data', {}),
            'created_at': datetime.now().isoformat()
        }


class CheckpointManager(ICheckpointManager):
    """Checkpoint管理器实现 - 重构版本
    
    协调checkpoint的创建、保存和恢复。
    """
    
    def __init__(
        self,
        checkpoint_store: ICheckpointStore,
        config: CheckpointConfig,
        policy: Optional[ICheckpointPolicy] = None,
        serializer: Optional[Serializer] = None,
        cache_manager: Optional[CacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化checkpoint管理器
        
        Args:
            checkpoint_store: checkpoint存储
            config: checkpoint配置
            policy: checkpoint策略
            serializer: 序列化器
            cache_manager: 缓存管理器
            performance_monitor: 性能监控器
        """
        self.checkpoint_store = checkpoint_store
        self.config = config
        self.policy = policy or DefaultCheckpointPolicy(config)
        self.serializer = serializer or Serializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        
        # 公用组件
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        self.id_generator = IDGenerator()
        
        logger.debug(f"Checkpoint管理器初始化完成，存储类型: {config.storage_type}")
    
    async def create_checkpoint(
        self,
        thread_id: str,
        workflow_id: str,
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint"""
        operation_id = self.monitor.start_operation("create_checkpoint")
        
        try:
            # 生成checkpoint ID
            checkpoint_id = self.id_generator.generate_checkpoint_id()
            
            # 准备checkpoint数据
            checkpoint_data = {
                'id': checkpoint_id,
                'thread_id': thread_id,
                'workflow_id': workflow_id,
                'state_data': {},  # 先初始化为空字典
                'original_state': state,  # 保存原始状态对象
                'metadata': metadata or {},
                'created_at': self.temporal.now(),
                'updated_at': self.temporal.now()
            }
            
            # 序列化状态数据
            serialized_state = self.serializer.serialize(state, "compact_json")
            checkpoint_data['serialized_state'] = serialized_state
            
            # 反序列化回来作为state_data，确保一致性
            checkpoint_data['state_data'] = self.serializer.deserialize(serialized_state, "compact_json")
            
            # 保存checkpoint
            success = await self.checkpoint_store.save(checkpoint_data)
            
            if success:
                # 缓存checkpoint
                if self.cache:
                    await self.cache.set(checkpoint_id, checkpoint_data, ttl=3600)
                
                logger.debug(f"Checkpoint创建成功: {checkpoint_id}")
                
                # 记录性能指标
                duration = self.monitor.end_operation(
                    operation_id, "create_checkpoint", True,
                    {"thread_id": thread_id, "workflow_id": workflow_id}
                )
                
                return checkpoint_id
            else:
                raise RuntimeError("创建checkpoint失败")
                
        except Exception as e:
            logger.error(f"创建checkpoint失败: {e}")
            
            # 记录失败指标
            self.monitor.end_operation(
                operation_id, "create_checkpoint", False,
                {"error": str(e)}
            )
            
            raise
    
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint"""
        operation_id = self.monitor.start_operation("get_checkpoint")
        
        try:
            # 先从缓存获取
            if self.cache:
                cached_checkpoint = await self.cache.get(checkpoint_id)
                if cached_checkpoint:
                    self.monitor.end_operation(
                        operation_id, "get_checkpoint", True,
                        {"cache_hit": True}
                    )
                    return cast(Dict[str, Any], cached_checkpoint)
            
            # 从存储加载
            checkpoint = await self.checkpoint_store.load_by_thread(thread_id, checkpoint_id)
            
            if checkpoint:
                # 反序列化状态数据
                if 'serialized_state' in checkpoint:
                    checkpoint['state_data'] = self.serializer.deserialize(
                        checkpoint['serialized_state'], "compact_json"
                    )
                
                # 缓存结果（包含original_state）
                if self.cache:
                    await self.cache.set(checkpoint_id, checkpoint, ttl=3600)
                
                self.monitor.end_operation(
                    operation_id, "get_checkpoint", True,
                    {"cache_hit": False}
                )
                
                return checkpoint
            
            return None
            
        except Exception as e:
            logger.error(f"获取checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "get_checkpoint", False,
                {"error": str(e)}
            )
            
            return None
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        operation_id = self.monitor.start_operation("list_checkpoints")
        
        try:
            result = await self.checkpoint_store.list_by_thread(thread_id)
            
            self.monitor.end_operation(
                operation_id, "list_checkpoints", True,
                {"thread_id": thread_id, "count": len(result)}
            )
            
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "list_checkpoints", False,
                {"error": str(e)}
            )
            
            return []
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        operation_id = self.monitor.start_operation("delete_checkpoint")
        
        try:
            result = await self.checkpoint_store.delete_by_thread(thread_id, checkpoint_id)
            
            # 清理缓存
            if result and self.cache:
                await self.cache.delete(checkpoint_id)
            
            self.monitor.end_operation(
                operation_id, "delete_checkpoint", True,
                {"thread_id": thread_id, "checkpoint_id": checkpoint_id}
            )
            
            return result
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "delete_checkpoint", False,
                {"error": str(e)}
            )
            
            return False
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        operation_id = self.monitor.start_operation("get_latest_checkpoint")
        
        try:
            result = await self.checkpoint_store.get_latest(thread_id)
            
            self.monitor.end_operation(
                operation_id, "get_latest_checkpoint", True,
                {"thread_id": thread_id}
            )
            
            return result
        except Exception as e:
            logger.error(f"获取最新checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "get_latest_checkpoint", False,
                {"error": str(e)}
            )
            
            return None
    
    async def restore_from_checkpoint(self, thread_id: str, checkpoint_id: str) -> Any:
        """从checkpoint恢复状态
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态对象，如果checkpoint不存在则返回None
            
        Raises:
            Exception: 恢复过程中发生错误
        """
        operation_id = self.monitor.start_operation("checkpoint_restore")
        
        try:
            # 获取checkpoint数据
            checkpoint = await self.get_checkpoint(thread_id, checkpoint_id)
            if not checkpoint:
                self.monitor.end_operation(
                    operation_id, "checkpoint_restore", False,
                    {"error": "checkpoint_not_found"}
                )
                return None
            
            # 返回原始状态对象
            original_state = checkpoint.get('original_state')
            if original_state:
                self.monitor.end_operation(
                    operation_id, "checkpoint_restore", True,
                    {"thread_id": thread_id, "checkpoint_id": checkpoint_id}
                )
                return original_state
            
            # 如果没有原始状态对象，尝试从序列化数据恢复
            if 'serialized_state' in checkpoint:
                restored_state = self.serializer.deserialize(
                    checkpoint['serialized_state'], "compact_json"
                )
                
                self.monitor.end_operation(
                    operation_id, "checkpoint_restore", True,
                    {"thread_id": thread_id, "checkpoint_id": checkpoint_id}
                )
                return restored_state
            
            # 如果都没有，返回空字典作为后备
            self.monitor.end_operation(
                operation_id, "checkpoint_restore", True,
                {"thread_id": thread_id, "checkpoint_id": checkpoint_id, "fallback": "empty_dict"}
            )
            return {}
            
        except Exception as e:
            logger.error(f"恢复checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "checkpoint_restore", False,
                {"error": str(e)}
            )
            
            raise
    
    async def auto_save_checkpoint(
        self,
        thread_id: str,
        workflow_id: str,
        state: Any,
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存checkpoint"""
        operation_id = self.monitor.start_operation("auto_save_checkpoint")
        
        try:
            context: Dict[str, Any] = {
                'trigger_reason': trigger_reason,
                'node_name': getattr(state, 'current_step', None),
                'tags': [trigger_reason],
                'custom_data': {}
            }
            
            # 检查是否应该保存checkpoint
            if not self.policy.should_save_checkpoint(thread_id, workflow_id, state, context):
                self.monitor.end_operation(
                    operation_id, "auto_save_checkpoint", True,
                    {"reason": "not_needed", "trigger_reason": trigger_reason}
                )
                return None
            
            # 获取元数据
            metadata = self.policy.get_checkpoint_metadata(thread_id, workflow_id, state, context)
            
            # 创建checkpoint
            checkpoint_id = await self.create_checkpoint(thread_id, workflow_id, state, metadata)
            
            # 清理旧checkpoint
            if self.config.max_checkpoints > 0:
                await self.cleanup_checkpoints(thread_id, self.config.max_checkpoints)
            
            self.monitor.end_operation(
                operation_id, "auto_save_checkpoint", True,
                {"checkpoint_id": checkpoint_id, "trigger_reason": trigger_reason}
            )
            
            return checkpoint_id
        except Exception as e:
            logger.error(f"自动保存checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "auto_save_checkpoint", False,
                {"error": str(e)}
            )
            
            return None
    
    async def cleanup_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint"""
        operation_id = self.monitor.start_operation("cleanup_checkpoints")
        
        try:
            result = await self.checkpoint_store.cleanup_old_checkpoints(thread_id, max_count)
            
            self.monitor.end_operation(
                operation_id, "cleanup_checkpoints", True,
                {"thread_id": thread_id, "max_count": max_count, "cleaned": result}
            )
            
            return result
        except Exception as e:
            logger.error(f"清理checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "cleanup_checkpoints", False,
                {"error": str(e)}
            )
            
            return 0
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        operation_id = self.monitor.start_operation("get_checkpoints_by_workflow")
        
        try:
            if hasattr(self.checkpoint_store, 'get_checkpoints_by_workflow'):
                result = await self.checkpoint_store.get_checkpoints_by_workflow(thread_id, workflow_id)
            else:
                # 过滤所有checkpoint
                all_checkpoints = await self.list_checkpoints(thread_id)
                result = [cp for cp in all_checkpoints if cp.get('workflow_id') == workflow_id]
            
            self.monitor.end_operation(
                operation_id, "get_checkpoints_by_workflow", True,
                {"thread_id": thread_id, "workflow_id": workflow_id, "count": len(result)}
            )
            
            return result
        except Exception as e:
            logger.error(f"获取工作流checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "get_checkpoints_by_workflow", False,
                {"error": str(e)}
            )
            
            return []
    
    async def get_checkpoint_count(self, thread_id: str) -> int:
        """获取thread的checkpoint数量"""
        operation_id = self.monitor.start_operation("get_checkpoint_count")
        
        try:
            if hasattr(self.checkpoint_store, 'get_checkpoint_count'):
                result = await self.checkpoint_store.get_checkpoint_count(thread_id)
            else:
                checkpoints = await self.list_checkpoints(thread_id)
                result = len(checkpoints)
            
            self.monitor.end_operation(
                operation_id, "get_checkpoint_count", True,
                {"thread_id": thread_id, "count": result}
            )
            
            return cast(int, result)
        except Exception as e:
            logger.error(f"获取checkpoint数量失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "get_checkpoint_count", False,
                {"error": str(e)}
            )
            
            return 0
    
    async def copy_checkpoint(
        self,
        source_thread_id: str,
        source_checkpoint_id: str,
        target_thread_id: str
    ) -> str:
        """复制checkpoint到另一个thread"""
        operation_id = self.monitor.start_operation("copy_checkpoint")
        
        try:
            # 获取源checkpoint
            source_checkpoint = await self.get_checkpoint(source_thread_id, source_checkpoint_id)
            if not source_checkpoint:
                raise ValueError(f"源checkpoint不存在: {source_checkpoint_id}")
            
            # 创建新的checkpoint ID
            new_checkpoint_id = self.id_generator.generate_checkpoint_id()
            
            # 复制数据并更新thread ID
            checkpoint_data = source_checkpoint.copy()
            checkpoint_data['id'] = new_checkpoint_id
            checkpoint_data['thread_id'] = target_thread_id
            checkpoint_data['created_at'] = self.temporal.now()
            checkpoint_data['updated_at'] = self.temporal.now()
            
            # 保存到目标thread
            success = await self.checkpoint_store.save(checkpoint_data)
            if success:
                logger.debug(f"成功复制checkpoint从 {source_thread_id}:{source_checkpoint_id} 到 {target_thread_id}:{new_checkpoint_id}")
                
                self.monitor.end_operation(
                    operation_id, "copy_checkpoint", True,
                    {
                        "source_thread_id": source_thread_id,
                        "source_checkpoint_id": source_checkpoint_id,
                        "target_thread_id": target_thread_id,
                        "new_checkpoint_id": new_checkpoint_id
                    }
                )
                
                return new_checkpoint_id
            else:
                raise RuntimeError("复制checkpoint失败")
        except Exception as e:
            logger.error(f"复制checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "copy_checkpoint", False,
                {"error": str(e)}
            )
            
            raise
    
    async def export_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """导出checkpoint数据"""
        operation_id = self.monitor.start_operation("export_checkpoint")
        
        try:
            checkpoint = await self.get_checkpoint(thread_id, checkpoint_id)
            if not checkpoint:
                raise ValueError(f"Checkpoint不存在: {checkpoint_id}")
            
            self.monitor.end_operation(
                operation_id, "export_checkpoint", True,
                {"thread_id": thread_id, "checkpoint_id": checkpoint_id}
            )
            
            # 返回checkpoint数据
            return checkpoint
        except Exception as e:
            logger.error(f"导出checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "export_checkpoint", False,
                {"error": str(e)}
            )
            
            raise
    
    async def import_checkpoint(
        self,
        thread_id: str,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """导入checkpoint数据"""
        operation_id = self.monitor.start_operation("import_checkpoint")
        
        try:
            # 创建新的checkpoint ID
            new_checkpoint_id = self.id_generator.generate_checkpoint_id()
            
            # 更新数据
            checkpoint_data = checkpoint_data.copy()
            checkpoint_data['id'] = new_checkpoint_id
            checkpoint_data['thread_id'] = thread_id
            checkpoint_data['created_at'] = self.temporal.now()
            checkpoint_data['updated_at'] = self.temporal.now()
            
            # 保存checkpoint
            success = await self.checkpoint_store.save(checkpoint_data)
            if success:
                logger.debug(f"成功导入checkpoint到 {thread_id}:{new_checkpoint_id}")
                
                self.monitor.end_operation(
                    operation_id, "import_checkpoint", True,
                    {"thread_id": thread_id, "checkpoint_id": new_checkpoint_id}
                )
                
                return new_checkpoint_id
            else:
                raise RuntimeError("导入checkpoint失败")
        except Exception as e:
            logger.error(f"导入checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "import_checkpoint", False,
                {"error": str(e)}
            )
            
            raise
    
    def get_langgraph_checkpointer(self) -> Any:
        """获取LangGraph原生的checkpointer"""
        if hasattr(self.checkpoint_store, 'get_langgraph_checkpointer'):
            return self.checkpoint_store.get_langgraph_checkpointer()
        return None