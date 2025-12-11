"""存储编排器

提供存储相关的业务编排功能，协调多个领域服务。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.checkpoints.storage import (
    ThreadCheckpointDomainService,
    CheckpointManager,
    CheckpointType
)
from src.core.threads.checkpoints.manager import ThreadCheckpointManager
from src.core.threads.checkpoints.storage.repository import IThreadCheckpointRepository
from src.core.threads.checkpoints.storage.models import ThreadCheckpoint


logger = get_logger(__name__)


class StorageOrchestrator:
    """存储编排器 - 业务编排层
    
    协调多个领域服务，提供高级的存储业务功能。
    """
    
    def __init__(
        self,
        checkpoint_domain_service: ThreadCheckpointDomainService,
        checkpoint_manager: ThreadCheckpointManager,
        checkpoint_storage_manager: CheckpointManager
    ):
        """初始化存储编排器
        
        Args:
            checkpoint_domain_service: 检查点领域服务
            checkpoint_manager: 检查点管理器
            checkpoint_storage_manager: 检查点存储管理器
        """
        self._checkpoint_domain_service = checkpoint_domain_service
        self._checkpoint_manager = checkpoint_manager
        self._checkpoint_storage_manager = checkpoint_storage_manager
        
        logger.info("StorageOrchestrator initialized")
    
    async def create_thread_checkpoint_with_backup(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        create_backup: bool = True
    ) -> Dict[str, str]:
        """创建线程检查点并备份 - 业务编排
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            create_backup: 是否创建备份
            
        Returns:
            包含检查点ID和备份ID的字典
        """
        try:
            # 1. 创建并备份检查点（调用管理器）
            result = await self._checkpoint_manager.create_and_backup_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                checkpoint_type=checkpoint_type,
                metadata=metadata,
                create_backup=create_backup
            )
            
            logger.info(f"Created checkpoint with backup for thread {thread_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint with backup for thread {thread_id}: {e}")
            raise
    
    async def restore_thread_checkpoint_with_validation(
        self,
        thread_id: str,
        checkpoint_id: str,
        validate_thread: bool = True
    ) -> Dict[str, Any]:
        """恢复线程检查点并验证 - 业务编排
        
        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID
            validate_thread: 是否验证线程状态
            
        Returns:
            恢复的状态数据
        """
        try:
            # 1. 恢复并验证检查点（调用管理器）
            state_data = await self._checkpoint_manager.restore_with_validation(
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                validate_thread=validate_thread
            )
            
            logger.info(f"Restored checkpoint with validation for thread {thread_id}")
            return state_data
            
        except Exception as e:
            logger.error(f"Failed to restore checkpoint with validation for thread {thread_id}: {e}")
            raise
    
    async def create_thread_checkpoint_chain(
        self,
        thread_id: str,
        state_data_list: List[Dict[str, Any]],
        chain_metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """创建线程检查点链 - 业务编排
        
        Args:
            thread_id: 线程ID
            state_data_list: 状态数据列表
            chain_metadata: 链元数据
            
        Returns:
            检查点ID列表
        """
        try:
            # 1. 创建检查点链（调用管理器）
            checkpoint_ids = await self._checkpoint_manager.create_checkpoint_chain(
                thread_id=thread_id,
                state_data_list=state_data_list,
                chain_metadata=chain_metadata
            )
            
            logger.info(f"Created checkpoint chain with {len(checkpoint_ids)} checkpoints for thread {thread_id}")
            return checkpoint_ids
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint chain for thread {thread_id}: {e}")
            raise
    
    async def get_thread_checkpoint_timeline(
        self,
        thread_id: str,
        include_backups: bool = True
    ) -> List[Dict[str, Any]]:
        """获取线程检查点时间线 - 业务编排
        
        Args:
            thread_id: 线程ID
            include_backups: 是否包含备份
            
        Returns:
            时间线数据
        """
        try:
            # 1. 获取检查点时间线（调用管理器）
            timeline = await self._checkpoint_manager.get_thread_checkpoint_timeline(
                thread_id=thread_id,
                include_backups=include_backups
            )
            
            logger.info(f"Retrieved checkpoint timeline for thread {thread_id}")
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint timeline for thread {thread_id}: {e}")
            raise
    
    async def optimize_thread_checkpoint_storage(
        self,
        thread_id: str,
        max_checkpoints: int = 50,
        archive_days: int = 30
    ) -> Dict[str, int]:
        """优化线程检查点存储 - 业务编排
        
        Args:
            thread_id: 线程ID
            max_checkpoints: 最大检查点数量
            archive_days: 归档天数
            
        Returns:
            优化结果统计
        """
        try:
            # 1. 优化检查点存储（调用管理器）
            results = await self._checkpoint_manager.optimize_checkpoint_storage(
                thread_id=thread_id,
                max_checkpoints=max_checkpoints,
                archive_days=archive_days
            )
            
            logger.info(f"Optimized checkpoint storage for thread {thread_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to optimize checkpoint storage for thread {thread_id}: {e}")
            raise
    
    async def cleanup_expired_checkpoints_for_thread(
        self,
        thread_id: str
    ) -> int:
        """清理线程的过期检查点 - 业务编排
        
        Args:
            thread_id: 线程ID
            
        Returns:
            清理的检查点数量
        """
        try:
            # 1. 清理过期检查点（调用领域服务）
            deleted_count = await self._checkpoint_domain_service.cleanup_expired_checkpoints(thread_id)
            
            logger.info(f"Cleaned up {deleted_count} expired checkpoints for thread {thread_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired checkpoints for thread {thread_id}: {e}")
            raise
    
    async def create_manual_checkpoint_for_thread(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ThreadCheckpoint:
        """为线程创建手动检查点 - 业务编排
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            创建的检查点
        """
        try:
            # 1. 创建手动检查点（调用领域服务）
            checkpoint = await self._checkpoint_domain_service.create_manual_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                title=title,
                description=description,
                tags=tags
            )
            
            logger.info(f"Created manual checkpoint {checkpoint.id} for thread {thread_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create manual checkpoint for thread {thread_id}: {e}")
            raise
    
    async def create_error_checkpoint_for_thread(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        error_message: str,
        error_type: Optional[str] = None
    ) -> ThreadCheckpoint:
        """为线程创建错误检查点 - 业务编排
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            创建的检查点
        """
        try:
            # 1. 创建错误检查点（调用领域服务）
            checkpoint = await self._checkpoint_domain_service.create_error_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                error_message=error_message,
                error_type=error_type
            )
            
            logger.info(f"Created error checkpoint {checkpoint.id} for thread {thread_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create error checkpoint for thread {thread_id}: {e}")
            raise
    
    async def create_milestone_checkpoint_for_thread(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        milestone_name: str,
        description: Optional[str] = None
    ) -> ThreadCheckpoint:
        """为线程创建里程碑检查点 - 业务编排
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            创建的检查点
        """
        try:
            # 1. 创建里程碑检查点（调用领域服务）
            checkpoint = await self._checkpoint_domain_service.create_milestone_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                milestone_name=milestone_name,
                description=description
            )
            
            logger.info(f"Created milestone checkpoint {checkpoint.id} for thread {thread_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create milestone checkpoint for thread {thread_id}: {e}")
            raise
    
    async def get_comprehensive_checkpoint_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取综合检查点统计信息 - 业务编排
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            综合统计信息
        """
        try:
            # 1. 获取综合统计信息（调用管理器）
            stats = await self._checkpoint_manager.get_comprehensive_statistics(thread_id)
            
            logger.info(f"Retrieved comprehensive checkpoint statistics for thread {thread_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive checkpoint statistics: {e}")
            raise
    
    async def extend_checkpoint_expiration(
        self,
        checkpoint_id: str,
        hours: int
    ) -> bool:
        """延长检查点过期时间 - 业务编排
        
        Args:
            checkpoint_id: 检查点ID
            hours: 延长的小时数
            
        Returns:
            是否成功
        """
        try:
            # 1. 延长检查点过期时间（调用领域服务）
            success = await self._checkpoint_domain_service.extend_checkpoint_expiration(
                checkpoint_id=checkpoint_id,
                hours=hours
            )
            
            if success:
                logger.info(f"Extended expiration for checkpoint {checkpoint_id} by {hours} hours")
            else:
                logger.warning(f"Failed to extend expiration for checkpoint {checkpoint_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to extend expiration for checkpoint {checkpoint_id}: {e}")
            raise
    
    async def create_checkpoint_backup(
        self,
        checkpoint_id: str
    ) -> str:
        """创建检查点备份 - 业务编排
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份ID
        """
        try:
            # 1. 创建备份（调用存储管理器）
            backup_id = await self._checkpoint_storage_manager.create_backup(checkpoint_id)
            
            logger.info(f"Created backup {backup_id} for checkpoint {checkpoint_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup for checkpoint {checkpoint_id}: {e}")
            raise
    
    async def restore_from_checkpoint_backup(
        self,
        backup_id: str
    ) -> Optional[Dict[str, Any]]:
        """从检查点备份恢复 - 业务编排
        
        Args:
            backup_id: 备份ID
            
        Returns:
            恢复的状态数据
        """
        try:
            # 1. 从备份恢复（调用存储管理器）
            state_data = await self._checkpoint_storage_manager.restore_from_backup(backup_id)
            
            if state_data:
                logger.info(f"Restored from backup {backup_id}")
            else:
                logger.warning(f"Failed to restore from backup {backup_id}")
            
            return state_data
            
        except Exception as e:
            logger.error(f"Failed to restore from backup {backup_id}: {e}")
            raise
    
    async def get_checkpoint_backup_chain(
        self,
        checkpoint_id: str
    ) -> List[ThreadCheckpoint]:
        """获取检查点备份链 - 业务编排
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份链列表
        """
        try:
            # 1. 获取备份链（调用存储管理器）
            backup_chain = await self._checkpoint_storage_manager.get_backup_chain(checkpoint_id)
            
            logger.info(f"Retrieved backup chain with {len(backup_chain)} backups for checkpoint {checkpoint_id}")
            return backup_chain
            
        except Exception as e:
            logger.error(f"Failed to get backup chain for checkpoint {checkpoint_id}: {e}")
            raise


class ThreadStorageService:
    """线程存储服务 - 业务编排层
    
    专门处理线程相关的存储业务编排。
    """
    
    def __init__(
        self,
        storage_orchestrator: StorageOrchestrator,
        checkpoint_domain_service: ThreadCheckpointDomainService
    ):
        """初始化线程存储服务
        
        Args:
            storage_orchestrator: 存储编排器
            checkpoint_domain_service: 检查点领域服务
        """
        self._storage_orchestrator = storage_orchestrator
        self._checkpoint_domain_service = checkpoint_domain_service
        
        logger.info("ThreadStorageService initialized")
    
    async def initialize_thread_storage(
        self,
        thread_id: str,
        initial_state: Dict[str, Any]
    ) -> str:
        """初始化线程存储 - 业务编排
        
        Args:
            thread_id: 线程ID
            initial_state: 初始状态
            
        Returns:
            初始检查点ID
        """
        try:
            # 1. 创建初始检查点
            checkpoint = await self._storage_orchestrator.create_milestone_checkpoint_for_thread(
                thread_id=thread_id,
                state_data=initial_state,
                milestone_name="thread_initialization",
                description="Thread initialization checkpoint"
            )
            
            logger.info(f"Initialized storage for thread {thread_id} with checkpoint {checkpoint.id}")
            return checkpoint.id
            
        except Exception as e:
            logger.error(f"Failed to initialize storage for thread {thread_id}: {e}")
            raise
    
    async def finalize_thread_storage(
        self,
        thread_id: str,
        final_state: Dict[str, Any]
    ) -> str:
        """终结线程存储 - 业务编排
        
        Args:
            thread_id: 线程ID
            final_state: 最终状态
            
        Returns:
            最终检查点ID
        """
        try:
            # 1. 创建最终检查点
            checkpoint = await self._storage_orchestrator.create_milestone_checkpoint_for_thread(
                thread_id=thread_id,
                state_data=final_state,
                milestone_name="thread_finalization",
                description="Thread finalization checkpoint"
            )
            
            # 2. 清理过期检查点
            await self._storage_orchestrator.cleanup_expired_checkpoints_for_thread(thread_id)
            
            logger.info(f"Finalized storage for thread {thread_id} with checkpoint {checkpoint.id}")
            return checkpoint.id
            
        except Exception as e:
            logger.error(f"Failed to finalize storage for thread {thread_id}: {e}")
            raise
    
    async def backup_thread_storage(
        self,
        thread_id: str
    ) -> Dict[str, List[str]]:
        """备份线程存储 - 业务编排
        
        Args:
            thread_id: 线程ID
            
        Returns:
            备份结果
        """
        try:
            # 1. 获取线程的所有检查点
            timeline = await self._storage_orchestrator.get_thread_checkpoint_timeline(
                thread_id=thread_id,
                include_backups=False
            )
            
            backup_results: Dict[str, List[str]] = {}
            
            # 2. 为每个重要检查点创建备份
            for item in timeline:
                checkpoint_id = item["id"]
                checkpoint_type = item["type"]
                
                # 只为手动和里程碑检查点创建备份
                if checkpoint_type in ["manual", "milestone"]:
                    try:
                        backup_id = await self._storage_orchestrator.create_checkpoint_backup(checkpoint_id)
                        if checkpoint_id not in backup_results:
                            backup_results[checkpoint_id] = []
                        backup_results[checkpoint_id].append(backup_id)
                    except Exception as e:
                        logger.warning(f"Failed to create backup for checkpoint {checkpoint_id}: {e}")
            
            logger.info(f"Created backups for thread {thread_id}: {len(backup_results)} checkpoints")
            return backup_results
            
        except Exception as e:
            logger.error(f"Failed to backup storage for thread {thread_id}: {e}")
            raise