"""内置条件函数实现

提供符合IFunction接口的内置条件函数实现。
"""

from typing import Dict, Any, Optional, List
from src.interfaces.workflow.functions import IConditionFunction, FunctionType, FunctionMetadata
from src.interfaces.state.workflow import IWorkflowState


class HasToolCallsCondition(IConditionFunction):
    """检查是否有工具调用的条件函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:has_tool_calls",
            name="has_tool_calls",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否有工具调用",
            category="builtin"
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
                "description": "条件配置参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估是否有工具调用"""
        messages = state.get_data("messages", [])
        if not messages:
            return False

        last_message = messages[-1]
        # 检查LangChain消息的tool_calls属性
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            return True

        # 检查消息的metadata中的tool_calls
        if hasattr(last_message, 'metadata'):
            metadata = getattr(last_message, 'metadata', {})
            if isinstance(metadata, dict) and metadata.get("tool_calls"):
                return True

        # 检查消息内容
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', ''))
            return "tool_call" in content.lower() or "调用工具" in content

        return False


class NoToolCallsCondition(IConditionFunction):
    """检查是否没有工具调用的条件函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:no_tool_calls",
            name="no_tool_calls",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否没有工具调用",
            category="builtin"
        )
        self._initialized = False
        self._has_tool_calls = HasToolCallsCondition()
    
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
                "description": "条件配置参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return self._has_tool_calls.initialize(config)
    
    def cleanup(self) -> bool:
        self._initialized = False
        return self._has_tool_calls.cleanup()
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估是否没有工具调用"""
        return not self._has_tool_calls.evaluate(state, condition)


class HasToolResultsCondition(IConditionFunction):
    """检查是否有工具执行结果的条件函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:has_tool_results",
            name="has_tool_results",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否有工具执行结果",
            category="builtin"
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
                "description": "条件配置参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估是否有工具执行结果"""
        return len(state.get_data("tool_results", [])) > 0


class HasErrorsCondition(IConditionFunction):
    """检查是否有错误的条件函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:has_errors",
            name="has_errors",
            function_type=FunctionType.CONDITION,
            description="检查工作流状态中是否有错误",
            category="builtin"
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
                "description": "条件配置参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估是否有错误"""
        # 检查工具结果中的错误
        for result in state.get_data("tool_results", []):
            # 处理字典格式的工具结果
            if isinstance(result, dict):
                if not result.get("success", True):
                    return True
            # 处理Mock对象（用于测试）- 优先检查Mock对象
            elif hasattr(result, 'get_data') and callable(result.get):
                try:
                    success = result.get("success", True)
                    # 如果success为False，表示有错误
                    if success is False:
                        return True
                except:
                    # 如果get方法调用失败，忽略这个结果
                    pass
            # 处理ToolResult对象
            elif hasattr(result, 'success'):
                try:
                    if not result.success:
                        return True
                except:
                    # 如果访问success属性失败，忽略这个结果
                    pass
        return False


class MaxIterationsReachedCondition(IConditionFunction):
    """检查是否达到最大迭代次数的条件函数"""
    
    def __init__(self):
        self._metadata = FunctionMetadata(
            function_id="condition:max_iterations_reached",
            name="max_iterations_reached",
            function_type=FunctionType.CONDITION,
            description="检查是否达到最大迭代次数",
            category="builtin"
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
                "description": "条件配置参数",
                "default": {}
            }
        }
    
    def get_return_type(self) -> str:
        return "bool"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._initialized = True
        return True
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        errors = []
        if "state" not in params:
            errors.append("缺少必需参数: state")
        return errors
    
    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata.to_dict()
    
    def evaluate(self, state: IWorkflowState, condition: Dict[str, Any]) -> bool:
        """评估是否达到最大迭代次数"""
        # 优先使用工作流级别的迭代计数
        workflow_iteration_count = state.get_data("workflow_iteration_count")
        workflow_max_iterations = state.get_data("workflow_max_iterations")
        
        # 如果没有工作流级别的计数，使用旧的字段
        if workflow_iteration_count is None:
            workflow_iteration_count = state.get_data("iteration_count", 0)
        if workflow_max_iterations is None:
            workflow_max_iterations = state.get_data("max_iterations", 10)
            
        return bool(workflow_iteration_count >= workflow_max_iterations)


class BuiltinConditionFunctions:
    """内置条件函数集合"""
    
    @staticmethod
    def get_all_functions() -> Dict[str, IConditionFunction]:
        """获取所有内置条件函数
        
        Returns:
            Dict[str, IConditionFunction]: 条件函数字典
        """
        return {
            "has_tool_calls": HasToolCallsCondition(),
            "no_tool_calls": NoToolCallsCondition(),
            "has_tool_results": HasToolResultsCondition(),
            "has_errors": HasErrorsCondition(),
            "max_iterations_reached": MaxIterationsReachedCondition(),
        }
    
    @staticmethod
    def get_function(name: str) -> Optional[IConditionFunction]:
        """获取指定的内置条件函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[IConditionFunction]: 条件函数，如果不存在返回None
        """
        functions = BuiltinConditionFunctions.get_all_functions()
        return functions.get(name)
    
    @staticmethod
    def list_functions() -> List[str]:
        """列出所有内置条件函数名称
        
        Returns:
            List[str]: 函数名称列表
        """
        return list(BuiltinConditionFunctions.get_all_functions().keys())