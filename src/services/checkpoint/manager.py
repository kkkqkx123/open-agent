"""Checkpoint管理器服务

实现ICheckpointManager接口，负责checkpoint的创建、保存、恢复和管理。
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.interfaces.checkpoint import ICheckpointManager
from src.interfaces.repository import ICheckpointRepository
from src.core.common.exceptions import (
    CheckpointNotFoundError,
    CheckpointStorageError,
    CheckpointValidationError
)
from src.core.common.serialization import Serializer
from .config_service import CheckpointConfigService
from src.core.config.models.checkpoint_config import CheckpointConfig as CoreCheckpointConfig


logger = logging.getLogger(__name__)


class CheckpointManager(ICheckpointManager):
    """Checkpoint管理器实现
    
    提供checkpoint的完整生命周期管理功能。
    """
    
    def __init__(self,
                 checkpoint_repository: ICheckpointRepository,
                 config_service: Optional[CheckpointConfigService] = None):
        """初始化checkpoint管理器
        
        Args:
            checkpoint_repository: checkpoint Repository
            config_service: 配置服务实例
        """
        self._checkpoint_repository = checkpoint_repository
        self.config_service = config_service or CheckpointConfigService()
        self.core_config: CoreCheckpointConfig = self.config_service.get_config()
        self.serializer = Serializer()
        
        # 从配置中获取参数
        self.max_checkpoints_per_thread = self.core_config.max_checkpoints
        self.enable_compression = self.core_config.compression
        self.enable_performance_monitoring = self.core_config.enabled
        self.cleanup_threshold = self.core_config.retention_days
    
    async def create_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            metadata: 可选的元数据
            
        Returns:
            str: checkpoint ID
        """
        try:
            if not thread_id:
                raise CheckpointValidationError("thread_id不能为空")
            
            if not workflow_id:
                raise CheckpointValidationError("workflow_id不能为空")
            
            # 生成checkpoint ID
            checkpoint_id = str(uuid.uuid4())
            
            # 序列化状态
            serialized_state = self.serializer.serialize(state, format=self.serializer.FORMAT_JSON)
            
            # 准备checkpoint数据字典
            checkpoint_data_dict = {
                "id": checkpoint_id,
                "thread_id": thread_id,
                "session_id": "",  # 暂时为空，可从上下文获取
                "workflow_id": workflow_id,
                "state_data": serialized_state,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 保存到Repository
            checkpoint_id = await self._checkpoint_repository.save_checkpoint(checkpoint_data_dict)
            
            logger.info(f"Created checkpoint: {checkpoint_id} for thread: {thread_id}, workflow: {workflow_id}")
            
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise CheckpointStorageError(f"创建checkpoint失败: {e}") from e
    
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        try:
            # 从Repository获取checkpoint数据
            checkpoint_data = await self._checkpoint_repository.load_checkpoint(checkpoint_id)
            
            if not checkpoint_data:
                logger.info(f"Checkpoint not found: {checkpoint_id} for thread: {thread_id}")
                return None
                
            logger.info(f"Getting checkpoint: {checkpoint_id} for thread: {thread_id}")
            return checkpoint_data
            
        except CheckpointNotFoundError:
            logger.info(f"Checkpoint not found: {checkpoint_id} for thread: {thread_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
            raise CheckpointStorageError(f"获取checkpoint失败: {e}") from e
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        try:
            # 从Repository获取checkpoint列表
            checkpoints = await self._checkpoint_repository.list_checkpoints(thread_id)
            
            logger.info(f"Listing checkpoints for thread: {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            raise CheckpointStorageError(f"列出checkpoint失败: {e}") from e
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 从Repository删除checkpoint
            success = await self._checkpoint_repository.delete_checkpoint(checkpoint_id)
            
            logger.info(f"Deleting checkpoint: {checkpoint_id} for thread: {thread_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            raise CheckpointStorageError(f"删除checkpoint失败: {e}") from e
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        try:
            # 从Repository获取最新checkpoint
            checkpoint_data = await self._checkpoint_repository.get_latest_checkpoint(thread_id)
            
            if checkpoint_data:
                logger.info(f"Getting latest checkpoint for thread: {thread_id}")
                return checkpoint_data
            else:
                logger.info(f"No checkpoint found for thread: {thread_id}")
                return None
            
        except CheckpointNotFoundError:
            logger.info(f"No checkpoint found for thread: {thread_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint: {e}")
            raise CheckpointStorageError(f"获取最新checkpoint失败: {e}") from e
    
    async def restore_from_checkpoint(
        self, 
        thread_id: str, 
        checkpoint_id: str
    ) -> Optional[Any]:
        """从checkpoint恢复状态
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Any]: 恢复的工作流状态，如果失败则返回None
        """
        try:
            # 获取checkpoint数据
            checkpoint_data = await self.get_checkpoint(thread_id, checkpoint_id)
            if not checkpoint_data:
                logger.warning(f"Checkpoint not found: {checkpoint_id}")
                return None
            
            # 反序列化状态
            state_data = checkpoint_data.get('state_data', '')
            if isinstance(state_data, str):
                restored_state = self.serializer.deserialize(state_data, format=self.serializer.FORMAT_JSON)
            else:
                restored_state = state_data
            
            logger.info(f"Restored from checkpoint: {checkpoint_id} for thread: {thread_id}")
            return restored_state
            
        except Exception as e:
            logger.error(f"Failed to restore from checkpoint: {e}")
            raise CheckpointStorageError(f"从checkpoint恢复失败: {e}") from e
    
    async def auto_save_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state: Any,
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            trigger_reason: 触发原因
            
        Returns:
            Optional[str]: checkpoint ID，如果保存失败则返回None
        """
        try:
            # 创建元数据，包含触发原因
            metadata = {
                'trigger_reason': trigger_reason,
                'auto_save': True,
                'saved_at': datetime.now().isoformat()
            }
            
            # 创建checkpoint
            checkpoint_id = await self.create_checkpoint(
                thread_id=thread_id,
                workflow_id=workflow_id,
                state=state,
                metadata=metadata
            )
            
            logger.info(f"Auto-saved checkpoint: {checkpoint_id} for thread: {thread_id}, reason: {trigger_reason}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to auto-save checkpoint: {e}")
            return None
    
    async def cleanup_checkpoints(self, thread_id: str, max_count: Optional[int] = None) -> int:
        """清理旧的checkpoint
        
        Args:
            thread_id: thread ID
            max_count: 保留的最大数量，如果为None则使用配置中的值
            
        Returns:
            int: 删除的checkpoint数量
        """
        try:
            # 如果没有指定max_count，使用配置中的值
            if max_count is None:
                max_count = self.max_checkpoints_per_thread
            
            # 获取所有checkpoint
            all_checkpoints = await self.list_checkpoints(thread_id)
            
            if len(all_checkpoints) <= max_count:
                # 不需要清理
                return 0
            
            # 按创建时间排序，保留最新的max_count个
            sorted_checkpoints = sorted(
                all_checkpoints,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
            
            # 需要删除的checkpoint
            checkpoints_to_delete = sorted_checkpoints[max_count:]
            
            # 删除旧的checkpoint
            deleted_count = 0
            for checkpoint in checkpoints_to_delete:
                checkpoint_id = checkpoint.get('id', '')
                if checkpoint_id:
                    success = await self.delete_checkpoint(thread_id, checkpoint_id)
                    if success:
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old checkpoints for thread: {thread_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
            raise CheckpointStorageError(f"清理checkpoint失败: {e}") from e

    async def copy_checkpoint(
        self,
        source_thread_id: str,
        source_checkpoint_id: str,
        target_thread_id: str
    ) -> str:
        """复制checkpoint到另一个thread"""
        try:
            # 获取源checkpoint
            source_checkpoint = await self.get_checkpoint(source_thread_id, source_checkpoint_id)
            if not source_checkpoint:
                raise CheckpointNotFoundError(f"源checkpoint不存在: {source_checkpoint_id}")
            
            # 修改checkpoint数据以适应目标thread
            new_checkpoint_id = str(uuid.uuid4())
            source_checkpoint['id'] = new_checkpoint_id
            source_checkpoint['thread_id'] = target_thread_id
            source_checkpoint['created_at'] = datetime.now().isoformat()
            source_checkpoint['updated_at'] = datetime.now().isoformat()
            
            # 保存到目标thread
            await self._checkpoint_repository.save_checkpoint(source_checkpoint)
            
            logger.info(f"Copied checkpoint from {source_thread_id}:{source_checkpoint_id} to {target_thread_id}:{new_checkpoint_id}")
            
            return new_checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to copy checkpoint: {e}")
            raise CheckpointStorageError(f"复制checkpoint失败: {e}") from e

    async def export_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """导出checkpoint数据"""
        try:
            checkpoint_data = await self.get_checkpoint(thread_id, checkpoint_id)
            if not checkpoint_data:
                raise CheckpointNotFoundError(f"Checkpoint不存在: {checkpoint_id}")
            
            logger.info(f"Exported checkpoint: {checkpoint_id}")
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Failed to export checkpoint: {e}")
            raise CheckpointStorageError(f"导出checkpoint失败: {e}") from e

    async def import_checkpoint(
        self,
        thread_id: str,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """导入checkpoint数据"""
        try:
            # 生成新的checkpoint ID
            new_checkpoint_id = str(uuid.uuid4())
            checkpoint_data['id'] = new_checkpoint_id
            checkpoint_data['thread_id'] = thread_id
            checkpoint_data['created_at'] = datetime.now().isoformat()
            checkpoint_data['updated_at'] = datetime.now().isoformat()
            
            # 保存checkpoint
            await self._checkpoint_repository.save_checkpoint(checkpoint_data)
            
            logger.info(f"Imported checkpoint: {new_checkpoint_id} to thread: {thread_id}")
            
            return new_checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to import checkpoint: {e}")
            raise CheckpointStorageError(f"导入checkpoint失败: {e}") from e