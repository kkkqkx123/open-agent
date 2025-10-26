"""Checkpoint管理器实现

提供checkpoint的创建、保存、恢复和管理功能。
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...domain.checkpoint.interfaces import ICheckpointStore
from ...domain.checkpoint.config import CheckpointConfig
from .interfaces import ICheckpointManager, ICheckpointPolicy

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
    
    def should_save_checkpoint(self, session_id: str, workflow_id: str, 
                              state: Any, context: Dict[str, Any]) -> bool:
        """判断是否应该保存checkpoint
        
        Args:
            session_id: 会话ID
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
            session_key = f"{session_id}_{workflow_id}"
            step_count = self._step_counters.get(session_key, 0) + 1
            self._step_counters[session_key] = step_count
            
            if step_count % self.config.save_interval == 0:
                return True
        
        return False
    
    def get_checkpoint_metadata(self, session_id: str, workflow_id: str,
                               state: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取checkpoint元数据
        
        Args:
            session_id: 会话ID
            workflow_id: 工作流ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: checkpoint元数据
        """
        session_key = f"{session_id}_{workflow_id}"
        step_count = self._step_counters.get(session_key, 0)
        
        return {
            'checkpoint_id': str(uuid.uuid4()),
            'session_id': session_id,
            'workflow_id': workflow_id,
            'step_count': step_count,
            'node_name': context.get('node_name'),
            'trigger_reason': context.get('trigger_reason', 'auto_save'),
            'tags': context.get('tags', []),
            'custom_data': context.get('custom_data', {}),
            'created_at': datetime.now().isoformat()
        }


class CheckpointManager(ICheckpointManager):
    """Checkpoint管理器实现
    
    协调checkpoint的创建、保存和恢复。
    """
    
    def __init__(
        self, 
        checkpoint_store: ICheckpointStore,
        config: CheckpointConfig,
        policy: Optional[ICheckpointPolicy] = None
    ):
        """初始化checkpoint管理器
        
        Args:
            checkpoint_store: checkpoint存储
            config: checkpoint配置
            policy: checkpoint策略，如果为None则使用默认策略
        """
        self.checkpoint_store = checkpoint_store
        self.config = config
        self.policy = policy or DefaultCheckpointPolicy(config)
        
        logger.debug(f"Checkpoint管理器初始化完成，存储类型: {config.storage_type}")
    
    async def create_checkpoint(
        self, 
        session_id: str, 
        workflow_id: str, 
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint
        
        Args:
            session_id: 会话ID
            workflow_id: 工作流ID
            state: 工作流状态
            metadata: 可选的元数据
            
        Returns:
            str: checkpoint ID
        """
        try:
            checkpoint_id = str(uuid.uuid4())
            
            checkpoint_data = {
                'id': checkpoint_id,
                'session_id': session_id,
                'workflow_id': workflow_id,
                'state_data': state,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            success = await self.checkpoint_store.save(checkpoint_data)
            if success:
                logger.debug(f"Checkpoint创建成功: {checkpoint_id}")
                return checkpoint_id
            else:
                raise RuntimeError("创建checkpoint失败")
        except Exception as e:
            logger.error(f"创建checkpoint失败: {e}")
            raise
    
    async def get_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint
        
        Args:
            session_id: 会话ID
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        try:
            # 尝试使用存储的load_by_session方法
            if hasattr(self.checkpoint_store, 'load_by_session'):
                return await self.checkpoint_store.load_by_session(session_id, checkpoint_id)  # type: ignore
            else:
                # 回退到通用load方法
                return await self.checkpoint_store.load(checkpoint_id)
        except Exception as e:
            logger.error(f"获取checkpoint失败: {e}")
            return None
    
    async def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            return await self.checkpoint_store.list_by_session(session_id)
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            return []
    
    async def delete_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            session_id: 会话ID
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 尝试使用存储的delete_by_session方法
            if hasattr(self.checkpoint_store, 'delete_by_session'):
                return await self.checkpoint_store.delete_by_session(session_id, checkpoint_id)  # type: ignore
            else:
                # 回退到通用delete方法
                return await self.checkpoint_store.delete(checkpoint_id)
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            return False
    
    async def get_latest_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        try:
            return await self.checkpoint_store.get_latest(session_id)
        except Exception as e:
            logger.error(f"获取最新checkpoint失败: {e}")
            return None
    
    async def restore_from_checkpoint(
        self, 
        session_id: str, 
        checkpoint_id: str
    ) -> Optional[Any]:
        """从checkpoint恢复状态
        
        Args:
            session_id: 会话ID
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Any]: 恢复的工作流状态，如果失败则返回None
        """
        try:
            checkpoint = await self.get_checkpoint(session_id, checkpoint_id)
            if checkpoint:
                return checkpoint.get('state_data')
            return None
        except Exception as e:
            logger.error(f"从checkpoint恢复状态失败: {e}")
            return None
    
    async def auto_save_checkpoint(
        self, 
        session_id: str, 
        workflow_id: str, 
        state: Any,
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存checkpoint
        
        Args:
            session_id: 会话ID
            workflow_id: 工作流ID
            state: 工作流状态
            trigger_reason: 触发原因
            
        Returns:
            Optional[str]: checkpoint ID，如果保存失败则返回None
        """
        try:
            context = {
                'trigger_reason': trigger_reason,
                'node_name': getattr(state, 'current_step', None),
                'tags': [trigger_reason],
                'custom_data': {}
            }
            
            # 检查是否应该保存checkpoint
            if not self.policy.should_save_checkpoint(session_id, workflow_id, state, context):
                return None
            
            # 获取元数据
            metadata = self.policy.get_checkpoint_metadata(session_id, workflow_id, state, context)
            
            # 创建checkpoint
            checkpoint_id = await self.create_checkpoint(session_id, workflow_id, state, metadata)
            
            # 清理旧checkpoint
            if self.config.max_checkpoints > 0:
                await self.cleanup_checkpoints(session_id, self.config.max_checkpoints)
            
            return checkpoint_id
        except Exception as e:
            logger.error(f"自动保存checkpoint失败: {e}")
            return None
    
    async def cleanup_checkpoints(self, session_id: str, max_count: int) -> int:
        """清理旧的checkpoint
        
        Args:
            session_id: 会话ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        try:
            return await self.checkpoint_store.cleanup_old_checkpoints(session_id, max_count)
        except Exception as e:
            logger.error(f"清理checkpoint失败: {e}")
            return 0
    
    async def get_checkpoints_by_workflow(self, session_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint
        
        Args:
            session_id: 会话ID
            workflow_id: 工作流ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            if hasattr(self.checkpoint_store, 'get_checkpoints_by_workflow'):
                return await self.checkpoint_store.get_checkpoints_by_workflow(session_id, workflow_id)
            else:
                # 过滤所有checkpoint
                all_checkpoints = await self.list_checkpoints(session_id)
                return [cp for cp in all_checkpoints if cp.get('workflow_id') == workflow_id]
        except Exception as e:
            logger.error(f"获取工作流checkpoint失败: {e}")
            return []
    
    async def get_checkpoint_count(self, session_id: str) -> int:
        """获取会话的checkpoint数量
        
        Args:
            session_id: 会话ID
            
        Returns:
            int: checkpoint数量
        """
        try:
            if hasattr(self.checkpoint_store, 'get_checkpoint_count'):
                return await self.checkpoint_store.get_checkpoint_count(session_id)  # type: ignore
            else:
                checkpoints = await self.list_checkpoints(session_id)
                return len(checkpoints)
        except Exception as e:
            logger.error(f"获取checkpoint数量失败: {e}")
            return 0
    
    def get_langgraph_checkpointer(self):
        """获取LangGraph原生的checkpointer
        
        Returns:
            LangGraph原生的checkpointer实例，如果存储支持的话
        """
        if hasattr(self.checkpoint_store, 'get_langgraph_checkpointer'):
            return self.checkpoint_store.get_langgraph_checkpointer()  # type: ignore
        return None