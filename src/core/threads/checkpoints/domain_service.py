"""Thread检查点领域服务

实现Thread检查点的核心业务逻辑和领域规则，遵循DDD领域服务原则。
不依赖任何外部服务层，只包含纯粹的领域逻辑。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import ThreadCheckpoint, CheckpointStatistics, CheckpointStatus, CheckpointType


class ThreadCheckpointDomainService:
    """Thread检查点领域服务
    
    包含Thread检查点的核心业务逻辑和领域规则。
    不依赖外部服务，只处理领域内的业务逻辑。
    """
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    DEFAULT_EXPIRATION_HOURS = 24
    MAX_CHECKPOINT_SIZE_MB = 100
    MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP = 1
    
    def __init__(self, repository):
        """初始化领域服务
        
        Args:
            repository: 检查点仓储接口
        """
        self._repository = repository
    
    def validate_create_checkpoint(self, thread_id: str, state_data: Dict[str, Any]) -> None:
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
    
    def create_checkpoint_entity(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> ThreadCheckpoint:
        """创建检查点实体 - 纯领域逻辑
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            expiration_hours: 过期小时数
            
        Returns:
            创建的检查点实体
            
        Raises:
            ValueError: 业务规则验证失败
        """
        # 业务规则验证
        self.validate_create_checkpoint(thread_id, state_data)
        
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
        
        return checkpoint
    
    def validate_checkpoint_restore(self, checkpoint: ThreadCheckpoint) -> None:
        """验证检查点恢复的业务规则
        
        Args:
            checkpoint: 检查点
            
        Raises:
            ValueError: 验证失败
        """
        if not checkpoint.can_restore():
            raise ValueError(f"Checkpoint {checkpoint.id} cannot be restored: {checkpoint.status}")
    
    def should_cleanup_checkpoint(self, checkpoint: ThreadCheckpoint) -> bool:
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
    
    def get_checkpoint_cleanup_candidates(self, checkpoints: List[ThreadCheckpoint]) -> List[ThreadCheckpoint]:
        """获取需要清理的检查点候选列表
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            需要清理的检查点列表
        """
        return [cp for cp in checkpoints if cp.is_expired() or self.should_cleanup_checkpoint(cp)]
    
    def get_checkpoint_limit_enforcement_candidates(self, checkpoints: List[ThreadCheckpoint]) -> List[ThreadCheckpoint]:
        """获取需要强制执行限制的检查点候选列表
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            需要删除的检查点列表
        """
        # 按创建时间排序，保留最新的50个
        sorted_checkpoints = sorted(checkpoints, key=lambda x: x.created_at, reverse=True)
        
        # 删除超过50个的旧检查点（保留手动和里程碑检查点）
        candidates = []
        for checkpoint in sorted_checkpoints[50:]:
            if checkpoint.checkpoint_type in [CheckpointType.AUTO, CheckpointType.ERROR]:
                candidates.append(checkpoint)
        
        return candidates
    
    def get_oldest_auto_checkpoints(self, checkpoints: List[ThreadCheckpoint], count: int = 10) -> List[ThreadCheckpoint]:
        """获取最旧的自动检查点
        
        Args:
            checkpoints: 检查点列表
            count: 返回数量
            
        Returns:
            最旧的自动检查点列表
        """
        # 过滤出自动检查点并按创建时间排序
        auto_checkpoints = [
            cp for cp in checkpoints 
            if cp.checkpoint_type == CheckpointType.AUTO
        ]
        auto_checkpoints.sort(key=lambda x: x.created_at)
        
        return auto_checkpoints[:count]
    
    def get_archive_candidates(self, checkpoints: List[ThreadCheckpoint], days: int = 30) -> List[ThreadCheckpoint]:
        """获取需要归档的检查点候选列表
        
        Args:
            checkpoints: 检查点列表
            days: 归档天数阈值
            
        Returns:
            需要归档的检查点列表
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        candidates = []
        for checkpoint in checkpoints:
            if (checkpoint.created_at < cutoff_time and 
                checkpoint.status == CheckpointStatus.ACTIVE and
                checkpoint.checkpoint_type != CheckpointType.MANUAL):  # 不归档手动检查点
                candidates.append(checkpoint)
        
        return candidates
    
    def calculate_checkpoint_statistics(self, checkpoints: List[ThreadCheckpoint]) -> CheckpointStatistics:
        """计算检查点统计信息
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            统计信息
        """
        if not checkpoints:
            return CheckpointStatistics()
        
        # 基本统计
        total_checkpoints = len(checkpoints)
        active_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.ACTIVE)
        expired_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.EXPIRED)
        corrupted_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.CORRUPTED)
        archived_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.ARCHIVED)
        
        # 大小统计
        total_size_bytes = sum(cp.size_bytes for cp in checkpoints)
        average_size_bytes = total_size_bytes / total_checkpoints if total_checkpoints > 0 else 0
        largest_checkpoint_bytes = max(cp.size_bytes for cp in checkpoints) if checkpoints else 0
        smallest_checkpoint_bytes = min(cp.size_bytes for cp in checkpoints) if checkpoints else 0
        
        # 恢复统计
        total_restores = sum(cp.restore_count for cp in checkpoints)
        average_restores = total_restores / total_checkpoints if total_checkpoints > 0 else 0
        
        # 年龄统计
        now = datetime.now()
        ages_hours = [(now - cp.created_at).total_seconds() / 3600.0 for cp in checkpoints]
        oldest_checkpoint_age_hours = max(ages_hours) if ages_hours else 0
        newest_checkpoint_age_hours = min(ages_hours) if ages_hours else 0
        average_age_hours = sum(ages_hours) / len(ages_hours) if ages_hours else 0
        
        return CheckpointStatistics(
            total_checkpoints=total_checkpoints,
            active_checkpoints=active_checkpoints,
            expired_checkpoints=expired_checkpoints,
            corrupted_checkpoints=corrupted_checkpoints,
            archived_checkpoints=archived_checkpoints,
            total_size_bytes=total_size_bytes,
            average_size_bytes=average_size_bytes,
            largest_checkpoint_bytes=largest_checkpoint_bytes,
            smallest_checkpoint_bytes=smallest_checkpoint_bytes,
            total_restores=total_restores,
            average_restores=average_restores,
            oldest_checkpoint_age_hours=oldest_checkpoint_age_hours,
            newest_checkpoint_age_hours=newest_checkpoint_age_hours,
            average_age_hours=average_age_hours,
        )
    
    def create_manual_checkpoint_metadata(
        self, 
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建手动检查点元数据
        
        Args:
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            元数据字典
        """
        metadata = {}
        if title:
            metadata["title"] = title
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = tags
        
        return metadata
    
    def create_error_checkpoint_metadata(
        self, 
        error_message: str,
        error_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建错误检查点元数据
        
        Args:
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            元数据字典
        """
        return {
            "error_message": error_message,
            "error_type": error_type or "Unknown",
            "error_timestamp": datetime.now().isoformat()
        }
    
    def create_milestone_checkpoint_metadata(
        self, 
        milestone_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建里程碑检查点元数据
        
        Args:
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            元数据字典
        """
        return {
            "milestone_name": milestone_name,
            "description": description or f"Milestone: {milestone_name}",
            "milestone_timestamp": datetime.now().isoformat()
        }
    
    def create_backup_metadata(self, original_checkpoint_id: str, original_created_at: datetime) -> Dict[str, Any]:
        """创建备份检查点元数据
        
        Args:
            original_checkpoint_id: 原检查点ID
            original_created_at: 原检查点创建时间
            
        Returns:
            元数据字典
        """
        return {
            "backup_of": original_checkpoint_id,
            "backup_timestamp": datetime.now().isoformat(),
            "original_created_at": original_created_at.isoformat()
        }
    
    def get_backup_chain(self, checkpoints: List[ThreadCheckpoint], checkpoint_id: str) -> List[ThreadCheckpoint]:
        """获取检查点的备份链
        
        Args:
            checkpoints: 检查点列表
            checkpoint_id: 检查点ID
            
        Returns:
            备份链列表
        """
        # 过滤出该检查点的备份
        backups = [
            cp for cp in checkpoints 
            if cp.metadata.get("backup_of") == checkpoint_id
        ]
        
        # 按备份时间排序
        backups.sort(key=lambda x: x.metadata.get("backup_timestamp") or "", reverse=True)
        
        return backups