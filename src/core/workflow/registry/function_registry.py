"""核心层函数注册表

提供业务层的函数管理功能，依赖基础设施层的FunctionRegistry。
"""

from typing import Dict, Any, Optional
from src.interfaces.workflow.functions import FunctionType
from src.interfaces.state.workflow import IWorkflowState
from src.infrastructure.graph.registry.function_registry import FunctionRegistry as InfraFunctionRegistry
from src.interfaces.dependency_injection import get_logger


class FunctionRegistry:
    """核心层函数注册表
    
    提供业务层的函数管理功能，依赖基础设施层的FunctionRegistry。
    """
    
    def __init__(self, infra_registry: Optional[InfraFunctionRegistry] = None):
        """初始化函数注册表
        
        Args:
            infra_registry: 基础设施层函数注册表
        """
        self.logger = get_logger(self.__class__.__name__)
        self._infra_registry = infra_registry or InfraFunctionRegistry()
        self._load_builtin_functions()
    
    def _load_builtin_functions(self) -> None:
        """加载内置函数（使用Core层直接实现）"""
        from src.core.workflow.graph.functions.nodes import BuiltinNodeFunctions
        from src.core.workflow.graph.functions.conditions import BuiltinConditionFunctions
        from src.core.workflow.graph.functions.routing import BuiltinRouteFunctions
        from src.core.workflow.graph.functions.triggers import BuiltinTriggerFunctions
        
        # 注册节点函数
        for function in BuiltinNodeFunctions.get_all_functions():
            self._infra_registry.register(function)
        
        # 注册条件函数
        for function in BuiltinConditionFunctions.get_all_functions():
            self._infra_registry.register(function)
        
        # 注册路由函数
        for function in BuiltinRouteFunctions.get_all_functions():
            self._infra_registry.register(function)
        
        # 注册触发器函数
        for function in BuiltinTriggerFunctions.get_all_functions():
            self._infra_registry.register(function)
        
        self.logger.info("内置函数加载完成")
    
    def execute_node_function(self, function_id: str, state: IWorkflowState, config: Dict[str, Any]) -> Any:
        """执行节点函数
        
        Args:
            function_id: 函数ID
            state: 工作流状态
            config: 节点配置
            
        Returns:
            Any: 执行结果
            
        Raises:
            ValueError: 函数不存在或类型错误
        """
        function = self._infra_registry.get(function_id)
        if not function:
            raise ValueError(f"节点函数不存在: {function_id}")
        
        from src.interfaces.workflow.functions import INodeFunction
        if not isinstance(function, INodeFunction):
            raise ValueError(f"函数不是节点函数: {function_id}")
        
        import asyncio
        if function.is_async:
            return asyncio.run(function.execute(state, config))
        else:
            return function.execute(state, config)
    
    def evaluate_condition(self, function_id: str, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估条件函数
        
        Args:
            function_id: 函数ID
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            ValueError: 函数不存在或类型错误
        """
        function = self._infra_registry.get(function_id)
        if not function:
            raise ValueError(f"条件函数不存在: {function_id}")
        
        from src.interfaces.workflow.functions import IConditionFunction
        if not isinstance(function, IConditionFunction):
            raise ValueError(f"函数不是条件函数: {function_id}")
        
        return function.evaluate(state, condition)
    
    def route_to_node(self, function_id: str, state: IWorkflowState, params: Dict[str, Any]) -> Optional[str]:
        """路由到节点
        
        Args:
            function_id: 函数ID
            state: 工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID
            
        Raises:
            ValueError: 函数不存在或类型错误
        """
        function = self._infra_registry.get(function_id)
        if not function:
            raise ValueError(f"路由函数不存在: {function_id}")
        
        from src.interfaces.workflow.functions import IRouteFunction
        if not isinstance(function, IRouteFunction):
            raise ValueError(f"函数不是路由函数: {function_id}")
        
        return function.route(state, params)
    
    def check_trigger(self, function_id: str, state: IWorkflowState, config: Dict[str, Any]) -> bool:
        """检查触发器
        
        Args:
            function_id: 函数ID
            state: 工作流状态
            config: 触发器配置
            
        Returns:
            bool: 是否应该触发
            
        Raises:
            ValueError: 函数不存在或类型错误
        """
        function = self._infra_registry.get(function_id)
        if not function:
            raise ValueError(f"触发器函数不存在: {function_id}")
        
        from src.interfaces.workflow.functions import ITriggerFunction
        if not isinstance(function, ITriggerFunction):
            raise ValueError(f"函数不是触发器函数: {function_id}")
        
        return function.should_trigger(state, config)
    
    # 兼容性方法（用于现有代码）
    def get_node_function(self, name: str) -> Optional[Any]:
        """获取节点函数（兼容性方法）
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Any]: 函数实例
        """
        # 尝试按名称查找
        for function in self._infra_registry.get_node_functions():
            if function.name == name:
                return function
        return None
    
    def get_condition_function(self, name: str) -> Optional[Any]:
        """获取条件函数（兼容性方法）
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Any]: 函数实例
        """
        for function in self._infra_registry.get_condition_functions():
            if function.name == name:
                return function
        return None
    
    def get_route_function(self, name: str) -> Optional[Any]:
        """获取路由函数（兼容性方法）
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Any]: 函数实例
        """
        for function in self._infra_registry.get_route_functions():
            if function.name == name:
                return function
        return None
    
    def get_trigger_function(self, name: str) -> Optional[Any]:
        """获取触发器函数（兼容性方法）
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Any]: 函数实例
        """
        for function in self._infra_registry.get_trigger_functions():
            if function.name == name:
                return function
        return None
    
    # 注册表方法
    def register_function(self, function: Any, overwrite: bool = False) -> None:
        """注册函数（兼容性方法）
        
        Args:
            function: 函数实例
            overwrite: 是否覆盖
        """
        # 检查是否是新的IFunction接口
        if hasattr(function, 'function_id'):
            self._infra_registry.register(function)
        else:
            # 旧的Callable函数，需要包装
            self.logger.warning("尝试注册旧式Callable函数，建议使用新的IFunction接口")
    
    def unregister_function(self, function_id: str) -> bool:
        """注销函数
        
        Args:
            function_id: 函数ID
            
        Returns:
            bool: 是否成功注销
        """
        return self._infra_registry.unregister(function_id)
    
    def list_node_functions(self) -> list:
        """列出节点函数（兼容性方法）
        
        Returns:
            list: 函数名称列表
        """
        return [func.name for func in self._infra_registry.get_node_functions()]
    
    def list_condition_functions(self) -> list:
        """列出条件函数（兼容性方法）
        
        Returns:
            list: 函数名称列表
        """
        return [func.name for func in self._infra_registry.get_condition_functions()]
    
    def list_route_functions(self) -> list:
        """列出路由函数（兼容性方法）
        
        Returns:
            list: 函数名称列表
        """
        return [func.name for func in self._infra_registry.get_route_functions()]
    
    def list_trigger_functions(self) -> list:
        """列出触发器函数（兼容性方法）
        
        Returns:
            list: 函数名称列表
        """
        return [func.name for func in self._infra_registry.get_trigger_functions()]
    
    def get_function_info(self, name: str, function_type: str) -> Optional[Dict[str, Any]]:
        """获取函数信息（兼容性方法）
        
        Args:
            name: 函数名称
            function_type: 函数类型
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息
        """
        # 根据类型获取函数
        if function_type == "node_function":
            function = self.get_node_function(name)
        elif function_type == "condition_function":
            function = self.get_condition_function(name)
        elif function_type == "route_function":
            function = self.get_route_function(name)
        elif function_type == "trigger_function":
            function = self.get_trigger_function(name)
        else:
            return None
        
        if function:
            return self._infra_registry.get_function_info(function.function_id)
        
        return None
    
    def get_function_schema(self, function_type: str, name: str) -> Dict[str, Any]:
        """获取函数配置Schema（兼容性方法）
        
        Args:
            function_type: 函数类型
            name: 函数名称
            
        Returns:
            Dict: 配置Schema
        """
        function = None
        if function_type == "node_function":
            function = self.get_node_function(name)
        elif function_type == "condition_function":
            function = self.get_condition_function(name)
        elif function_type == "route_function":
            function = self.get_route_function(name)
        elif function_type == "trigger_function":
            function = self.get_trigger_function(name)
        
        if not function:
            raise ValueError(f"函数不存在: {name}")
        
        # 返回基本Schema
        return {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "description": "函数配置"
                }
            },
            "required": []
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._infra_registry.get_stats()
        return {
            "node_functions": stats["by_type"].get("node", 0),
            "condition_functions": stats["by_type"].get("condition", 0),
            "route_functions": stats["by_type"].get("route", 0),
            "trigger_functions": stats["by_type"].get("trigger", 0),
            "total_functions": stats["total"]
        }
    
    def clear(self, function_type: Optional[str] = None) -> None:
        """清除函数
        
        Args:
            function_type: 要清除的函数类型
        """
        if function_type:
            # 映射旧类型到新类型
            type_mapping = {
                "node_function": FunctionType.NODE,
                "condition_function": FunctionType.CONDITION,
                "route_function": FunctionType.ROUTE,
                "trigger_function": FunctionType.TRIGGER
            }
            new_type = type_mapping.get(function_type)
            if new_type:
                self._infra_registry.clear(new_type)
        else:
            self._infra_registry.clear()


# 全局函数注册表实例
_global_registry: Optional[FunctionRegistry] = None


def get_global_function_registry() -> FunctionRegistry:
    """获取全局函数注册表
    
    Returns:
        FunctionRegistry: 全局函数注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = FunctionRegistry()
    return _global_registry


def reset_global_function_registry() -> None:
    """重置全局函数注册表（用于测试）"""
    global _global_registry
    _global_registry = None