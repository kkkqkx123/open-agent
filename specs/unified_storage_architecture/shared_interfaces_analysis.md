# 各模块存储接口复用分析

## 概述

基于已设计的各模块接口，分析如何共同复用存储模块的基本接口定义，确保架构的一致性和可维护性。

## 统一存储接口分析

### 核心存储接口 (IUnifiedStorage)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from datetime import datetime

class IUnifiedStorage(ABC):
    """统一存储接口 - 所有模块的基础"""
    
    # 基础CRUD操作
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据并返回ID"""
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID加载数据"""
        pass
    
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据"""
        pass
    
    # 查询操作
    @abstractmethod
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        pass
    
    @abstractmethod
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        pass
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        pass
    
    # 高级操作
    @abstractmethod
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务"""
        pass
```

### 通用数据模型

```python
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class UnifiedStorageData(BaseModel):
    """统一存储数据模型"""
    id: str
    type: str  # 数据类型标识
    data: Dict[str, Any]  # 实际数据
    session_id: Optional[str] = None  # 可选的会话ID
    thread_id: Optional[str] = None  # 可选的线程ID
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

## 各模块接口复用分析

### 1. Session模块复用

#### 复用方式
- **直接使用**：Session模块需求简单，可以直接使用IUnifiedStorage接口
- **数据类型**：使用`type = "session"`标识
- **查询模式**：基于session_id和metadata的简单查询

#### 实现示例
```python
class SessionService:
    """Session服务 - 直接复用统一存储接口"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """保存会话"""
        data = UnifiedStorageData(
            id=session_id,
            type="session",
            data=session_data,
            metadata=session_data.get("metadata", {}),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await self._storage.save(data.dict())
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        data = await self._storage.load(session_id)
        if data and data.get("type") == "session":
            return data.get("data")
        return None
    
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        query_filters = {"type": "session"}
        if filters:
            # 将过滤器转换为metadata查询
            for key, value in filters.items():
                query_filters[f"metadata.{key}"] = value
        
        results = await self._storage.list(query_filters)
        return [result.get("data") for result in results]
```

### 2. Thread模块复用

#### 复用方式
- **适配器模式**：使用ThreadUnifiedAdapter适配IUnifiedStorage
- **数据类型**：使用`type = "thread"`, `"thread_branch"`, `"thread_snapshot"`
- **关系管理**：通过thread_id关联不同类型的数据

#### 实现示例
```python
class ThreadUnifiedAdapter:
    """Thread统一适配器 - 复用统一存储接口"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    async def save_thread(self, thread: 'Thread') -> None:
        """保存Thread"""
        data = UnifiedStorageData(
            id=thread.thread_id,
            type="thread",
            data=thread.to_dict(),
            created_at=thread.created_at,
            updated_at=datetime.now()
        )
        await self._storage.save(data.dict())
    
    async def save_branch(self, branch: 'ThreadBranch') -> None:
        """保存Branch"""
        data = UnifiedStorageData(
            id=branch.branch_id,
            type="thread_branch",
            thread_id=branch.source_thread_id,
            data=branch.to_dict(),
            created_at=branch.created_at,
            updated_at=datetime.now()
        )
        await self._storage.save(data.dict())
    
    async def get_thread_with_branches(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有分支"""
        # 使用事务获取相关数据
        operations = [
            {"type": "load", "id": thread_id},
            {"type": "list", "filters": {"type": "thread_branch", "thread_id": thread_id}}
        ]
        
        results = await self._storage.transaction(operations)
        thread_data = results[0]
        branch_data = results[1]
        
        return {
            "thread": thread_data.get("data") if thread_data else None,
            "branches": [b.get("data") for b in branch_data] if branch_data else []
        }
```

### 3. History模块复用

#### 复用方式
- **适配器模式**：使用HistoryStore适配IUnifiedStorage
- **数据类型**：使用多种类型标识不同记录
- **统计查询**：利用统一存储的聚合查询能力

#### 实现示例
```python
class HistoryStore:
    """History存储适配器 - 复用统一存储接口"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        data = UnifiedStorageData(
            id=record.record_id,
            type="message",
            session_id=record.session_id,
            data=record.to_dict(),
            created_at=record.timestamp,
            updated_at=record.timestamp
        )
        await self._storage.save(data.dict())
    
    async def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取Token统计"""
        # 使用统一存储的聚合查询
        filters = {
            "type": "token_usage",
            "session_id": session_id
        }
        
        results = await self._storage.list(filters)
        
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        
        for result in results:
            data = result.get("data", {})
            total_tokens += data.get("total_tokens", 0)
            prompt_tokens += data.get("prompt_tokens", 0)
            completion_tokens += data.get("completion_tokens", 0)
        
        return {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "record_count": len(results)
        }
```

### 4. Checkpoint模块复用

#### 复用方式
- **适配器模式**：使用CheckpointStore适配IUnifiedStorage
- **数据类型**：使用`type = "checkpoint"`
- **特殊处理**：压缩、序列化等在适配器层处理

#### 实现示例
```python
class CheckpointStore:
    """Checkpoint存储适配器 - 复用统一存储接口"""
    
    def __init__(self, storage: IUnifiedStorage, serializer: Serializer):
        self._storage = storage
        self._serializer = serializer
    
    async def save(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state_data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存checkpoint"""
        import uuid
        
        checkpoint_id = str(uuid.uuid4())
        
        # 序列化状态数据
        serialized_state = self._serializer.serialize(state_data)
        
        data = UnifiedStorageData(
            id=checkpoint_id,
            type="checkpoint",
            thread_id=thread_id,
            data={
                "workflow_id": workflow_id,
                "state_data": serialized_state,
                "metadata": metadata or {}
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await self._storage.save(data.dict())
        return checkpoint_id
    
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint"""
        data = await self._storage.load(checkpoint_id)
        if not data or data.get("type") != "checkpoint":
            return None
        
        # 反序列化状态数据
        checkpoint_data = data.get("data", {})
        serialized_state = checkpoint_data.get("state_data")
        state_data = self._serializer.deserialize(serialized_state)
        
        return {
            "id": data["id"],
            "thread_id": data["thread_id"],
            "workflow_id": checkpoint_data["workflow_id"],
            "state_data": state_data,
            "metadata": checkpoint_data.get("metadata", {}),
            "created_at": data["created_at"],
            "updated_at": data["updated_at"]
        }
```

## 共享接口设计

### 1. 基础存储操作接口

```python
class IBaseStorageOperations(ABC):
    """基础存储操作接口 - 所有模块共享"""
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        pass
    
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据"""
        pass
```

### 2. 查询操作接口

```python
class IQueryOperations(ABC):
    """查询操作接口 - 所有模块共享"""
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        pass
    
    @abstractmethod
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        pass
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        pass
```

### 3. 高级操作接口

```python
class IAdvancedOperations(ABC):
    """高级操作接口 - 复杂模块使用"""
    
    @abstractmethod
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务"""
        pass
    
    @abstractmethod
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        pass
    
    @abstractmethod
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        pass
```

### 4. 模块特定接口

```python
class IModuleSpecificOperations(ABC):
    """模块特定操作接口"""
    
    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取数据"""
        pass
    
    @abstractmethod
    async def get_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """根据线程ID获取数据"""
        pass
    
    @abstractmethod
    async def cleanup_old_data(self, retention_days: int) -> int:
        """清理旧数据"""
        pass
```

## 统一存储接口实现

### 完整的统一存储接口

```python
class IUnifiedStorage(
    IBaseStorageOperations,
    IQueryOperations,
    IAdvancedOperations,
    IModuleSpecificOperations
):
    """完整的统一存储接口"""
    pass
```

### 基础存储实现

```python
class BaseStorage(IUnifiedStorage):
    """基础存储实现 - 提供所有模块共享的功能"""
    
    def __init__(self, serializer: Optional[Serializer] = None):
        self.serializer = serializer or Serializer()
    
    # 实现所有接口方法...
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据 - 所有模块共享"""
        # 添加时间戳
        now = datetime.now()
        data["created_at"] = now
        data["updated_at"] = now
        
        # 实际保存逻辑由子类实现
        return await self._save_impl(data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据 - 所有模块共享"""
        return await self._load_impl(id)
    
    # 其他方法的实现...
    
    # 抽象方法，由具体存储实现
    @abstractmethod
    async def _save_impl(self, data: Dict[str, Any]) -> str:
        """实际保存实现"""
        pass
    
    @abstractmethod
    async def _load_impl(self, id: str) -> Optional[Dict[str, Any]]:
        """实际加载实现"""
        pass
```

## 适配器基类

### 通用适配器基类

```python
class BaseStorageAdapter(ABC):
    """存储适配器基类 - 所有模块适配器的基类"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    def _create_storage_data(
        self, 
        id: str, 
        type: str, 
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建标准存储数据格式"""
        return {
            "id": id,
            "type": type,
            "data": data,
            "session_id": session_id,
            "thread_id": thread_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    def _extract_data(self, storage_data: Dict[str, Any], expected_type: str) -> Optional[Dict[str, Any]]:
        """提取存储数据"""
        if storage_data and storage_data.get("type") == expected_type:
            return storage_data.get("data")
        return None
    
    async def _save_with_type(
        self, 
        id: str, 
        type: str, 
        data: Dict[str, Any],
        **kwargs
    ) -> None:
        """保存带类型的数据"""
        storage_data = self._create_storage_data(id, type, data, **kwargs)
        await self._storage.save(storage_data)
    
    async def _load_by_type(
        self, 
        id: str, 
        expected_type: str
    ) -> Optional[Dict[str, Any]]:
        """按类型加载数据"""
        storage_data = await self._storage.load(id)
        return self._extract_data(storage_data, expected_type)
```

### 模块适配器实现

```python
class SessionStorageAdapter(BaseStorageAdapter):
    """Session存储适配器"""
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """保存会话"""
        await self._save_with_type(session_id, "session", session_data)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        return await self._load_by_type(session_id, "session")

class ThreadStorageAdapter(BaseStorageAdapter):
    """Thread存储适配器"""
    
    async def save_thread(self, thread: 'Thread') -> None:
        """保存Thread"""
        await self._save_with_type(
            thread.thread_id, 
            "thread", 
            thread.to_dict()
        )
    
    async def get_thread(self, thread_id: str) -> Optional['Thread']:
        """获取Thread"""
        data = await self._load_by_type(thread_id, "thread")
        return Thread.from_dict(data) if data else None

class HistoryStorageAdapter(BaseStorageAdapter):
    """History存储适配器"""
    
    async def record_message(self, record: 'MessageRecord') -> None:
        """记录消息"""
        await self._save_with_type(
            record.record_id,
            "message",
            record.to_dict(),
            session_id=record.session_id
        )
    
    async def get_messages(self, session_id: str) -> List['MessageRecord']:
        """获取消息"""
        filters = {"type": "message", "session_id": session_id}
        results = await self._storage.list(filters)
        return [MessageRecord.from_dict(r.get("data")) for r in results]

class CheckpointStorageAdapter(BaseStorageAdapter):
    """Checkpoint存储适配器"""
    
    def __init__(self, storage: IUnifiedStorage, serializer: Serializer):
        super().__init__(storage)
        self._serializer = serializer
    
    async def save_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state_data: Any
    ) -> str:
        """保存checkpoint"""
        import uuid
        checkpoint_id = str(uuid.uuid4())
        
        # 序列化状态数据
        serialized_state = self._serializer.serialize(state_data)
        
        data = {
            "workflow_id": workflow_id,
            "state_data": serialized_state
        }
        
        await self._save_with_type(
            checkpoint_id,
            "checkpoint",
            data,
            thread_id=thread_id
        )
        
        return checkpoint_id
```

## 复用优势分析

### 1. 代码复用

- **统一接口**：所有模块使用相同的存储接口
- **共享实现**：基础功能在基类中实现，避免重复
- **一致的行为**：所有模块的存储行为保持一致

### 2. 维护性

- **单一修改点**：存储逻辑的修改只需要在一个地方进行
- **统一的错误处理**：所有模块使用相同的错误处理机制
- **统一的监控**：可以统一监控所有模块的存储操作

### 3. 扩展性

- **新模块支持**：新模块可以轻松复用现有存储基础设施
- **功能增强**：存储功能的增强会自动惠及所有模块
- **插件机制**：可以轻松添加新的存储后端

### 4. 性能优化

- **统一优化**：存储性能优化会惠及所有模块
- **缓存共享**：可以共享缓存机制
- **连接池复用**：可以复用数据库连接池

## 最佳实践建议

### 1. 数据类型命名规范

```python
class DataType:
    """数据类型常量"""
    SESSION = "session"
    THREAD = "thread"
    THREAD_BRANCH = "thread_branch"
    THREAD_SNAPSHOT = "thread_snapshot"
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    CHECKPOINT = "checkpoint"
    CHECKPOINT_VERSION = "checkpoint_version"
```

### 2. 元数据标准

```python
class StandardMetadata:
    """标准元数据字段"""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    VERSION = "version"
    STATUS = "status"
    TAGS = "tags"
    SOURCE = "source"
```

### 3. 错误处理标准

```python
class StorageErrorHandler:
    """统一错误处理"""
    
    @staticmethod
    def handle_storage_error(error: Exception, operation: str, context: Dict[str, Any]) -> None:
        """处理存储错误"""
        logger.error(f"Storage error in {operation}: {error}", extra=context)
        
        # 根据错误类型进行特定处理
        if isinstance(error, StorageConnectionError):
            # 处理连接错误
            pass
        elif isinstance(error, StorageValidationError):
            # 处理验证错误
            pass
```

### 4. 性能监控标准

```python
class StoragePerformanceMonitor:
    """统一性能监控"""
    
    def __init__(self):
        self._metrics = {}
    
    async def monitor_operation(self, operation: str, func, *args, **kwargs):
        """监控存储操作"""
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            self._record_metric(operation, duration, success)
        
        return result
    
    def _record_metric(self, operation: str, duration: float, success: bool):
        """记录性能指标"""
        if operation not in self._metrics:
            self._metrics[operation] = {
                "count": 0,
                "total_duration": 0,
                "success_count": 0
            }
        
        self._metrics[operation]["count"] += 1
        self._metrics[operation]["total_duration"] += duration
        if success:
            self._metrics[operation]["success_count"] += 1
```

## 结论

通过统一存储接口的设计，各模块可以有效地复用存储基础设施，同时保持各自的特定需求。这种设计提供了：

1. **高度的一致性**：所有模块使用相同的存储模式
2. **良好的可维护性**：存储逻辑集中管理
3. **强大的扩展性**：易于添加新模块和新功能
4. **优秀的性能**：统一的优化和监控

这种架构设计为项目的长期发展奠定了坚实的基础。