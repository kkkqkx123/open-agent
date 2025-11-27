# 子任务3：核心工具模块重构方案

## 现状分析

### 1. 当前实现的双重方法模式

**BaseTool基类**（src/core/tools/base.py）:
- `execute(**kwargs)` - 抽象同步方法（必须由子类实现）
- `execute_async(**kwargs)` - 异步方法（默认实现：用线程池包装同步方法）
- `safe_execute()` - 安全同步执行
- `safe_execute_async()` - 安全异步执行

**RestTool实现**（src/core/tools/types/rest_tool.py）:
- ✗ 反模式：同步方法包装异步方法
  ```python
  def execute(self, **kwargs):
      loop = asyncio.new_event_loop()  # 每次调用都创建新的事件循环
      asyncio.set_event_loop(loop)
      try:
          return loop.run_until_complete(self.execute_async(**kwargs))
      finally:
          loop.close()
  ```
- 异步方法才是真实实现

**BuiltinTool实现**（src/core/tools/types/builtin_tool.py）:
- 纯同步实现，无异步方法
- 适合快速本地计算

**NativeTool实现**（src/core/tools/types/native_tool.py）:
- 纯同步实现，无异步方法
- 有状态管理

### 2. 问题识别

| 问题 | 影响 | 严重性 |
|------|------|--------|
| RestTool在同步调用时创建新事件循环 | 性能下降、资源浪费 | 🔴 高 |
| 事件循环管理不当（嵌套循环风险） | 可能导致"事件循环已运行"错误 | 🔴 高 |
| 基类设计不清晰（同异混合） | 维护困难、契约模糊 | 🟡 中 |
| 执行器没有统一处理同异兼容 | 代码重复 | 🟡 中 |

### 3. 执行器现状（src/core/tools/executor.py）

**AsyncToolExecutor**:
- ✓ 有`execute()`同步方法
- ✓ 有`execute_async()`异步方法  
- ✓ 使用线程池执行同步工具
- ✓ 异步工具直接调用`execute_async()`

---

## 重构方案：保留同步+异步双重执行模式

### 设计理由

**为什么应该保留同步和异步两种方式：**

1. **工具属性不同**：
   - 本地计算工具（Calculator）→ 同步，快速返回
   - I/O密集工具（REST、HTTP）→ 异步，避免阻塞
   - 有状态工具（Native）→ 可双向支持

2. **调用场景多样**：
   - 同步上下文（脚本、CLI）→ 需要`execute()`
   - 异步上下文（FastAPI、LangGraph）→ 需要`execute_async()`
   - 并发工具调用 → 必须异步

3. **性能优化**：
   - 快速工具不应因异步框架开销而减速
   - I/O工具应避免线程池开销，使用原生异步

4. **向后兼容**：
   - 现有同步工具继续工作
   - 新工具逐步采用最优实现

---

## 详细重构方案

### Phase 1: 修复BaseTool基类设计

**目标**：明确同步/异步职责，移除歧义

**src/core/tools/base.py**:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import asyncio
import time
from src.interfaces.tool.base import ITool, ToolResult


class BaseTool(ITool, ABC):
    """工具基类 - 支持同步和异步两种执行模式
    
    设计原则：
    1. 子类必须实现 execute() 或 execute_async() 之一（或都实现）
    2. 同步工具：只实现 execute()，异步调用通过线程池包装
    3. 异步工具：优先实现 execute_async()，同步调用通过新事件循环包装（仅在必要时）
    4. 双模工具：都实现，同步快速路径不依赖异步
    """
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        self._name = name
        self._description = description
        self._parameters_schema = parameters_schema
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return self._parameters_schema
    
    @parameters_schema.setter
    def parameters_schema(self, value: Dict[str, Any]) -> None:
        self._parameters_schema = value
    
    # ==================== 执行接口 ====================
    
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具
        
        默认实现：在新事件循环中运行 execute_async()（用于纯异步工具）
        
        子类实现选项：
        1. 重写此方法为同步实现（推荐用于本地快速工具）
        2. 不重写，使用默认异步包装（I/O密集工具）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        # 尝试使用新事件循环运行异步版本
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 当前已有事件循环，不能嵌套调用
                raise RuntimeError(
                    f"工具 {self.name} 不支持在异步上下文中同步调用。"
                    "请使用 execute_async() 或在线程池中执行。"
                )
        except RuntimeError:
            pass
        
        # 创建新事件循环执行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.execute_async(**kwargs))
        finally:
            loop.close()
    
    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具
        
        默认实现：在线程池中运行 execute()（用于纯同步工具）
        
        子类实现选项：
        1. 重写此方法为异步实现（推荐用于I/O密集工具）
        2. 不重写，使用默认线程池包装（同步工具保持兼容）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.execute(**kwargs))
    
    # ==================== 安全执行接口 ====================
    
    def safe_execute(self, **kwargs: Any) -> ToolResult:
        """安全执行工具（同步）- 包含参数验证和错误处理"""
        try:
            self.validate_parameters(kwargs)
            result, execution_time = self._measure_execution_time(
                self.execute, **kwargs
            )
            return self._create_result(
                success=True, output=result, execution_time=execution_time
            )
        except Exception as e:
            return self._create_result(success=False, error=str(e))
    
    async def safe_execute_async(self, **kwargs: Any) -> ToolResult:
        """安全执行工具（异步）- 包含参数验证和错误处理"""
        try:
            self.validate_parameters(kwargs)
            result, execution_time = await self._measure_execution_time_async(
                self.execute_async, **kwargs
            )
            return self._create_result(
                success=True, output=result, execution_time=execution_time
            )
        except Exception as e:
            return self._create_result(success=False, error=str(e))
    
    # ==================== 辅助方法 ====================
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema"""
        return self._parameters_schema
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        # [保持现有实现，省略]
        ...
    
    def initialize_context(self, session_id: Optional[str] = None) -> Optional[str]:
        """初始化工具上下文（默认实现）"""
        return session_id
    
    def cleanup_context(self) -> bool:
        """清理工具上下文（默认实现）"""
        return True
    
    def get_context_info(self) -> Optional[Dict[str, Any]]:
        """获取上下文信息（默认实现）"""
        return None
    
    def _create_result(self, success: bool, output: Any = None, 
                      error: Optional[str] = None,
                      execution_time: Optional[float] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> ToolResult:
        """创建工具执行结果"""
        return ToolResult(
            success=success,
            output=output,
            error=error,
            tool_name=self.name,
            execution_time=execution_time,
            metadata=metadata,
        )
    
    def _measure_execution_time(self, func: Any, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """测量同步函数执行时间"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result, time.time() - start_time
        except Exception:
            raise
    
    async def _measure_execution_time_async(self, func: Any, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """测量异步函数执行时间"""
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result, time.time() - start_time
        except Exception:
            raise
```

---

### Phase 2: 优化工具实现

#### 2.1 RestTool（I/O密集 → 纯异步优先）

**src/core/tools/types/rest_tool.py**:

```python
class RestTool(StatefulBaseTool):
    """REST工具 - 纯异步实现
    
    设计：
    - execute_async() 是主要实现
    - execute() 通过基类默认包装（创建新事件循环）
    - 不应在同步上下文中频繁调用 execute()
    """
    
    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具 - 主要实现"""
        try:
            session = await self._get_persistent_session()
            headers = self._build_headers(kwargs)
            url = self._build_url(kwargs)
            data = self._build_request_data(kwargs)
            
            async with session.request(
                method=self.config.method,
                url=url,
                headers=headers,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
            ) as response:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
                result = self._parse_response(response, response_data)
                
                # 更新连接状态
                conn_state = self.get_connection_state()
                self.update_connection_state({
                    'last_used': time.time(),
                    'request_count': (conn_state or {}).get('request_count', 0) + 1
                })
                
                return result
        except aiohttp.ClientError as e:
            raise ValueError(f"HTTP请求错误: {str(e)}")
        except asyncio.TimeoutError:
            raise ValueError(f"请求超时: {self.config.timeout}秒")
        except Exception as e:
            raise ValueError(f"工具执行错误: {str(e)}")
    
    # execute() 继承基类默认实现，自动通过事件循环包装异步方法
```

#### 2.2 BuiltinTool（本地快速 → 纯同步）

```python
class BuiltinTool(BaseTool):
    """内置工具 - 纯同步实现
    
    设计：
    - execute() 是直接实现
    - execute_async() 通过基类默认包装（使用线程池）
    """
    
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具 - 主要实现（快速路径）"""
        try:
            return self.func(**kwargs)
        except Exception as e:
            raise ValueError(f"内置工具执行错误: {str(e)}")
    
    # execute_async() 继承基类默认实现，通过线程池包装
```

#### 2.3 NativeTool（有状态 → 同步优先）

```python
class NativeTool(StatefulBaseTool):
    """原生工具 - 同步实现（可扩展为异步）
    
    设计：
    - execute() 是主要实现
    - execute_async() 继承基类默认包装
    """
    
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具 - 主要实现"""
        # [保持现有实现]
        ...
```

---

### Phase 3: 优化执行器

**src/core/tools/executor.py** - 完整重构：

```python
class AsyncToolExecutor(IToolExecutor, AsyncContextManager):
    """工具执行器 - 统一处理同异模式
    
    设计原则：
    1. execute() 调用同步工具 - 快速路径
    2. execute_async() 调用异步工具 - 并发路径
    3. 自动检测工具特性，选择最优执行策略
    """
    
    def __init__(
        self,
        tool_manager: Any,
        logger: ILogger,
        default_timeout: int = 30,
        max_workers: int = 4,
        max_concurrent: int = 10,
        batch_size: int = 10,
    ):
        self.tool_manager = tool_manager
        self.logger = logger
        self.default_timeout = default_timeout
        self.max_workers = max_workers
        
        self.concurrency_limiter = ConcurrencyLimiter(max_concurrent)
        self.batch_processor = AsyncBatchProcessor(batch_size)
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = AsyncLock()
    
    # ==================== 同步执行 ====================
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """同步执行工具调用
        
        策略：
        - 优先调用工具的 execute() 方法
        - 只在异步专用工具上创建事件循环
        """
        start_time = time.time()
        try:
            tool = self.tool_manager.get_tool(tool_call.name)
            timeout = tool_call.timeout or self.default_timeout
            
            self.logger.info(f"开始执行工具: {tool_call.name}")
            
            # 验证参数
            if not tool.validate_parameters(tool_call.arguments):
                return ToolResult(
                    success=False,
                    error="参数验证失败",
                    tool_name=tool_call.name,
                    execution_time=time.time() - start_time
                )
            
            # 直接调用同步方法
            if hasattr(tool, "safe_execute"):
                result = tool.safe_execute(**tool_call.arguments)
            else:
                output = tool.execute(**tool_call.arguments)
                result = ToolResult(
                    success=True, output=output, tool_name=tool_call.name
                )
            
            result.execution_time = time.time() - start_time
            
            if result.success:
                self.logger.info(
                    f"工具执行成功: {tool_call.name}, "
                    f"耗时: {result.execution_time:.2f}秒"
                )
            else:
                self.logger.error(
                    f"工具执行失败: {tool_call.name}, "
                    f"错误: {result.error}"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工具执行异常: {str(e)}"
            self.logger.error(
                f"工具执行异常: {tool_call.name}, 错误: {error_msg}"
            )
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_call.name,
                execution_time=execution_time,
            )
    
    # ==================== 异步执行 ====================
    
    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用
        
        策略：
        - 优先调用工具的 execute_async() 方法
        - 对于纯同步工具，在线程池中执行
        """
        start_time = time.time()
        try:
            tool = self.tool_manager.get_tool(tool_call.name)
            timeout = tool_call.timeout or self.default_timeout
            
            self.logger.info(f"开始异步执行工具: {tool_call.name}")
            
            # 验证参数
            if not tool.validate_parameters(tool_call.arguments):
                return ToolResult(
                    success=False,
                    error="参数验证失败",
                    tool_name=tool_call.name,
                    execution_time=time.time() - start_time
                )
            
            # 检查是否有真正的异步实现（不是基类默认包装）
            is_async_native = self._is_async_native_implementation(tool)
            
            if is_async_native:
                # 异步工具 - 直接调用
                result = await asyncio.wait_for(
                    self._execute_async_with_limit(
                        tool.safe_execute_async(**tool_call.arguments),
                        timeout
                    ),
                    timeout=timeout
                )
            else:
                # 纯同步工具 - 在线程池中执行
                thread_pool = self._thread_pool
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        thread_pool,
                        lambda: tool.safe_execute(**tool_call.arguments)
                    ),
                    timeout=timeout
                )
            
            result.execution_time = time.time() - start_time
            
            if result.success:
                self.logger.info(
                    f"异步工具执行成功: {tool_call.name}, "
                    f"耗时: {result.execution_time:.2f}秒"
                )
            else:
                self.logger.error(
                    f"异步工具执行失败: {tool_call.name}, "
                    f"错误: {result.error}"
                )
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"工具执行超时: {tool_call.timeout or self.default_timeout}秒"
            self.logger.error(f"工具超时: {tool_call.name}")
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_call.name,
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"异步工具执行异常: {str(e)}"
            self.logger.error(f"异步工具异常: {tool_call.name}, 错误: {error_msg}")
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_call.name,
                execution_time=execution_time,
            )
    
    # ==================== 辅助方法 ====================
    
    def _is_async_native_implementation(self, tool: ITool) -> bool:
        """检查工具是否有真正的异步实现
        
        返回False表示工具的execute_async()是基类默认包装的（实际是同步工具）
        """
        # 检查工具类定义中是否有execute_async的自定义实现
        tool_class = type(tool)
        
        # 获取方法的定义类
        execute_async_method = getattr(tool_class, 'execute_async', None)
        if execute_async_method is None:
            return False
        
        # 检查方法是否在基类中定义
        # 如果在子类中定义，则为真正的异步实现
        for cls in tool_class.__mro__:
            if 'execute_async' in cls.__dict__:
                # 找到定义execute_async的类
                return cls.__name__ != 'BaseTool'  # 不是基类默认实现
        
        return False
    
    async def _execute_async_with_limit(self, coro, timeout):
        """在并发限制下执行异步协程"""
        async with self.concurrency_limiter.semaphore:
            return await asyncio.wait_for(coro, timeout=timeout)
    
    def execute_parallel(
        self,
        tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """同步并行执行 - 使用线程池"""
        # [保持现有实现]
        ...
    
    async def execute_parallel_async(
        self,
        tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """异步并行执行 - 使用asyncio.gather()"""
        # [保持现有实现]
        ...
```

---

## 实施步骤

### Step 1: 更新BaseTool基类
- [ ] 修改`execute()`：明确设计为同步优先，默认包装异步
- [ ] 修改`execute_async()`：设计为异步优先，默认包装同步
- [ ] 添加`_is_async_native_implementation()`检测工具真实特性
- [ ] 更新文档说明同异模式选择

### Step 2: 优化工具实现
- [ ] RestTool：移除反模式，只实现`execute_async()`
- [ ] BuiltinTool：确保`execute()`是快速同步实现
- [ ] NativeTool：保持同步实现，`execute_async()`由基类包装

### Step 3: 优化执行器
- [ ] 实现`_is_async_native_implementation()`检测
- [ ] 同步执行器直接调用`safe_execute()`
- [ ] 异步执行器智能选择：
  - 异步工具 → 直接调用`safe_execute_async()`
  - 同步工具 → 在线程池执行`safe_execute()`

### Step 4: 测试和验证
- [ ] 单元测试：各工具的同异执行
- [ ] 集成测试：执行器的工具识别
- [ ] 性能测试：同步vs异步执行时间

### Step 5: 文档更新
- [ ] 工具开发指南：何时实现同步/异步
- [ ] 迁移指南：现有工具的改进方案

---

## 总结

| 方案特点 | 说明 |
|---------|------|
| **兼容性** | ✓ 保留同步/异步双模，现有代码无缝升级 |
| **性能** | ✓ 快速本地工具用同步，I/O工具用异步，无额外开销 |
| **易维护** | ✓ 清晰的设计原则，减少歧义 |
| **易扩展** | ✓ 工具类型定位明确，新工具易于选择实现方式 |
| **异常处理** | ✓ 检测嵌套事件循环，避免"循环已运行"错误 |

这个方案既保留了同步和异步的灵活性，又通过明确的设计原则避免了反模式和性能问题。
