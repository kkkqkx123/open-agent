"""
Thread检查点服务

整合Thread特定的业务逻辑和管理功能，基于统一的checkpoint模型。
与通用的CheckpointService协作，提供Thread特定的业务逻辑。
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta

from src.services.logger.injection import get_logger
from src.core.checkpoint.models import Checkpoint, CheckpointType, CheckpointStatus, CheckpointStatistics
from src.core.checkpoint.factory import CheckpointFactory
from src.core.checkpoint.validators import CheckpointValidator
from src.core.checkpoint.interfaces import ICheckpointRepository
from src.services.checkpoint.service import CheckpointService

if TYPE_CHECKING:
    from src.interfaces.repository.checkpoint import ICheckpointRepository as ICheckpointRepositoryInterface

from .extensions import ThreadCheckpointExtension
from .adapters import ThreadCheckpointRepositoryAdapter


logger = get_logger(__name__)


class ThreadCheckpointService:
    """Thread检查点服务
    
    整合Thread特定的业务逻辑和管理功能。
    依赖于通用的CheckpointService进行底层checkpoint操作。
    """
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    DEFAULT_EXPIRATION_HOURS = 24
    MAX_CHECKPOINT_SIZE_MB = 100
    MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP = 1
    
    def __init__(
        self,
        repository: ICheckpointRepository,
        checkpoint_service: Optional[CheckpointService] = None,
        checkpoint_factory: Optional[CheckpointFactory] = None,
        validator: Optional[CheckpointValidator] = None
    ):
        """初始化服务
        
        Args:
            repository: 检查点仓储
            checkpoint_service: 通用的检查点服务
            checkpoint_factory: 检查点工厂
            validator: 检查点验证器
        """
        self._repository = ThreadCheckpointRepositoryAdapter(repository)
        self._checkpoint_service = checkpoint_service or CheckpointService(repository)  # type: ignore[arg-type]
        self._factory = checkpoint_factory or CheckpointFactory()
        self._validator = validator or CheckpointValidator()
        logger.info("ThreadCheckpointService initialized")
    
    async def create_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> Checkpoint:
        """创建检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            expiration_hours: 过期小时数
            
        Returns:
            创建的检查点
            
        Raises:
            ValueError: 业务规则验证失败
        """
        try:
            # 业务规则验证
            self._validate_create_checkpoint(thread_id, state_data)
            
            # 检查点数量限制业务规则
            await self._enforce_checkpoint_limit(thread_id)
            
            # 创建检查点
            checkpoint = ThreadCheckpointExtension.create_thread_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                checkpoint_type=checkpoint_type,
                metadata=metadata,
                expiration_hours=expiration_hours
            )
            
            # 验证检查点
            self._validator.validate_checkpoint(checkpoint)
            
            # 使用通用服务保存检查点
            config = CheckpointFactory.create_config(
                thread_id=thread_id,
                checkpoint_ns="thread",
                checkpoint_id=checkpoint.id
            )
            
            checkpoint_id = await self._checkpoint_service.save_checkpoint(
                config=config,
                checkpoint=checkpoint,
                metadata=checkpoint.metadata.to_dict()
            )
            
            if not checkpoint_id:
                raise ValueError("Failed to save checkpoint")
            
            logger.info(f"Created checkpoint {checkpoint.id} for thread {thread_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint for thread {thread_id}: {e}")
            raise
    
    async def restore_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """从检查点恢复
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态数据，失败返回None
        """
        try:
            # 查找检查点
            checkpoint = await self._repository.find_by_id(checkpoint_id)
            if checkpoint is None:
                logger.warning(f"Checkpoint {checkpoint_id} not found")
                return None
            
            # 业务逻辑验证
            if not checkpoint.can_restore():
                raise ValueError(f"Checkpoint {checkpoint_id} cannot be restored: {checkpoint.status}")
            
            # 标记为已恢复
            checkpoint.mark_restored()
            
            # 使用通用服务更新检查点
            config = CheckpointFactory.create_config(
                thread_id=checkpoint.thread_id or "",
                checkpoint_ns="thread",
                checkpoint_id=checkpoint.id
            )
            
            await self._checkpoint_service.update_checkpoint_metadata(
                checkpoint_id=checkpoint_id,
                metadata=checkpoint.metadata.to_dict()
            )
            
            logger.info(f"Restored from checkpoint {checkpoint_id}")
            return checkpoint.state_data
            
        except Exception as e:
            logger.error(f"Failed to restore from checkpoint {checkpoint_id}: {e}")
            raise
    
    async def create_manual_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Checkpoint:
        """创建手动检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            创建的检查点
        """
        return await self.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MANUAL,
            metadata={
                "title": title,
                "description": description,
                "tags": tags or []
            },
            expiration_hours=None  # 手动检查点不过期
        )
    
    async def create_error_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        error_message: str,
        error_type: Optional[str] = None
    ) -> Checkpoint:
        """创建错误检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            创建的检查点
        """
        return await self.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.ERROR,
            metadata={
                "error_message": error_message,
                "error_type": error_type or "Unknown",
                "error_timestamp": datetime.now().isoformat()
            },
            expiration_hours=72  # 错误检查点保留3天
        )
    
    async def create_milestone_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        milestone_name: str,
        description: Optional[str] = None
    ) -> Checkpoint:
        """创建里程碑检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            创建的检查点
        """
        return await self.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MILESTONE,
            metadata={
                "milestone_name": milestone_name,
                "description": description or f"Milestone: {milestone_name}",
                "milestone_timestamp": datetime.now().isoformat()
            },
            expiration_hours=168  # 里程碑检查点保留7天
        )
    
    async def create_backup(self, checkpoint_id: str) -> Checkpoint:
        """创建检查点备份
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份检查点
        """
        try:
            # 获取原检查点
            checkpoint = await self._repository.find_by_id(checkpoint_id)
            if checkpoint is None:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")
            
            # 创建备份检查点
            backup_checkpoint = ThreadCheckpointExtension.create_backup_checkpoint(checkpoint)
            
            # 使用通用服务保存备份
            config = CheckpointFactory.create_config(
                thread_id=checkpoint.thread_id or "",
                checkpoint_ns="thread",
                checkpoint_id=backup_checkpoint.id
            )
            
            backup_id = await self._checkpoint_service.save_checkpoint(
                config=config,
                checkpoint=backup_checkpoint,
                metadata=backup_checkpoint.metadata.to_dict()
            )
            
            if not backup_id:
                raise ValueError("Failed to save backup checkpoint")
            
            logger.info(f"Created backup {backup_checkpoint.id} for checkpoint {checkpoint_id}")
            return backup_checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create backup for checkpoint {checkpoint_id}: {e}")
            raise
    
    async def restore_from_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """从备份恢复
        
        Args:
            backup_id: 备份ID
            
        Returns:
            恢复的状态数据
        """
        return await self.restore_from_checkpoint(backup_id)
    
    async def cleanup_expired_checkpoints(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点
        
        Args:
            thread_id: 线程ID，None表示清理所有线程的过期检查点
            
        Returns:
            清理的检查点数量
        """
        try:
            if thread_id:
                # 清理指定线程的过期检查点
                checkpoints = await self._repository.find_by_thread(thread_id)
                expired_checkpoints = [
                    cp for cp in checkpoints 
                    if cp.is_expired() or ThreadCheckpointExtension.should_cleanup_checkpoint(cp)
                ]
            else:
                # 清理所有过期检查点
                expired_checkpoints = await self._repository.find_expired()
            
            # 删除过期检查点
            deleted_count = 0
            for checkpoint in expired_checkpoints:
                try:
                    config = CheckpointFactory.create_config(
                         thread_id=checkpoint.thread_id or "",
                         checkpoint_ns="thread",
                         checkpoint_id=checkpoint.id
                     )
                    
                    if await self._checkpoint_service.delete_checkpoint(config):
                        deleted_count += 1
                        logger.debug(f"Deleted expired checkpoint {checkpoint.id}")
                except Exception as e:
                    logger.warning(f"Failed to delete expired checkpoint {checkpoint.id}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} expired checkpoints")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired checkpoints: {e}")
            raise
    
    async def get_thread_checkpoint_history(
        self,
        thread_id: str,
        limit: int = 50
    ) -> List[Checkpoint]:
        """获取线程检查点历史
        
        Args:
            thread_id: 线程ID
            limit: 返回数量限制
            
        Returns:
            检查点历史列表
        """
        try:
            checkpoints = await self._repository.find_by_thread(thread_id)
            return checkpoints[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint history for thread {thread_id}: {e}")
            raise
    
    async def get_checkpoint_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> CheckpointStatistics:
        """获取检查点统计信息
        
        Args:
            thread_id: 线程ID，None表示全局统计
            
        Returns:
            统计信息
        """
        try:
            return await self._repository.get_statistics(thread_id)
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint statistics: {e}")
            raise
    
    async def archive_old_checkpoints(self, thread_id: str, days: int = 30) -> int:
        """归档旧检查点
        
        Args:
            thread_id: 线程ID
            days: 归档天数阈值
            
        Returns:
            归档的检查点数量
        """
        try:
            # 查找旧检查点
            checkpoints = await self._repository.find_by_thread(thread_id)
            cutoff_time = datetime.now() - timedelta(days=days)
            
            archived_count = 0
            for checkpoint in checkpoints:
                if (checkpoint.ts < cutoff_time and 
                    checkpoint.status == CheckpointStatus.ACTIVE and
                    checkpoint.checkpoint_type != CheckpointType.MANUAL):  # 不归档手动检查点
                    
                    checkpoint.mark_archived()
                    
                    # 使用通用服务更新检查点
                    config = CheckpointFactory.create_config(
                        thread_id=checkpoint.thread_id or "",
                        checkpoint_ns="thread",
                        checkpoint_id=checkpoint.id
                    )
                    
                    await self._checkpoint_service.update_checkpoint_metadata(
                        checkpoint_id=checkpoint.id,
                        metadata=checkpoint.metadata.to_dict()
                    )
                    archived_count += 1
            
            logger.info(f"Archived {archived_count} old checkpoints for thread {thread_id}")
            return archived_count
            
        except Exception as e:
            logger.error(f"Failed to archive old checkpoints for thread {thread_id}: {e}")
            raise
    
    async def extend_checkpoint_expiration(
        self,
        checkpoint_id: str,
        hours: int
    ) -> bool:
        """延长检查点过期时间
        
        Args:
            checkpoint_id: 检查点ID
            hours: 延长的小时数
            
        Returns:
            是否成功
        """
        try:
            checkpoint = await self._repository.find_by_id(checkpoint_id)
            if checkpoint is None:
                return False
            
            checkpoint.extend_expiration(hours)
            
            # 使用通用服务更新检查点
            config = CheckpointFactory.create_config(
                thread_id=checkpoint.thread_id or "",
                checkpoint_ns="thread",
                checkpoint_id=checkpoint.id
            )
            
            await self._checkpoint_service.update_checkpoint_metadata(
                checkpoint_id=checkpoint.id,
                metadata=checkpoint.metadata.to_dict()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend expiration for checkpoint {checkpoint_id}: {e}")
            raise
    
    async def create_checkpoint_chain(
        self,
        thread_id: str,
        state_data_list: List[Dict[str, Any]],
        chain_metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """创建检查点链
        
        Args:
            thread_id: 线程ID
            state_data_list: 状态数据列表
            chain_metadata: 链元数据
            
        Returns:
            检查点ID列表
        """
        try:
            checkpoints = ThreadCheckpointExtension.create_checkpoint_chain(
                thread_id=thread_id,
                state_data_list=state_data_list,
                chain_metadata=chain_metadata
            )
            
            # 使用通用服务批量保存检查点
            configs = []
            for checkpoint in checkpoints:
                config = CheckpointFactory.create_config(
                    thread_id=thread_id,
                    checkpoint_ns="thread",
                    checkpoint_id=checkpoint.id
                )
                configs.append(config)
            
            checkpoint_ids = await self._checkpoint_service.batch_save_checkpoints(
                checkpoints=checkpoints,
                configs=configs
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
        """获取线程检查点时间线
        
        Args:
            thread_id: 线程ID
            include_backups: 是否包含备份
            
        Returns:
            时间线数据
        """
        try:
            # 获取检查点历史
            checkpoints = await self._repository.find_by_thread(thread_id)
            
            timeline = []
            for checkpoint in checkpoints:
                timeline_item = ThreadCheckpointExtension.get_checkpoint_summary(checkpoint)
                
                # 添加备份信息
                if include_backups:
                    backups = await self._repository.find_backup_chain(checkpoint.id)
                    timeline_item["backups"] = [
                        ThreadCheckpointExtension.get_checkpoint_summary(backup)
                        for backup in backups
                    ]
                
                timeline.append(timeline_item)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint timeline for thread {thread_id}: {e}")
            raise
    
    async def optimize_checkpoint_storage(
        self,
        thread_id: str,
        max_checkpoints: int = 50,
        archive_days: int = 30
    ) -> Dict[str, int]:
        """优化检查点存储
        
        Args:
            thread_id: 线程ID
            max_checkpoints: 最大检查点数量
            archive_days: 归档天数
            
        Returns:
            优化结果统计
        """
        try:
            results = {
                "archived": 0,
                "deleted": 0,
                "backups_created": 0
            }
            
            # 1. 归档旧检查点
            archived_count = await self.archive_old_checkpoints(thread_id, archive_days)
            results["archived"] = archived_count
            
            # 2. 清理过期检查点
            deleted_count = await self.cleanup_expired_checkpoints(thread_id)
            results["deleted"] = deleted_count
            
            # 3. 检查是否需要创建备份
            checkpoints = await self._repository.find_by_thread(thread_id)
            important_checkpoints = [
                cp for cp in checkpoints 
                if cp.checkpoint_type in [CheckpointType.MANUAL, CheckpointType.MILESTONE]
                and cp.metadata.restore_count == 0  # 没有备份的重要检查点
            ]
            
            for checkpoint in important_checkpoints[:5]:  # 最多创建5个备份
                try:
                    await self.create_backup(checkpoint.id)
                    results["backups_created"] += 1
                except Exception as e:
                    logger.warning(f"Failed to create backup for checkpoint {checkpoint.id}: {e}")
            
            logger.info(f"Optimized checkpoint storage for thread {thread_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to optimize checkpoint storage for thread {thread_id}: {e}")
            raise
    
    # 私有方法 - 业务规则实现
    def _validate_create_checkpoint(self, thread_id: str, state_data: Dict[str, Any]) -> None:
        """验证创建检查点的业务规则
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            
        Raises:
            ValueError: 验证失败
        """
        if not thread_id:
            raise ValueError("Thread ID cannot be empty")
        
        if not state_data:
            raise ValueError("State data cannot be empty")
        
        # 检查数据大小
        import json
        size_mb = len(json.dumps(state_data)) / (1024 * 1024)
        if size_mb > self.MAX_CHECKPOINT_SIZE_MB:
            raise ValueError(f"Checkpoint data too large: {size_mb:.2f}MB > {self.MAX_CHECKPOINT_SIZE_MB}MB")
    
    async def _enforce_checkpoint_limit(self, thread_id: str) -> None:
        """强制执行检查点数量限制
        
        Args:
            thread_id: 线程ID
        """
        try:
            # 获取当前检查点数量
            count = await self._repository.count_by_thread(thread_id)
            
            if count >= self.MAX_CHECKPOINTS_PER_THREAD:
                # 清理旧检查点
                await self._cleanup_old_checkpoints(thread_id)
                
                # 再次检查
                count = await self._repository.count_by_thread(thread_id)
                if count >= self.MAX_CHECKPOINTS_PER_THREAD:
                    # 如果还是超过限制，删除最旧的自动检查点
                    await self._delete_oldest_auto_checkpoints(thread_id)
                    
        except Exception as e:
            logger.warning(f"Failed to enforce checkpoint limit for thread {thread_id}: {e}")
    
    async def _cleanup_old_checkpoints(self, thread_id: str) -> None:
        """清理旧检查点
        
        Args:
            thread_id: 线程ID
        """
        try:
            checkpoints = await self._repository.find_by_thread(thread_id)
            
            # 按创建时间排序，保留最新的50个
            checkpoints.sort(key=lambda x: x.ts, reverse=True)
            
            # 删除超过50个的旧检查点（保留手动和里程碑检查点）
            for checkpoint in checkpoints[50:]:
                if checkpoint.checkpoint_type in [CheckpointType.AUTO, CheckpointType.ERROR]:
                    config = CheckpointFactory.create_config(
                        thread_id=checkpoint.thread_id or "",
                        checkpoint_ns="thread",
                        checkpoint_id=checkpoint.id
                    )
                   
                    await self._checkpoint_service.delete_checkpoint(config)
                    logger.debug(f"Deleted old checkpoint {checkpoint.id}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old checkpoints for thread {thread_id}: {e}")
    
    async def _delete_oldest_auto_checkpoints(self, thread_id: str) -> None:
        """删除最旧的自动检查点
        
        Args:
            thread_id: 线程ID
        """
        try:
            checkpoints = await self._repository.find_by_thread(thread_id)
            
            # 过滤出自动检查点并按创建时间排序
            auto_checkpoints = [
                cp for cp in checkpoints 
                if cp.checkpoint_type == CheckpointType.AUTO
            ]
            auto_checkpoints.sort(key=lambda x: x.ts)
            
            # 删除最旧的10个自动检查点
            for checkpoint in auto_checkpoints[:10]:
                config = CheckpointFactory.create_config(
                    thread_id=checkpoint.thread_id or "",
                    checkpoint_ns="thread",
                    checkpoint_id=checkpoint.id
                )
                
                await self._checkpoint_service.delete_checkpoint(config)
                logger.debug(f"Deleted oldest auto checkpoint {checkpoint.id}")
                
        except Exception as e:
            logger.warning(f"Failed to delete oldest auto checkpoints for thread {thread_id}: {e}")