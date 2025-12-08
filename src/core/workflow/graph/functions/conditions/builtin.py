"""Core层条件函数实现

提供符合IConditionFunction接口的条件函数实现，直接在Core层实现业务逻辑。
"""

from typing import Dict, Any

from src.interfaces.workflow.functions import IConditionFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class HasToolCallsCondition(IConditionFunction):
    """检查是否有工具调用的条件函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:has_tool_calls",
            name="has_tool_calls",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否有工具调用",
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
            "condition": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "条件配置",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化条件函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理条件函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证条件配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        messages = state.get("messages", [])
        for message in messages:
            if message.get("tool_calls"):
                return True
        return False


class NoToolCallsCondition(IConditionFunction):
    """检查是否没有工具调用的条件函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:no_tool_calls",
            name="no_tool_calls",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否没有工具调用",
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
            "condition": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "条件配置",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化条件函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理条件函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证条件配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        messages = state.get("messages", [])
        for message in messages:
            if message.get("tool_calls"):
                return False
        return True


class HasToolResultsCondition(IConditionFunction):
    """检查是否有工具结果的条件函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:has_tool_results",
            name="has_tool_results",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否有工具结果",
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
            "condition": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "条件配置",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化条件函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理条件函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证条件配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        tool_results = state.get("tool_results", [])
        return len(tool_results) > 0


class HasErrorsCondition(IConditionFunction):
    """检查是否有错误的条件函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:has_errors",
            name="has_errors",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否有错误",
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
            "condition": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "条件配置",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化条件函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理条件函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证条件配置"""
        return []  # 无特殊配置要求
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        # 检查工具结果中的错误
        tool_results = state.get("tool_results", [])
        for result in tool_results:
            if not result.get("success", True):
                return True
        
        # 检查消息中的错误
        messages = state.get("messages", [])
        for message in messages:
            if message.get("type") == "error":
                return True
        
        return False


class MaxIterationsReachedCondition(IConditionFunction):
    """检查是否达到最大迭代次数的条件函数 - Core层直接实现"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:max_iterations_reached",
            name="max_iterations_reached",
            function_type=FunctionType.CONDITION,
            description="检查是否达到最大迭代次数",
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
            "condition": {
                "type": "Dict[str, Any]",
                "required": False,
                "description": "条件配置，包含max_iterations",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化条件函数"""
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        """清理条件函数资源"""
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> list[str]:
        """验证条件配置"""
        return []  # 在evaluate中验证
    
    def validate_parameters(self, params: Dict[str, Any]) -> list[str]:
        """验证调用参数"""
        errors = []
        
        if "state" not in params:
            errors.append("state参数是必需的")
        
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估条件
        
        Args:
            state: 工作流状态
            condition: 条件配置
            
        Returns:
            bool: 条件是否满足
        """
        max_iterations = condition.get("max_iterations", 10)
        iteration_count = state.get("iteration_count", 0)
        return iteration_count >= max_iterations


class BuiltinConditionFunctions:
    """内置条件函数集合"""
    
    @staticmethod
    def get_all_functions():
        """获取所有内置条件函数"""
        return [
            HasToolCallsCondition(),
            NoToolCallsCondition(),
            HasToolResultsCondition(),
            HasErrorsCondition(),
            MaxIterationsReachedCondition(),
        ]
    
    @staticmethod
    def get_function_by_name(name: str):
        """根据名称获取条件函数"""
        functions = {
            "has_tool_calls": HasToolCallsCondition,
            "no_tool_calls": NoToolCallsCondition,
            "has_tool_results": HasToolResultsCondition,
            "has_errors": HasErrorsCondition,
            "max_iterations_reached": MaxIterationsReachedCondition,
        }
        
        function_class = functions.get(name)
        return function_class() if function_class else None