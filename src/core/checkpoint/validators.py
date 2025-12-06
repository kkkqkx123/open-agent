"""
检查点验证器

提供检查点数据的验证功能，确保数据的完整性和正确性。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .models import Checkpoint, CheckpointMetadata, CheckpointTuple


class CheckpointValidationError(Exception):
    """检查点验证错误"""
    pass


class CheckpointValidator:
    """检查点验证器
    
    提供各种检查点相关数据的验证功能。
    """
    
    @staticmethod
    def validate_checkpoint(checkpoint: Checkpoint) -> None:
        """验证检查点
        
        Args:
            checkpoint: 检查点实例
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not checkpoint.id:
            raise CheckpointValidationError("检查点ID不能为空")
        
        if not isinstance(checkpoint.id, str):
            raise CheckpointValidationError("检查点ID必须是字符串")
        
        if not checkpoint.ts:
            raise CheckpointValidationError("检查点时间戳不能为空")
        
        # 验证时间戳格式
        try:
            datetime.fromisoformat(checkpoint.ts)
        except ValueError as e:
            raise CheckpointValidationError(f"无效的时间戳格式: {e}")
        
        # 验证通道值
        if not isinstance(checkpoint.channel_values, dict):
            raise CheckpointValidationError("通道值必须是字典")
        
        # 验证通道版本
        if not isinstance(checkpoint.channel_versions, dict):
            raise CheckpointValidationError("通道版本必须是字典")
        
        # 验证版本 seen
        if not isinstance(checkpoint.versions_seen, dict):
            raise CheckpointValidationError("版本 seen 必须是字典")
    
    @staticmethod
    def validate_metadata(metadata: CheckpointMetadata) -> None:
        """验证检查点元数据
        
        Args:
            metadata: 检查点元数据实例
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        # 验证步数
        if metadata.step is not None and not isinstance(metadata.step, int):
            raise CheckpointValidationError("检查点步数必须是整数")
        
        if metadata.step is not None and metadata.step < 0:
            raise CheckpointValidationError("检查点步数不能为负数")
        
        # 验证父检查点映射
        if metadata.parents is not None:
            if not isinstance(metadata.parents, dict):
                raise CheckpointValidationError("父检查点映射必须是字典")
            
            for key, value in metadata.parents.items():
                if not isinstance(key, str):
                    raise CheckpointValidationError("父检查点映射的键必须是字符串")
                if not isinstance(value, str):
                    raise CheckpointValidationError("父检查点映射的值必须是字符串")
        
        # 验证创建时间
        if metadata.created_at is not None and not isinstance(metadata.created_at, datetime):
            raise CheckpointValidationError("创建时间必须是datetime对象")
    
    @staticmethod
    def validate_tuple(checkpoint_tuple: CheckpointTuple) -> None:
        """验证检查点元组
        
        Args:
            checkpoint_tuple: 检查点元组实例
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        # 验证配置
        CheckpointValidator._validate_config(checkpoint_tuple.config)
        
        # 验证检查点
        CheckpointValidator.validate_checkpoint(checkpoint_tuple.checkpoint)
        
        # 验证元数据
        CheckpointValidator.validate_metadata(checkpoint_tuple.metadata)
        
        # 验证父配置
        if checkpoint_tuple.parent_config is not None:
            CheckpointValidator._validate_config(checkpoint_tuple.parent_config)
        
        # 验证待写入数据
        if checkpoint_tuple.pending_writes is not None:
            if not isinstance(checkpoint_tuple.pending_writes, list):
                raise CheckpointValidationError("待写入数据必须是列表")
            
            for write in checkpoint_tuple.pending_writes:
                if not isinstance(write, (tuple, list)) or len(write) != 2:
                    raise CheckpointValidationError("待写入数据必须是(通道, 值)对")
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """验证配置
        
        Args:
            config: 配置字典
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(config, dict):
            raise CheckpointValidationError("配置必须是字典")
        
        if "configurable" not in config:
            raise CheckpointValidationError("配置必须包含configurable字段")
        
        if not isinstance(config["configurable"], dict):
            raise CheckpointValidationError("configurable字段必须是字典")
        
        configurable = config["configurable"]
        
        # 验证线程ID
        if "thread_id" not in configurable:
            raise CheckpointValidationError("配置必须包含thread_id")
        
        if not isinstance(configurable["thread_id"], str):
            raise CheckpointValidationError("thread_id必须是字符串")
        
        # 验证检查点命名空间
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        if not isinstance(checkpoint_ns, str):
            raise CheckpointValidationError("checkpoint_ns必须是字符串")
        
        # 验证检查点ID
        checkpoint_id = configurable.get("checkpoint_id")
        if checkpoint_id is not None and not isinstance(checkpoint_id, str):
            raise CheckpointValidationError("checkpoint_id必须是字符串")
    
    @staticmethod
    def validate_channel_data(channel_values: Dict[str, Any]) -> None:
        """验证通道数据
        
        Args:
            channel_values: 通道值字典
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(channel_values, dict):
            raise CheckpointValidationError("通道值必须是字典")
        
        for key, value in channel_values.items():
            if not isinstance(key, str):
                raise CheckpointValidationError("通道名称必须是字符串")
    
    @staticmethod
    def validate_version_data(channel_versions: Dict[str, Any]) -> None:
        """验证版本数据
        
        Args:
            channel_versions: 通道版本字典
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(channel_versions, dict):
            raise CheckpointValidationError("通道版本必须是字典")
        
        for key, value in channel_versions.items():
            if not isinstance(key, str):
                raise CheckpointValidationError("通道名称必须是字符串")
            
            if not isinstance(value, (int, float, str)):
                raise CheckpointValidationError("版本值必须是数字或字符串")
    
    @staticmethod
    def validate_write_data(writes: List[tuple[str, Any]]) -> None:
        """验证写入数据
        
        Args:
            writes: 写入数据列表
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(writes, list):
            raise CheckpointValidationError("写入数据必须是列表")
        
        for write in writes:
            if not isinstance(write, (tuple, list)) or len(write) != 2:
                raise CheckpointValidationError("写入数据必须是(通道, 值)对")
            
            channel, value = write
            if not isinstance(channel, str):
                raise CheckpointValidationError("通道名称必须是字符串")
    
    @staticmethod
    def validate_checkpoint_id(checkpoint_id: str) -> None:
        """验证检查点ID
        
        Args:
            checkpoint_id: 检查点ID
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(checkpoint_id, str):
            raise CheckpointValidationError("检查点ID必须是字符串")
        
        if not checkpoint_id.strip():
            raise CheckpointValidationError("检查点ID不能为空")
    
    @staticmethod
    def validate_thread_id(thread_id: str) -> None:
        """验证线程ID
        
        Args:
            thread_id: 线程ID
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(thread_id, str):
            raise CheckpointValidationError("线程ID必须是字符串")
        
        if not thread_id.strip():
            raise CheckpointValidationError("线程ID不能为空")
    
    @staticmethod
    def validate_checkpoint_ns(checkpoint_ns: str) -> None:
        """验证检查点命名空间
        
        Args:
            checkpoint_ns: 检查点命名空间
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(checkpoint_ns, str):
            raise CheckpointValidationError("检查点命名空间必须是字符串")
    
    @staticmethod
    def validate_filter_conditions(filters: Dict[str, Any]) -> None:
        """验证过滤条件
        
        Args:
            filters: 过滤条件字典
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
        """
        if not isinstance(filters, dict):
            raise CheckpointValidationError("过滤条件必须是字典")
        
        # 可以根据需要添加更具体的验证逻辑
        pass