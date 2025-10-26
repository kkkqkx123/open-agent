"""
内置工具实现

BuiltinTool用于包装项目内部的Python函数，支持同步和异步函数。
"""

import asyncio
import inspect
from typing import Any, Dict, Callable, Optional, Union
from functools import wraps

from ..base import BaseTool



class BuiltinTool(BaseTool):
    """内置工具

    用于包装项目内部Python函数的工具实现。
    """

    def __init__(self, func: Callable, config: Any):
        
        """初始化内置工具

        Args:
            func: Python函数
            config: 内置工具配置
        """
        # 从配置获取基本信息，如果未提供则从函数推断
        name = config.name or func.__name__
        description = config.description or func.__doc__ or f"内置工具: {name}"
        
        # 如果配置中提供了parameters_schema，使用它，但要根据函数签名调整required列表
        if config.parameters_schema:
            parameters_schema = self._merge_schema_with_function(config.parameters_schema, func)
        else:
            parameters_schema = self._infer_schema(func)

        super().__init__(
            name=name, description=description, parameters_schema=parameters_schema
        )

        self.func = func
        self.config = config
        self.is_async = inspect.iscoroutinefunction(func)

    def _infer_schema(self, func: Callable[..., Any]) -> Dict[str, Any]:
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

            # 构建属性描述
            param_desc = {"type": param_type, "description": f"参数 {param_name}"}

            # 添加默认值
            if param.default != inspect.Parameter.empty:
                param_desc["default"] = param.default
            else:
                # 只有在没有默认值时才添加到required列表
                required.append(param_name)

            properties[param_name] = param_desc

        return {"type": "object", "properties": properties, "required": required}

    def _merge_schema_with_function(self, schema: Dict[str, Any], func: Callable[..., Any]) -> Dict[str, Any]:
        """将提供的schema与函数签名合并，特别是根据函数签名调整required列表

        Args:
            schema: 提供的参数Schema
            func: Python函数

        Returns:
            Dict[str, Any]: 合并后的参数Schema
        """
        sig = inspect.signature(func)
        
        # 复制原始schema
        merged_schema = schema.copy()
        merged_properties = merged_schema.get("properties", {}).copy()
        
        # 根据函数签名重新确定required列表
        required = []
        for param_name, param in sig.parameters.items():
            # 跳过self参数（方法）
            if param_name == "self":
                continue
                
            # 如果参数没有默认值，则添加到required列表
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
            # 确保参数在properties中存在
            if param_name not in merged_properties:
                # 如果不在，则推断类型并添加
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
                
                param_desc = {"type": param_type, "description": f"参数 {param_name}"}
                if param.default != inspect.Parameter.empty:
                    param_desc["default"] = param.default
                    
                merged_properties[param_name] = param_desc
        
        merged_schema["properties"] = merged_properties
        merged_schema["required"] = required
        
        return merged_schema

    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        try:
            # 如果是异步函数，在事件循环中运行
            if self.is_async:
                try:
                    # 尝试获取当前运行的事件循环
                    loop = asyncio.get_running_loop()
                    # 如果已经在事件循环中，创建新的任务
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # 创建一个函数来运行异步函数
                        def run_async() -> Any:
                            return asyncio.run(self.func(**kwargs))
                        future = executor.submit(run_async)
                        return future.result()
                except RuntimeError:
                    # 没有运行的事件循环，尝试获取或创建新的事件循环
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 如果已经在事件循环中，创建新的任务
                            import concurrent.futures

                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                # 创建一个函数来运行异步函数
                                def run_async() -> Any:
                                    return asyncio.run(self.func(**kwargs))
                                future = executor.submit(run_async)
                                return future.result()
                        else:
                            return loop.run_until_complete(self.func(**kwargs))
                    except RuntimeError:
                        # 如果获取事件循环失败（可能循环已关闭），创建新的事件循环
                        # 直接调用asyncio.run运行异步函数
                        # self.func(**kwargs)返回协程对象，可以直接传递给asyncio.run
                        coro = self.func(**kwargs)
                        return asyncio.run(coro)
            else:
                # 直接调用同步函数
                return self.func(**kwargs)

        except Exception as e:
            raise ValueError(f"内置工具执行错误: {str(e)}")

    async def execute_async(self, **kwargs: Any) -> Any:
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
                # 使用lambda包装函数调用，确保参数正确传递
                return await loop.run_in_executor(None, lambda: self.func(**kwargs))

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

        from src.infrastructure.tools.config import BuiltinToolConfig
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
            from src.infrastructure.tools.config import BuiltinToolConfig
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
            def wrapper(*args: Any, **kwargs: Any) -> Any:
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
