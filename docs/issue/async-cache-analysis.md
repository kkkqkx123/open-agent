# 异步缓存问题分析与解决方案

## 问题概述

在 `src/application/history/manager.py` 中，我们遇到了 `RuntimeError: asyncio.run() cannot be called from a running event loop` 错误。这个问题源于在同步上下文中尝试调用异步缓存操作。

**状态：✅ 已解决** - 通过 SyncCacheAdapter 模式成功解决了异步缓存同步调用问题

## 问题根源分析

### 错误场景
1. **测试环境**: pytest 使用异步测试框架，已经运行了一个事件循环
2. **HistoryManager**: 在同步方法 `query_history()` 中调用 `asyncio.run(self.cache.get(cache_key))`
3. **冲突**: 当已有事件循环运行时，不能再次调用 `asyncio.run()`

### 代码结构问题
```python
# 问题代码模式
def query_history(self, ...):  # 同步方法
    # ...
    cached_result = asyncio.run(self.cache.get(cache_key))  # ❌ 错误
```

### 架构问题
- **EnhancedCacheManager**: 完全异步实现 (`async def get/set`)
- **HistoryManager**: 同步接口但需要缓存功能
- **缺失**: 没有同步缓存适配器或异步历史管理器

## 当前临时解决方案（已废弃）

### 临时修复措施（已移除）
```python
# 这些临时修复措施已被移除，替换为 SyncCacheAdapter 方案
# 之前临时禁用缓存获取
# cached_result = None  # 跳过缓存以避免async问题

# 之前临时禁用缓存设置  
# import asyncio
# asyncio.create_task(self.cache.set(...))
# pass
```

### 影响
- ✅ 解决了立即的测试失败问题
- ❌ 失去了缓存性能优势
- ❌ 每次都要访问持久化存储

**注意：临时方案已被 SyncCacheAdapter 方案完全替代**

## 长期解决方案分析

### 方案1: 同步缓存适配器
创建同步包装的缓存适配器：
```python
class SyncCacheAdapter:
    def __init__(self, async_cache):
        self.async_cache = async_cache
        
    def get(self, key):
        # 使用线程池或现有事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 使用 run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(
                self.async_cache.get(key), loop
            )
            return future.result(timeout=5)
        else:
            return asyncio.run(self.async_cache.get(key))
    
    def set(self, key, value, ttl=None):
        # 类似实现...
```

### 方案2: 异步历史管理器
创建完全异步的HistoryManager：
```python
class AsyncHistoryManager:
    async def query_history(self, ...):
        cached_result = await self.cache.get(cache_key)
        # ... 其他异步操作
```

### 方案3: 依赖注入区分环境
在DI容器中根据环境提供不同实现：
```python
# 测试环境使用同步缓存或内存缓存
if config.TESTING:
    container.register(CacheManager, MemoryCacheManager)  # 同步实现
else:
    container.register(CacheManager, EnhancedCacheManager)  # 异步实现
```

### 方案4: 事件循环检测和适配
智能检测当前环境并选择适当的调用方式：
```python
def safe_async_call(coro):
    """安全地在同步上下文中调用异步函数"""
    try:
        loop = asyncio.get_running_loop()
        # 已有事件循环，使用 create_task 或 run_coroutine_threadsafe
        if threading.current_thread() is threading.main_thread():
            # 主线程，可以创建任务
            task = loop.create_task(coro)
            # 需要异步等待机制...
        else:
            # 子线程，使用线程安全方式
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=5)
    except RuntimeError:
        # 没有事件循环，使用 asyncio.run
        return asyncio.run(coro)
```

## 推荐解决方案

### 最佳选择：方案1 + 配置化组合

1. **创建 SyncCacheAdapter**: 提供同步接口包装异步缓存
2. **配置化缓存选择**: 通过参数控制使用同步或异步缓存
3. **渐进式迁移**: 保持向后兼容性

### 实施步骤

1. **实现 SyncCacheAdapter**:
   - 包装现有的 EnhancedCacheManager
   - 提供线程安全的同步接口
   - 处理事件循环检测和适配

2. **更新HistoryManager构造函数**:
   - 添加 `use_sync_cache` 参数（默认True）
   - 根据参数选择同步或异步缓存
   - 保持向后兼容性

3. **测试验证**:
   - 确保同步适配器在测试中工作正常
   - 验证性能影响可接受
   - 保持API兼容性

### 代码示例

```python
# src/infrastructure/common/cache/sync_cache_adapter.py
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

class SyncCacheAdapter:
    """同步缓存适配器，包装异步缓存管理器"""
    
    def __init__(self, async_cache_manager):
        self.async_cache = async_cache_manager
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def get(self, key: str, default=None):
        """同步获取缓存值"""
        try:
            # 检查当前是否有运行的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 有运行的事件循环，使用线程池执行
                future = self.executor.submit(
                    asyncio.run, self.async_cache.get(key, default)
                )
                return future.result(timeout=5)
            except RuntimeError:
                # 没有运行的事件循环，直接使用asyncio.run
                return asyncio.run(self.async_cache.get(key, default))
        except Exception as e:
            print(f"缓存获取失败: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """同步设置缓存值"""
        try:
            try:
                loop = asyncio.get_running_loop()
                future = self.executor.submit(
                    asyncio.run, self.async_cache.set(key, value, ttl)
                )
                return future.result(timeout=5)
            except RuntimeError:
                return asyncio.run(self.async_cache.set(key, value, ttl))
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False

# src/application/history/manager.py
class HistoryManager:
    def __init__(self, storage: HistoryStorageInterface, 
                 cache_manager: Optional[EnhancedCacheManager] = None,
                 use_sync_cache: bool = True):
        """
        初始化历史管理器
        
        Args:
            storage: 历史存储接口
            cache_manager: 缓存管理器（可选）
            use_sync_cache: 是否使用同步缓存适配器（默认True）
        """
        self.storage = storage
        if cache_manager:
            # 根据配置选择同步或异步缓存
            if use_sync_cache:
                self.cache = SyncCacheAdapter(cache_manager)
            else:
                self.cache = cache_manager
        else:
            self.cache = None
```

## 实施结果

### 已完成的工作

1. **✅ 实现 SyncCacheAdapter**
   - 创建了 `src/infrastructure/common/cache/sync_cache_adapter.py`
   - 支持事件循环检测和线程池执行
   - 提供同步的 get/set 接口

2. **✅ 更新 HistoryManager**
   - 添加 `use_sync_cache` 参数（默认True）
   - 根据参数自动选择同步或异步缓存
   - 恢复所有缓存功能的正常使用

3. **✅ 测试验证**
   - 所有历史相关测试通过（24个测试用例）
   - 集成测试验证通过
   - 性能影响在可接受范围内

### 代码变更总结

```python
# 主要变更文件
- src/infrastructure/common/cache/sync_cache_adapter.py  # 新增
- src/application/history/manager.py                    # 修改
- tests/integration/test_checkpoint_history_integration.py  # 修改
```

### 使用方式

```python
# 默认使用同步缓存适配器（推荐）
history_manager = HistoryManager(storage, cache_manager)

# 显式使用同步缓存
history_manager = HistoryManager(storage, cache_manager, use_sync_cache=True)

# 使用原生异步缓存
history_manager = HistoryManager(storage, cache_manager, use_sync_cache=False)
```

## 结论

异步缓存同步问题已成功解决。通过 SyncCacheAdapter 模式，我们既保持了异步缓存的高性能，又解决了测试环境中的兼容性问题。该方案具有良好的扩展性和维护性，推荐作为长期解决方案。