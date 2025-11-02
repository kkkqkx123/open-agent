"""基于LangGraph标准的内存checkpoint存储实现

使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
支持生产环境下的SQLite数据库存储选项。
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Tuple, Union, cast
from datetime import datetime

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import CheckpointTuple

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from .types import CheckpointError, CheckpointNotFoundError, CheckpointStorageError
from .performance import monitor_performance

logger = logging.getLogger(__name__)


from .base_store import BaseCheckpointStore


class MemoryCheckpointAdapter:
    """LangGraph内存checkpoint适配器
    
    将LangGraph原生的内存checkpoint存储适配到项目的接口。
    仅支持InMemorySaver。
    """
    
    def __init__(self, checkpointer: Any, serializer: Optional[ICheckpointSerializer] = None):
        """初始化适配器
        
        Args:
            checkpointer: LangGraph原生的checkpointer (InMemorySaver)
            serializer: 状态序列化器
        """
        self.checkpointer = checkpointer
        self.serializer = serializer
        
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
        # 序列化状态
        if self.serializer:
            try:
                serialized_state = self.serializer.serialize(state)
            except Exception as e:
                logger.error(f"状态序列化失败: {e}")
                raise CheckpointStorageError(f"状态序列化失败: {e}")
        else:
            serialized_state = state
        
        # 优化：直接在channel_values中存储状态，避免在metadata中重复存储
        channel_values = {
            "state": serialized_state,  # 使用更明确的字段名存储状态
            "workflow_id": workflow_id
        }
        
        # 优化：metadata中只存储必要的元数据，不重复存储状态数据
        enhanced_metadata = metadata.copy()
        enhanced_metadata['workflow_id'] = workflow_id
        
        return {
            "v": 4,
            "ts": datetime.now().isoformat(),
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
                if self.serializer:
                    return self.serializer.deserialize(state_data) if state_data else {}
                return state_data
            
            # 如果以上都失败，返回空字典
            return {}
        except Exception as e:
            logger.error(f"提取状态失败: {e}")
            return {}
    
    def _normalize_metadata(self, metadata: Any) -> Dict[str, Any]:
        """标准化metadata为字典格式
        
        Args:
            metadata: 原始metadata对象
            
        Returns:
            Dict[str, Any]: 标准化的metadata字典
        """
        if not metadata:
            return {}
            
        try:
            if isinstance(metadata, dict):
                return dict(metadata)
            elif hasattr(metadata, '__dict__'):
                return dict(metadata.__dict__)
            elif hasattr(metadata, '__getitem__'):
                # 尝试转换为字典
                return {k: metadata[k] for k in metadata}
            else:
                # 如果无法转换，返回空字典
                return {}
        except Exception as e:
            logger.error(f"标准化metadata失败: {e}")
            return {}
    
    @monitor_performance("adapter.put")
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any],
            metadata: Dict[str, Any], new_versions: Dict[str, Any]) -> bool:
        """保存checkpoint
        
        Args:
            config: 配置
            checkpoint: checkpoint数据
            metadata: 元数据
            new_versions: 新版本信息
            
        Returns:
            bool: 是否保存成功
        """
        try:
            logger.debug(f"保存checkpoint，thread_id: {config.get('configurable', {}).get('thread_id')}")
            self.checkpointer.put(config, checkpoint, metadata, new_versions)
            return True
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            raise CheckpointStorageError(f"保存checkpoint失败: {e}")
    
    @monitor_performance("adapter.get")
    def get(self, config: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """获取checkpoint
        
        Args:
            config: 配置
            
        Returns:
            Optional[Tuple[Dict[str, Any], Dict[str, Any]]]: checkpoint和元数据
        """
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
                        metadata = self._normalize_metadata(result.metadata)
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
                                        metadata = self._normalize_metadata(checkpoint_tuple.metadata)
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
            return None
        except Exception as e:
            logger.error(f"获取checkpoint失败: {e}")
            raise CheckpointNotFoundError(f"获取checkpoint失败: {e}")
    
    @monitor_performance("adapter.list")
    def list(self, config: Dict[str, Any], limit: Optional[int] = None) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """列出checkpoint
        
        Args:
            config: 配置
            limit: 限制数量
            
        Returns:
            List[Tuple[Dict[str, Any], Dict[str, Any]]]: checkpoint列表
        """
        try:
            checkpoint_tuples = list(self.checkpointer.list(config, limit=limit))
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                # CheckpointTuple有config, checkpoint, metadata等属性
                if hasattr(checkpoint_tuple, 'checkpoint'):
                    checkpoint = dict(checkpoint_tuple.checkpoint) if hasattr(checkpoint_tuple.checkpoint, '__dict__') else checkpoint_tuple.checkpoint
                    metadata = self._normalize_metadata(checkpoint_tuple.metadata)
                    result.append((checkpoint, metadata))
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}")
    
    @monitor_performance("adapter.delete")
    def delete(self, config: Dict[str, Any]) -> bool:
        """删除checkpoint
        
        Args:
            config: 配置
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # LangGraph的InMemorySaver使用delete_thread方法
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                if hasattr(self.checkpointer, 'delete_thread'):
                    self.checkpointer.delete_thread(thread_id)
                    return True
                else:
                    # 对于数据库存储，可能需要其他删除方式
                    logger.warning(f"当前checkpointer不支持delete_thread方法: {type(self.checkpointer)}")
            return False
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            raise CheckpointStorageError(f"删除checkpoint失败: {e}")


class MemoryCheckpointStore(BaseCheckpointStore):
    """基于LangGraph标准的内存checkpoint存储实现
    
    使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
    仅支持内存存储。
    """
    
    def __init__(self,
                 serializer: Optional[ICheckpointSerializer] = None,
                 max_checkpoints_per_thread: int = 1000,
                 enable_performance_monitoring: bool = True):
        """初始化内存存储
        
        Args:
            serializer: 状态序列化器
            max_checkpoints_per_thread: 每个线程最大checkpoint数量
            enable_performance_monitoring: 是否启用性能监控
        """
        super().__init__(serializer, max_checkpoints_per_thread, enable_performance_monitoring)
        
        # 使用内存存储，适合开发和测试环境
        self._checkpointer = InMemorySaver()
        logger.info("使用内存存储")
        
        self._adapter = MemoryCheckpointAdapter(self._checkpointer, serializer)
        
        # 内部checkpoint_id到thread_id的映射，用于支持load和delete方法
        self._checkpoint_thread_mapping: Dict[str, str] = {}
        
        logger.debug("checkpoint存储初始化完成")
    
    def _ensure_checkpointer_initialized(self):
        """确保checkpointer已初始化"""
        # 内存存储不需要额外初始化
        pass
    
    def _update_checkpoint_mapping(self, thread_id: str, checkpoint_id: str):
        """更新checkpoint到thread的映射
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
        """
        self._checkpoint_thread_mapping[checkpoint_id] = thread_id
    
    def _get_thread_id_from_checkpoint(self, checkpoint_id: str) -> Optional[str]:
        """从checkpoint ID获取thread ID
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[str]: thread ID，如果不存在则返回None
        """
        return self._checkpoint_thread_mapping.get(checkpoint_id)
    
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
    
    def _create_langgraph_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Any:
        """创建LangGraph标准checkpoint
        
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
            
        Returns:
            LangGraph checkpoint对象
        """
        # 直接使用adapter中的实现
        checkpoint, _ = self._adapter._create_langgraph_checkpoint(state, workflow_id, metadata)
        return checkpoint
    
    def _extract_state_from_checkpoint(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            metadata: 可选的元数据
            
        Returns:
            提取的状态对象
        """
        # 直接使用adapter中的实现
        return self._adapter._extract_state_from_checkpoint(checkpoint, metadata)
    
    def _normalize_metadata(self, metadata: Any) -> Dict[str, Any]:
        """标准化metadata为字典格式
        
        Args:
            metadata: 原始metadata对象
            
        Returns:
            标准化的metadata字典
        """
        # 直接使用adapter中的实现
        return self._adapter._normalize_metadata(metadata)
    
    @monitor_performance("store.save")
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据
        
        Args:
            checkpoint_data: checkpoint数据字典，包含thread_id, workflow_id, state_data, metadata
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保checkpointer已初始化
            self._ensure_checkpointer_initialized()
            
            thread_id = checkpoint_data.get('thread_id')
            if not thread_id:
                raise ValueError("checkpoint_data必须包含'thread_id'")
                
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 检查checkpoint数量限制
            current_count = await self.get_checkpoint_count(thread_id)
            if current_count >= self.max_checkpoints_per_thread:
                logger.warning(f"线程 {thread_id} 的checkpoint数量已达到最大限制 {self.max_checkpoints_per_thread}")
                # 清理旧的checkpoint
                await self.cleanup_old_checkpoints(thread_id, self.max_checkpoints_per_thread - 1)
            
            # 将workflow_id添加到metadata中
            metadata['workflow_id'] = workflow_id
            
            # 创建LangGraph配置（包含checkpoint_ns字段）
            config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
            
            # 创建LangGraph checkpoint
            checkpoint, enhanced_metadata = self._adapter._create_langgraph_checkpoint(state, workflow_id, metadata)
            
            # 更新映射关系
            self._update_checkpoint_mapping(thread_id, checkpoint['id'])
            
            # 保存checkpoint
            success = self._adapter.put(config, checkpoint, enhanced_metadata, {})
            if success:
                logger.debug(f"成功保存checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
            return success
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            raise CheckpointStorageError(f"保存checkpoint失败: {e}")
    
    @monitor_performance("store.load_by_thread")
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据
        """
        try:
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
                
                return {
                    'id': checkpoint.get('id'),
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': self._adapter._extract_state_from_checkpoint(checkpoint, metadata),
                    'metadata': metadata,
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                }
            return None
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"加载checkpoint失败: {e}")
            raise CheckpointStorageError(f"加载checkpoint失败: {e}")
    
    @monitor_performance("store.list_by_thread")
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
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
            return result
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}")
    
    @monitor_performance("store.delete_by_thread")
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID，如果为None则删除所有
            
        Returns:
            bool: 是否删除成功
        """
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
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                return True
            else:
                # 删除整个会话的所有checkpoint
                config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
                self._adapter.delete(config)
                
                # 清理映射关系
                checkpoints_to_delete = [cp_id for cp_id, cp_thread_id in self._checkpoint_thread_mapping.items() if cp_thread_id == thread_id]
                for cp_id in checkpoints_to_delete:
                    self._checkpoint_thread_mapping.pop(cp_id, None)
                
                return True
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            raise CheckpointStorageError(f"删除checkpoint失败: {e}")
    
    
    @monitor_performance("store.cleanup_old_checkpoints")
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个
        
        Args:
            thread_id: thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        try:
            checkpoints = await self.list_by_thread(thread_id)
            if len(checkpoints) <= max_count:
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
            
            # 重新保存需要保留的checkpoint
            for checkpoint_data in checkpoints_data:
                await self.save(checkpoint_data)
            
            return len(checkpoints_to_delete)
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"清理旧checkpoint失败: {e}")
            raise CheckpointStorageError(f"清理旧checkpoint失败: {e}")
    
    
    
    def clear(self):
        """清除所有checkpoint（仅用于测试）"""
        try:
            # 创建新的InMemorySaver实例来清除所有数据
            self._checkpointer = InMemorySaver()
            self._adapter = MemoryCheckpointAdapter(self._checkpointer, self.serializer)
            self._checkpoint_thread_mapping.clear()
            logger.debug("内存checkpoint存储已清空")
        except Exception as e:
            logger.error(f"清空内存checkpoint存储失败: {e}")
            raise CheckpointStorageError(f"清空内存checkpoint存储失败: {e}")
    
    def get_langgraph_checkpointer(self):
        """获取LangGraph原生的checkpointer
        
        Returns:
            LangGraph原生的checkpointer实例
        """
        return self._checkpointer
    
    