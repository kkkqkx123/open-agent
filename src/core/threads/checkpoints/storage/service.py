"""Thread检查点领域服务

实现Thread检查点的业务逻辑和领域规则，遵循DDD领域服务原则。
"""

from src.interfaces.dependency_injection import get_logger
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import ThreadCheckpoint, CheckpointStatistics, CheckpointStatus, CheckpointType
from .repository import IThreadCheckpointRepository, RepositoryError


logger = get_logger(__name__)


class ThreadCheckpointDomainService:
    """Thread检查点领域服务
    
    包含Thread检查点的复杂业务逻辑和领域规则。
    """
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    DEFAULT_EXPIRATION_HOURS = 24
    MAX_CHECKPOINT_SIZE_MB = 100
    MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP = 1
    
    def __init__(self, repository: IThreadCheckpointRepository):
        """初始化领域服务
        
        Args:
            repository: 检查点仓储
        """
        self._repository = repository
        logger.info("ThreadCheckpointDomainService initialized")
    
    async def create_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> ThreadCheckpoint:
        """创建检查点 - 包含业务逻辑
        
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
            RepositoryError: 仓储操作失败
        """
        try:
            # 业务规则验证
            self._validate_create_checkpoint(thread_id, state_data)
            
            # 检查点数量限制业务规则
            await self._enforce_checkpoint_limit(thread_id)
            
            # 创建检查点
            checkpoint = ThreadCheckpoint(
                thread_id=thread_id,
                state_data=state_data,
                checkpoint_type=checkpoint_type,
                metadata=metadata or {}
            )
            
            # 设置过期时间
            if expiration_hours is None:
                expiration_hours = self.DEFAULT_EXPIRATION_HOURS
            checkpoint.set_expiration(expiration_hours)
            
            # 保存检查点
            success = await self._repository.save(checkpoint)
            if not success:
                raise RepositoryError("Failed to save checkpoint")
            
            logger.info(f"Created checkpoint {checkpoint.id} for thread {thread_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint for thread {thread_id}: {e}")
            raise
    
    async def restore_from_checkpoint(
        self, 
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """从检查点恢复 - 包含业务逻辑
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态数据，失败返回None
            
        Raises:
            ValueError: 业务规则验证失败
            RepositoryError: 仓储操作失败
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
            await self._repository.update(checkpoint)
            
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
    ) -> ThreadCheckpoint:
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
        # 构建元数据
        metadata = {}
        if title:
            metadata["title"] = title
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = tags
        
        # 手动检查点不过期
        return await self.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MANUAL,
            metadata=metadata,
            expiration_hours=None  # 手动检查点不过期
        )
    
    async def create_error_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        error_message: str,
        error_type: Optional[str] = None
    ) -> ThreadCheckpoint:
        """创建错误检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            创建的检查点
        """
        # 构建元数据
        metadata = {
            "error_message": error_message,
            "error_type": error_type or "Unknown",
            "error_timestamp": datetime.now().isoformat()
        }
        
        # 错误检查点保留时间更长
        return await self.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.ERROR,
            metadata=metadata,
            expiration_hours=72  # 错误检查点保留3天
        )
    
    async def create_milestone_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        milestone_name: str,
        description: Optional[str] = None
    ) -> ThreadCheckpoint:
        """创建里程碑检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            创建的检查点
        """
        # 构建元数据
        metadata = {
            "milestone_name": milestone_name,
            "description": description or f"Milestone: {milestone_name}",
            "milestone_timestamp": datetime.now().isoformat()
        }
        
        # 里程碑检查点保留时间很长
        return await self.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MILESTONE,
            metadata=metadata,
            expiration_hours=168  # 里程碑检查点保留7天
        )
    
    async def cleanup_expired_checkpoints(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点 - 业务逻辑
        
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
                    if cp.is_expired() or self._should_cleanup_checkpoint(cp)
                ]
            else:
                # 清理所有过期检查点
                expired_checkpoints = await self._repository.find_expired()
            
            # 删除过期检查点
            deleted_count = 0
            for checkpoint in expired_checkpoints:
                try:
                    if await self._repository.delete(checkpoint.id):
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
    ) -> List[ThreadCheckpoint]:
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
                if (checkpoint.created_at < cutoff_time and 
                    checkpoint.status == CheckpointStatus.ACTIVE and
                    checkpoint.checkpoint_type != CheckpointType.MANUAL):  # 不归档手动检查点
                    
                    checkpoint.mark_archived()
                    if await self._repository.update(checkpoint):
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
            return await self._repository.update(checkpoint)
            
        except Exception as e:
            logger.error(f"Failed to extend expiration for checkpoint {checkpoint_id}: {e}")
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
            checkpoints.sort(key=lambda x: x.created_at, reverse=True)
            
            # 删除超过50个的旧检查点（保留手动和里程碑检查点）
            for checkpoint in checkpoints[50:]:
                if checkpoint.checkpoint_type in [CheckpointType.AUTO, CheckpointType.ERROR]:
                    await self._repository.delete(checkpoint.id)
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
            auto_checkpoints.sort(key=lambda x: x.created_at)
            
            # 删除最旧的10个自动检查点
            for checkpoint in auto_checkpoints[:10]:
                await self._repository.delete(checkpoint.id)
                logger.debug(f"Deleted oldest auto checkpoint {checkpoint.id}")
                
        except Exception as e:
            logger.warning(f"Failed to delete oldest auto checkpoints for thread {thread_id}: {e}")
    
    def _should_cleanup_checkpoint(self, checkpoint: ThreadCheckpoint) -> bool:
        """判断是否应该清理检查点
        
        Args:
            checkpoint: 检查点
            
        Returns:
            是否应该清理
        """
        # 手动和里程碑检查点不自动清理
        if checkpoint.checkpoint_type in [CheckpointType.MANUAL, CheckpointType.MILESTONE]:
            return False
        
        # 检查年龄
        age_hours = checkpoint.get_age_hours()
        if age_hours < self.MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP:
            return False
        
        # 错误检查点保留更长时间
        if checkpoint.checkpoint_type == CheckpointType.ERROR:
            return age_hours > 72  # 3天
        
        # 自动检查点保留24小时
        return age_hours > 24


class CheckpointManager:
    """检查点管理器
    
    提供高级的检查点管理功能。
    """
    
    def __init__(self, domain_service: ThreadCheckpointDomainService):
        """初始化管理器
        
        Args:
            domain_service: 检查点领域服务
        """
        self._domain_service = domain_service
        logger.info("CheckpointManager initialized")
    
    async def create_backup(self, checkpoint_id: str) -> str:
        """创建检查点备份
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份ID
        """
        try:
            # 获取原检查点
            checkpoint = await self._domain_service._repository.find_by_id(checkpoint_id)
            if checkpoint is None:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")
            
            # 创建备份检查点
            backup_metadata = checkpoint.metadata.copy()
            backup_metadata.update({
                "backup_of": checkpoint_id,
                "backup_timestamp": datetime.now().isoformat(),
                "original_created_at": checkpoint.created_at.isoformat()
            })
            
            backup_checkpoint = await self._domain_service.create_checkpoint(
                thread_id=checkpoint.thread_id,
                state_data=checkpoint.state_data,
                checkpoint_type=checkpoint.checkpoint_type,
                metadata=backup_metadata,
                expiration_hours=None  # 备份不过期
            )
            
            logger.info(f"Created backup {backup_checkpoint.id} for checkpoint {checkpoint_id}")
            return backup_checkpoint.id
            
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
        try:
            return await self._domain_service.restore_from_checkpoint(backup_id)
            
        except Exception as e:
            logger.error(f"Failed to restore from backup {backup_id}: {e}")
            raise
    
    async def get_backup_chain(self, checkpoint_id: str) -> List[ThreadCheckpoint]:
        """获取检查点的备份链
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            备份链列表
        """
        try:
            # 获取原检查点
            checkpoint = await self._domain_service._repository.find_by_id(checkpoint_id)
            if checkpoint is None:
                return []
            
            # 查找所有备份
            checkpoints = await self._domain_service._repository.find_by_thread(checkpoint.thread_id)
            
            # 过滤出该检查点的备份
            backups = [
                cp for cp in checkpoints 
                if cp.metadata.get("backup_of") == checkpoint_id
            ]
            
            # 按备份时间排序
            backups.sort(key=lambda x: x.metadata.get("backup_timestamp") or "", reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to get backup chain for checkpoint {checkpoint_id}: {e}")
            raise