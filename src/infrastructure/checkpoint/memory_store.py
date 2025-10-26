"""基于LangGraph标准的内存checkpoint存储实现

使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from langgraph.checkpoint.memory import InMemorySaver

from ...domain.checkpoint.interfaces import ICheckpointStore, ICheckpointSerializer

logger = logging.getLogger(__name__)


class MemoryCheckpointAdapter:
    """LangGraph内存checkpoint适配器
    
    将LangGraph原生的内存checkpoint存储适配到项目的接口。
    """
    
    def __init__(self, checkpointer: InMemorySaver, serializer: Optional[ICheckpointSerializer] = None):
        """初始化适配器
        
        Args:
            checkpointer: LangGraph原生的checkpointer
            serializer: 状态序列化器
        """
        self.checkpointer = checkpointer
        self.serializer = serializer
    
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
            serialized_state = {"state": state} if hasattr(state, '__dict__') else {"raw": str(state)}
        
        return {
            "v": 4,
            "ts": datetime.now().isoformat(),
            "id": str(uuid.uuid4()),
            "channel_values": {
                "state": serialized_state,
                "workflow_id": workflow_id,
                **metadata
            },
            "channel_versions": {
                "__start__": 2,
                "state": 1,
                "workflow_id": 1
            },
            "versions_seen": {
                "__start__": {"__start__": 1},
                "state": {"__start__": 1}
            }
        }
    
    def _extract_state_from_checkpoint(self, checkpoint: Dict[str, Any]) -> Any:
        """从LangGraph checkpoint提取状态
        
        Args:
            checkpoint: LangGraph checkpoint
            
        Returns:
            Any: 提取的状态
        """
        channel_values = checkpoint.get("channel_values", {})
        state_data = channel_values.get("state")
        
        if self.serializer and state_data:
            return self.serializer.deserialize(state_data)
        
        return state_data
    
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
            self.checkpointer.put(config, checkpoint, metadata, new_versions)  # type: ignore
            return True
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            return False
    
    def get(self, config: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """获取checkpoint
        
        Args:
            config: 配置
            
        Returns:
            Optional[Tuple[Dict[str, Any], Dict[str, Any]]]: checkpoint和元数据
        """
        try:
            result = self.checkpointer.get(config)  # type: ignore
            if result:
                # LangGraph的get方法返回的是字典，我们需要转换为元组格式
                # 将Checkpoint对象转换为字典
                checkpoint_dict = dict(result) if hasattr(result, '__dict__') else result
                return (checkpoint_dict, {})  # type: ignore
            return None
        except Exception as e:
            logger.error(f"获取checkpoint失败: {e}")
            return None
    
    def list(self, config: Dict[str, Any], limit: Optional[int] = None) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """列出checkpoint
        
        Args:
            config: 配置
            limit: 限制数量
            
        Returns:
            List[Tuple[Dict[str, Any], Dict[str, Any]]]: checkpoint列表
        """
        try:
            checkpoint_tuples = list(self.checkpointer.list(config, limit=limit))  # type: ignore
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                # CheckpointTuple有config, checkpoint, metadata等属性
                result.append((checkpoint_tuple.checkpoint, checkpoint_tuple.metadata))
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            return []
    
    def delete(self, config: Dict[str, Any]) -> bool:
        """删除checkpoint
        
        Args:
            config: 配置
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # LangGraph的InMemorySaver使用delete_thread方法，只需要thread_id
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                self.checkpointer.delete_thread(thread_id)  # type: ignore
                return True
            return False
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            return False


class MemoryCheckpointStore(ICheckpointStore):
    """基于LangGraph标准的内存checkpoint存储实现
    
    使用LangGraph原生的InMemorySaver，符合LangGraph最佳实践。
    """
    
    def __init__(self, serializer: Optional[ICheckpointSerializer] = None):
        """初始化内存存储
        
        Args:
            serializer: 状态序列化器
        """
        self.serializer = serializer
        
        # 创建LangGraph原生存储
        self._checkpointer = InMemorySaver()
        self._adapter = MemoryCheckpointAdapter(self._checkpointer, serializer)
        
        logger.debug("内存checkpoint存储初始化完成")
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据
        
        Args:
            checkpoint_data: checkpoint数据字典，包含session_id, workflow_id, state_data, metadata
            
        Returns:
            bool: 是否保存成功
        """
        try:
            session_id = checkpoint_data['session_id']
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 将workflow_id添加到metadata中，因为LangGraph的channel_values在获取时为空
            metadata['workflow_id'] = workflow_id
            
            # 创建LangGraph配置
            config = self._adapter._create_langgraph_config(session_id)
            
            # 创建LangGraph checkpoint
            checkpoint = self._adapter._create_langgraph_checkpoint(state, workflow_id, metadata)
            
            # 保存checkpoint
            return self._adapter.put(config, checkpoint, metadata, {})
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            return False
    
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        # 注意：LangGraph的checkpoint ID需要配合thread_id使用
        # 这里我们需要从checkpoint_id中提取session_id，或者使用其他方式
        # 暂时返回None，需要在实际使用时完善
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
            config = self._adapter._create_langgraph_config(session_id, checkpoint_id)
            
            # 使用list方法获取checkpoint，因为get方法的channel_values为空
            checkpoints = self._adapter.list(config)
            
            if checkpoints:
                # 获取最新的checkpoint（第一个）
                checkpoint, metadata = checkpoints[0]
                
                # 如果指定了checkpoint_id，找到匹配的checkpoint
                if checkpoint_id:
                    for cp, meta in checkpoints:
                        if cp.get('id') == checkpoint_id:
                            checkpoint, metadata = cp, meta
                            break
                
                # 从metadata中获取workflow_id，因为LangGraph的channel_values为空
                # 我们在保存时将workflow_id放在metadata中
                workflow_id = metadata.get('workflow_id')
                
                return {
                    'id': checkpoint.get('id'),
                    'session_id': session_id,
                    'workflow_id': workflow_id,
                    'state_data': self._adapter._extract_state_from_checkpoint(checkpoint),
                    'metadata': metadata,
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                }
            return None
        except Exception as e:
            logger.error(f"加载checkpoint失败: {e}")
            return None
    
    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            config = self._adapter._create_langgraph_config(session_id)
            checkpoints = self._adapter.list(config)
            
            result = []
            for checkpoint, metadata in checkpoints:
                # 从metadata中获取workflow_id
                workflow_id = metadata.get('workflow_id')
                result.append({
                    'id': checkpoint.get('id'),
                    'session_id': session_id,
                    'workflow_id': workflow_id,
                    'state_data': self._adapter._extract_state_from_checkpoint(checkpoint),
                    'metadata': metadata,
                    'created_at': checkpoint.get('ts'),
                    'updated_at': checkpoint.get('ts')
                })
            
            # 按创建时间倒序排列
            result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return result
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            return []
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        # 注意：LangGraph需要thread_id来删除checkpoint
        # 这里需要从checkpoint_id中提取session_id
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
            if checkpoint_id:
                # LangGraph的InMemorySaver不支持删除单个checkpoint
                # 我们通过重新保存除要删除的checkpoint之外的所有checkpoint来模拟
                checkpoints = await self.list_by_session(session_id)
                
                # 找到要保留的checkpoint（除要删除的之外）
                checkpoints_to_keep = []
                for checkpoint in checkpoints:
                    if checkpoint['id'] != checkpoint_id:
                        # 重新构造checkpoint数据
                        checkpoint_data = {
                            'session_id': session_id,
                            'workflow_id': checkpoint['workflow_id'],
                            'state_data': checkpoint['state_data'],
                            'metadata': checkpoint['metadata']
                        }
                        checkpoints_to_keep.append(checkpoint_data)
                
                # 删除整个会话
                await self.delete_by_session(session_id)
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                return True
            else:
                # 删除整个会话的所有checkpoint
                config = self._adapter._create_langgraph_config(session_id)
                return self._adapter.delete(config)
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
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
            
            # 由于LangGraph的InMemorySaver不支持删除单个checkpoint，
            # 我们需要重新实现这个方法
            # 保存需要保留的checkpoint
            checkpoints_to_keep = checkpoints[:max_count]
            
            # 获取需要保留的checkpoint数据
            checkpoints_data = []
            for checkpoint in checkpoints_to_keep:
                # 重新构造checkpoint数据
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
            logger.error(f"清理旧checkpoint失败: {e}")
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
    
    def clear(self):
        """清除所有checkpoint（仅用于测试）"""
        try:
            # 创建新的InMemorySaver实例来清除所有数据
            self._checkpointer = InMemorySaver()
            self._adapter = MemoryCheckpointAdapter(self._checkpointer, self.serializer)
            logger.debug("内存checkpoint存储已清空")
        except Exception as e:
            logger.error(f"清空内存checkpoint存储失败: {e}")
    
    def get_langgraph_checkpointer(self):
        """获取LangGraph原生的checkpointer
        
        Returns:
            LangGraph原生的checkpointer实例
        """
        return self._checkpointer