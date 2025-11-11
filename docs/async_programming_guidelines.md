# 异步编程规范指南

## 概述

本文档定义了项目中异步编程的规范和最佳实践，旨在提高代码质量、性能和可维护性。

## 核心原则

### 1. 明确区分同步和异步代码

- **同步代码**：用于CPU密集型任务、简单数据处理和快速操作
- **异步代码**：用于I/O密集型任务、网络请求和并发操作

```python
# 好的做法：明确分离
class SyncProcessor:
    def process_data(self, data):  # 同步处理
        return data.upper()

class AsyncProcessor:
    async def fetch_data(self, url):  # 异步获取
        async with aiohttp.ClientSession() as session:
            return await session.get(url)

# 避免：混合同步/异步
class MixedProcessor:
    def execute(self, data):
        loop = asyncio.new_event_loop()  # 不推荐
        return loop.run_until_complete(self.async_execute(data))
    
    async def async_execute(self, data):
        return await some_async_operation(data)
```

### 2. 使用真正异步的I/O操作

```python
# 好的做法：使用异步HTTP客户端
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# 避免：在线程池中执行同步I/O
async def fetch_data_bad(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: requests.get(url).json())
```

### 3. 避免不必要的异步包装

```python
# 避免：为简单操作添加异步延迟
async def process_data(data):
    await asyncio.sleep(0.01)  # 无意义的延迟
    return data.upper()

# 推荐：直接执行同步操作
def process_data(data):
    return data.upper()
```

## 异步编程模式

### 1. 事件循环管理

使用统一的事件循环管理器：

```python
from src.infrastructure.async_utils.event_loop_manager import event_loop_manager, run_async

# 在同步环境中运行异步代码
def sync_function():
    result = run_async(async_function())
    return result

# 直接使用事件循环管理器
def another_sync_function():
    future = event_loop_manager.create_task(async_function())
    return future.result()
```

### 2. 并发控制

使用信号量控制并发数量：

```python
from src.infrastructure.async_utils.event_loop_manager import AsyncLock

class ConcurrencyLimiter:
    def __init__(self, max_concurrent=10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_with_limit(self, coro):
        async with self.semaphore:
            return await coro
```

### 3. 资源管理

使用异步上下文管理器：

```python
class AsyncResource(AsyncContextManager):
    async def __aenter__(self):
        self.resource = await acquire_resource()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.resource.close()

# 使用方式
async with AsyncResource() as resource:
    await resource.do_something()
```

## 工具实现规范

### 1. 同步工具

```python
class SyncTool(BaseTool):
    def execute(self, **kwargs):
        # 直接执行同步操作
        return self.sync_operation(**kwargs)
    
    def sync_operation(self, **kwargs):
        # 同步实现
        pass
```

### 2. 异步工具

```python
class AsyncTool(BaseTool):
    async def execute_async(self, **kwargs):
        # 直接执行异步操作
        return await self.async_operation(**kwargs)
    
    def execute(self, **kwargs):
        # 通过事件循环管理器运行
        return run_async(self.execute_async(**kwargs))
    
    async def async_operation(self, **kwargs):
        # 异步实现
        pass
```

### 3. 工具工厂

```python
class ToolFactory:
    @staticmethod
    def create_tool(func, config):
        if inspect.iscoroutinefunction(func):
            return AsyncTool(func, config)
        else:
            return SyncTool(func, config)
```

## 性能优化指南

### 1. 批处理

```python
class AsyncBatchProcessor:
    async def process_batch(self, requests):
        # 批量处理请求
        tasks = [self.process_request(req) for req in requests]
        return await asyncio.gather(*tasks)
```

### 2. 连接池

```python
class AsyncHTTPClient:
    def __init__(self):
        self._session = None
    
    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
```

### 3. 缓存

```python
class AsyncCache:
    def __init__(self):
        self._cache = {}
        self._lock = AsyncLock()
    
    async def get_or_set(self, key, factory):
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = await factory()
            return self._cache[key]
```

## 错误处理

### 1. 异步异常处理

```python
async def async_operation():
    try:
        result = await some_async_call()
        return result
    except asyncio.TimeoutError:
        logger.error("操作超时")
        raise
    except Exception as e:
        logger.error(f"异步操作失败: {e}")
        raise
```

### 2. 并发异常处理

```python
async def parallel_operations():
    tasks = [operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"操作 {i} 失败: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)
    
    return processed_results
```

## 测试指南

### 1. 异步测试

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    client = AsyncHTTPClient()
    yield client
    await client.close()

async def test_async_operation(async_client):
    result = await async_client.get_data()
    assert result is not None
```

### 2. Mock异步操作

```python
class MockAsyncClient:
    async def get_data(self):
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return {"data": "mock_result"}
```

## 迁移指南

### 1. 识别伪异步代码

查找以下模式：
- 使用`asyncio.run`包装同步代码
- 使用`run_in_executor`执行简单操作
- 使用`asyncio.sleep`模拟延迟

### 2. 迁移步骤

1. **第一阶段**：移除明显的伪异步代码
2. **第二阶段**：优化事件循环管理
3. **第三阶段**：统一异步编程模型

### 3. 兼容性保证

```python
# 提供同步和异步两个版本
class DualInterfaceTool:
    def execute(self, **kwargs):
        return self._sync_execute(**kwargs)
    
    async def execute_async(self, **kwargs):
        return await self._async_execute(**kwargs)
```

## 监控和调试

### 1. 性能监控

```python
class AsyncPerformanceMonitor:
    async def monitor_coroutine(self, coro_name, coro):
        start_time = time.time()
        try:
            result = await coro
            execution_time = time.time() - start_time
            logger.info(f"{coro_name} 执行时间: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{coro_name} 执行失败: {e}, 耗时: {execution_time:.2f}秒")
            raise
```

### 2. 调试技巧

```python
# 启用异步调试
asyncio.get_event_loop().set_debug(True)

# 使用日志追踪异步操作
logger.debug(f"开始异步操作: {operation_name}")
result = await async_operation()
logger.debug(f"完成异步操作: {operation_name}")
```

## 最佳实践总结

1. **明确分离**：同步和异步代码应该明确分离
2. **真正异步**：只对真正的I/O操作使用异步
3. **资源管理**：使用异步上下文管理器管理资源
4. **并发控制**：使用信号量控制并发数量
5. **错误处理**：正确处理异步异常
6. **性能监控**：监控异步操作的性能
7. **测试覆盖**：确保异步代码有充分的测试覆盖

## 工具和库推荐

- **HTTP客户端**：aiohttp
- **数据库**：asyncpg, aiomysql
- **任务队列**：celery, dramatiq
- **测试框架**：pytest-asyncio
- **监控**：prometheus-client, structlog

## 参考资源

- [Python asyncio 官方文档](https://docs.python.org/3/library/asyncio.html)
- [Real Python Async/Await 教程](https://realpython.com/async-io-python/)
- [AIOHTTP 文档](https://docs.aiohttp.org/)