"""
原生工具实现

NativeTool用于复杂的、有状态的项目内实现工具。
"""

import asyncio
import inspect
import time
from typing import Any, Dict, Callable, Optional, Union, Coroutine
from functools import wraps
from src.interfaces.dependency_injection import get_logger

from ..base_stateful import StatefulBaseTool

logger = get_logger(__name__)


class NativeTool(StatefulBaseTool):
    """原生工具 - 同步实现
    
    用于包装复杂的、有状态的Python函数，支持状态管理。
    
    设计：
    - execute() 是主要实现（带状态管理）
    - execute_async() 通过基类默认包装（使用线程池）
    """
    
    def __init__(self, func: Callable, config: Any, state_manager):
        """初始化原生工具
        
        Args:
            func: Python函数
            config: 工具配置
            state_manager: 状态管理器
        """
        # 从配置获取基本信息
        name = config.name or func.__name__
        description = config.description or func.__doc__ or f"原生工具: {name}"
        
        # 处理参数Schema
        if config.parameters_schema:
            parameters_schema = self._merge_schema_with_function(config.parameters_schema, func)
        else:
            parameters_schema = self._infer_schema(func)
        
        super().__init__(
            name=name, 
            description=description, 
            parameters_schema=parameters_schema,
            state_manager=state_manager,
            config=config
        )
        
        self.func = func
        self._state_injection = config.get('state_injection', True)
        self._state_parameter_name = config.get('state_parameter_name', 'state')
    
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
        """执行工具（带状态管理）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        if not self.is_initialized:
            raise RuntimeError("工具未初始化，请先调用 initialize_context()")
        
        try:
            # 记录执行开始
            self.add_to_history('execution_start', {
                'parameters': kwargs,
                'timestamp': time.time()
            })
            
            # 更新连接状态
            self.update_connection_state({
                'active': True,
                'last_used': time.time()
            })
            
            # 准备函数参数
            func_kwargs = kwargs.copy()
            
            # 注入状态参数
            if self._state_injection:
                current_state = self.get_business_state()
                if current_state:
                    func_kwargs[self._state_parameter_name] = current_state.get('data', {})
            
            # 执行函数
            result = self.func(**func_kwargs)
            
            # 处理返回结果中的状态更新
            if isinstance(result, dict) and 'state' in result:
                self.update_business_state({'data': result['state']})
                # 从结果中移除状态数据
                result = {k: v for k, v in result.items() if k != 'state'}
            
            # 记录执行成功
            self.add_to_history('execution_success', {
                'result_type': type(result).__name__,
                'timestamp': time.time()
            })
            
            # 更新连接状态
            self.update_connection_state({
                'active': False,
                'last_used': time.time()
            })
            
            return result
            
        except Exception as e:
            # 记录执行错误
            self.add_to_history('execution_error', {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': time.time()
            })
            
            # 更新连接状态
            conn_state = self.get_connection_state()
            error_count = (conn_state or {}).get('error_count', 0) + 1
            self.update_connection_state({
                'active': False,
                'last_used': time.time(),
                'error_count': error_count,
                'last_error': str(e)
            })
            
            raise ValueError(f"原生工具执行错误: {str(e)}")
    
    def get_function(self) -> Callable:
        """获取原始函数"""
        return self.func
    
    @classmethod
    def from_function(
        cls,
        func: Callable,
        state_manager,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
        state_injection: bool = True,
        state_parameter_name: str = "state",
    ) -> "NativeTool":
        """从函数创建工具实例"""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"原生工具: {tool_name}"
        
        # 创建一个简单的配置对象
        class SimpleConfig(dict):
            def __init__(self):
                super().__init__()
                self['name'] = tool_name
                self['description'] = tool_description
                self['parameters_schema'] = parameters_schema or {}
                self['state_injection'] = state_injection
                self['state_parameter_name'] = state_parameter_name
            
            def get(self, key, default=None):
                return self[key] if key in self else default
        
        config = SimpleConfig()
        return cls(func, config, state_manager)