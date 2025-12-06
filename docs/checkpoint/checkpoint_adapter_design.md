# Checkpoint适配器接口设计

## 概述

本文档设计连接Thread特定checkpoint模块和通用checkpoint模块的适配器接口，实现两套实现的统一和简化。

## 设计原则

### 1. 适配器模式原则
- 将一个类的接口转换成客户端希望的另外一个接口
- 使得原本由于接口不兼容而不能一起工作的那些类可以一起工作
- 隐藏底层实现的复杂性

### 2. 分层架构原则
- Session层通过Thread接口管理checkpoint
- Thread层提供统一的checkpoint管理接口
- 基础设施层提供通用的checkpoint抽象

### 3. 接口隔离原则
- 客户端不应该依赖它不需要的接口
- 类间的依赖关系应该建立在最小的接口上
- 避免接口污染

## 适配器接口设计

### 1. 核心适配器接口

#### ICheckpointAdapter
```python
class ICheckpointAdapter(ABC):
    """Checkpoint适配器接口
    
    提供Thread特定checkpoint和通用checkpoint之间的适配。
    """
    
    @abstractmethod
    def adapt_thread_checkpoint_to_checkpoint(self, thread_checkpoint: ThreadCheckpoint) -> Checkpoint:
        """将Thread检查点适配为通用检查点
        
        Args:
            thread_checkpoint: Thread检查点
            
        Returns:
            通用检查点
        """
        pass
    
    @abstractmethod
    def adapt_checkpoint_to_thread_checkpoint(self, checkpoint: Checkpoint, thread_id: str) -> ThreadCheckpoint:
        """将通用检查点适配为Thread检查点
        
        Args:
            checkpoint: 通用检查点
            thread_id: Thread ID
            
        Returns:
            Thread检查点
        """
        pass
    
    @abstractmethod
    def adapt_config_to_thread_context(self, config: Dict[str, Any]) -> ThreadContext:
        """将配置适配为Thread上下文
        
        Args:
            config: 通用配置
            
        Returns:
            Thread上下文
        """
        pass
```

#### ICheckpointServiceAdapter
```python
class ICheckpointServiceAdapter(ABC):
    """Checkpoint服务适配器接口
    
    提供Thread特定checkpoint服务和通用checkpoint服务之间的适配。
    """
    
    @abstractmethod
    async def adapt_save_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """适配保存检查点操作
        
        Args:
            thread_id: Thread ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            
        Returns:
            检查点ID
        """
        pass
    
    @abstractmethod
    async def adapt_load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """适配加载检查点操作
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            状态数据
        """
        pass
    
    @abstractmethod
    async def adapt_list_checkpoints(
        self,
        thread_id: str,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[ThreadCheckpoint]:
        """适配列出检查点操作
        
        Args:
            thread_id: Thread ID
            filter: 过滤条件
            
        Returns:
            Thread检查点列表
        """
        pass
```

### 2. 存储适配器接口

#### ICheckpointStorageAdapter
```python
class ICheckpointStorageAdapter(ABC):
    """Checkpoint存储适配器接口
    
    提供Thread特定存储和通用存储之间的适配。
    """
    
    @abstractmethod
    async def adapt_save_to_storage(
        self,
        thread_checkpoint: ThreadCheckpoint,
        storage: ICheckpointRepository
    ) -> str:
        """适配保存到存储操作
        
        Args:
            thread_checkpoint: Thread检查点
            storage: 通用存储
            
        Returns:
            检查点ID
        """
        pass
    
    @abstractmethod
    async def adapt_load_from_storage(
        self,
        thread_id: str,
        checkpoint_id: str,
        storage: ICheckpointRepository
    ) -> Optional[ThreadCheckpoint]:
        """适配从存储加载操作
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            storage: 通用存储
            
        Returns:
            Thread检查点
        """
        pass
    
    @abstractmethod
    async def adapt_list_from_storage(
        self,
        thread_id: str,
        storage: ICheckpointRepository,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[ThreadCheckpoint]:
        """适配从存储列表操作
        
        Args:
            thread_id: Thread ID
            storage: 通用存储
            filter: 过滤条件
            
        Returns:
            Thread检查点列表
        """
        pass
```

### 3. 管理器适配器接口

#### ICheckpointManagerAdapter
```python
class ICheckpointManagerAdapter(ABC):
    """Checkpoint管理器适配器接口
    
    提供Thread特定管理器和通用管理器之间的适配。
    """
    
    @abstractmethod
    def adapt_thread_manager_to_service(
        self,
        thread_manager: ThreadCheckpointManager
    ) -> ICheckpointService:
        """将Thread管理器适配为通用服务
        
        Args:
            thread_manager: Thread检查点管理器
            
        Returns:
            通用检查点服务
        """
        pass
    
    @abstractmethod
    def adapt_service_to_thread_manager(
        self,
        service: ICheckpointService,
        thread_id: str
    ) -> ThreadCheckpointManager:
        """将通用服务适配为Thread管理器
        
        Args:
            service: 通用检查点服务
            thread_id: Thread ID
            
        Returns:
            Thread检查点管理器
        """
        pass
```

## 适配器实现设计

### 1. 核心适配器实现

#### CheckpointAdapter
```python
class CheckpointAdapter(ICheckpointAdapter):
    """Checkpoint适配器实现"""
    
    def __init__(self):
        self._type_mapper = CheckpointTypeMapper()
        self._metadata_mapper = CheckpointMetadataMapper()
    
    def adapt_thread_checkpoint_to_checkpoint(self, thread_checkpoint: ThreadCheckpoint) -> Checkpoint:
        """将Thread检查点适配为通用检查点"""
        # 映射检查点类型
        checkpoint_type = self._type_mapper.to_generic_type(thread_checkpoint.checkpoint_type)
        
        # 映射元数据
        metadata = self._metadata_mapper.to_generic_metadata(thread_checkpoint.metadata)
        
        # 创建通用检查点
        checkpoint = Checkpoint(
            id=thread_checkpoint.id,
            channel_values={"state": thread_checkpoint.state_data},
            channel_versions={"v": "1.0"},
            versions_seen={"v": "1.0"}
        )
        
        # 添加Thread特定信息到元数据
        metadata.update({
            "thread_id": thread_checkpoint.thread_id,
            "checkpoint_type": checkpoint_type,
            "status": thread_checkpoint.status.value,
            "created_at": thread_checkpoint.created_at.isoformat(),
            "updated_at": thread_checkpoint.updated_at.isoformat(),
            "expires_at": thread_checkpoint.expires_at.isoformat() if thread_checkpoint.expires_at else None,
            "size_bytes": thread_checkpoint.size_bytes,
            "restore_count": thread_checkpoint.restore_count
        })
        
        return checkpoint
    
    def adapt_checkpoint_to_thread_checkpoint(self, checkpoint: Checkpoint, thread_id: str) -> ThreadCheckpoint:
        """将通用检查点适配为Thread检查点"""
        # 从元数据提取Thread特定信息
        metadata = checkpoint.get("metadata", {})
        
        # 映射检查点类型
        checkpoint_type = self._type_mapper.from_generic_type(
            metadata.get("checkpoint_type", "auto")
        )
        
        # 映射状态
        state_data = checkpoint.get("channel_values", {}).get("state", {})
        
        # 创建Thread检查点
        thread_checkpoint = ThreadCheckpoint(
            id=checkpoint.id,
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            metadata=metadata.get("custom_data", {})
        )
        
        # 设置状态
        status = metadata.get("status", "active")
        thread_checkpoint.status = CheckpointStatus(status)
        
        # 设置时间戳
        if metadata.get("created_at"):
            thread_checkpoint.created_at = datetime.fromisoformat(metadata["created_at"])
        if metadata.get("updated_at"):
            thread_checkpoint.updated_at = datetime.fromisoformat(metadata["updated_at"])
        if metadata.get("expires_at"):
            thread_checkpoint.expires_at = datetime.fromisoformat(metadata["expires_at"])
        
        # 设置统计信息
        thread_checkpoint.size_bytes = metadata.get("size_bytes", 0)
        thread_checkpoint.restore_count = metadata.get("restore_count", 0)
        
        return thread_checkpoint
```

### 2. 服务适配器实现

#### CheckpointServiceAdapter
```python
class CheckpointServiceAdapter(ICheckpointServiceAdapter):
    """Checkpoint服务适配器实现"""
    
    def __init__(
        self,
        thread_domain_service: ThreadCheckpointDomainService,
        generic_service: ICheckpointService,
        adapter: ICheckpointAdapter
    ):
        self._thread_domain_service = thread_domain_service
        self._generic_service = generic_service
        self._adapter = adapter
    
    async def adapt_save_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """适配保存检查点操作"""
        # 使用Thread领域服务创建检查点
        thread_checkpoint = await self._thread_domain_service.create_checkpoint(
            thread_id=thread_id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            metadata=metadata
        )
        
        # 适配为通用检查点
        generic_checkpoint = self._adapter.adapt_thread_checkpoint_to_checkpoint(thread_checkpoint)
        
        # 保存到通用存储
        config = {"configurable": {"thread_id": thread_id, "checkpoint_id": thread_checkpoint.id}}
        await self._generic_service.save_checkpoint(
            config=config,
            checkpoint=generic_checkpoint.to_dict(),
            metadata=thread_checkpoint.metadata
        )
        
        return thread_checkpoint.id
    
    async def adapt_load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """适配加载检查点操作"""
        # 从Thread领域服务加载
        thread_checkpoint = await self._thread_domain_service._repository.find_by_id(checkpoint_id)
        if thread_checkpoint:
            return thread_checkpoint.state_data
        
        # 从通用存储加载
        config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}
        generic_checkpoint = await self._generic_service.load_checkpoint(config)
        if generic_checkpoint:
            # 适配为Thread检查点
            thread_checkpoint = self._adapter.adapt_checkpoint_to_thread_checkpoint(
                Checkpoint.from_dict(generic_checkpoint), thread_id
            )
            return thread_checkpoint.state_data
        
        return None
```

### 3. 存储适配器实现

#### CheckpointStorageAdapter
```python
class CheckpointStorageAdapter(ICheckpointStorageAdapter):
    """Checkpoint存储适配器实现"""
    
    def __init__(self, adapter: ICheckpointAdapter):
        self._adapter = adapter
    
    async def adapt_save_to_storage(
        self,
        thread_checkpoint: ThreadCheckpoint,
        storage: ICheckpointRepository
    ) -> str:
        """适配保存到存储操作"""
        # 适配为通用检查点
        generic_checkpoint = self._adapter.adapt_thread_checkpoint_to_checkpoint(thread_checkpoint)
        
        # 构建配置
        config = {
            "configurable": {
                "thread_id": thread_checkpoint.thread_id,
                "checkpoint_id": thread_checkpoint.id
            }
        }
        
        # 保存到通用存储
        checkpoint_data = {
            **generic_checkpoint.to_dict(),
            "metadata": thread_checkpoint.metadata,
            "config": config
        }
        
        return await storage.save_checkpoint(checkpoint_data)
    
    async def adapt_load_from_storage(
        self,
        thread_id: str,
        checkpoint_id: str,
        storage: ICheckpointRepository
    ) -> Optional[ThreadCheckpoint]:
        """适配从存储加载操作"""
        # 从通用存储加载
        checkpoint_data = await storage.load_checkpoint(checkpoint_id)
        if not checkpoint_data:
            return None
        
        # 适配为Thread检查点
        generic_checkpoint = Checkpoint.from_dict(checkpoint_data)
        thread_checkpoint = self._adapter.adapt_checkpoint_to_thread_checkpoint(
            generic_checkpoint, thread_id
        )
        
        return thread_checkpoint
```

## 映射器设计

### 1. 类型映射器

#### CheckpointTypeMapper
```python
class CheckpointTypeMapper:
    """检查点类型映射器"""
    
    def to_generic_type(self, thread_type: CheckpointType) -> str:
        """将Thread检查点类型映射为通用类型"""
        mapping = {
            CheckpointType.MANUAL: "manual",
            CheckpointType.AUTO: "auto",
            CheckpointType.ERROR: "error",
            CheckpointType.MILESTONE: "milestone"
        }
        return mapping.get(thread_type, "auto")
    
    def from_generic_type(self, generic_type: str) -> CheckpointType:
        """将通用类型映射为Thread检查点类型"""
        mapping = {
            "manual": CheckpointType.MANUAL,
            "auto": CheckpointType.AUTO,
            "error": CheckpointType.ERROR,
            "milestone": CheckpointType.MILESTONE
        }
        return mapping.get(generic_type, CheckpointType.AUTO)
```

### 2. 元数据映射器

#### CheckpointMetadataMapper
```python
class CheckpointMetadataMapper:
    """检查点元数据映射器"""
    
    def to_generic_metadata(self, thread_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """将Thread元数据映射为通用元数据"""
        # 提取通用元数据
        generic_metadata = {
            "custom_data": thread_metadata.copy()
        }
        
        # 处理特殊字段
        if "title" in thread_metadata:
            generic_metadata["title"] = thread_metadata["title"]
        if "description" in thread_metadata:
            generic_metadata["description"] = thread_metadata["description"]
        if "tags" in thread_metadata:
            generic_metadata["tags"] = thread_metadata["tags"]
        
        return generic_metadata
    
    def from_generic_metadata(self, generic_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """将通用元数据映射为Thread元数据"""
        thread_metadata = {}
        
        # 提取自定义数据
        if "custom_data" in generic_metadata:
            thread_metadata.update(generic_metadata["custom_data"])
        
        # 处理特殊字段
        if "title" in generic_metadata:
            thread_metadata["title"] = generic_metadata["title"]
        if "description" in generic_metadata:
            thread_metadata["description"] = generic_metadata["description"]
        if "tags" in generic_metadata:
            thread_metadata["tags"] = generic_metadata["tags"]
        
        return thread_metadata
```

## 适配器工厂设计

### CheckpointAdapterFactory
```python
class CheckpointAdapterFactory:
    """Checkpoint适配器工厂"""
    
    def __init__(self):
        self._adapters = {}
    
    def create_adapter(
        self,
        adapter_type: str,
        thread_domain_service: Optional[ThreadCheckpointDomainService] = None,
        generic_service: Optional[ICheckpointService] = None
    ) -> ICheckpointAdapter:
        """创建适配器实例
        
        Args:
            adapter_type: 适配器类型
            thread_domain_service: Thread领域服务
            generic_service: 通用服务
            
        Returns:
            适配器实例
        """
        if adapter_type == "service":
            return CheckpointServiceAdapter(
                thread_domain_service=thread_domain_service,
                generic_service=generic_service,
                adapter=CheckpointAdapter()
            )
        elif adapter_type == "storage":
            return CheckpointStorageAdapter(adapter=CheckpointAdapter())
        else:
            return CheckpointAdapter()
```

## 使用示例

### 1. 基本使用
```python
# 创建适配器
adapter_factory = CheckpointAdapterFactory()
service_adapter = adapter_factory.create_adapter(
    "service",
    thread_domain_service=thread_domain_service,
    generic_service=generic_service
)

# 使用适配器保存检查点
checkpoint_id = await service_adapter.adapt_save_checkpoint(
    thread_id="thread_123",
    state_data={"key": "value"},
    checkpoint_type=CheckpointType.MANUAL,
    metadata={"title": "Manual Checkpoint"}
)
```

### 2. 存储适配
```python
# 创建存储适配器
storage_adapter = adapter_factory.create_adapter("storage")

# 使用适配器保存到存储
checkpoint_id = await storage_adapter.adapt_save_to_storage(
    thread_checkpoint=thread_checkpoint,
    storage=generic_storage
)
```

## 总结

通过适配器接口设计，我们实现了：

1. **接口统一**: 提供统一的接口来操作Thread特定和通用的checkpoint
2. **实现隔离**: 隐藏底层实现的复杂性，客户端只需关注接口
3. **灵活扩展**: 可以轻松添加新的适配器实现
4. **向后兼容**: 保持现有代码的兼容性

这种设计为后续的重构提供了坚实的基础，确保两套实现能够无缝集成。