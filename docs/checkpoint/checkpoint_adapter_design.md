# Checkpoint适配器设计文档

## 概述

本文档设计适配器接口，用于连接通用的checkpoint基础设施和Thread特定的checkpoint业务逻辑，实现分层统一架构。

## 设计原则

### 1. 适配器模式原则
- 将一个类的接口转换成客户端希望的另外一个接口
- 使得原本由于接口不兼容而不能一起工作的那些类可以一起工作
- 保持现有代码的兼容性，同时提供新的统一接口

### 2. 分层架构原则
- 基础设施层提供通用的checkpoint抽象
- Thread层提供特定的业务逻辑扩展
- 通过适配器层连接两层实现

### 3. 渐进迁移原则
- 支持新旧接口并存
- 提供平滑的迁移路径
- 最小化对现有系统的影响

## 适配器架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)                │
├─────────────────────────────────────────────────────────────┤
│  SessionCheckpointManager  │  ThreadCheckpointService      │
├─────────────────────────────────────────────────────────────┤
│                    适配器层 (Adapter Layer)                  │
├─────────────────────────────────────────────────────────────┤
│  CheckpointServiceAdapter  │  ThreadCheckpointAdapter      │
├─────────────────────────────────────────────────────────────┤
│                    业务层 (Business Layer)                  │
├─────────────────────────────────────────────────────────────┤
│  ThreadCheckpointDomainService  │  CheckpointManager        │
├─────────────────────────────────────────────────────────────┤
│                  基础设施层 (Infrastructure Layer)           │
├─────────────────────────────────────────────────────────────┤
│  CheckpointRepository  │  ThreadCheckpointRepository       │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心适配器接口

#### 2.1 ICheckpointServiceAdapter

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from collections.abc import AsyncIterator

class ICheckpointServiceAdapter(ABC):
    """Checkpoint服务适配器接口
    
    提供统一的checkpoint服务接口，适配通用checkpoint和Thread特定checkpoint。
    """
    
    @abstractmethod
    async def save_checkpoint(
        self, 
        config: Dict[str, Any], 
        checkpoint: Dict[str, Any], 
        metadata: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存检查点
        
        Args:
            config: 可运行配置
            checkpoint: 检查点数据
            metadata: 检查点元数据
            thread_context: Thread上下文信息（可选）
            
        Returns:
            检查点ID
        """
        pass
    
    @abstractmethod
    async def load_checkpoint(
        self, 
        config: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """加载检查点
        
        Args:
            config: 可运行配置
            thread_context: Thread上下文信息（可选）
            
        Returns:
            检查点数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def load_checkpoint_tuple(
        self, 
        config: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """加载检查点元组
        
        Args:
            config: 可运行配置
            thread_context: Thread上下文信息（可选）
            
        Returns:
            检查点元组，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_checkpoints(
        self, 
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        thread_context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """列出检查点
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            thread_context: Thread上下文信息（可选）
            
        Yields:
            检查点元组的异步迭代器
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(
        self, 
        config: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """删除检查点
        
        Args:
            config: 可运行配置
            thread_context: Thread上下文信息（可选）
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(
        self, 
        max_age_days: int = 30,
        thread_context: Optional[Dict[str, Any]] = None
    ) -> int:
        """清理旧检查点
        
        Args:
            max_age_days: 最大保留天数
            thread_context: Thread上下文信息（可选）
            
        Returns:
            清理的检查点数量
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_stats(
        self,
        thread_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Args:
            thread_context: Thread上下文信息（可选）
            
        Returns:
            统计信息字典
        """
        pass
```

#### 2.2 IThreadCheckpointAdapter

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.core.threads.checkpoints.storage.models import (
    ThreadCheckpoint, 
    CheckpointType, 
    CheckpointStatus
)

class IThreadCheckpointAdapter(ABC):
    """Thread检查点适配器接口
    
    提供Thread特定的checkpoint操作接口，适配Thread业务逻辑到通用基础设施。
    """
    
    @abstractmethod
    async def create_thread_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> ThreadCheckpoint:
        """创建Thread检查点
        
        Args:
            thread_id: Thread ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            expiration_hours: 过期小时数
            
        Returns:
            创建的检查点
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_thread_checkpoint(
        self, 
        thread_id: str, 
        checkpoint_id: str
    ) -> Optional[ThreadCheckpoint]:
        """获取Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            检查点对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list_thread_checkpoints(
        self, 
        thread_id: str, 
        status: Optional[CheckpointStatus] = None
    ) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点
        
        Args:
            thread_id: Thread ID
            status: 可选的状态过滤
            
        Returns:
            检查点列表，按创建时间倒序排列
        """
        pass
    
    @abstractmethod
    async def delete_thread_checkpoint(
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
    async def get_latest_checkpoint(
        self, 
        thread_id: str
    ) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点
        
        Args:
            thread_id: Thread ID
            
        Returns:
            最新的检查点对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def cleanup_thread_checkpoints(
        self, 
        thread_id: str, 
        max_count: int
    ) -> int:
        """清理旧的检查点
        
        Args:
            thread_id: Thread ID
            max_count: 保留的最大数量
            
        Returns:
            删除的检查点数量
        """
        pass
```

### 3. 适配器实现

#### 3.1 CheckpointServiceAdapter

```python
class CheckpointServiceAdapter(ICheckpointServiceAdapter):
    """Checkpoint服务适配器实现
    
    将通用的checkpoint服务适配到Thread特定的业务逻辑。
    """
    
    def __init__(
        self,
        checkpoint_service: ICheckpointService,
        thread_checkpoint_service: Optional[IThreadCheckpointManager] = None
    ):
        """初始化适配器
        
        Args:
            checkpoint_service: 通用checkpoint服务
            thread_checkpoint_service: Thread特定checkpoint服务（可选）
        """
        self._checkpoint_service = checkpoint_service
        self._thread_checkpoint_service = thread_checkpoint_service
    
    async def save_checkpoint(
        self, 
        config: Dict[str, Any], 
        checkpoint: Dict[str, Any], 
        metadata: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存检查点
        
        根据是否有Thread上下文，选择使用Thread特定服务或通用服务。
        """
        if thread_context and self._thread_checkpoint_service:
            # 使用Thread特定服务
            thread_id = thread_context.get("thread_id")
            checkpoint_type = thread_context.get("checkpoint_type", CheckpointType.AUTO)
            expiration_hours = thread_context.get("expiration_hours")
            
            thread_checkpoint = await self._thread_checkpoint_service.create_checkpoint(
                thread_id=thread_id,
                state=checkpoint,
                checkpoint_type=checkpoint_type,
                metadata=metadata
            )
            return thread_checkpoint.id
        else:
            # 使用通用服务
            return await self._checkpoint_service.save_checkpoint(
                config, checkpoint, metadata
            )
    
    async def load_checkpoint(
        self, 
        config: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """加载检查点"""
        if thread_context and self._thread_checkpoint_service:
            # 使用Thread特定服务
            thread_id = thread_context.get("thread_id")
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            
            if checkpoint_id:
                checkpoint = await self._thread_checkpoint_service.get_checkpoint(
                    thread_id, checkpoint_id
                )
                return checkpoint.state_data if checkpoint else None
            else:
                # 获取最新检查点
                latest = await self._thread_checkpoint_service.get_latest_checkpoint(thread_id)
                return latest.state_data if latest else None
        else:
            # 使用通用服务
            return await self._checkpoint_service.load_checkpoint(config)
    
    # 其他方法实现...
```

#### 3.2 ThreadCheckpointAdapter

```python
class ThreadCheckpointAdapter(IThreadCheckpointAdapter):
    """Thread检查点适配器实现
    
    将Thread特定的checkpoint操作适配到通用的checkpoint基础设施。
    """
    
    def __init__(
        self,
        thread_checkpoint_domain_service: ThreadCheckpointDomainService,
        checkpoint_service: ICheckpointService
    ):
        """初始化适配器
        
        Args:
            thread_checkpoint_domain_service: Thread检查点领域服务
            checkpoint_service: 通用checkpoint服务
        """
        self._domain_service = thread_checkpoint_domain_service
        self._checkpoint_service = checkpoint_service
    
    async def create_thread_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> ThreadCheckpoint:
        """创建Thread检查点
        
        使用Thread领域服务创建检查点，同时保存到通用基础设施。
        """
        # 1. 使用Thread领域服务创建检查点
        thread_checkpoint = await self._domain_service.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            metadata=metadata,
            expiration_hours=expiration_hours
        )
        
        # 2. 同时保存到通用基础设施（用于兼容性）
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "thread",
                "checkpoint_id": thread_checkpoint.id
            }
        }
        
        await self._checkpoint_service.save_checkpoint(
            config=config,
            checkpoint=state_data,
            metadata=thread_checkpoint.metadata
        )
        
        return thread_checkpoint
    
    async def restore_from_checkpoint(
        self, 
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """从检查点恢复"""
        return await self._domain_service.restore_from_checkpoint(checkpoint_id)
    
    # 其他方法实现...
```

### 4. 存储适配器

#### 4.1 ICheckpointStorageAdapter

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class ICheckpointStorageAdapter(ABC):
    """Checkpoint存储适配器接口
    
    提供统一的存储接口，适配通用存储和Thread特定存储。
    """
    
    @abstractmethod
    async def save_checkpoint_data(
        self, 
        checkpoint_id: str, 
        data: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存检查点数据
        
        Args:
            checkpoint_id: 检查点ID
            data: 检查点数据
            thread_context: Thread上下文信息（可选）
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load_checkpoint_data(
        self, 
        checkpoint_id: str,
        thread_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """加载检查点数据
        
        Args:
            checkpoint_id: 检查点ID
            thread_context: Thread上下文信息（可选）
            
        Returns:
            检查点数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint_data(
        self, 
        checkpoint_id: str,
        thread_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """删除检查点数据
        
        Args:
            checkpoint_id: 检查点ID
            thread_context: Thread上下文信息（可选）
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_checkpoint_data(
        self,
        thread_context: Optional[Dict[str, Any]] = None,
        filter: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出检查点数据
        
        Args:
            thread_context: Thread上下文信息（可选）
            filter: 过滤条件
            limit: 返回数量限制
            
        Returns:
            检查点数据列表
        """
        pass
```

#### 4.2 CheckpointStorageAdapter

```python
class CheckpointStorageAdapter(ICheckpointStorageAdapter):
    """Checkpoint存储适配器实现
    
    将通用存储和Thread特定存储适配到统一接口。
    """
    
    def __init__(
        self,
        checkpoint_repository: ICheckpointRepository,
        thread_checkpoint_repository: IThreadCheckpointRepository
    ):
        """初始化存储适配器
        
        Args:
            checkpoint_repository: 通用checkpoint仓储
            thread_checkpoint_repository: Thread特定checkpoint仓储
        """
        self._checkpoint_repository = checkpoint_repository
        self._thread_checkpoint_repository = thread_checkpoint_repository
    
    async def save_checkpoint_data(
        self, 
        checkpoint_id: str, 
        data: Dict[str, Any],
        thread_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存检查点数据"""
        if thread_context:
            # 保存到Thread特定存储
            thread_id = thread_context.get("thread_id")
            # 创建ThreadCheckpoint对象并保存
            # ...
            return True
        else:
            # 保存到通用存储
            return await self._checkpoint_repository.save_checkpoint(data)
    
    # 其他方法实现...
```

## 适配器工厂

### 1. ICheckpointAdapterFactory

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class ICheckpointAdapterFactory(ABC):
    """Checkpoint适配器工厂接口"""
    
    @abstractmethod
    def create_service_adapter(
        self, 
        config: Dict[str, Any]
    ) -> ICheckpointServiceAdapter:
        """创建服务适配器"""
        pass
    
    @abstractmethod
    def create_thread_adapter(
        self, 
        config: Dict[str, Any]
    ) -> IThreadCheckpointAdapter:
        """创建Thread适配器"""
        pass
    
    @abstractmethod
    def create_storage_adapter(
        self, 
        config: Dict[str, Any]
    ) -> ICheckpointStorageAdapter:
        """创建存储适配器"""
        pass
```

### 2. CheckpointAdapterFactory

```python
class CheckpointAdapterFactory(ICheckpointAdapterFactory):
    """Checkpoint适配器工厂实现"""
    
    def __init__(
        self,
        checkpoint_service: ICheckpointService,
        thread_checkpoint_service: IThreadCheckpointManager,
        checkpoint_repository: ICheckpointRepository,
        thread_checkpoint_repository: IThreadCheckpointRepository
    ):
        """初始化工厂"""
        self._checkpoint_service = checkpoint_service
        self._thread_checkpoint_service = thread_checkpoint_service
        self._checkpoint_repository = checkpoint_repository
        self._thread_checkpoint_repository = thread_checkpoint_repository
    
    def create_service_adapter(
        self, 
        config: Dict[str, Any]
    ) -> ICheckpointServiceAdapter:
        """创建服务适配器"""
        return CheckpointServiceAdapter(
            checkpoint_service=self._checkpoint_service,
            thread_checkpoint_service=self._thread_checkpoint_service
        )
    
    def create_thread_adapter(
        self, 
        config: Dict[str, Any]
    ) -> IThreadCheckpointAdapter:
        """创建Thread适配器"""
        return ThreadCheckpointAdapter(
            thread_checkpoint_domain_service=self._thread_checkpoint_service,
            checkpoint_service=self._checkpoint_service
        )
    
    def create_storage_adapter(
        self, 
        config: Dict[str, Any]
    ) -> ICheckpointStorageAdapter:
        """创建存储适配器"""
        return CheckpointStorageAdapter(
            checkpoint_repository=self._checkpoint_repository,
            thread_checkpoint_repository=self._thread_checkpoint_repository
        )
```

## 迁移策略

### 1. 渐进式迁移

#### 阶段1：适配器实现
- 实现所有适配器接口
- 保持现有接口不变
- 新增适配器层

#### 阶段2：逐步替换
- 新代码使用适配器接口
- 现有代码逐步迁移
- 提供兼容性包装

#### 阶段3：完全迁移
- 移除旧接口
- 统一使用适配器接口
- 清理冗余代码

### 2. 兼容性保证

#### 接口兼容
- 保留现有接口作为适配器的包装
- 提供废弃警告
- 逐步引导使用新接口

#### 数据兼容
- 支持新旧数据格式
- 提供数据迁移工具
- 保证数据完整性

#### 功能兼容
- 保持现有功能不变
- 新功能通过适配器提供
- 渐进式功能增强

## 测试策略

### 1. 单元测试
- 每个适配器独立测试
- 模拟依赖组件
- 验证接口契约

### 2. 集成测试
- 适配器与实际组件集成
- 端到端功能验证
- 性能和稳定性测试

### 3. 兼容性测试
- 新旧接口对比测试
- 数据格式兼容性验证
- 迁移过程测试

## 总结

通过适配器模式，我们可以实现通用checkpoint基础设施和Thread特定业务逻辑的无缝集成，同时保持系统的可扩展性和可维护性。适配器设计遵循分层架构原则，提供了清晰的职责分离和统一的接口，为后续的重构和优化奠定了基础。