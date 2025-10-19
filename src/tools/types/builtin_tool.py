"""
内置工具实现

BuiltinTool用于包装项目内部的Python函数，支持同步和异步函数。
"""

import asyncio
import inspect
from typing import Any, Dict, Callable, Optional, Union
from functools import wraps

from ..base import BaseTool
from ..config import BuiltinToolConfig


class BuiltinTool(BaseTool):
    """内置工具

    用于包装项目内部Python函数的工具实现。
    """

    def __init__(self, func: Callable, config: BuiltinToolConfig):
        """初始化内置工具

        Args:
            func: Python函数
            config: 内置工具配置
        """
        # 从配置获取基本信息，如果未提供则从函数推断
        name = config.name or func.__name__
        description = config.description or func.__doc__ or f"内置工具: {name}"
        parameters_schema = config.parameters_schema or self._infer_schema(func)

        super().__init__(
            name=name, description=description, parameters_schema=parameters_schema
        )

        self.func = func
        self.config = config
        self.is_async = inspect.iscoroutinefunction(func)

    def _infer_schema(self, func: Callable) -> Dict[str, Any]:
        """从函数签名推断参数Schema

        Args:
            func: Python函数

        Returns:
            Dict[str, Any]: 参数Schema
        """
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            # 跳过self参数（方法）
            if param_name == "self":
                continue

            # 推断参数类型
            param_type = "string"  # 默认类型
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"

            # 确定是否必需
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

            # 构建属性描述
            param_desc = {"type": param_type, "description": f"参数 {param_name}"}

            # 添加默认值
            if param.default != inspect.Parameter.empty:
                param_desc["default"] = param.default

            properties[param_name] = param_desc

        return {"type": "object", "properties": properties, "required": required}

    def execute(self, **kwargs) -> Any:
        """同步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        try:
            # 如果是异步函数，在事件循环中运行
            if self.is_async:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，创建新的任务
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.func(**kwargs))
                        return future.result()
                else:
                    return loop.run_until_complete(self.func(**kwargs))
            else:
                # 直接调用同步函数
                return self.func(**kwargs)

        except Exception as e:
            raise ValueError(f"内置工具执行错误: {str(e)}")

    async def execute_async(self, **kwargs) -> Any:
        """异步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        try:
            # 如果是异步函数，直接调用
            if self.is_async:
                return await self.func(**kwargs)
            else:
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.func, **kwargs)

        except Exception as e:
            raise ValueError(f"内置工具异步执行错误: {str(e)}")

    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> "BuiltinTool":
        """从函数创建工具实例

        Args:
            func: Python函数
            name: 工具名称（可选，默认使用函数名）
            description: 工具描述（可选，默认使用函数文档）
            parameters_schema: 参数Schema（可选，默认从函数签名推断）

        Returns:
            BuiltinTool: 工具实例
        """
        # 提供默认值
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"内置工具: {tool_name}"

        config = BuiltinToolConfig(
            name=tool_name,
            tool_type="builtin",
            description=tool_description,
            parameters_schema=parameters_schema or {},
        )

        return cls(func, config)

    @classmethod
    def create_tool(
        cls, name: str, description: str, parameters_schema: Dict[str, Any]
    ) -> Callable:
        """创建工具装饰器

        Args:
            name: 工具名称
            description: 工具描述
            parameters_schema: 参数Schema

        Returns:
            Callable: 装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            """装饰器函数

            Args:
                func: 被装饰的函数

            Returns:
                Callable: 装饰后的函数
            """
            config = BuiltinToolConfig(
                name=name,
                tool_type="builtin",
                description=description,
                parameters_schema=parameters_schema,
            )

            # 创建工具实例
            tool = cls(func, config)

            # 保留原函数属性
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            # 将工具实例附加到函数上
            setattr(wrapper, "_tool", tool)

            return wrapper

        return decorator

    def get_function(self) -> Callable:
        """获取原始函数

        Returns:
            Callable: 原始函数
        """
        return self.func

    def is_async_function(self) -> bool:
        """检查是否为异步函数

        Returns:
            bool: 是否为异步函数
        """
        return self.is_async
