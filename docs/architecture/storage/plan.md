## 存储层异步统一重构方案

### 总体策略

按照您的要求，我们将从基础设施层开始，逐步统一整个存储层为异步架构，不保留向后兼容性，彻底解决所有遗留问题。

### 第一阶段：统一基础设施层缓存管理

#### 1.1 移除 SyncCacheManager

**文件：** [`src/infrastructure/common/cache/cache_manager.py`](src/infrastructure/common/cache/cache_manager.py:310)

```python
# 删除整个 SyncCacheManager 类（第309-358行）
# 同步包装器不再需要，因为所有调用方都将使用异步接口
```

#### 1.2 更新缓存模块导出

**文件：** [`src/infrastructure/common/cache/__init__.py`](src/infrastructure/common/cache/__init__.py:7)

```python
# 修改前
from .cache_manager import CacheManager, SyncCacheManager

__all__ = [
    "CacheEntry",
    "CacheStats",
    "CacheManager",
    "SyncCacheManager"
]

# 修改后
from .cache_manager import CacheManager

__all__ = [
    "CacheEntry",
    "CacheStats",
    "CacheManager"
]
```

### 第二阶段：重构 BaseStorage 类

#### 2.1 简化 BaseStorage 构造函数

**文件：** [`src/infrastructure/common/storage/base_storage.py`](src/infrastructure/common/storage/base_storage.py:18)

```python
# 修改前
def __init__(
    self,
    serializer: Optional[Serializer] = None,
    temporal_manager: Optional[TemporalManager] = None,
    metadata_manager: Optional[MetadataManager] = None,
    cache_manager: Optional[Union[CacheManager, SyncCacheManager]] = None
):

# 修改后
def __init__(
    self,
    serializer: Optional[Serializer] = None,
    temporal_manager: Optional[TemporalManager] = None,
    metadata_manager: Optional[MetadataManager] = None,
    cache_manager: Optional[CacheManager] = None  # 只接受异步缓存管理器
):
```

#### 2.2 移除所有异步检查逻辑

**文件：** [`src/infrastructure/common/storage/base_storage.py`](src/infrastructure/common/storage/base_storage.py:70)

```python
# 修改前（第70-73行）
if success and self.cache and data.get("id"):
    if asyncio.iscoroutinefunction(self.cache.set):
        await self.cache.set(data["id"], data, ttl=ttl)
    else:
        self.cache.set(data["id"], data, ttl=ttl)

# 修改后
if success and self.cache and data.get("id"):
    await self.cache.set(data["id"], data, ttl=ttl)
```

同样修改其他缓存调用点（第88-95行、第102-105行、第148-151行、第203-206行）。

#### 2.3 移除不必要的类型转换

**文件：** [`src/infrastructure/common/storage/base_storage.py`](src/infrastructure/common/storage/base_storage.py:91)

```python
# 修改前（第91行）
return cast(Optional[Dict[str, Any]], cached_data)

# 修改后
return cached_data
```

同样修改第95行的类型转换。

### 第三阶段：更新 HistoryStorageAdapter 为异步

#### 3.1 更新导入

**文件：** [`src/infrastructure/common/storage/history_storage_adapter.py`](src/infrastructure/common/storage/history_storage_adapter.py:14)

```python
# 修改前
from ..cache.cache_manager import CacheManager, SyncCacheManager

# 修改后
from ..cache.cache_manager import CacheManager
```

#### 3.2 更新构造函数

**文件：** [`src/infrastructure/common/storage/history_storage_adapter.py`](src/infrastructure/common/storage/history_storage_adapter.py:20)

```python
# 修改前
def __init__(self, base_storage: BaseStorage, cache_manager: Optional[Union[CacheManager, SyncCacheManager]] = None):

# 修改后
def __init__(self, base_storage: BaseStorage, cache_manager: Optional[CacheManager] = None):
```

#### 3.3 将所有方法改为异步

**文件：** [`src/infrastructure/common/storage/history_storage_adapter.py`](src/infrastructure/common/storage/history_storage_adapter.py:30)

```python
# 修改前
def record_message(self, record: MessageRecord) -> None:
    # ...
    asyncio.create_task(self.base_storage.save_with_metadata(data))

# 修改后
async def record_message(self, record: MessageRecord) -> None:
    # ...
    await self.base_storage.save_with_metadata(data)
```

同样修改所有其他方法：
- `record_tool_call` (第46行)
- `query_history` (第61行)
- `record_llm_request` (第105行)
- `record_llm_response` (第122行)
- `record_token_usage` (第140行)
- `record_cost` (第159行)
- `get_token_statistics` (第180行)
- `get_cost_statistics` (第203行)
- `get_llm_statistics` (第230行)

#### 3.4 移除 asyncio.run 和 asyncio.create_task

**文件：** [`src/infrastructure/common/storage/history_storage_adapter.py`](src/infrastructure/common/storage/history_storage_adapter.py:67)

```python
# 修改前
all_records = asyncio.run(self.base_storage.list({
    "session_id": query.session_id
}))

# 修改后
all_records = await self.base_storage.list({
    "session_id": query.session_id
})
```

同样修改其他使用 `asyncio.run` 的地方（第185行、第208行、第235行、第241行）。

### 第四阶段：更新 ServiceCacheAdapter 为异步

#### 4.1 更新导入

**文件：** [`src/infrastructure/cache/service_cache_adapter.py`](src/infrastructure/cache/service_cache_adapter.py:8)

```python
# 修改前
from ..common.cache.cache_manager import CacheManager, SyncCacheManager

# 修改后
from ..common.cache.cache_manager import CacheManager
```

#### 4.2 更新构造函数

**文件：** [`src/infrastructure/cache/service_cache_adapter.py`](src/infrastructure/cache/service_cache_adapter.py:18)

```python
# 修改前
def __init__(self, cache_manager: Optional[Union[CacheManager, SyncCacheManager]] = None):

# 修改后
def __init__(self, cache_manager: Optional[CacheManager] = None):
```

#### 4.3 简化实现，移除同步包装逻辑

**文件：** [`src/infrastructure/cache/service_cache_adapter.py`](src/infrastructure/cache/service_cache_adapter.py:11)

```python
# 整个类可以大幅简化，因为不再需要同步包装
class ServiceCacheAdapter(IServiceCache):
    """服务缓存适配器 - 将CacheManager适配为IServiceCache接口"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """初始化服务缓存适配器"""
        self._cache_manager = cache_manager or CacheManager()
    
    def _get_cache_key(self, service_type: Type) -> str:
        """将服务类型转换为缓存键"""
        return f"service:{service_type.__module__}.{service_type.__name__}"
    
    async def get(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例"""
        key = self._get_cache_key(service_type)
        return await self._cache_manager.get(key)
    
    async def put(self, service_type: Type, instance: Any) -> None:
        """将服务实例放入缓存"""
        key = self._get_cache_key(service_type)
        await self._cache_manager.set(key, instance)
    
    async def remove(self, service_type: Type) -> None:
        """从缓存移除服务实例"""
        key = self._get_cache_key(service_type)
        await self._cache_manager.delete(key)
    
    async def clear(self) -> None:
        """清除所有缓存"""
        await self._cache_manager.clear()
    
    async def optimize(self) -> Dict[str, Any]:
        """优化缓存"""
        stats = await self.get_stats()
        return {
            "expired_removed": 0,
            "lru_removed": 0,
            "final_cache_size": stats.get("cache_size", 0),
            "hit_rate": stats.get("hit_rate", 0.0)
        }
    
    async def get_size(self) -> int:
        """获取缓存大小"""
        stats = await self.get_stats()
        return stats.get("cache_size", 0)
    
    async def get_memory_usage(self) -> int:
        """获取内存使用量"""
        stats = await self.get_stats()
        cache_size = stats.get("cache_size", 0)
        return cache_size * 1024
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            return await self._cache_manager.get_stats()
        except Exception as e:
            return {
                "error": str(e),
                "cache_size": 0,
                "hit_rate": 0.0
            }
    
    async def close(self) -> None:
        """关闭适配器"""
        # 不需要特别清理，CacheManager会自动处理
        pass
```

### 第五阶段：更新 HistoryManager 为完全异步

#### 5.1 将 get_llm_statistics 改为异步

**文件：** [`src/application/history/manager.py`](src/application/history/manager.py:489)

```python
# 修改前
def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
    # ...
    if self.cache:
        import asyncio
        cached_stats = asyncio.run(self.cache.get(cache_key))
    # ...
    if self.cache:
        import asyncio
        asyncio.create_task(self.cache.set(cache_key, result, ttl=600))

# 修改后
async def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
    # ...
    if self.cache:
        cached_stats = await self.cache.get(cache_key)
    # ...
    if self.cache:
        await self.cache.set(cache_key, result, ttl=600)
```

#### 5.2 更新接口定义

**文件：** [`src/domain/history/interfaces.py`](src/domain/history/interfaces.py:5)

需要将 `get_llm_statistics` 方法也标记为异步。

### 第六阶段：更新所有调用方代码

#### 6.1 更新 TUI 集成

**文件：** [`src/presentation/tui/history_integration.py`](src/presentation/tui/history_integration.py:20)

需要确保所有调用 `HistoryStorageAdapter` 的地方都使用 `await`。

#### 6.2 更新 API 服务

**文件：** [`src/presentation/api/services/history_service.py`](src/presentation/api/services/history_service.py:38)

需要更新所有调用历史管理器的地方为异步。

#### 6.3 更新依赖注入配置

所有注册这些服务的地方都需要更新为异步工厂方法。

### 实施顺序

1. **第一阶段**：统一基础设施层缓存管理
2. **第二阶段**：重构 BaseStorage 类
3. **第三阶段**：更新 HistoryStorageAdapter 为异步
4. **第四阶段**：更新 ServiceCacheAdapter 为异步
5. **第五阶段**：更新 HistoryManager 为完全异步
6. **第六阶段**：更新所有调用方代码

每个阶段完成后进行测试，确保没有破坏现有功能。这个方案彻底解决了异步/同步混合的问题，使整个存储层架构更加清晰和一致。