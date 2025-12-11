"""
内置工具实现

BuiltinTool用于简单的、无状态的内置功能，如计算器、哈希转换等。
"""

import asyncio
import inspect
from typing import Any, Dict, Callable, Optional, Union, Coroutine
from functools import wraps
from src.interfaces.dependency_injection import get_logger

from ..base import BaseTool

logger = get_logger(__name__)


class BuiltinTool(BaseTool):
    """内置工具 - 纯同步实现
    
    用于包装简单的、无状态的Python函数，如计算器、哈希转换等。
    
    设计：
    - execute() 是直接实现（快速同步路径）
    - execute_async() 通过基类默认包装（使用线程池）
    """
    
    def __init__(self, func: Callable, config: Any):
        """初始化内置工具
        
        Args:
            func: Python函数
            config: 工具配置
        """
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
        """执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        try:
            # 直接调用函数
            return self.func(**kwargs)
        except Exception as e:
            raise ValueError(f"内置工具执行错误: {str(e)}")
    
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
    ) -> "BuiltinTool":
        """从函数创建工具实例"""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"内置工具: {tool_name}"
        
        # 创建一个简单的配置对象
        class SimpleConfig:
            def __init__(self):
                self.name = tool_name
                self.description = tool_description
                self.parameters_schema = parameters_schema or {}
        
        config = SimpleConfig()
        return cls(func, config)