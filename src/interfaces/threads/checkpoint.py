"""
Thread检查点相关接口定义

定义Thread检查点的存储、管理、序列化和策略接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Generic, TypeVar
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime

from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointType

V = TypeVar("V", int, float, str)


class IThreadCheckpointStorage(Generic[V], ABC):
    """Thread检查点存储接口
    
    整合了原有的IThreadCheckpointStorage和ICheckpointSaver功能，
    提供统一的检查点存储和管理接口。
    """
    
    # === 原有IThreadCheckpointStorage接口方法 ===
    
    @abstractmethod
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存Thread检查点
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """根据ID查找检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点实体，不存在返回None
        """
        pass
    
    @abstractmethod
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            最新检查点，不存在返回None
        """
        pass
    
    @abstractmethod
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量
        
        Args:
            thread_id: 线程ID
            
        Returns:
            检查点数量
        """
        pass
    
    # === 原有ICheckpointSaver接口方法 ===
    
    @abstractmethod
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        pass
    
    @abstractmethod
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点元组，如果未找到则为None
        """
        pass
    
    @abstractmethod
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """列出匹配给定条件的检查点
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            匹配的检查点元组的迭代器
        """
        pass
    
    @abstractmethod
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, V],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点
        
        Args:
            config: 检查点的配置
            checkpoint: 要存储的检查点
            metadata: 检查点的额外元数据
            new_versions: 作为此写入的新通道版本
            
        Returns:
            存储检查点后更新的配置
        """
        pass
    
    @abstractmethod
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        pass
    
    # === 异步方法 ===
    
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步获取检查点
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        return self.get(config)
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步获取检查点元组
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点元组，如果未找到则为None
        """
        return self.get_tuple(config)
    
    async def alist(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步列出匹配给定条件的检查点
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            匹配的检查点元组的异步迭代器
        """
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item
    
    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, V],
    ) -> Dict[str, Any]:
        """异步存储检查点
        
        Args:
            config: 检查点的配置
            checkpoint: 要存储的检查点
            metadata: 检查点的额外元数据
            new_versions: 作为此写入的新通道版本
            
        Returns:
            存储检查点后更新的配置
        """
        return self.put(config, checkpoint, metadata, new_versions)
    
    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """异步存储中间写入
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        self.put_writes(config, writes, task_id, task_path)
    
    def get_next_version(self, current: Optional[V], channel: None) -> V:
        """生成通道的下一个版本ID
        
        默认使用整数版本，每次递增1。如果覆盖，可以使用str/int/float版本，
        只要它们是单调递增的。
        
        Args:
            current: 通道的当前版本标识符(int、float或str)
            channel: 已弃用的参数，为向后兼容保留
            
        Returns:
            V: 下一个版本标识符，必须是递增的
        """
        if isinstance(current, str):
            raise NotImplementedError
        elif current is None:
            return 1  # type: ignore
        else:
            return current + 1


class IThreadCheckpointManager(ABC):
    """Thread检查点管理器接口"""
    
    @abstractmethod
    async def create_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThreadCheckpoint:
        """创建Thread检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            
        Returns:
            创建的检查点
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """从检查点恢复
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态数据
        """
        pass
    
    @abstractmethod
    async def get_thread_checkpoint_history(
        self,
        thread_id: str,
        limit: int = 50
    ) -> List[ThreadCheckpoint]:
        """获取Thread的检查点历史
        
        Args:
            thread_id: 线程ID
            limit: 返回数量限制
            
        Returns:
            检查点历史列表
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_statistics(self, thread_id: str) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Args:
            thread_id: 线程ID
            
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_checkpoints(self, thread_id: str) -> int:
        """清理过期检查点
        
        Args:
            thread_id: 线程ID
            
        Returns:
            清理的检查点数量
        """
        pass


class IThreadCheckpointSerializer(ABC):
    """Thread检查点序列化接口"""
    
    @abstractmethod
    def serialize(self, checkpoint: ThreadCheckpoint) -> bytes:
        """序列化检查点
        
        Args:
            checkpoint: 检查点实体
            
        Returns:
            序列化后的字节数据
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes) -> ThreadCheckpoint:
        """反序列化检查点
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            检查点实体
        """
        pass
    
    @abstractmethod
    def serialize_state(self, state: Dict[str, Any]) -> bytes:
        """序列化状态数据
        
        Args:
            state: 状态数据
            
        Returns:
            序列化后的字节数据
        """
        pass
    
    @abstractmethod
    def deserialize_state(self, data: bytes) -> Dict[str, Any]:
        """反序列化状态数据
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            状态数据
        """
        pass


class IThreadCheckpointPolicy(ABC):
    """Thread检查点策略接口"""
    
    @abstractmethod
    def should_save_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """判断是否应该保存检查点
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            context: 上下文信息
            
        Returns:
            是否应该保存
        """
        pass
    
    @abstractmethod
    def get_checkpoint_metadata(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取检查点元数据
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            context: 上下文信息
            
        Returns:
            检查点元数据
        """
        pass
    
    @abstractmethod
    def should_cleanup_checkpoint(
        self,
        checkpoint: ThreadCheckpoint,
        context: Dict[str, Any]
    ) -> bool:
        """判断是否应该清理检查点
        
        Args:
            checkpoint: 检查点实体
            context: 上下文信息
            
        Returns:
            是否应该清理
        """
        pass
    
    @abstractmethod
    def get_checkpoint_ttl(
        self,
        checkpoint_type: CheckpointType,
        context: Dict[str, Any]
    ) -> int:
        """获取检查点生存时间（小时）
        
        Args:
            checkpoint_type: 检查点类型
            context: 上下文信息
            
        Returns:
            生存时间（小时）
        """
        pass
    
    @abstractmethod
    def get_max_checkpoints_per_thread(
        self,
        thread_id: str,
        context: Dict[str, Any]
    ) -> int:
        """获取每个线程的最大检查点数量
        
        Args:
            thread_id: 线程ID
            context: 上下文信息
            
        Returns:
            最大检查点数量
        """
        pass


# === 检查点异常定义 ===

class CheckpointError(Exception):
    """检查点基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化异常
        
        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """返回异常字符串表示"""
        if self.details:
            return f"{self.message} (详情: {self.details})"
        return self.message


class CheckpointValidationError(CheckpointError):
    """检查点验证错误
    
    当检查点数据验证失败时抛出。
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        """初始化验证错误
        
        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 验证失败的值
        """
        details = {}
        if field is not None:
            details["field"] = field
        if value is not None:
            details["value"] = value
        
        super().__init__(message, details)
        self.field = field
        self.value = value


class CheckpointNotFoundError(CheckpointError):
    """检查点未找到错误
    
    当请求的检查点不存在时抛出。
    """
    
    def __init__(self, checkpoint_id: str, thread_id: Optional[str] = None):
        """初始化未找到错误
        
        Args:
            checkpoint_id: 检查点ID
            thread_id: 线程ID（可选）
        """
        message = f"检查点未找到: {checkpoint_id}"
        details = {"checkpoint_id": checkpoint_id}
        
        if thread_id:
            details["thread_id"] = thread_id
            message += f" (线程: {thread_id})"
        
        super().__init__(message, details)
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id


class CheckpointStorageError(CheckpointError):
    """检查点存储错误
    
    当存储操作失败时抛出。
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, storage_type: Optional[str] = None):
        """初始化存储错误
        
        Args:
            message: 错误消息
            operation: 失败的操作类型
            storage_type: 存储类型
        """
        details = {}
        if operation:
            details["operation"] = operation
        if storage_type:
            details["storage_type"] = storage_type
        
        super().__init__(message, details)
        self.operation = operation
        self.storage_type = storage_type


class CheckpointConflictError(CheckpointError):
    """检查点冲突错误
    
    当检查点操作发生冲突时抛出（如并发修改）。
    """
    
    def __init__(self, message: str, checkpoint_id: str, conflict_type: Optional[str] = None):
        """初始化冲突错误
        
        Args:
            message: 错误消息
            checkpoint_id: 检查点ID
            conflict_type: 冲突类型
        """
        details = {"checkpoint_id": checkpoint_id}
        if conflict_type:
            details["conflict_type"] = conflict_type
        
        super().__init__(message, details)
        self.checkpoint_id = checkpoint_id
        self.conflict_type = conflict_type


class CheckpointTimeoutError(CheckpointError):
    """检查点超时错误
    
    当检查点操作超时时抛出。
    """
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, operation: Optional[str] = None):
        """初始化超时错误
        
        Args:
            message: 错误消息
            timeout_seconds: 超时时间（秒）
            operation: 超时的操作
        """
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class CheckpointQuotaExceededError(CheckpointError):
    """检查点配额超限错误
    
    当检查点数量或大小超过配额时抛出。
    """
    
    def __init__(self, message: str, quota_type: str, current_value: int, max_value: int):
        """初始化配额超限错误
        
        Args:
            message: 错误消息
            quota_type: 配额类型（如 "count", "size"）
            current_value: 当前值
            max_value: 最大值
        """
        details = {
            "quota_type": quota_type,
            "current_value": current_value,
            "max_value": max_value
        }
        
        super().__init__(message, details)
        self.quota_type = quota_type
        self.current_value = current_value
        self.max_value = max_value


class CheckpointCorruptionError(CheckpointError):
    """检查点损坏错误
    
    当检查点数据损坏时抛出。
    """
    
    def __init__(self, message: str, checkpoint_id: str, corruption_details: Optional[str] = None):
        """初始化损坏错误
        
        Args:
            message: 错误消息
            checkpoint_id: 检查点ID
            corruption_details: 损坏详情
        """
        details = {"checkpoint_id": checkpoint_id}
        if corruption_details:
            details["corruption_details"] = corruption_details
        
        super().__init__(message, details)
        self.checkpoint_id = checkpoint_id
        self.corruption_details = corruption_details


class CheckpointVersionError(CheckpointError):
    """检查点版本错误
    
    当检查点版本不兼容时抛出。
    """
    
    def __init__(self, message: str, expected_version: Optional[str] = None, actual_version: Optional[str] = None):
        """初始化版本错误
        
        Args:
            message: 错误消息
            expected_version: 期望的版本
            actual_version: 实际的版本
        """
        details = {}
        if expected_version:
            details["expected_version"] = expected_version
        if actual_version:
            details["actual_version"] = actual_version
        
        super().__init__(message, details)
        self.expected_version = expected_version
        self.actual_version = actual_version


class CheckpointConfigurationError(CheckpointError):
    """检查点配置错误
    
    当检查点配置无效时抛出。
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        """初始化配置错误
        
        Args:
            message: 错误消息
            config_key: 配置键
            config_value: 配置值
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value
        
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class CheckpointHookError(CheckpointError):
    """检查点Hook错误
    
    当检查点Hook执行失败时抛出。
    """
    
    def __init__(self, message: str, hook_name: Optional[str] = None, hook_type: Optional[str] = None):
        """初始化Hook错误
        
        Args:
            message: 错误消息
            hook_name: Hook名称
            hook_type: Hook类型（如 "before_save", "after_load"）
        """
        details = {}
        if hook_name:
            details["hook_name"] = hook_name
        if hook_type:
            details["hook_type"] = hook_type
        
        super().__init__(message, details)
        self.hook_name = hook_name
        self.hook_type = hook_type


class CheckpointCacheError(CheckpointError):
    """检查点缓存错误
    
    当检查点缓存操作失败时抛出。
    """
    
    def __init__(self, message: str, cache_operation: Optional[str] = None, cache_key: Optional[str] = None):
        """初始化缓存错误
        
        Args:
            message: 错误消息
            cache_operation: 缓存操作类型
            cache_key: 缓存键
        """
        details = {}
        if cache_operation:
            details["cache_operation"] = cache_operation
        if cache_key:
            details["cache_key"] = cache_key
        
        super().__init__(message, details)
        self.cache_operation = cache_operation
        self.cache_key = cache_key


class CheckpointResourceError(CheckpointError):
    """检查点资源错误
     
    当检查点资源不足时抛出。
    """
     
    def __init__(self, message: str, resource_type: str, required_amount: Optional[int] = None, available_amount: Optional[int] = None):
        """初始化资源错误
         
        Args:
            message: 错误消息
            resource_type: 资源类型（如 "memory", "disk"）
            required_amount: 需要的资源量
            available_amount: 可用的资源量
        """
        details: Dict[str, Any] = {"resource_type": resource_type}
        if required_amount is not None:
            details["required_amount"] = required_amount
        if available_amount is not None:
            details["available_amount"] = available_amount
        
        super().__init__(message, details)
        self.resource_type = resource_type
        self.required_amount = required_amount
        self.available_amount = available_amount