"""
Thread检查点扩展功能

提供Thread特定的检查点创建和管理功能，基于统一的checkpoint模型。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.checkpoint.models import Checkpoint, CheckpointMetadata, CheckpointType, CheckpointStatus
from src.core.checkpoint.factory import CheckpointFactory


class ThreadCheckpointExtension:
    """Thread检查点扩展功能
    
    提供Thread特定的检查点创建和管理方法。
    """
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    DEFAULT_EXPIRATION_HOURS = 24
    MAX_CHECKPOINT_SIZE_MB = 100
    
    @staticmethod
    def create_thread_checkpoint(
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> Checkpoint:
        """创建Thread特定的检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 额外元数据
            expiration_hours: 过期小时数
            
        Returns:
            创建的检查点
            
        Raises:
            ValueError: 参数验证失败
        """
        # 验证参数
        if not thread_id:
            raise ValueError("Thread ID cannot be empty")
        
        if not state_data:
            raise ValueError("State data cannot be empty")
        
        # 检查数据大小
        import json
        size_mb = len(json.dumps(state_data)) / (1024 * 1024)
        if size_mb > ThreadCheckpointExtension.MAX_CHECKPOINT_SIZE_MB:
            raise ValueError(f"Checkpoint data too large: {size_mb:.2f}MB > {ThreadCheckpointExtension.MAX_CHECKPOINT_SIZE_MB}MB")
        
        # 构建元数据
        checkpoint_metadata = CheckpointMetadata(
            thread_id=thread_id,
            source="thread",
            **(metadata or {})
        )
        
        # 创建检查点
        checkpoint = Checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            metadata=checkpoint_metadata
        )
        
        # 设置过期时间
        if expiration_hours is None:
            expiration_hours = ThreadCheckpointExtension.DEFAULT_EXPIRATION_HOURS
        
        # 手动检查点不过期
        if checkpoint_type != CheckpointType.MANUAL:
            checkpoint.set_expiration(expiration_hours)
        
        return checkpoint
    
    @staticmethod
    def create_manual_checkpoint(
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
        # 构建元数据
        metadata = {
            "title": title,
            "description": description,
            "tags": tags or [],
        }
        
        return ThreadCheckpointExtension.create_thread_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MANUAL,
            metadata=metadata,
            expiration_hours=None  # 手动检查点不过期
        )
    
    @staticmethod
    def create_error_checkpoint(
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
        # 构建元数据
        metadata = {
            "error_message": error_message,
            "error_type": error_type or "Unknown",
            "error_timestamp": datetime.now().isoformat()
        }
        
        # 错误检查点保留时间更长
        return ThreadCheckpointExtension.create_thread_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.ERROR,
            metadata=metadata,
            expiration_hours=72  # 错误检查点保留3天
        )
    
    @staticmethod
    def create_milestone_checkpoint(
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
        # 构建元数据
        metadata = {
            "milestone_name": milestone_name,
            "description": description or f"Milestone: {milestone_name}",
            "milestone_timestamp": datetime.now().isoformat()
        }
        
        # 里程碑检查点保留时间很长
        return ThreadCheckpointExtension.create_thread_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MILESTONE,
            metadata=metadata,
            expiration_hours=168  # 里程碑检查点保留7天
        )
    
    @staticmethod
    def create_backup_checkpoint(
        original_checkpoint: Checkpoint,
        backup_metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """创建备份检查点
        
        Args:
            original_checkpoint: 原始检查点
            backup_metadata: 备份元数据
            
        Returns:
            创建的备份检查点
        """
        # 构建备份元数据
        metadata = original_checkpoint.metadata.custom_data.copy()
        metadata.update({
            "backup_of": original_checkpoint.id,
            "backup_timestamp": datetime.now().isoformat(),
            "original_created_at": original_checkpoint.ts.isoformat(),
            **(backup_metadata or {})
        })
        
        # 创建备份检查点
        backup_checkpoint = Checkpoint(
            thread_id=original_checkpoint.thread_id,
            state_data=original_checkpoint.state_data,
            checkpoint_type=original_checkpoint.checkpoint_type,
            metadata=CheckpointMetadata(
                thread_id=original_checkpoint.thread_id,
                source="backup",
                custom_data=metadata
            )
        )
        
        # 备份不过期
        return backup_checkpoint
    
    @staticmethod
    def should_cleanup_checkpoint(checkpoint: Checkpoint) -> bool:
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
        if age_hours < 1:  # 最小1小时
            return False
        
        # 错误检查点保留更长时间
        if checkpoint.checkpoint_type == CheckpointType.ERROR:
            return age_hours > 72  # 3天
        
        # 自动检查点保留24小时
        return age_hours > 24
    
    @staticmethod
    def validate_checkpoint_limit(current_count: int, thread_id: str) -> None:
        """验证检查点数量限制
        
        Args:
            current_count: 当前检查点数量
            thread_id: 线程ID
            
        Raises:
            ValueError: 超过限制
        """
        if current_count >= ThreadCheckpointExtension.MAX_CHECKPOINTS_PER_THREAD:
            raise ValueError(
                f"Checkpoint limit exceeded for thread {thread_id}: "
                f"{current_count}/{ThreadCheckpointExtension.MAX_CHECKPOINTS_PER_THREAD}"
            )
    
    @staticmethod
    def create_checkpoint_chain(
        thread_id: str,
        state_data_list: List[Dict[str, Any]],
        chain_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Checkpoint]:
        """创建检查点链
        
        Args:
            thread_id: 线程ID
            state_data_list: 状态数据列表
            chain_metadata: 链元数据
            
        Returns:
            检查点链列表
        """
        checkpoints = []
        
        for i, state_data in enumerate(state_data_list):
            # 为链中的每个检查点添加元数据
            metadata = {
                "chain_index": i,
                "chain_length": len(state_data_list),
                "chain_metadata": chain_metadata or {}
            }
            
            # 创建检查点
            checkpoint = ThreadCheckpointExtension.create_thread_checkpoint(
                thread_id=thread_id,
                state_data=state_data,
                metadata=metadata
            )
            
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    @staticmethod
    def enrich_checkpoint_metadata(
        checkpoint: Checkpoint,
        additional_metadata: Dict[str, Any]
    ) -> None:
        """丰富检查点元数据
        
        Args:
            checkpoint: 检查点
            additional_metadata: 额外元数据
        """
        # 更新自定义数据
        checkpoint.metadata.custom_data.update(additional_metadata)
        checkpoint.metadata.updated_at = datetime.now()
    
    @staticmethod
    def get_checkpoint_summary(checkpoint: Checkpoint) -> Dict[str, Any]:
        """获取检查点摘要
        
        Args:
            checkpoint: 检查点
            
        Returns:
            检查点摘要
        """
        return {
            "id": checkpoint.id,
            "thread_id": checkpoint.thread_id,
            "type": checkpoint.checkpoint_type.value,
            "status": checkpoint.status.value,
            "created_at": checkpoint.ts.isoformat(),
            "size_bytes": checkpoint.metadata.size_bytes,
            "restore_count": checkpoint.metadata.restore_count,
            "title": checkpoint.metadata.title,
            "description": checkpoint.metadata.description,
            "tags": checkpoint.metadata.tags,
            "is_expired": checkpoint.is_expired(),
            "can_restore": checkpoint.can_restore(),
            "age_hours": checkpoint.get_age_hours(),
        }