# Checkpoint模块接口规范

## 概述

本文档定义了checkpoint模块重构后的统一接口规范，包括Session层、Thread层和基础设施层的接口定义，以及它们之间的交互协议。

## 架构层次

### 三层架构结构

```
┌─────────────────────────────────────────────────────────────┐
│                        Session层                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           SessionCheckpointManager                  │    │
│  │  - 制定全局checkpoint策略                            │    │
│  │  - 协调多Thread的checkpoint操作                     │    │
│  │  - 监控checkpoint使用情况                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Thread层                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           ThreadCheckpointService                   │    │
│  │  - 实现Thread特定的业务逻辑                          │    │
│  │  - 管理checkpoint的生命周期                         │    │
│  │  - 处理checkpoint的错误和异常                       │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           CheckpointAdapter                         │    │
│  │  - 连接Thread特定和通用checkpoint                   │    │
│  │  - 提供统一的接口给上层调用者                       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           CheckpointRepository                      │    │
│  │  - 提供统一的存储抽象                               │    │
│  │  - 实现具体的存储后端                               │    │
│  │  - 处理数据的持久化和检索                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Session层接口

### ISessionCheckpointManager

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class ISessionCheckpointManager(ABC):
    """Session检查点管理器接口
    
    负责Session级别的checkpoint策略制定和协调。
    """
    
    @abstractmethod
    async def set_global_checkpoint_policy(
        self,
        session_id: str,
        policy: Dict[str, Any]
    ) -> None:
        """设置全局checkpoint策略
        
        Args:
            session_id: Session ID
            policy: 策略配置
        """
        pass
    
    @abstractmethod
    async def get_global_checkpoint_policy(self, session_id: str) -> Dict[str, Any]:
        """获取全局checkpoint策略
        
        Args:
            session_id: Session ID
            
        Returns:
            策略配置
        """
        pass
    
    @abstractmethod
    async def coordinate_thread_checkpoints(
        self,
        session_id: str,
        thread_ids: List[str],
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """协调多Thread的checkpoint操作
        
        Args:
            session_id: Session ID
            thread_ids: Thread ID列表
            operation: 操作类型
            **kwargs: 操作参数
            
        Returns:
            操作结果
        """
        pass
    
    @abstractmethod
    async def monitor_checkpoint_usage(self, session_id: str) -> Dict[str, Any]:
        """监控checkpoint使用情况
        
        Args:
            session_id: Session ID
            
        Returns:
            使用情况统计
        """
        pass
    
    @abstractmethod
    async def cleanup_session_checkpoints(
        self,
        session_id: str,
        cleanup_policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """清理Session级别的checkpoint
        
        Args:
            session_id: Session ID
            cleanup_policy: 清理策略
            
        Returns:
            清理结果统计
        """
        pass
    
    @abstractmethod
    async def get_session_checkpoint_statistics(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """获取Session级别的checkpoint统计信息
        
        Args:
            session_id: Session ID
            
        Returns:
            统计信息
        """
        pass
```

## Thread层接口

### IThreadCheckpointService

```python
class IThreadCheckpointService(ABC):
    """Thread检查点服务接口
    
    提供Thread特定的checkpoint业务逻辑。
    """
    
    @abstractmethod
    async def create_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> str:
        """创建Thread检查点
        
        Args:
            thread_id: Thread ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            expiration_hours: 过期小时数
            
        Returns:
            检查点ID
        """
        pass
    
    @abstractmethod
    async def restore_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """从检查点恢复
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态数据
        """
        pass
    
    @abstractmethod
    async def list_checkpoints(
        self,
        thread_id: str,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[ThreadCheckpoint]:
        """列出Thread的检查点
        
        Args:
            thread_id: Thread ID
            filter: 过滤条件
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """删除Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_statistics(
        self,
        thread_id: str
    ) -> CheckpointStatistics:
        """获取Thread检查点统计信息
        
        Args:
            thread_id: Thread ID
            
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    async def cleanup_checkpoints(
        self,
        thread_id: str,
        cleanup_policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """清理Thread检查点
        
        Args:
            thread_id: Thread ID
            cleanup_policy: 清理策略
            
        Returns:
            清理结果统计
        """
        pass
```

### ICheckpointAdapter

```python
class ICheckpointAdapter(ABC):
    """Checkpoint适配器接口
    
    提供Thread特定checkpoint和通用checkpoint之间的适配。
    """
    
    @abstractmethod
    def adapt_thread_checkpoint_to_checkpoint(
        self,
        thread_checkpoint: ThreadCheckpoint
    ) -> Checkpoint:
        """将Thread检查点适配为通用检查点
        
        Args:
            thread_checkpoint: Thread检查点
            
        Returns:
            通用检查点
        """
        pass
    
    @abstractmethod
    def adapt_checkpoint_to_thread_checkpoint(
        self,
        checkpoint: Checkpoint,
        thread_id: str
    ) -> ThreadCheckpoint:
        """将通用检查点适配为Thread检查点
        
        Args:
            checkpoint: 通用检查点
            thread_id: Thread ID
            
        Returns:
            Thread检查点
        """
        pass
    
    @abstractmethod
    def adapt_config_to_thread_context(
        self,
        config: Dict[str, Any]
    ) -> ThreadContext:
        """将配置适配为Thread上下文
        
        Args:
            config: 通用配置
            
        Returns:
            Thread上下文
        """
        pass
```

## 基础设施层接口

### ICheckpointRepository

```python
class ICheckpointRepository(ABC):
    """Checkpoint仓储接口
    
    提供统一的checkpoint存储抽象。
    """
    
    @abstractmethod
    async def save_checkpoint(
        self,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """保存检查点
        
        Args:
            checkpoint_data: 检查点数据
            
        Returns:
            检查点ID
        """
        pass
    
    @abstractmethod
    async def load_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点数据
        """
        pass
    
    @abstractmethod
    async def list_checkpoints(
        self,
        thread_id: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出检查点
        
        Args:
            thread_id: Thread ID
            filter: 过滤条件
            limit: 限制数量
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(
        self,
        checkpoint_id: str
    ) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Args:
            thread_id: Thread ID
            
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(
        self,
        thread_id: Optional[str] = None,
        max_count: Optional[int] = None
    ) -> int:
        """清理旧检查点
        
        Args:
            thread_id: Thread ID
            max_count: 最大保留数量
            
        Returns:
            清理数量
        """
        pass
```

### ICheckpointCache

```python
class ICheckpointCache(ABC):
    """Checkpoint缓存接口
    
    提供checkpoint缓存功能。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息
        """
        pass
```

## 数据模型

### ThreadContext

```python
@dataclass
class ThreadContext:
    """Thread上下文
    
    包含Thread相关的上下文信息。
    """
    thread_id: str
    session_id: Optional[str] = None
    checkpoint_ns: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_config(self) -> Dict[str, Any]:
        """转换为配置字典
        
        Returns:
            配置字典
        """
        return {
            "configurable": {
                "thread_id": self.thread_id,
                "checkpoint_ns": self.checkpoint_ns,
                "session_id": self.session_id
            }
        }
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ThreadContext":
        """从配置字典创建
        
        Args:
            config: 配置字典
            
        Returns:
            Thread上下文
        """
        configurable = config.get("configurable", {})
        return cls(
            thread_id=configurable.get("thread_id", ""),
            session_id=configurable.get("session_id"),
            checkpoint_ns=configurable.get("checkpoint_ns", "default"),
            metadata=config.get("metadata", {})
        )
```

### CheckpointPolicy

```python
@dataclass
class CheckpointPolicy:
    """检查点策略
    
    定义checkpoint的策略配置。
    """
    max_checkpoints_per_thread: int = 100
    default_expiration_hours: int = 24
    auto_save_enabled: bool = True
    backup_enabled: bool = True
    cleanup_enabled: bool = True
    cleanup_interval_hours: int = 6
    
    # 类型特定策略
    manual_expiration_hours: Optional[int] = None  # 永不过期
    auto_expiration_hours: int = 24
    error_expiration_hours: int = 72
    milestone_expiration_hours: int = 168
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            策略字典
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointPolicy":
        """从字典创建
        
        Args:
            data: 策略字典
            
        Returns:
            检查点策略
        """
        return cls(**data)
```

## 交互协议

### Session-Thread交互协议

```python
class SessionThreadProtocol:
    """Session-Thread交互协议
    
    定义Session和Thread之间的交互协议。
    """
    
    # 操作类型
    OPERATION_CREATE_CHECKPOINT = "create_checkpoint"
    OPERATION_RESTORE_CHECKPOINT = "restore_checkpoint"
    OPERATION_DELETE_CHECKPOINT = "delete_checkpoint"
    OPERATION_CLEANUP_CHECKPOINTS = "cleanup_checkpoints"
    OPERATION_LIST_CHECKPOINTS = "list_checkpoints"
    
    # 状态码
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_PARTIAL_SUCCESS = "partial_success"
    
    @staticmethod
    def create_operation_request(
        operation: str,
        thread_ids: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """创建操作请求
        
        Args:
            operation: 操作类型
            thread_ids: Thread ID列表
            **kwargs: 操作参数
            
        Returns:
            操作请求
        """
        return {
            "operation": operation,
            "thread_ids": thread_ids,
            "parameters": kwargs,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_operation_response(
        operation: str,
        results: Dict[str, Any],
        status: str = STATUS_SUCCESS,
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建操作响应
        
        Args:
            operation: 操作类型
            results: 操作结果
            status: 状态码
            errors: 错误列表
            
        Returns:
            操作响应
        """
        return {
            "operation": operation,
            "status": status,
            "results": results,
            "errors": errors or [],
            "timestamp": datetime.now().isoformat()
        }
```

### Thread-Storage交互协议

```python
class ThreadStorageProtocol:
    """Thread-Storage交互协议
    
    定义Thread和Storage之间的交互协议。
    """
    
    # 存储操作类型
    STORAGE_SAVE = "save"
    STORAGE_LOAD = "load"
    STORAGE_LIST = "list"
    STORAGE_DELETE = "delete"
    STORAGE_CLEANUP = "cleanup"
    
    # 数据格式
    DATA_FORMAT_THREAD_CHECKPOINT = "thread_checkpoint"
    DATA_FORMAT_GENERIC_CHECKPOINT = "generic_checkpoint"
    
    @staticmethod
    def create_storage_request(
        operation: str,
        data_format: str,
        **kwargs
    ) -> Dict[str, Any]:
        """创建存储请求
        
        Args:
            operation: 存储操作类型
            data_format: 数据格式
            **kwargs: 操作参数
            
        Returns:
            存储请求
        """
        return {
            "operation": operation,
            "data_format": data_format,
            "parameters": kwargs,
            "timestamp": datetime.now().isoformat()
        }
```

## 错误处理

### 异常层次结构

```python
class CheckpointError(Exception):
    """Checkpoint基础异常"""
    pass

class CheckpointValidationError(CheckpointError):
    """Checkpoint验证异常"""
    pass

class CheckpointNotFoundError(CheckpointError):
    """Checkpoint未找到异常"""
    pass

class CheckpointStorageError(CheckpointError):
    """Checkpoint存储异常"""
    pass

class CheckpointAdapterError(CheckpointError):
    """Checkpoint适配器异常"""
    pass

class ThreadCheckpointError(CheckpointError):
    """Thread检查点异常"""
    pass

class SessionCheckpointError(CheckpointError):
    """Session检查点异常"""
    pass
```

## 配置规范

### Checkpoint配置

```yaml
# checkpoint配置示例
checkpoint:
  # 全局策略
  global_policy:
    max_checkpoints_per_thread: 100
    default_expiration_hours: 24
    auto_save_enabled: true
    backup_enabled: true
    cleanup_enabled: true
    cleanup_interval_hours: 6
  
  # 存储配置
  storage:
    type: "sqlite"  # memory, file, sqlite
    connection_string: "sqlite:///checkpoints.db"
    cache_enabled: true
    cache_size: 100
    cache_ttl: 3600
  
  # Thread特定配置
  thread:
    types:
      manual:
        expiration_hours: null  # 永不过期
      auto:
        expiration_hours: 24
      error:
        expiration_hours: 72
      milestone:
        expiration_hours: 168
    
    limits:
      max_size_mb: 100
      max_checkpoints: 100
      cleanup_threshold: 50
  
  # Session配置
  session:
    coordination_enabled: true
    monitoring_enabled: true
    statistics_enabled: true
    cleanup_policy:
      enabled: true
      interval_hours: 24
      retention_days: 30
```

## 总结

本接口规范定义了checkpoint模块重构后的统一接口，包括：

1. **分层接口**: Session层、Thread层和基础设施层的清晰接口定义
2. **交互协议**: 层与层之间的标准化交互协议
3. **数据模型**: 统一的数据模型和上下文定义
4. **错误处理**: 完整的异常层次结构
5. **配置规范**: 标准化的配置格式

这些接口和规范为checkpoint模块的重构提供了清晰的指导，确保重构后的系统具有良好的可维护性和扩展性。