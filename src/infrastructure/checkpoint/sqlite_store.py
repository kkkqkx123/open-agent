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

from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointSerializer
from ..config.checkpoint_config_service import CheckpointConfigService

logger = logging.getLogger(__name__)


class SQLiteCheckpointStore(ICheckpointStore):
    """基于SQLite的checkpoint存储实现
    
    使用LangGraph的SqliteSaver，支持持久化存储。
    """
    
    def __init__(self, sqlite_path: Optional[str] = None, serializer: Optional[ICheckpointSerializer] = None,
                 config_service: Optional[CheckpointConfigService] = None):
        """初始化SQLite存储
        
        Args:
            sqlite_path: SQLite数据库路径（可选，如果未提供则从配置获取）
            serializer: 状态序列化器
            config_service: 配置服务实例
        """
        self.serializer = serializer
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
    
    def _get_checkpointer(self):
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
                "__root__": serialized_state,
                "workflow_id": workflow_id
            },
            "channel_versions": {
                "__root__": 1,
                "__start__": 2,
                "workflow_id": 1
            },
            "versions_seen": {
                "__root__": {"__start__": 1},
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
            
        # 首先尝试从metadata中获取state_data（这是主要的提取方式）
        if metadata:
            try:
                # 处理不同类型的metadata对象
                if hasattr(metadata, 'get'):
                    # 字典或类似字典的对象
                    state_data = metadata.get('state_data')
                elif hasattr(metadata, '__getitem__'):
                    # 支持索引访问的对象
                    state_data = metadata['state_data'] if 'state_data' in metadata else None
                else:
                    state_data = None
                
                if state_data is not None:
                    if self.serializer:
                        return self.serializer.deserialize(state_data) if state_data else {}
                    return state_data
            except (KeyError, AttributeError, TypeError):
                # 如果从metadata获取失败，继续尝试其他方式
                pass
            
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
            
            state_data = channel_values.get("__root__")
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
            thread_id = checkpoint_data['thread_id']
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 将workflow_id和state_data添加到metadata中
            metadata['workflow_id'] = workflow_id
            metadata['state_data'] = state
            
            # 创建LangGraph配置
            config = self._create_langgraph_config(thread_id)
            
            # 创建LangGraph checkpoint
            checkpoint = self._create_langgraph_checkpoint(state, workflow_id, metadata)
            
            # 使用上下文管理器保存checkpoint
            with self._get_checkpointer() as checkpointer:
                # 使用LangGraph的格式来保存
                checkpointer.put(config, checkpoint, metadata, {})  # type: ignore
            
            logger.debug(f"成功保存SQLite checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"保存SQLite checkpoint失败: {e}")
            return False
    
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        logger.warning("load方法需要配合thread_id使用，建议使用load_by_session方法")
        return None
    
    async def load_by_session(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据会话ID加载checkpoint
        
        Args:
            thread_id: 会话ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据
        """
        return await self.load_by_thread(thread_id, checkpoint_id)
    
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
                result = checkpointer.get(config)  # type: ignore
            
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
                            list_results = list(checkpointer.list(config))  # type: ignore
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
        except Exception as e:
            logger.error(f"加载SQLite checkpoint失败: {e}")
            return None
    
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
                checkpoint_tuples = list(checkpointer.list(config))  # type: ignore
            
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
        except Exception as e:
            logger.error(f"列出SQLite checkpoint失败: {e}")
            return []
    
    async def list_by_session(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint
        
        Args:
            thread_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            config = self._create_langgraph_config(thread_id)
            
            # 使用上下文管理器列出checkpoint
            with self._get_checkpointer() as checkpointer:
                checkpoint_tuples = list(checkpointer.list(config))  # type: ignore
            
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
        except Exception as e:
            logger.error(f"列出SQLite checkpoint失败: {e}")
            return []
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        # Since we need thread_id to delete a specific checkpoint,
        # we can't implement this method properly without it.
        # This is a limitation of the LangGraph checkpoint system.
        logger.warning("delete方法需要配合thread_id使用，建议使用delete_by_thread方法")
        return False
    
    async def delete_by_session(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据会话ID删除checkpoint
        
        Args:
            thread_id: 会话ID
            checkpoint_id: 可选的checkpoint ID，如果为None则删除所有
            
        Returns:
            bool: 是否删除成功
        """
        return await self.delete_by_thread(thread_id, checkpoint_id)
    
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
                checkpoints = await self.list_by_session(thread_id)
                
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
        except Exception as e:
            logger.error(f"删除SQLite checkpoint失败: {e}")
            return False
    
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest checkpoint for a thread
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: Latest checkpoint data, or None if not found
        """

        checkpoints = await self.list_by_thread(thread_id)
        return checkpoints[0] if checkpoints else None
    
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
        except Exception as e:
            logger.error(f"清理旧SQLite checkpoint失败: {e}")
            return 0
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all checkpoints for a specified workflow
        
        Args:
            thread_id: thread ID
            workflow_id: Workflow ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint list, sorted by creation time in descending order
        """

        checkpoints = await self.list_by_thread(thread_id)
        return [cp for cp in checkpoints if cp.get('workflow_id') == workflow_id]
    
    async def get_checkpoint_count(self, thread_id: str) -> int:
        """Get the number of checkpoints for a thread
        
        Args:
            thread_id: thread ID
            
        Returns:
            int: Number of checkpoints
        """

        checkpoints = await self.list_by_thread(thread_id)
        return len(checkpoints)