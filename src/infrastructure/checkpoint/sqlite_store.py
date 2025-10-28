"""基于SQLite的checkpoint存储实现

使用LangGraph的SqliteSaver，适合生产环境使用。
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.checkpoint.sqlite import SqliteSaver

from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointSerializer

logger = logging.getLogger(__name__)


class SQLiteCheckpointStore(ICheckpointStore):
    """基于SQLite的checkpoint存储实现
    
    使用LangGraph的SqliteSaver，支持持久化存储。
    """
    
    def __init__(self, sqlite_path: str = "checkpoints.db", serializer: Optional[ICheckpointSerializer] = None):
        """初始化SQLite存储
        
        Args:
            sqlite_path: SQLite数据库路径
            serializer: 状态序列化器
        """
        self.sqlite_path = sqlite_path
        self.serializer = serializer
        self._checkpointer = None
        
        logger.info(f"SQLite checkpoint存储初始化: {sqlite_path}")
    
    def _ensure_checkpointer_initialized(self):
        """确保checkpointer已初始化"""
        if self._checkpointer is None:
            try:
                self._checkpointer = SqliteSaver.from_conn_string(self.sqlite_path)
                logger.info(f"SQLite checkpointer已初始化: {self.sqlite_path}")
            except Exception as e:
                logger.error(f"SQLite checkpointer初始化失败: {e}")
                raise
    
    def _create_langgraph_config(self, session_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """创建LangGraph标准配置
        
        Args:
            session_id: 会话ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Dict[str, Any]: LangGraph配置
        """
        config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        return config
    
    def _create_langgraph_checkpoint(self, state: Any, workflow_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """创建LangGraph标准checkpoint
        
        Args:
            state: 工作流状态
            workflow_id: 工作流ID
            metadata: 元数据
            
        Returns:
            Dict[str, Any]: LangGraph checkpoint
        """
        # 序列化状态
        if self.serializer:
            serialized_state = self.serializer.serialize(state)
        else:
            serialized_state = state
        
        return {
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
            }
        }
    
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
            
        # 首先尝试从metadata中获取state_data
        if metadata and 'state_data' in metadata:
            state_data = metadata['state_data']
            if self.serializer:
                return self.serializer.deserialize(state_data) if state_data else {}
            return state_data
            
        channel_values = checkpoint.get("channel_values", {})
        
        # 从__root__通道获取状态
        state_data = channel_values.get("__root__")
        if state_data is not None:
            if self.serializer:
                return self.serializer.deserialize(state_data) if state_data else {}
            return state_data
        
        # 如果以上都失败，返回空字典
        return {}
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据
        
        Args:
            checkpoint_data: checkpoint数据字典，包含session_id, workflow_id, state_data, metadata
            
        Returns:
            bool: 是否保存成功
        """
        try:
            self._ensure_checkpointer_initialized()
            
            session_id = checkpoint_data['session_id']
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 将workflow_id和state_data添加到metadata中
            metadata['workflow_id'] = workflow_id
            metadata['state_data'] = state
            
            # 创建LangGraph配置
            config = self._create_langgraph_config(session_id)
            
            # 创建LangGraph checkpoint
            checkpoint = self._create_langgraph_checkpoint(state, workflow_id, metadata)
            
            # 使用上下文管理器保存checkpoint
            with self._checkpointer as checkpointer:
                checkpointer.put(config, checkpoint, metadata, {})
            
            logger.debug(f"成功保存SQLite checkpoint，session_id: {session_id}, workflow_id: {workflow_id}")
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
        logger.warning("load方法需要配合session_id使用，建议使用load_by_session方法")
        return None
    
    async def load_by_session(self, session_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据会话ID加载checkpoint
        
        Args:
            session_id: 会话ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据
        """
        try:
            self._ensure_checkpointer_initialized()
            
            config = self._create_langgraph_config(session_id, checkpoint_id)
            
            # 使用上下文管理器获取checkpoint
            with self._checkpointer as checkpointer:
                result = checkpointer.get(config)
            
            if result:
                # LangGraph的get方法返回的是Checkpoint对象或字典
                if hasattr(result, '__dict__'):
                    checkpoint = dict(result)
                else:
                    checkpoint = result
                
                # 从metadata中获取workflow_id
                workflow_id = 'unknown'  # 默认值
                
                return {
                    'id': checkpoint.get('id'),
                    'session_id': session_id,
                    'workflow_id': workflow_id,
                    'state_data': self._extract_state_from_checkpoint(checkpoint),
                    'metadata': {},
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                }
            return None
        except Exception as e:
            logger.error(f"加载SQLite checkpoint失败: {e}")
            return None
    
    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            self._ensure_checkpointer_initialized()
            
            config = self._create_langgraph_config(session_id)
            
            # 使用上下文管理器列出checkpoint
            with self._checkpointer as checkpointer:
                checkpoint_tuples = list(checkpointer.list(config))
            
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                # CheckpointTuple有config, checkpoint, metadata等属性
                if hasattr(checkpoint_tuple, 'checkpoint'):
                    checkpoint = dict(checkpoint_tuple.checkpoint) if hasattr(checkpoint_tuple.checkpoint, '__dict__') else checkpoint_tuple.checkpoint
                    metadata = dict(checkpoint_tuple.metadata) if hasattr(checkpoint_tuple.metadata, '__dict__') else checkpoint_tuple.metadata
                    
                    workflow_id = metadata.get('workflow_id', 'unknown')
                    result.append({
                        'id': checkpoint.get('id'),
                        'session_id': session_id,
                        'workflow_id': workflow_id,
                        'state_data': self._extract_state_from_checkpoint(checkpoint, metadata),
                        'metadata': metadata,
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
        logger.warning("delete方法需要配合session_id使用，建议使用delete_by_session方法")
        return False
    
    async def delete_by_session(self, session_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据会话ID删除checkpoint
        
        Args:
            session_id: 会话ID
            checkpoint_id: 可选的checkpoint ID，如果为None则删除所有
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self._ensure_checkpointer_initialized()
            
            if checkpoint_id:
                # SQLiteSaver不支持删除单个checkpoint
                # 我们通过重新保存除要删除的checkpoint之外的所有checkpoint来模拟
                checkpoints = await self.list_by_session(session_id)
                
                # 找到要保留的checkpoint（除要删除的之外）
                checkpoints_to_keep = []
                for checkpoint in checkpoints:
                    if checkpoint['id'] != checkpoint_id:
                        checkpoint_data = {
                            'session_id': session_id,
                            'workflow_id': checkpoint['workflow_id'],
                            'state_data': checkpoint['state_data'],
                            'metadata': checkpoint['metadata']
                        }
                        checkpoints_to_keep.append(checkpoint_data)
                
                # 删除整个会话
                config = self._create_langgraph_config(session_id)
                with self._checkpointer as checkpointer:
                    checkpointer.delete_thread(session_id)
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                return True
            else:
                # 删除整个会话的所有checkpoint
                config = self._create_langgraph_config(session_id)
                with self._checkpointer as checkpointer:
                    checkpointer.delete_thread(session_id)
                return True
        except Exception as e:
            logger.error(f"删除SQLite checkpoint失败: {e}")
            return False
    
    async def get_latest(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        checkpoints = await self.list_by_session(session_id)
        return checkpoints[0] if checkpoints else None
    
    async def cleanup_old_checkpoints(self, session_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个
        
        Args:
            session_id: 会话ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        try:
            checkpoints = await self.list_by_session(session_id)
            if len(checkpoints) <= max_count:
                return 0
            
            # 保存需要保留的checkpoint
            checkpoints_to_keep = checkpoints[:max_count]
            
            # 获取需要保留的checkpoint数据
            checkpoints_data = []
            for checkpoint in checkpoints_to_keep:
                checkpoint_data = {
                    'session_id': session_id,
                    'workflow_id': checkpoint['workflow_id'],
                    'state_data': checkpoint['state_data'],
                    'metadata': checkpoint['metadata']
                }
                checkpoints_data.append(checkpoint_data)
            
            # 删除整个会话
            await self.delete_by_session(session_id)
            
            # 重新保存需要保留的checkpoint
            for checkpoint_data in checkpoints_data:
                await self.save(checkpoint_data)
            
            return len(checkpoints) - max_count
        except Exception as e:
            logger.error(f"清理旧SQLite checkpoint失败: {e}")
            return 0
    
    async def get_checkpoints_by_workflow(self, session_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint
        
        Args:
            session_id: 会话ID
            workflow_id: 工作流ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        checkpoints = await self.list_by_session(session_id)
        return [cp for cp in checkpoints if cp.get('workflow_id') == workflow_id]
    
    async def get_checkpoint_count(self, session_id: str) -> int:
        """获取会话的checkpoint数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            int: checkpoint数量
        """
        checkpoints = await self.list_by_session(session_id)
        return len(checkpoints)