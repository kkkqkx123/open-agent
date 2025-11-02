"""基于SQLite的checkpoint存储实现

使用LangGraph的SqliteSaver，适合生产环境使用。
"""

import logging
import uuid
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.base import CheckpointTuple, Checkpoint
from langchain_core.runnables.config import RunnableConfig

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ..config.checkpoint_config_service import CheckpointConfigService
from .types import CheckpointError, CheckpointNotFoundError, CheckpointStorageError
from .base_store import BaseCheckpointStore
from .performance import monitor_performance
from typing import Any, Callable

logger = logging.getLogger(__name__)


class SQLiteCheckpointStore(BaseCheckpointStore):
    """基于SQLite的checkpoint存储实现
    
    使用LangGraph的SqliteSaver，支持持久化存储。
    """
    
    def __init__(self, sqlite_path: Optional[str] = None, serializer: Optional[ICheckpointSerializer] = None,
                 config_service: Optional[CheckpointConfigService] = None,
                 max_checkpoints_per_thread: int = 1000,
                 enable_performance_monitoring: bool = True):
        """初始化SQLite存储
        
        Args:
            sqlite_path: SQLite数据库路径（可选，如果未提供则从配置获取）
            serializer: 状态序列化器
            config_service: 配置服务实例
            max_checkpoints_per_thread: 每个线程最大checkpoint数量
            enable_performance_monitoring: 是否启用性能监控
        """
        super().__init__(serializer, max_checkpoints_per_thread, enable_performance_monitoring)
        self.config_service = config_service or CheckpointConfigService()
        
        # 获取数据库路径
        if sqlite_path:
            self.sqlite_path = sqlite_path
        else:
            self.sqlite_path = self.config_service.get_db_path()
        
        # 确保目录存在
        db_dir = os.path.dirname(self.sqlite_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # 保存连接字符串而不是checkpointer实例，因为SqliteSaver.from_conn_string返回的是上下文管理器
        self._conn_string = self.sqlite_path
        
        logger.info(f"SQLite checkpoint存储初始化: {self.sqlite_path}")
    
    def _get_checkpointer(self) -> Any:
        """获取checkpointer实例（在with语句中使用）"""
        return SqliteSaver.from_conn_string(self._conn_string)
    
    def _create_langgraph_config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> RunnableConfig:
        """创建LangGraph标准配置
         
        Args:
            thread_id: 会话ID
            checkpoint_id: 可选的checkpoint ID
             
        Returns:
            RunnableConfig: LangGraph配置
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        return config
    
    def _create_langgraph_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Checkpoint:
        """创建LangGraph标准checkpoint
         
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
             
        Returns:
            Checkpoint: LangGraph checkpoint
        """
        # 序列化状态
        if self.serializer:
            serialized_state = self.serializer.serialize(state)
        else:
            serialized_state = state
         
        checkpoint: Checkpoint = {
            "v": 4,
            "ts": datetime.now().isoformat(),
            "id": str(uuid.uuid4()),
            "channel_values": {
                "state": serialized_state,  # 使用更明确的字段名存储状态
                "workflow_id": workflow_id
            },
            "channel_versions": {
                "state": 1,
                "__start__": 2,
                "workflow_id": 1
            },
            "versions_seen": {
                "state": {"__start__": 1},
                "__start__": {"__start__": 1}
            },
            "updated_channels": []
        }
        return checkpoint
    
    def _extract_state_from_checkpoint(self, checkpoint: Any, metadata: Optional[Any] = None) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            metadata: 可选的元数据，用于获取状态数据
            
        Returns:
            Any: 提取的状态
        """
        if not checkpoint:
            return {}
            
        # 从checkpoint的channel_values获取状态
        try:
            # 如果checkpoint是字典
            if isinstance(checkpoint, dict):
                channel_values = checkpoint.get("channel_values", {})
            # 如果checkpoint是CheckpointTuple，从其checkpoint属性获取
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
        except (AttributeError, TypeError):
            # 如果从channel_values获取失败，返回空字典
            pass
        
        # 如果以上都失败，返回空字典
        return {}
    
    def _extract_metadata_value(self, metadata: Any, key: str, default: Any = None) -> Any:
        """从metadata中提取值
        
        Args:
            metadata: metadata对象
            key: 要提取的键
            default: 默认值
            
        Returns:
            Any: 提取的值
        """
        if not metadata:
            return default
            
        try:
            if hasattr(metadata, 'get'):
                return metadata.get(key, default)
            elif hasattr(metadata, '__getitem__'):
                return metadata[key] if key in metadata else default
            else:
                return default
        except (KeyError, AttributeError, TypeError):
            return default
    
    
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
                return dict(metadata)
            elif hasattr(metadata, '__getitem__'):
                # 尝试转换为字典
                return {k: metadata[k] for k in metadata}
            else:
                # 如果无法转换，返回空字典
                return {}
        except (AttributeError, TypeError):
            return {}
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据
        
        Args:
            checkpoint_data: checkpoint数据字典，包含thread_id, workflow_id, state_data, metadata
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 检查checkpoint数量限制
            thread_id = checkpoint_data['thread_id']
            current_count = await self.get_checkpoint_count(thread_id)
            if current_count >= self.max_checkpoints_per_thread:
                logger.warning(f"线程 {thread_id} 的checkpoint数量已达到最大限制 {self.max_checkpoints_per_thread}")
                # 清理旧的checkpoint
                await self.cleanup_old_checkpoints(thread_id, self.max_checkpoints_per_thread - 1)
            
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 添加必要的元数据字段
            metadata['workflow_id'] = workflow_id
            metadata['state_data'] = state
            
            # 创建LangGraph配置
            config = self._create_langgraph_config(thread_id)
            
            # 创建LangGraph checkpoint
            checkpoint = self._create_langgraph_checkpoint(state, workflow_id, metadata)
            
            # 使用上下文管理器保存checkpoint
            with self._get_checkpointer() as checkpointer:
                # 使用LangGraph的格式来保存
                checkpointer.put(config, checkpoint, metadata, {})
            
            logger.debug(f"成功保存SQLite checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
            return True
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"保存SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"保存SQLite checkpoint失败: {e}")
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据
        """
        try:
            config = self._create_langgraph_config(thread_id, checkpoint_id)
            
            # 使用上下文管理器获取checkpoint
            with self._get_checkpointer() as checkpointer:
                result = checkpointer.get(config)
            
            if result:
                # 检查result是字典还是CheckpointTuple
                if isinstance(result, CheckpointTuple):
                    checkpoint = result.checkpoint
                    metadata = result.metadata
                else:
                    # 如果是字典格式
                    checkpoint = result
                    # 尝试从list方法获取metadata
                    try:
                        config = self._create_langgraph_config(thread_id)
                        with self._get_checkpointer() as checkpointer:
                            list_results = list(checkpointer.list(config))
                        for checkpoint_tuple in list_results:
                            if hasattr(checkpoint_tuple, 'checkpoint') and hasattr(checkpoint_tuple, 'metadata'):
                                # 找到匹配的checkpoint，返回其metadata
                                if checkpoint_tuple.checkpoint.get('id') == checkpoint.get('id'):
                                    metadata = checkpoint_tuple.metadata
                                    break
                        else:
                            metadata = {}
                    except Exception:
                        metadata = {}
                
                # 从metadata中获取workflow_id
                workflow_id = self._extract_metadata_value(metadata, 'workflow_id', 'unknown')
                
                # 标准化metadata为字典格式
                normalized_metadata = self._normalize_metadata(metadata)
                
                return {
                    'id': checkpoint.get('id'),
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': self._extract_state_from_checkpoint(checkpoint, metadata),
                    'metadata': normalized_metadata,
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                }
            return None
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"加载SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"加载SQLite checkpoint失败: {e}")
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint list, sorted by creation time in descending order
        """
        try:
            config = self._create_langgraph_config(thread_id)
            
            # 使用上下文管理器列出checkpoint
            with self._get_checkpointer() as checkpointer:
                checkpoint_tuples = list(checkpointer.list(config))
            
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                # CheckpointTuple有config, checkpoint, metadata等属性
                if isinstance(checkpoint_tuple, CheckpointTuple):
                    checkpoint = checkpoint_tuple.checkpoint
                    metadata = checkpoint_tuple.metadata
                    
                    workflow_id = self._extract_metadata_value(metadata, 'workflow_id', 'unknown')
                    normalized_metadata = self._normalize_metadata(metadata)
                    
                    result.append({
                        'id': checkpoint.get('id'),
                        'thread_id': thread_id,
                        'workflow_id': workflow_id,
                        'state_data': self._extract_state_from_checkpoint(checkpoint, metadata),
                        'metadata': normalized_metadata,
                        'created_at': checkpoint.get('ts'),
                        'updated_at': checkpoint.get('ts')
                    })
            
            # 按创建时间倒序排列
            result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return result
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"列出SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"列出SQLite checkpoint失败: {e}")
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: Optional checkpoint ID, if None, delete all
            
        Returns:
            bool: Whether deletion was successful
        """
        try:
            if checkpoint_id:
                # SQLiteSaver不支持删除单个checkpoint
                # 我们通过重新保存除要删除的checkpoint之外的所有checkpoint来模拟
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
                config = self._create_langgraph_config(thread_id)
                with self._get_checkpointer() as checkpointer:
                    checkpointer.delete_thread(thread_id)
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                return True
            else:
                # 删除整个会话的所有checkpoint
                config = self._create_langgraph_config(thread_id)
                with self._get_checkpointer() as checkpointer:
                    checkpointer.delete_thread(thread_id)
                return True
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"删除SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"删除SQLite checkpoint失败: {e}")
    
    
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """Clean up old checkpoints, keeping the latest max_count
        
        Args:
            thread_id: thread ID
            max_count: Maximum number to keep
            
        Returns:
            int: Number of deleted checkpoints
        """
        try:
            checkpoints = await self.list_by_thread(thread_id)
            if len(checkpoints) <= max_count:
                return 0
            
            # 保存需要保留的checkpoint
            checkpoints_to_keep = checkpoints[:max_count]
            
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
            
            # 重新保存需要保留的checkpoint
            for checkpoint_data in checkpoints_data:
                await self.save(checkpoint_data)
            
            return len(checkpoints) - max_count
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"清理旧SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"清理旧SQLite checkpoint失败: {e}")
    
    
    
    def clear(self) -> None:
        """清除所有checkpoint（仅用于测试）"""
        try:
            # 由于SQLiteSaver没有直接的清除方法，我们可以通过删除数据库文件来实现
            import os
            if os.path.exists(self.sqlite_path):
                os.remove(self.sqlite_path)
                # 重新创建数据库
                db_dir = os.path.dirname(self.sqlite_path)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
            logger.debug("SQLite checkpoint存储已清空")
        except Exception as e:
            logger.error(f"清空SQLite checkpoint存储失败: {e}")
            raise CheckpointStorageError(f"清空SQLite checkpoint存储失败: {e}")
    
    def get_langgraph_checkpointer(self) -> Any:
        """获取LangGraph原生的checkpointer
        
        Returns:
            LangGraph原生的checkpointer实例
        """
        return self._get_checkpointer()
    
    