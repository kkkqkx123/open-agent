"""基于LangGraph标准的内存checkpoint存储实现 - 重构版本

使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
支持生产环境下的SQLite数据库存储选项。
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Tuple, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import CheckpointTuple

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ...infrastructure.common.serialization.universal_serializer import Serializer
from ...common.cache.cache_manager import CacheManager
from ...infrastructure.common.temporal.temporal_manager import TemporalManager
from ...infrastructure.common.metadata.metadata_manager import MetadataManager
from ...infrastructure.common.monitoring.performance_monitor import PerformanceMonitor
from .types import CheckpointNotFoundError, CheckpointStorageError

logger = logging.getLogger(__name__)


from .base_store import BaseCheckpointStore


class MemoryCheckpointAdapter:
    """LangGraph内存checkpoint适配器 - 重构版本
    
    将LangGraph原生的内存checkpoint存储适配到项目的接口。
    仅支持InMemorySaver。
    """
    
    def __init__(
        self, 
        checkpointer: Any, 
        serializer: Optional[ICheckpointSerializer] = None,
        universal_serializer: Optional[Serializer] = None,
        cache_manager: Optional[CacheManager] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """初始化适配器
        
        Args:
            checkpointer: LangGraph原生的checkpointer (InMemorySaver)
            serializer: 状态序列化器
            universal_serializer: 通用序列化器
            cache_manager: 缓存管理器
            performance_monitor: 性能监控器
        """
        self.checkpointer = checkpointer
        self.serializer = serializer
        self.universal_serializer = universal_serializer or Serializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        
        # 公用组件
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        
        # 验证checkpointer类型
        if not hasattr(checkpointer, 'put') or not hasattr(checkpointer, 'get'):
            raise CheckpointStorageError("提供的checkpointer不符合要求")
    
    def _create_langgraph_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """创建LangGraph标准配置
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Dict[str, Any]: LangGraph配置
        """
        config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        return config
    
    def _create_langgraph_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """创建LangGraph标准checkpoint
        
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (LangGraph checkpoint, 增强的metadata)
        """
        # 使用公用序列化器序列化状态
        try:
            serialized_state = self.universal_serializer.serialize(state, "compact_json")
        except Exception as e:
            logger.error(f"状态序列化失败: {e}")
            raise CheckpointStorageError(f"状态序列化失败: {e}")
        
        # 优化：直接在channel_values中存储状态，避免在metadata中重复存储
        channel_values = {
            "state": serialized_state,  # 使用更明确的字段名存储状态
            "workflow_id": workflow_id
        }
        
        # 使用公用组件处理元数据
        enhanced_metadata = self.metadata.normalize_metadata(metadata)
        enhanced_metadata['workflow_id'] = workflow_id
        
        return {
            "v": 4,
            "ts": self.temporal.format_timestamp(self.temporal.now(), "iso"),
            "id": str(uuid.uuid4()),
            "channel_values": channel_values,
            "channel_versions": {
                "state": 1,
                "__start__": 2,
                "workflow_id": 1
            },
            "versions_seen": {
                "state": {"__start__": 1},
                "__start__": {"__start__": 1}
            }
        }, enhanced_metadata
    
    def _extract_state_from_checkpoint(self, checkpoint: Any, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            metadata: 可选的元数据，用于获取状态数据
            
        Returns:
            Any: 提取的状态
        """
        if not checkpoint:
            return {}
        
        try:
            # 从checkpoint的channel_values获取状态
            if isinstance(checkpoint, dict):
                channel_values = checkpoint.get("channel_values", {})
            elif hasattr(checkpoint, 'checkpoint'):
                channel_values = checkpoint.checkpoint.get("channel_values", {})
            else:
                channel_values = {}
            
            # 优化：从新的state字段获取状态数据
            state_data = channel_values.get("state")
            if state_data is not None:
                # 使用公用序列化器反序列化
                return self.universal_serializer.deserialize(state_data, "compact_json")
            
            # 如果以上都失败，返回空字典
            return {}
        except Exception as e:
            logger.error(f"提取状态失败: {e}")
            return {}
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> bool:
        """保存checkpoint"""
        operation_id = self.monitor.start_operation("adapter.put")
        
        try:
            logger.debug(f"保存checkpoint，thread_id: {config.get('configurable', {}).get('thread_id')}")
            self.checkpointer.put(config, checkpoint, metadata, new_versions)
            
            self.monitor.end_operation(operation_id, "adapter.put", True)
            return True
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            
            self.monitor.end_operation(operation_id, "adapter.put", False, {"error": str(e)})
            raise CheckpointStorageError(f"保存checkpoint失败: {e}")
    
    def get(self, config: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """获取checkpoint"""
        operation_id = self.monitor.start_operation("adapter.get")
        
        try:
            result = self.checkpointer.get(config)
            if result:
                # 处理不同类型的结果
                if isinstance(result, CheckpointTuple):
                    checkpoint_obj = result.checkpoint
                    # 确保checkpoint_dict是字典类型
                    if isinstance(checkpoint_obj, dict):
                        checkpoint_dict = checkpoint_obj
                    else:
                        checkpoint_dict = {"checkpoint": checkpoint_obj}
                    metadata = self.metadata.normalize_metadata(result.metadata)
                    # 使用cast确保类型安全
                    return (cast(Dict[str, Any], checkpoint_dict), metadata)
                elif isinstance(result, dict):
                    checkpoint_dict = result
                    # 尝试从list方法获取metadata
                    try:
                        list_results = self.checkpointer.list(config)
                        for checkpoint_tuple in list_results:
                            if hasattr(checkpoint_tuple, 'checkpoint') and hasattr(checkpoint_tuple, 'metadata'):
                                # 找到匹配的checkpoint，返回其metadata
                                checkpoint_tuple_checkpoint = checkpoint_tuple.checkpoint
                                checkpoint_id = checkpoint_tuple_checkpoint.get('id') if hasattr(checkpoint_tuple_checkpoint, 'get') else None
                                result_id = checkpoint_dict.get('id')
                                if checkpoint_id == result_id:
                                    metadata = self.metadata.normalize_metadata(checkpoint_tuple.metadata)
                                    # 确保返回的是字典类型
                                    if not isinstance(checkpoint_dict, dict):
                                        checkpoint_dict = {"checkpoint": checkpoint_dict}
                                    return (cast(Dict[str, Any], checkpoint_dict), metadata)
                    except Exception as e:
                        logger.warning(f"获取metadata失败: {e}")
                    
                    # 如果没有找到匹配的metadata，返回空字典
                    # 确保返回的是字典类型
                    if not isinstance(checkpoint_dict, dict):
                        checkpoint_dict = {"checkpoint": checkpoint_dict}
                    return (cast(Dict[str, Any], checkpoint_dict), {})
            
            self.monitor.end_operation(operation_id, "adapter.get", True)
            return None
        except Exception as e:
            logger.error(f"获取checkpoint失败: {e}")
            
            self.monitor.end_operation(operation_id, "adapter.get", False, {"error": str(e)})
            raise CheckpointNotFoundError(f"获取checkpoint失败: {e}")
    
    def list(self, config: Dict[str, Any], limit: Optional[int] = None) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """列出checkpoint"""
        operation_id = self.monitor.start_operation("adapter.list")
        
        try:
            checkpoint_tuples = list(self.checkpointer.list(config, limit=limit))
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                # CheckpointTuple有config, checkpoint, metadata等属性
                if hasattr(checkpoint_tuple, 'checkpoint'):
                    checkpoint = dict(checkpoint_tuple.checkpoint) if hasattr(checkpoint_tuple.checkpoint, '__dict__') else checkpoint_tuple.checkpoint
                    metadata = self.metadata.normalize_metadata(checkpoint_tuple.metadata)
                    result.append((checkpoint, metadata))
            
            self.monitor.end_operation(operation_id, "adapter.list", True, {"count": len(result)})
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            
            self.monitor.end_operation(operation_id, "adapter.list", False, {"error": str(e)})
            raise CheckpointStorageError(f"列出checkpoint失败: {e}")
    
    def delete(self, config: Dict[str, Any]) -> bool:
        """删除checkpoint"""
        operation_id = self.monitor.start_operation("adapter.delete")
        
        try:
            # LangGraph的InMemorySaver使用delete_thread方法
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                if hasattr(self.checkpointer, 'delete_thread'):
                    self.checkpointer.delete_thread(thread_id)
                    
                    self.monitor.end_operation(operation_id, "adapter.delete", True, {"thread_id": thread_id})
                    return True
                else:
                    # 对于数据库存储，可能需要其他删除方式
                    logger.warning(f"当前checkpointer不支持delete_thread方法: {type(self.checkpointer)}")
            
            self.monitor.end_operation(operation_id, "adapter.delete", False, {"thread_id": thread_id})
            return False
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            
            self.monitor.end_operation(operation_id, "adapter.delete", False, {"error": str(e)})
            raise CheckpointStorageError(f"删除checkpoint失败: {e}")


class MemoryCheckpointStore(BaseCheckpointStore):
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
        super().__init__(serializer, max_checkpoints_per_thread, enable_performance_monitoring)
        
        # 使用公用组件
        self.universal_serializer = universal_serializer or Serializer()
        self.cache = cache_manager
        self.monitor = performance_monitor or PerformanceMonitor()
        self.temporal = TemporalManager()
        self.metadata = MetadataManager()
        
        # 使用内存存储，适合开发和测试环境
        self._checkpointer = InMemorySaver()
        logger.info("使用内存存储")
        
        self._adapter = MemoryCheckpointAdapter(
            self._checkpointer, 
            serializer,
            self.universal_serializer,
            self.cache,
            self.monitor
        )
        
        # 内部checkpoint_id到thread_id的映射，用于支持load和delete方法
        self._checkpoint_thread_mapping: Dict[str, str] = {}
        
        logger.debug("checkpoint存储初始化完成")
    
    def _ensure_checkpointer_initialized(self):
        """确保checkpointer已初始化"""
        # 内存存储不需要额外初始化
        pass
    
    def _update_checkpoint_mapping(self, thread_id: str, checkpoint_id: str):
        """更新checkpoint到thread的映射"""
        self._checkpoint_thread_mapping[checkpoint_id] = thread_id
    
    def _get_thread_id_from_checkpoint(self, checkpoint_id: str) -> Optional[str]:
        """从checkpoint ID获取thread ID"""
        return self._checkpoint_thread_mapping.get(checkpoint_id)
    
    def _create_langgraph_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """创建LangGraph标准配置"""
        config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        return config
    
    def _create_langgraph_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Any:
        """创建LangGraph标准checkpoint"""
        # 直接使用adapter中的实现
        checkpoint, _ = self._adapter._create_langgraph_checkpoint(state, workflow_id, metadata)
        return checkpoint
    
    def _extract_state_from_checkpoint(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态"""
        # 直接使用adapter中的实现
        return self._adapter._extract_state_from_checkpoint(checkpoint, metadata)
    
    def _normalize_metadata(self, metadata: Any) -> Dict[str, Any]:
        """标准化metadata为字典格式"""
        # 使用公用组件
        return self.metadata.normalize_metadata(metadata)
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        operation_id = self.monitor.start_operation("save_checkpoint")
        
        try:
            # 确保checkpointer已初始化
            self._ensure_checkpointer_initialized()
            
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
            
            # 使用公用组件处理元数据
            normalized_metadata = self.metadata.normalize_metadata(metadata)
            checkpoint_data['metadata'] = normalized_metadata
            
            # 创建LangGraph配置
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
            
            # 创建LangGraph checkpoint
            checkpoint, enhanced_metadata = self._adapter._create_langgraph_checkpoint(
                state, workflow_id, normalized_metadata
            )
            
            # 更新映射关系
            self._update_checkpoint_mapping(thread_id, checkpoint['id'])
            
            # 保存checkpoint
            success = self._adapter.put(config, checkpoint, enhanced_metadata, {})
            
            if success:
                # 缓存checkpoint
                if self.cache:
                    await self.cache.set(checkpoint['id'], checkpoint_data, ttl=3600)
                
                logger.debug(f"成功保存checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
                
                # 记录性能指标
                self.monitor.end_operation(
                    operation_id, "save_checkpoint", True,
                    {"thread_id": thread_id, "workflow_id": workflow_id}
                )
                
                return success
            else:
                raise RuntimeError("保存checkpoint失败")
                
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "save_checkpoint", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"保存checkpoint失败: {e}")
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint"""
        operation_id = self.monitor.start_operation("load_by_thread")
        
        try:
            # 先从缓存获取
            if self.cache and checkpoint_id:
                cached_checkpoint = await self.cache.get(checkpoint_id)
                if cached_checkpoint:
                    self.monitor.end_operation(
                        operation_id, "load_by_thread", True,
                        {"cache_hit": True}
                    )
                    return cached_checkpoint
            
            # 确保checkpointer已初始化
            self._ensure_checkpointer_initialized()
            
            # 创建LangGraph配置
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
            if checkpoint_id:
                config["configurable"]["checkpoint_id"] = checkpoint_id
            
            # 使用get方法获取指定checkpoint
            result = self._adapter.get(config)
            if result:
                checkpoint, metadata = result
                
                # 从metadata中获取workflow_id
                workflow_id = metadata.get('workflow_id', 'unknown')
                
                checkpoint_data = {
                    'id': checkpoint.get('id'),
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': self._adapter._extract_state_from_checkpoint(checkpoint, metadata),
                    'metadata': metadata,
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                }
                
                # 缓存结果
                if self.cache and checkpoint_id:
                    await self.cache.set(checkpoint_id, checkpoint_data, ttl=3600)
                
                self.monitor.end_operation(
                    operation_id, "load_by_thread", True,
                    {"cache_hit": False}
                )
                
                return checkpoint_data
            
            return None
        except Exception as e:
            logger.error(f"加载checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "load_by_thread", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"加载checkpoint失败: {e}")
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint"""
        operation_id = self.monitor.start_operation("list_by_thread")
        
        try:
            # 确保checkpointer已初始化
            self._ensure_checkpointer_initialized()
            
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
            checkpoint_tuples = self._adapter.list(config)
            
            result = []
            for checkpoint, metadata in checkpoint_tuples:
                workflow_id = metadata.get('workflow_id', 'unknown')
                checkpoint_id = checkpoint.get('id')
                
                # 更新映射关系
                if checkpoint_id:
                    self._update_checkpoint_mapping(thread_id, checkpoint_id)
                
                result.append({
                    'id': checkpoint_id,
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': self._adapter._extract_state_from_checkpoint(checkpoint, metadata),
                    'metadata': metadata,
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                })
            
            # 按创建时间倒序排列
            result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            self.monitor.end_operation(
                operation_id, "list_by_thread", True,
                {"thread_id": thread_id, "count": len(result)}
            )
            
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "list_by_thread", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"列出checkpoint失败: {e}")
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint"""
        operation_id = self.monitor.start_operation("delete_by_thread")
        
        try:
            # 确保checkpointer已初始化
            self._ensure_checkpointer_initialized()
            
            if checkpoint_id:
                # 优化：使用更高效的方式删除单个checkpoint
                checkpoints = await self.list_by_thread(thread_id)
                
                # 找到要保留的checkpoint（除要删除的之外）
                checkpoints_to_keep = []
                for checkpoint in checkpoints:
                    if checkpoint['id'] != checkpoint_id:
                        checkpoint_data = {
                            'thread_id': thread_id,
                            'workflow_id': checkpoint['workflow_id'],
                            'state_data': checkpoint['state_data'],
                            'metadata': checkpoint['metadata']
                        }
                        checkpoints_to_keep.append(checkpoint_data)
                
                # 删除整个会话
                config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
                self._adapter.delete(config)
                
                # 清理映射关系
                self._checkpoint_thread_mapping.pop(checkpoint_id, None)
                
                # 清理缓存
                if self.cache:
                    await self.cache.remove(checkpoint_id)
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                self.monitor.end_operation(
                    operation_id, "delete_by_thread", True,
                    {"thread_id": thread_id, "checkpoint_id": checkpoint_id}
                )
                
                return True
            else:
                # 删除整个会话的所有checkpoint
                config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
                self._adapter.delete(config)
                
                # 清理映射关系
                checkpoints_to_delete = [cp_id for cp_id, cp_thread_id in self._checkpoint_thread_mapping.items() if cp_thread_id == thread_id]
                for cp_id in checkpoints_to_delete:
                    self._checkpoint_thread_mapping.pop(cp_id, None)
                    
                    # 清理缓存
                    if self.cache:
                        await self.cache.remove(cp_id)
                
                self.monitor.end_operation(
                    operation_id, "delete_by_thread", True,
                    {"thread_id": thread_id, "all": True}
                )
                
                return True
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "delete_by_thread", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"删除checkpoint失败: {e}")
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        operation_id = self.monitor.start_operation("cleanup_old_checkpoints")
        
        try:
            checkpoints = await self.list_by_thread(thread_id)
            if len(checkpoints) <= max_count:
                self.monitor.end_operation(
                    operation_id, "cleanup_old_checkpoints", True,
                    {"thread_id": thread_id, "cleaned": 0}
                )
                return 0
            
            # 优化：使用更高效的方式清理
            checkpoints_to_keep = checkpoints[:max_count]
            checkpoints_to_delete = checkpoints[max_count:]
            
            # 获取需要保留的checkpoint数据
            checkpoints_data = []
            for checkpoint in checkpoints_to_keep:
                checkpoint_data = {
                    'thread_id': thread_id,
                    'workflow_id': checkpoint['workflow_id'],
                    'state_data': checkpoint['state_data'],
                    'metadata': checkpoint['metadata']
                }
                checkpoints_data.append(checkpoint_data)
            
            # 删除整个会话
            await self.delete_by_thread(thread_id)
            
            # 清理映射关系
            for checkpoint in checkpoints_to_delete:
                self._checkpoint_thread_mapping.pop(checkpoint['id'], None)
                
                # 清理缓存
                if self.cache:
                    await self.cache.remove(checkpoint['id'])
            
            # 重新保存需要保留的checkpoint
            for checkpoint_data in checkpoints_data:
                await self.save(checkpoint_data)
            
            self.monitor.end_operation(
                operation_id, "cleanup_old_checkpoints", True,
                {"thread_id": thread_id, "cleaned": len(checkpoints_to_delete)}
            )
            
            return len(checkpoints_to_delete)
        except Exception as e:
            logger.error(f"清理旧checkpoint失败: {e}")
            
            self.monitor.end_operation(
                operation_id, "cleanup_old_checkpoints", False,
                {"error": str(e)}
            )
            
            raise CheckpointStorageError(f"清理旧checkpoint失败: {e}")
    
    def clear(self):
        """清除所有checkpoint（仅用于测试）"""
        try:
            # 创建新的InMemorySaver实例来清除所有数据
            self._checkpointer = InMemorySaver()
            self._adapter = MemoryCheckpointAdapter(
                self._checkpointer, 
                self.serializer,
                self.universal_serializer,
                self.cache,
                self.monitor
            )
            self._checkpoint_thread_mapping.clear()
            logger.debug("内存checkpoint存储已清空")
        except Exception as e:
            logger.error(f"清空内存checkpoint存储失败: {e}")
            raise CheckpointStorageError(f"清空内存checkpoint存储失败: {e}")
    
    def get_langgraph_checkpointer(self):
        """获取LangGraph原生的checkpointer"""
        return self._checkpointer