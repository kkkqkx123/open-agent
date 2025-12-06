"""
检查点工厂和验证器

提供检查点的创建、验证和配置管理功能。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .models import Checkpoint, CheckpointMetadata, CheckpointTuple, CheckpointType, CheckpointStatus


class CheckpointValidationError(Exception):
    """检查点验证错误"""
    pass


class CheckpointValidator:
    """检查点验证器"""
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    MAX_CHECKPOINT_SIZE_MB = 100
    MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP = 1
    
    @classmethod
    def validate_checkpoint(cls, checkpoint: Checkpoint) -> None:
        """验证检查点
        
        Args:
            checkpoint: 检查点对象
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not checkpoint.id:
            raise CheckpointValidationError("Checkpoint ID cannot be empty")
        
        if not checkpoint.channel_values and not checkpoint.state_data:
            raise CheckpointValidationError("Checkpoint data cannot be empty")
        
        # 检查数据大小
        import json
        size_mb = len(json.dumps(checkpoint.to_dict())) / (1024 * 1024)
        if size_mb > cls.MAX_CHECKPOINT_SIZE_MB:
            raise CheckpointValidationError(
                f"Checkpoint data too large: {size_mb:.2f}MB > {cls.MAX_CHECKPOINT_SIZE_MB}MB"
            )
    
    @classmethod
    def validate_metadata(cls, metadata: CheckpointMetadata) -> None:
        """验证元数据
        
        Args:
            metadata: 元数据对象
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if metadata.size_bytes < 0:
            raise CheckpointValidationError("Size bytes cannot be negative")
        
        if metadata.restore_count < 0:
            raise CheckpointValidationError("Restore count cannot be negative")
    
    @classmethod
    def validate_thread_checkpoint_limit(cls, current_count: int) -> None:
        """验证Thread检查点数量限制
        
        Args:
            current_count: 当前检查点数量
            
        Raises:
            CheckpointValidationError: 超过限制时抛出
        """
        if current_count >= cls.MAX_CHECKPOINTS_PER_THREAD:
            raise CheckpointValidationError(
                f"Thread checkpoint limit exceeded: {current_count} >= {cls.MAX_CHECKPOINTS_PER_THREAD}"
            )
    
    @classmethod
    def should_cleanup_checkpoint(cls, checkpoint: Checkpoint) -> bool:
        """判断是否应该清理检查点
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            是否应该清理
        """
        # 手动和里程碑检查点不自动清理
        if checkpoint.checkpoint_type in [CheckpointType.MANUAL, CheckpointType.MILESTONE]:
            return False
        
        # 检查年龄
        age_hours = checkpoint.get_age_hours()
        if age_hours < cls.MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP:
            return False
        
        # 错误检查点保留更长时间
        if checkpoint.checkpoint_type == CheckpointType.ERROR:
            return age_hours > 72  # 3天
        
        # 自动检查点保留24小时
        return age_hours > 24


class CheckpointFactory:
    """检查点工厂"""
    
    @staticmethod
    def create_checkpoint(
        thread_id: Optional[str] = None,
        state_data: Optional[Dict[str, Any]] = None,
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """创建检查点
        
        Args:
            thread_id: Thread ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            
        Returns:
            检查点对象
        """
        checkpoint = Checkpoint(
            thread_id=thread_id,
            state_data=state_data or {},
            checkpoint_type=checkpoint_type
        )
        
        # 设置元数据
        if metadata:
            checkpoint.metadata.custom_data.update(metadata)
        
        return checkpoint
    
    @staticmethod
    def create_metadata(
        source: Optional[str] = None,
        step: Optional[int] = None,
        thread_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> CheckpointMetadata:
        """创建元数据
        
        Args:
            source: 来源
            step: 步数
            thread_id: Thread ID
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            元数据对象
        """
        return CheckpointMetadata(
            source=source,
            step=step,
            thread_id=thread_id,
            title=title,
            description=description,
            tags=tags or []
        )
    
    @staticmethod
    def create_tuple(
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        parent_config: Optional[Dict[str, Any]] = None
    ) -> CheckpointTuple:
        """创建检查点元组
        
        Args:
            config: 配置
            checkpoint: 检查点
            parent_config: 父配置
            
        Returns:
            检查点元组
        """
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            parent_config=parent_config
        )
    
    @staticmethod
    def extract_thread_id(config: Dict[str, Any]) -> Optional[str]:
        """从配置中提取Thread ID
        
        Args:
            config: 配置字典
            
        Returns:
            Thread ID
        """
        return config.get("configurable", {}).get("thread_id")
    
    @staticmethod
    def extract_checkpoint_id(config: Dict[str, Any]) -> Optional[str]:
        """从配置中提取检查点ID
        
        Args:
            config: 配置字典
            
        Returns:
            检查点ID
        """
        return config.get("configurable", {}).get("checkpoint_id")
    
    @staticmethod
    def create_config(
        thread_id: str,
        checkpoint_ns: str = "",
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建配置
        
        Args:
            thread_id: Thread ID
            checkpoint_ns: 检查点命名空间
            checkpoint_id: 检查点ID
            
        Returns:
            配置字典
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns
            }
        }
        
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        
        return config
    
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
            thread_id: Thread ID
            state_data: 状态数据
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            检查点对象
        """
        metadata = {}
        if title:
            metadata["title"] = title
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = tags
        
        return CheckpointFactory.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MANUAL,
            metadata=metadata
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
            thread_id: Thread ID
            state_data: 状态数据
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            检查点对象
        """
        metadata = {
            "error_message": error_message,
            "error_type": error_type or "Unknown",
            "error_timestamp": datetime.now().isoformat()
        }
        
        checkpoint = CheckpointFactory.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.ERROR,
            metadata=metadata
        )
        
        # 错误检查点保留72小时
        checkpoint.set_expiration(72)
        
        return checkpoint
    
    @staticmethod
    def create_milestone_checkpoint(
        thread_id: str,
        state_data: Dict[str, Any],
        milestone_name: str,
        description: Optional[str] = None
    ) -> Checkpoint:
        """创建里程碑检查点
        
        Args:
            thread_id: Thread ID
            state_data: 状态数据
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            检查点对象
        """
        metadata = {
            "milestone_name": milestone_name,
            "description": description or f"Milestone: {milestone_name}",
            "milestone_timestamp": datetime.now().isoformat()
        }
        
        checkpoint = CheckpointFactory.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=CheckpointType.MILESTONE,
            metadata=metadata
        )
        
        # 里程碑检查点保留7天
        checkpoint.set_expiration(168)
        
        return checkpoint
    
    @staticmethod
    def create_from_state(
        state: Dict[str, Any],
        config: Dict[str, Any],
        source: Optional[str] = None,
        step: Optional[int] = None
    ) -> CheckpointTuple:
        """从状态数据创建检查点
        
        Args:
            state: 状态数据
            config: 运行配置
            source: 检查点来源
            step: 检查点步数
            
        Returns:
            检查点元组
        """
        # 提取线程ID
        thread_id = CheckpointFactory.extract_thread_id(config)
        
        # 创建检查点
        checkpoint = Checkpoint(
            thread_id=thread_id,
            state_data=state,
            checkpoint_type=CheckpointType.AUTO,
            channel_values=state
        )
        
        # 创建元数据
        metadata = CheckpointMetadata(
            source=source,
            step=step,
            thread_id=thread_id,
            created_at=datetime.now()
        )
        checkpoint.metadata = metadata
        
        # 创建元组
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata
        )