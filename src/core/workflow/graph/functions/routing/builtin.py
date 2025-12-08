"""Core层路由函数实现

提供符合IRouteFunction接口的路由函数实现，直接在Core层实现业务逻辑。
"""

from typing import Dict, Any, Optional

from src.interfaces.workflow.functions import IRouteFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class HasToolCallsRouteFunction(IRouteFunction):
    """检查是否有工具调用的路由函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="route:has_tool_calls",
            name="has_tool_calls",
            function_type=FunctionType.ROUTE,
            description="检查工作流状态中是否有工具调用并决定路由",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "params": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "路由参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Optional[str]"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化路由函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理路由函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证路由配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def route(self, state: IWorkflowState, params: Dict[str, Any]) -> Optional[str]:
        """执行路由决策
        
        Args:
            state: 工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID，None表示无有效目标
        """
        messages = state.get("messages", [])
        for message in messages:
            if message.get("tool_calls"):
                return "tools"
        return "end"


class NoToolCallsRouteFunction(IRouteFunction):
    """检查是否没有工具调用的路由函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="route:no_tool_calls",
            name="no_tool_calls",
            function_type=FunctionType.ROUTE,
            description="检查工作流状态中是否没有工具调用并决定路由",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "params": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "路由参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Optional[str]"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化路由函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理路由函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证路由配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def route(self, state: IWorkflowState, params: Dict[str, Any]) -> Optional[str]:
        """执行路由决策
        
        Args:
            state: 工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID，None表示无有效目标
        """
        messages = state.get("messages", [])
        for message in messages:
            if message.get("tool_calls"):
                return None
        return "continue"


class HasToolResultsRouteFunction(IRouteFunction):
    """检查是否有工具结果的路由函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="route:has_tool_results",
            name="has_tool_results",
            function_type=FunctionType.ROUTE,
            description="检查工作流状态中是否有工具结果并决定路由",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "params": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "路由参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Optional[str]"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化路由函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理路由函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证路由配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def route(self, state: IWorkflowState, params: Dict[str, Any]) -> Optional[str]:
        """执行路由决策
        
        Args:
            state: 工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID，None表示无有效目标
        """
        tool_results = state.get("tool_results", [])
        if len(tool_results) > 0:
            return "analyze"
        return None


class MaxIterationsReachedRouteFunction(IRouteFunction):
    """检查是否达到最大迭代次数的路由函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="route:max_iterations_reached",
            name="max_iterations_reached",
            function_type=FunctionType.ROUTE,
            description="检查是否达到最大迭代次数并决定路由",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "params": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "路由参数，包含max_iterations",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Optional[str]"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化路由函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理路由函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证路由配置"""
        return []  # 在route中验证
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def route(self, state: IWorkflowState, params: Dict[str, Any]) -> Optional[str]:
        """执行路由决策
        
        Args:
            state: 工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID，None表示无有效目标
        """
        max_iterations = params.get("max_iterations", 10)
        iteration_count = state.get("iteration_count", 0)
        
        if iteration_count >= max_iterations:
            return "end"
        return None


class HasErrorsRouteFunction(IRouteFunction):
    """检查是否有错误的路由函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="route:has_errors",
            name="has_errors",
            function_type=FunctionType.ROUTE,
            description="检查工作流状态中是否有错误并决定路由",
            category="builtin",
            is_async=False
        )
        self._initialized = False
    
    @property
    def function_id(self) -> str:
        return self._metadata.function_id
    
    @property
    def name(self) -> str:
        return self._metadata.name
    
    @property
    def description(self) -> str:
        return self._metadata.description
    
    @property
    def version(self) -> str:
        return self._metadata.version
    
    @property
    def function_type(self) -> FunctionType:
        return self._metadata.function_type
    
    @property
    def is_async(self) -> bool:
        return self._metadata.is_async
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "state": {
                "type": "IWorkflowState",
                "required": True,
                "description": "当前工作流状态"
            },
            "params": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "路由参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "Optional[str]"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化路由函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理路由函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证路由配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def route(self, state: IWorkflowState, params: Dict[str, Any]) -> Optional[str]:
        """执行路由决策
        
        Args:
            state: 工作流状态
            params: 路由参数
            
        Returns:
            Optional[str]: 目标节点ID，None表示无有效目标
        """
        # 检查工具结果中的错误
        tool_results = state.get("tool_results", [])
        for result in tool_results:
            if not result.get("success", True):
                return "error_handler"
        
        # 检查消息中的错误
        messages = state.get("messages", [])
        for message in messages:
            if message.get("type") == "error":
                return "error_handler"
        
        return None


class BuiltinRouteFunctions:
    """内置路由函数集合"""
    
    @staticmethod
    def get_all_functions():
        """获取所有内置路由函数"""
        return [
            HasToolCallsRouteFunction(),
            NoToolCallsRouteFunction(),
            HasToolResultsRouteFunction(),
            MaxIterationsReachedRouteFunction(),
            HasErrorsRouteFunction(),
        ]
    
    @staticmethod
    def get_function_by_name(name: str):
        """根据名称获取路由函数"""
        functions = {
            "has_tool_calls": HasToolCallsRouteFunction,
            "no_tool_calls": NoToolCallsRouteFunction,
            "has_tool_results": HasToolResultsRouteFunction,
            "max_iterations_reached": MaxIterationsReachedRouteFunction,
            "has_errors": HasErrorsRouteFunction,
        }
        
        function_class = functions.get(name)
        return function_class() if function_class else None