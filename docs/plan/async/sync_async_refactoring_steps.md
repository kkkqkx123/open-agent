# 同步/异步重构具体执行步骤

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

### 1. 最简的同步/异步转换

使用最简单的方式进行同步/异步转换：

```python
# 推荐：直接使用 asyncio.run()
def sync_function():
    result = asyncio.run(async_function())
    return result

# 避免：复杂的事件循环管理
def sync_function_bad():
    # 不推荐使用复杂的事件循环管理器
    result = complex_event_loop_manager.run_async(async_function())
    return result
```

### 2. 并发控制

使用信号量控制并发数量：

```python
import asyncio

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

### 1. 纯异步工具（推荐）

```python
class AsyncTool(BaseTool):
    async def execute(self, **kwargs):
        # 统一的异步执行方法
        return await self.async_operation(**kwargs)
    
    async def async_operation(self, **kwargs):
        # 异步实现
        pass
```

### 2. 同步工具适配器（如需要）

```python
class SyncToolAdapter:
    """同步工具适配器，用于包装异步工具"""
    
    def __init__(self, async_tool):
        self._async_tool = async_tool
    
    def execute(self, **kwargs):
        # 简单的同步适配
        return asyncio.run(self._async_tool.execute(**kwargs))
```

### 3. 明确的工具创建

```python
# 明确创建异步工具
async_tool = AsyncTool(config)

# 如需同步支持，创建适配器
sync_tool = SyncToolAdapter(async_tool)
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
import asyncio

class AsyncCache:
    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()
    
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

### 1. 识别需要重构的代码模式

查找以下问题模式：
- 使用复杂的事件循环检测逻辑
- 同步方法包装异步方法
- 双重实现（同步+异步版本）
- 不必要的线程池包装

### 2. 重构原则

- **明确分离**：同步和异步代码应该明确分离
- **最简实现**：使用最简单的方式处理同步/异步转换
- **统一接口**：优先使用纯异步接口
- **适配器模式**：如需同步支持，使用适配器而非双重实现

## 最佳实践总结

1. **明确分离**：同步和异步代码应该明确分离，避免混用
2. **最简实践**：使用 `asyncio.run()` 进行简单的同步/异步转换
3. **真正异步**：只对真正的I/O操作使用异步，避免伪异步
4. **统一接口**：优先使用纯异步接口，避免双重实现
5. **资源管理**：使用异步上下文管理器管理资源
6. **并发控制**：使用信号量控制并发数量
7. **错误处理**：正确处理异步异常
8. **性能监控**：监控异步操作的性能
9. **测试覆盖**：确保异步代码有充分的测试覆盖

---

## 概述

本文档提供具体的检查与分析步骤，用于逐步检查代码库中的同步/异步混用问题并进行修改。每个子任务关注特定模块，包含查看、确认、执行步骤。

## 子任务 1：服务层模块 (src/services/)

### 1.1 查看步骤

**目标**：识别服务层中的同步调用异步代码问题

**执行命令**：
```bash
# 搜索服务层中的 asyncio.run 使用
grep -r "asyncio\.run" src/services/ --include="*.py"

# 搜索服务层中的事件循环管理
grep -r "asyncio\.get_event_loop\|asyncio\.new_event_loop" src/services/ --include="*.py"
```

**重点检查文件**：
- `src/services/state/snapshots.py`
- `src/services/state/persistence.py`
- `src/services/state/history.py`
- `src/services/prompts/loader.py`
- `src/services/llm/fallback_system/`

### 1.2 确认步骤

**检查清单**：
1. [ ] 确认每个 `asyncio.run()` 调用的上下文
2. [ ] 确认是否存在同步方法调用异步 Repository
3. [ ] 确认是否有重复的事件循环创建/销毁模式
4. [ ] 确认是否有复杂的线程池处理逻辑

**示例检查**：
```python
# 在 src/services/state/snapshots.py 中检查
def save_snapshot(self, snapshot: StateSnapshot) -> str:
    # 问题：同步方法调用异步 Repository
    snapshot_id = asyncio.run(self._snapshot_repository.save_snapshot(snapshot_dict))
    return snapshot_id
```

### 1.3 执行步骤

**重构方案**：

**步骤 1.3.1**：创建异步版本的服务方法
```python
# 在 src/services/state/snapshots.py 中添加
class SnapshotService:
    async def save_snapshot_async(self, snapshot: StateSnapshot) -> str:
        """异步保存快照"""
        snapshot_dict = {
            "snapshot_id": snapshot.snapshot_id,
            "agent_id": snapshot.agent_id,
            "domain_state": snapshot.domain_state,
            "timestamp": snapshot.timestamp,
            "snapshot_name": snapshot.snapshot_name,
            "metadata": snapshot.metadata
        }
        
        # 直接异步调用，无需转换
        snapshot_id = await self._snapshot_repository.save_snapshot(snapshot_dict)
        
        # 更新缓存
        self._update_cache(snapshot)
        
        # 清理旧快照
        await self.cleanup_old_snapshots_async(snapshot.agent_id)
        
        return snapshot_id
    
    async def cleanup_old_snapshots_async(self, agent_id: str):
        """异步清理旧快照"""
        # 将同步方法改为异步
        snapshots = await self._snapshot_repository.get_snapshots(agent_id, limit=1000)
        # ... 清理逻辑
```

**步骤 1.3.2**：保留同步方法作为适配器（临时）
```python
def save_snapshot(self, snapshot: StateSnapshot) -> str:
    """同步保存快照（适配器方法）"""
    # 添加弃用警告
    import warnings
    warnings.warn(
        "save_snapshot is deprecated, use save_snapshot_async instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 调用异步版本
    return asyncio.run(self.save_snapshot_async(snapshot))
```

**步骤 1.3.3**：更新调用方
```python
# 查找所有调用 save_snapshot 的地方
grep -r "save_snapshot" src/ --include="*.py"

# 逐步更新为异步调用
# 原代码：
# snapshot_id = snapshot_service.save_snapshot(snapshot)

# 新代码：
# snapshot_id = await snapshot_service.save_snapshot_async(snapshot)
```

## 子任务 2：适配器层模块 (src/adapters/)

### 2.1 查看步骤

**目标**：识别适配器层中的复杂同步/异步处理

**执行命令**：
```bash
# 搜索适配器层中的复杂事件循环处理
grep -r -A 10 -B 5 "asyncio\.get_event_loop" src/adapters/ --include="*.py"

# 搜索线程池使用
grep -r -A 5 -B 5 "ThreadPoolExecutor" src/adapters/ --include="*.py"
```

**重点检查文件**：
- `src/adapters/storage/adapters/sync_adapter.py`
- `src/adapters/storage/factory.py`
- `src/adapters/storage/core/transaction.py`
- `src/adapters/cli/commands.py`
- `src/adapters/tui/`

### 2.2 确认步骤

**检查清单**：
1. [ ] 确认是否有复杂的事件循环检测逻辑
2. [ ] 确认是否有线程池包装异步调用
3. [ ] 确认是否有同步/异步双重实现
4. [ ] 确认是否有不必要的事件循环创建

**示例检查**：
```python
# 在 src/adapters/storage/adapters/sync_adapter.py 中检查
def begin_transaction(self):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 复杂的线程池处理
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._transaction_manager.begin_transaction())
                future.result()
        else:
            asyncio.run(self._transaction_manager.begin_transaction())
    except Exception as e:
        logger.error(f"Failed to begin transaction: {e}")
        raise
```

### 2.3 执行步骤

**重构方案**：

**步骤 2.3.1**：简化同步适配器
```python
# 在 src/adapters/storage/adapters/sync_adapter.py 中简化
class SyncStorageAdapter:
    def begin_transaction(self):
        """开始事务（简化版本）"""
        try:
            # 直接调用，移除复杂的事件循环检测
            return asyncio.run(self._transaction_manager.begin_transaction())
        except Exception as e:
            logger.error(f"Failed to begin transaction: {e}")
            raise
    
    def commit_transaction(self):
        """提交事务（简化版本）"""
        try:
            return asyncio.run(self._transaction_manager.commit_transaction())
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise
```

**步骤 2.3.2**：创建纯异步适配器
```python
# 创建新文件 src/adapters/storage/adapters/async_adapter.py
class AsyncStorageAdapter:
    """纯异步存储适配器"""
    
    def __init__(self, backend):
        self._backend = backend
        self._transaction_manager = AsyncTransactionManager(backend)
    
    async def begin_transaction(self):
        """异步开始事务"""
        return await self._transaction_manager.begin_transaction()
    
    async def commit_transaction(self):
        """异步提交事务"""
        return await self._transaction_manager.commit_transaction()
    
    async def rollback_transaction(self):
        """异步回滚事务"""
        return await self._transaction_manager.rollback_transaction()
```

**步骤 2.3.3**：更新工厂模式
```python
# 在 src/adapters/storage/factory.py 中
class StorageFactory:
    @staticmethod
    def create_adapter(backend_type: str, async_mode: bool = False):
        backend = StorageFactory.create_backend(backend_type)
        
        if async_mode:
            return AsyncStorageAdapter(backend)
        else:
            return SyncStorageAdapter(backend)
```

## 子任务 3：核心工具模块 (src/core/tools/)

### 3.1 查看步骤

**目标**：识别工具层中的同步/异步双重实现

**执行命令**：
```bash
# 搜索工具层中的双重实现
grep -r -A 5 "def execute" src/core/tools/ --include="*.py"
grep -r -A 5 "def execute_async" src/core/tools/ --include="*.py"

# 搜索事件循环创建
grep -r -A 10 -B 5 "asyncio\.new_event_loop" src/core/tools/ --include="*.py"
```

**重点检查文件**：
- `src/core/tools/types/rest_tool.py`
- `src/core/tools/types/mcp_tool.py`
- `src/core/tools/types/rest/`
- `src/core/tools/executor.py`

### 3.2 确认步骤

**检查清单**：
1. [ ] 确认每个工具是否有同步和异步两个版本
2. [ ] 确认同步方法是否包装异步方法
3. [ ] 确认是否有重复的事件循环管理代码
4. [ ] 确认是否有不必要的复杂性

**示例检查**：
```python
# 在 src/core/tools/types/rest_tool.py 中检查
def execute(self, **kwargs):
    # 同步方法包装异步方法
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(self.execute_async(**kwargs))
    finally:
        loop.close()

async def execute_async(self, **kwargs):
    # 真正的异步实现
    pass
```

### 3.3 执行步骤

**重构方案**：

**步骤 3.3.1**：统一为异步实现
```python
# 在 src/core/tools/types/rest_tool.py 中
class RestTool:
    """REST 工具（纯异步实现）"""
    
    async def execute(self, **kwargs):
        """统一的异步执行方法"""
        return await self._http_client.request(**kwargs)
    
    # 移除 execute_async 方法，统一使用 execute
    
    # 如果需要同步支持，创建适配器
    class SyncAdapter:
        def __init__(self, async_tool):
            self._async_tool = async_tool
        
        def execute(self, **kwargs):
            return asyncio.run(self._async_tool.execute(**kwargs))
```

**步骤 3.3.2**：更新工具执行器
```python
# 在 src/core/tools/executor.py 中
class AsyncToolExecutor:
    """异步工具执行器"""
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具"""
        tool = self.tool_manager.get_tool(tool_call.name)
        
        # 直接调用异步方法
        if hasattr(tool, 'execute') and asyncio.iscoroutinefunction(tool.execute):
            result = await tool.execute(**tool_call.arguments)
        else:
            # 对于同步工具，在线程池中执行
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, tool.execute, **tool_call.arguments)
        
        return ToolResult(success=True, output=result, tool_name=tool_call.name)
```

## 子任务 4：工作流模块 (src/core/workflow/)

### 4.1 查看步骤

**目标**：识别工作流中的同步/异步混用问题

**执行命令**：
```bash
# 搜索工作流中的事件循环处理
grep -r -A 10 -B 5 "asyncio\." src/core/workflow/ --include="*.py"

# 搜索执行模式
grep -r -A 5 "execute.*async\|async.*execute" src/core/workflow/ --include="*.py"
```

**重点检查文件**：
- `src/core/workflow/execution/modes/`
- `src/core/workflow/execution/core/`
- `src/core/workflow/graph/nodes/`
- `src/core/workflow/loading/`
- `src/core/workflow/orchestration/`

### 4.2 确认步骤

**检查清单**：
1. [ ] 确认执行模式中的同步/异步处理
2. [ ] 确认节点执行中的事件循环管理
3. [ ] 确认是否有不必要的复杂性
4. [ ] 确认是否有重复的模式

### 4.3 执行步骤

**重构方案**：

**步骤 4.3.1**：简化执行模式
```python
# 在 src/core/workflow/execution/modes/async_mode.py 中
class AsyncExecutionMode:
    """纯异步执行模式"""
    
    async def execute_node(self, node, state, context):
        """异步执行节点"""
        # 直接异步执行，无需复杂的事件循环检测
        if hasattr(node, 'execute_async'):
            return await node.execute_async(state, context)
        else:
            # 同步节点在线程池中执行
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, node.execute, state, context)
```

**步骤 4.3.2**：统一节点接口
```python
# 在 src/core/workflow/graph/nodes/base.py 中
class BaseNode:
    """基础节点（统一异步接口）"""
    
    async def execute(self, state, context):
        """统一的异步执行方法"""
        raise NotImplementedError
    
    # 移除同步版本的 execute 方法
```

## 子任务 5：CLI 和 TUI 模块 (src/adapters/cli/, src/adapters/tui/)

### 5.1 查看步骤

**目标**：识别用户界面层中的同步/异步处理

**执行命令**：
```bash
# 搜索 CLI 中的异步调用
grep -r -A 5 -B 5 "asyncio\.run" src/adapters/cli/ --include="*.py"

# 搜索 TUI 中的异步处理
grep -r -A 10 -B 5 "asyncio\." src/adapters/tui/ --include="*.py"
```

**重点检查文件**：
- `src/adapters/cli/commands.py`
- `src/adapters/cli/run_command.py`
- `src/adapters/tui/state_manager.py`
- `src/adapters/tui/session_handler.py`

### 5.2 确认步骤

**检查清单**：
1. [ ] 确认 CLI 命令中的异步调用
2. [ ] 确认 TUI 中的状态管理异步处理
3. [ ] 确认是否有适当的错误处理
4. [ ] 确认用户体验是否受影响

### 5.3 执行步骤

**重构方案**：

**步骤 5.3.1**：简化 CLI 命令
```python
# 在 src/adapters/cli/commands.py 中
def list_sessions(format="table"):
    """列出会话（简化版本）"""
    try:
        container = get_global_container()
        session_manager = container.get(ISessionManager)
        
        # 直接调用，移除复杂的事件循环检测
        sessions = asyncio.run(session_manager.list_sessions())
        
        if format == "table":
            _print_sessions_table(sessions)
        else:
            print(json.dumps(sessions, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return 1
```

**步骤 5.3.2**：优化 TUI 状态管理
```python
# 在 src/adapters/tui/state_manager.py 中
class StateManager:
    """TUI 状态管理器（优化版本）"""
    
    def create_session(self, workflow_config: str, agent_config: Optional[str] = None) -> bool:
        """创建会话（简化版本）"""
        try:
            if not self.session_manager:
                return False
            
            # 创建用户请求
            user_request = UserRequestEntity(
                request_id=f"request_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id="",
                content=f"创建会话: {workflow_config}",
                metadata={
                    "workflow_config": workflow_config,
                    "agent_config": agent_config
                },
                timestamp=datetime.now()
            )
            
            # 直接调用，移除复杂的导入
            self.session_id = asyncio.run(
                self.session_manager.create_session(user_request)
            )
            
            if not self.session_id:
                return False

            # 清空消息历史
            self.message_history = []
            
            # 添加系统消息
            self.message_history.append({
                "type": "system",
                "content": f"新会话已创建: {self.session_id[:8]}..."
            })
            
            return True
            
        except Exception as e:
            print(f"创建会话失败: {e}")
            return False
```

## 子任务 6：验证和测试

### 6.1 查看步骤

**目标**：确保重构后的代码功能正确

**执行命令**：
```bash
# 运行相关测试
pytest tests/unit/services/ -v
pytest tests/unit/adapters/ -v
pytest tests/unit/core/tools/ -v
pytest tests/unit/core/workflow/ -v

# 检查类型错误
mypy src/services/ --follow-imports=silent
mypy src/adapters/ --follow-imports=silent
mypy src/core/tools/ --follow-imports=silent
mypy src/core/workflow/ --follow-imports=silent
```

### 6.2 确认步骤

**检查清单**：
1. [ ] 确认所有测试通过
2. [ ] 确认没有类型错误
3. [ ] 确认没有性能回归
4. [ ] 确认用户体验正常

### 6.3 执行步骤

**验证方案**：

**步骤 6.3.1**：功能测试
```python
# 创建测试文件 test_refactoring.py
import asyncio
import pytest
from src.services.state.snapshots import SnapshotService

class TestRefactoring:
    async def test_async_snapshot_service(self):
        """测试异步快照服务"""
        service = SnapshotService()
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot",
            agent_id="test_agent",
            domain_state={"key": "value"},
            timestamp="2023-01-01T00:00:00",
            snapshot_name="test_snapshot"
        )
        
        # 测试异步方法
        snapshot_id = await service.save_snapshot_async(snapshot)
        assert snapshot_id == "test_snapshot"
    
    def test_sync_adapter(self):
        """测试同步适配器"""
        service = SnapshotService()
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot",
            agent_id="test_agent",
            domain_state={"key": "value"},
            timestamp="2023-01-01T00:00:00",
            snapshot_name="test_snapshot"
        )
        
        # 测试同步适配器
        snapshot_id = service.save_snapshot(snapshot)
        assert snapshot_id == "test_snapshot"
```

**步骤 6.3.2**：性能测试
```python
# 创建性能测试
import time
import asyncio

def benchmark_sync_vs_async():
    """性能基准测试"""
    service = SnapshotService()
    snapshot = StateSnapshot(
        snapshot_id="benchmark_snapshot",
        agent_id="benchmark_agent",
        domain_state={"key": "value"},
        timestamp="2023-01-01T00:00:00",
        snapshot_name="benchmark_snapshot"
    )
    
    # 测试同步版本
    start_time = time.time()
    for _ in range(100):
        service.save_snapshot(snapshot)
    sync_time = time.time() - start_time
    
    # 测试异步版本
    async def async_benchmark():
        start_time = time.time()
        for _ in range(100):
            await service.save_snapshot_async(snapshot)
        return time.time() - start_time
    
    async_time = asyncio.run(async_benchmark())
    
    print(f"同步版本: {sync_time:.2f}s")
    print(f"异步版本: {async_time:.2f}s")
    print(f"性能提升: {((sync_time - async_time) / sync_time * 100):.1f}%")
```

## 执行顺序建议

1. **从底层开始**：先重构 Repository 层，然后是服务层，最后是适配器层
2. **逐步验证**：每个子任务完成后都要运行测试验证
3. **保持兼容**：在重构过程中保留同步接口作为适配器
4. **文档更新**：及时更新相关文档和使用示例

## 注意事项

1. **不要一次性重构所有模块**，按子任务逐步进行
2. **每次重构后都要运行测试**，确保功能正确
3. **保留向后兼容性**，在重构过程中提供适配器
4. **关注性能影响**，确保重构不会导致性能回归
5. **更新相关文档**，确保开发者了解新的使用方式