"""改进的内置工具实现

移除不必要的异步包装，提供清晰的同步/异步分离。
"""

import asyncio
import inspect
from typing import Any, Dict, Callable, Optional, Union, Coroutine
from functools import wraps
import logging

from ..base import BaseTool

logger = logging.getLogger(__name__)


class SyncRestTool(BaseTool):
    """同步内置工具
    
    专门用于包装同步函数，不涉及异步包装。
    """
    
    def __init__(self, func: Callable, config: Any):
        """初始化同步内置工具
        
        Args:
            func: 同步Python函数
            config: 内置工具配置
        """
        # 确保函数是同步的
        if inspect.iscoroutinefunction(func):
            raise ValueError("SyncRestTool只能包装同步函数")
        
        # 从配置获取基本信息
        name = config.name or func.__name__
        description = config.description or func.__doc__ or f"内置工具: {name}"
        
        # 处理参数Schema
        if config.parameters_schema:
            parameters_schema = self._merge_schema_with_function(config.parameters_schema, func)
        else:
            parameters_schema = self._infer_schema(func)
        
        super().__init__(
            name=name, 
            description=description, 
            parameters_schema=parameters_schema
        )
        
        self.func = func
        self.config = config
    
    def _infer_schema(self, func: Callable[..., Any]) -> Dict[str, Any]:
        """从函数签名推断参数Schema"""
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            # 推断参数类型
            param_type = "string"
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
                required.append(param_name)
            
            properties[param_name] = param_desc
        
        return {"type": "object", "properties": properties, "required": required}
    
    def _merge_schema_with_function(self, schema: Dict[str, Any], func: Callable[..., Any]) -> Dict[str, Any]:
        """将提供的schema与函数签名合并"""
        sig = inspect.signature(func)
        
        merged_schema = schema.copy()
        merged_properties = merged_schema.get("properties", {}).copy()
        
        # 根据函数签名重新确定required列表
        required = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
            # 确保参数在properties中存在
            if param_name not in merged_properties:
                param_type = "string"
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
            # 直接调用同步函数
            return self.func(**kwargs)
        except Exception as e:
            raise ValueError(f"同步内置工具执行错误: {str(e)}")
    
    def get_function(self) -> Callable:
        """获取原始函数"""
        return self.func
    
    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> "SyncRestTool":
        """从函数创建工具实例"""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"内置工具: {tool_name}"
        
        from src.core.tools.config import NativeToolConfig
        config = NativeToolConfig(
            name=tool_name,
            tool_type="Native_sync",
            description=tool_description,
            parameters_schema=parameters_schema or {},
        )
        
        return cls(func, config)


class AsyncRestTool(BaseTool):
    """异步内置工具
    
    专门用于包装异步函数，提供真正的异步执行。
    """
    
    def __init__(self, func: Callable, config: Any):
        """初始化异步内置工具
        
        Args:
            func: 异步Python函数
            config: 内置工具配置
        """
        # 确保函数是异步的
        if not inspect.iscoroutinefunction(func):
            raise ValueError("AsyncRestTool只能包装异步函数")
        
        # 从配置获取基本信息
        name = config.name or func.__name__
        description = config.description or func.__doc__ or f"异步内置工具: {name}"
        
        # 处理参数Schema
        if config.parameters_schema:
            parameters_schema = self._merge_schema_with_function(config.parameters_schema, func)
        else:
            parameters_schema = self._infer_schema(func)
        
        super().__init__(
            name=name, 
            description=description, 
            parameters_schema=parameters_schema
        )
        
        self.func = func
        self.config = config
    
    def _infer_schema(self, func: Callable[..., Any]) -> Dict[str, Any]:
        """从函数签名推断参数Schema"""
        # 与SyncRestTool相同的实现
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            param_type = "string"
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
            else:
                required.append(param_name)
            
            properties[param_name] = param_desc
        
        return {"type": "object", "properties": properties, "required": required}
    
    def _merge_schema_with_function(self, schema: Dict[str, Any], func: Callable[..., Any]) -> Dict[str, Any]:
        """将提供的schema与函数签名合并"""
        # 与SyncRestTool相同的实现
        sig = inspect.signature(func)
        
        merged_schema = schema.copy()
        merged_properties = merged_schema.get("properties", {}).copy()
        
        required = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
            if param_name not in merged_properties:
                param_type = "string"
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
    
    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        try:
            # 直接调用异步函数
            return await self.func(**kwargs)
        except Exception as e:
            raise ValueError(f"异步内置工具执行错误: {str(e)}")
    
    
    def get_function(self) -> Callable:
        """获取原始函数"""
        return self.func
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具（通过事件循环管理器）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        # 优化：检查是否已在事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果已在事件循环中，创建任务并等待
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self.execute_async(**kwargs))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，使用EventLoopManager
            from src.infrastructure.async_utils.event_loop_manager import run_async
            return run_async(self.execute_async(**kwargs))
    
    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> "AsyncRestTool":
        """从函数创建工具实例"""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"异步内置工具: {tool_name}"
        
        from src.core.tools.config import NativeToolConfig
        config = NativeToolConfig(
            name=tool_name,
            tool_type="Native_async",
            description=tool_description,
            parameters_schema=parameters_schema or {},
        )
        
        return cls(func, config)


class RestToolFactory:
    """内置工具工厂
    
    根据函数类型自动选择合适的工具实现。
    """
    
    @staticmethod
    def create_tool(
        func: Callable,
        config: Any,
    ) -> Union[SyncRestTool, AsyncRestTool]:
        """根据函数类型创建工具
        
        Args:
            func: Python函数
            config: 工具配置
            
        Returns:
            Union[SyncRestTool, AsyncRestTool]: 工具实例
        """
        if inspect.iscoroutinefunction(func):
            return AsyncRestTool(func, config)
        else:
            return SyncRestTool(func, config)
    
    @staticmethod
    def create_sync_tool(
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> SyncRestTool:
        """创建同步工具"""
        from src.core.tools.config import NativeToolConfig
        config = NativeToolConfig(
            name=name or func.__name__,
            tool_type="Native_sync",
            description=description or func.__doc__ or f"内置工具: {name}",
            parameters_schema=parameters_schema or {},
        )
        return SyncRestTool(func, config)
    
    @staticmethod
    def create_async_tool(
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> AsyncRestTool:
        """创建异步工具"""
        from src.core.tools.config import NativeToolConfig
        config = NativeToolConfig(
            name=name or func.__name__,
            tool_type="Native_async",
            description=description or func.__doc__ or f"异步内置工具: {name}",
            parameters_schema=parameters_schema or {},
        )
        return AsyncRestTool(func, config)


# 装饰器支持
def sync_Native_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_schema: Optional[Dict[str, Any]] = None,
):
    """同步内置工具装饰器"""
    def decorator(func: Callable) -> Callable:
        tool = RestToolFactory.create_sync_tool(func, name, description, parameters_schema)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 使用setattr动态添加_tool属性以避免类型检查错误
        setattr(wrapper, '_tool', tool)
        return wrapper
    
    return decorator


def async_Native_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_schema: Optional[Dict[str, Any]] = None,
):
    """异步内置工具装饰器"""
    def decorator(func: Callable) -> Callable:
        tool = RestToolFactory.create_async_tool(func, name, description, parameters_schema)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 使用setattr动态添加_tool属性以避免类型检查错误
        setattr(wrapper, '_tool', tool)
        return wrapper
    
    return decorator