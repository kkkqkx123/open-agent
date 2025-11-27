"""
工具基类实现

定义了所有工具类型的基础抽象类，提供通用的工具接口和功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import asyncio
import time
import json

from src.interfaces.tool.base import ITool, ToolResult


class BaseTool(ITool, ABC):
    """工具基类 - 支持多种实现模式
    
    设计目标：工具系统应该包容各种工具类型，不强制统一的执行方式。
    
    三种工具实现模式：
    ═════════════════════════════════════════════════════════════════════════
    
    【模式1】纯同步工具（本地计算密集）
    ───────────────────────────────────────
    适用场景：CPU密集、本地操作、快速完成、无I/O等待
    
    示例：
        class Calculator(BaseTool):
            def execute(self, x: int, y: int) -> int:
                return x + y
            # execute_async()会自动在线程池中调用execute()
    
    性能特征：
        同步调用: T = 直接执行时间
        异步调用: T = 线程调度 + 直接执行时间 + 上下文切换
    
    何时使用：
        ✓ 函数本身很快（<100ms）
        ✓ 不涉及I/O
        ✓ CPU密集操作
        ✗ 不适合长时间阻塞
    
    
    【模式2】纯异步工具（I/O密集）
    ───────────────────────────────────────
    适用场景：网络请求、数据库查询、文件I/O、外部API调用
    
    示例：
        class APIClient(BaseTool):
            async def execute_async(self, url: str) -> str:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        return await resp.text()
            # execute()会自动创建新事件循环调用execute_async()
    
    性能特征：
        同步调用: T = 新循环开销 + I/O等待时间 + 关闭开销
        异步调用: T = I/O等待时间（无线程开销！）
    
    何时使用：
        ✓ I/O密集操作
        ✓ 需要处理长延迟
        ✓ 在异步上下文中频繁调用
        ⚠ 同步调用时会有循环创建开销
    
    
    【模式3】混合工具（优化路径）
    ───────────────────────────────────────
    适用场景：需要同时优化同步和异步调用路径
    
    示例：
        class CachingAPI(BaseTool):
            def __init__(self):
                self.cache = {}
            
            def execute(self, key: str) -> str:
                # 同步快速路径：检查缓存
                if key in self.cache:
                    return self.cache[key]
                # 如果没有缓存，执行同步请求
                return requests.get(f"https://api.example.com/{key}").text
            
            async def execute_async(self, key: str) -> str:
                # 异步优化路径：异步请求+缓存
                if key in self.cache:
                    return self.cache[key]
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.example.com/{key}") as resp:
                        result = await resp.text()
                        self.cache[key] = result
                        return result
    
    性能特征：
        同步调用: T = 缓存检查 + 同步网络请求
        异步调用: T = 缓存检查 + 异步网络请求（无额外开销）
    
    何时使用：
        ✓ 既有缓存也有I/O
        ✓ 同步和异步调用都很频繁
        ✓ 需要两种调用路径都高效
    
    重要：两个方法应该返回相同的结果！
    
    ═════════════════════════════════════════════════════════════════════════
    
    设计原则：
    1. 子类应该明确自己属于哪种模式
    2. 只实现必要的方法（其他会自动适配）
    3. 如果两个都实现，确保结果一致（幂等性）
    4. 不要在两个方法间相互调用（会导致性能问题）
    5. 通过重写方法来优化性能，不要依赖默认实现
    """

    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        """初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            parameters_schema: 参数JSON Schema
        """
        self._name = name
        self._description = description
        self._parameters_schema = parameters_schema

    @property
    def name(self) -> str:
        """工具名称"""
        return self._name

    @property
    def description(self) -> str:
        """工具描述"""
        return self._description

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """参数Schema"""
        return self._parameters_schema

    @parameters_schema.setter
    def parameters_schema(self, value: Dict[str, Any]) -> None:
        """设置参数Schema"""
        self._parameters_schema = value

    # ==================== 执行接口 ====================
    
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具
        
        default默认实现取决于子类：
        
        1. 如果子类重写此方法 → 直接执行该方法
        2. 如果子类只实现execute_async() → 在新循环中运行execute_async()
        
        行为：
        ├─ 首先检查是否在运行的事件循环中（avoid嵌套循环）
        ├─ 如果在循环中，抛出RuntimeError
        └─ 如果不在循环中，创建新循环运行execute_async()
        
        推荐实现（根据工具类型）：
        
        【纯同步工具】
        class FastTool(BaseTool):
            def execute(self, **kwargs):
                return self.func(**kwargs)
            # 使用默认execute_async()（线程池方式）
        
        【纯异步工具】
        class AsyncTool(BaseTool):
            # 不重写execute()
            # 使用默认实现（创建新循环）
        
        【混合工具】
        class HybridTool(BaseTool):
            def execute(self, **kwargs):
                # 同步快速路径
                return self._sync_path(**kwargs)
            
            async def execute_async(self, **kwargs):
                # 异步优化路径
                return await self._async_path(**kwargs)
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
            
        Raises:
            RuntimeError: 在嵌套事件循环中调用（避免死锁）
        """
        # 检查是否已有运行中的事件循环（避免嵌套）
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                f"工具 {self.name} 不支持在异步上下文中同步调用。"
                "请使用 execute_async() 或在线程池中执行。"
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
        
        # 创建新事件循环执行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.execute_async(**kwargs))
        finally:
            loop.close()

    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具
        
        默认实现取决于子类：
        
        1. 如果子类重写此方法 → 直接执行该方法
        2. 如果子类只实现execute() → 在线程池中运行execute()
        
        行为：
        └─ 获取当前事件循环，在线程池中运行execute()
        
        推荐实现（根据工具类型）：
        
        【纯同步工具】
        class FastTool(BaseTool):
            def execute(self, **kwargs):
                return heavy_computation(**kwargs)
            # 使用默认execute_async()（线程池方式）
            # 异步调用会委托给线程池：避免阻塞事件循环
        
        【纯异步工具】
        class AsyncTool(BaseTool):
            async def execute_async(self, **kwargs):
                return await aiohttp.get(...)
            # 不重写execute()
            # 使用默认execute()（创建新循环）
        
        【混合工具】
        class HybridTool(BaseTool):
            def execute(self, **kwargs):
                # 同步快速路径
                return self._sync_path(**kwargs)
            
            async def execute_async(self, **kwargs):
                # 异步优化路径
                return await self._async_path(**kwargs)
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        
        Note:
            纯同步工具在异步调用时会使用线程池，这增加了少量开销（线程调度）。
            如果纯同步工具是I/O密集的，应考虑改为纯异步工具。
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.execute(**kwargs))

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema

        Returns:
            Dict[str, Any]: 工具参数Schema
        """
        return self._parameters_schema

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数

        Args:
            parameters: 待验证的参数

        Returns:
            bool: 验证是否成功
            
        Raises:
            ValueError: 参数验证失败
        """
        try:
            # 基础参数验证逻辑
            required_params = self._parameters_schema.get("required", [])

            # 检查必需参数
            for param in required_params:
                if param not in parameters:
                    raise ValueError(f"缺少必需参数: {param}")

            # 检查参数类型
            properties = self._parameters_schema.get("properties", {})
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    param_schema = properties[param_name]
                    expected_type = param_schema.get("type")

                    if expected_type == "string" and not isinstance(param_value, str):
                        raise ValueError(f"参数 {param_name} 应为字符串类型")
                    elif expected_type == "number" and not isinstance(
                        param_value, (int, float)
                    ):
                        raise ValueError(f"参数 {param_name} 应为数字类型")
                    elif expected_type == "integer" and not isinstance(param_value, int):
                        raise ValueError(f"参数 {param_name} 应为整数类型")
                    elif expected_type == "boolean" and not isinstance(param_value, bool):
                        raise ValueError(f"参数 {param_name} 应为布尔类型")
                    elif expected_type == "array" and not isinstance(param_value, list):
                        raise ValueError(f"参数 {param_name} 应为数组类型")
                    elif expected_type == "object" and not isinstance(param_value, dict):
                        raise ValueError(f"参数 {param_name} 应为对象类型")

            return True
        except ValueError:
            # 重新抛出 ValueError
            raise
        except Exception as e:
            raise ValueError(f"参数验证失败: {str(e)}")

    def initialize_context(self, session_id: Optional[str] = None) -> Optional[str]:
        """初始化工具上下文（默认实现）
        
        对于无状态工具（如BuiltinTool），此方法为空实现。
        有状态工具（如StatefulBaseTool）会重写此方法。
        """
        return session_id

    def cleanup_context(self) -> bool:
        """清理工具上下文（默认实现）
        
        对于无状态工具（如BuiltinTool），此方法为空实现。
        有状态工具（如StatefulBaseTool）会重写此方法。
        """
        return True

    def get_context_info(self) -> Optional[Dict[str, Any]]:
        """获取上下文信息（默认实现）
        
        对于无状态工具（如BuiltinTool），此方法返回None。
        有状态工具（如StatefulBaseTool）会重写此方法。
        """
        return None

    def _create_result(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """创建工具执行结果

        Args:
            success: 是否成功
            output: 输出结果
            error: 错误信息
            execution_time: 执行时间
            metadata: 元数据

        Returns:
            ToolResult: 执行结果
        """
        return ToolResult(
            success=success,
            output=output,
            error=error,
            tool_name=self.name,
            execution_time=execution_time,
            metadata=metadata,
        )

    def _measure_execution_time(self, func: Any, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """测量函数执行时间

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            tuple: (执行结果, 执行时间)
        """
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            raise e

    async def _measure_execution_time_async(self, func: Any, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """测量异步函数执行时间

        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            tuple: (执行结果, 执行时间)
        """
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            raise e

    def safe_execute(self, **kwargs: Any) -> ToolResult:
        """安全执行工具（同步）

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 验证参数
            self.validate_parameters(kwargs)

            # 执行并测量时间
            result, execution_time = self._measure_execution_time(
                self.execute, **kwargs
            )

            return self._create_result(
                success=True, output=result, execution_time=execution_time
            )
        except Exception as e:
            return self._create_result(success=False, error=str(e))

    async def safe_execute_async(self, **kwargs: Any) -> ToolResult:
        """安全执行工具（异步）

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 验证参数
            self.validate_parameters(kwargs)

            # 执行并测量时间
            result, execution_time = await self._measure_execution_time_async(
                self.execute_async, **kwargs
            )

            return self._create_result(
                success=True, output=result, execution_time=execution_time
            )
        except Exception as e:
            return self._create_result(success=False, error=str(e))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 工具信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._parameters_schema,
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)