"""条件评估器

提供统一的条件评估功能，包含所有条件判断函数的实现。
"""

from typing import Dict, Any, Callable, Optional
from .types import ConditionType
from src.interfaces.state.base import IState
from src.interfaces.state.workflow import IWorkflowState


class ConditionEvaluator:
    """条件评估器
    
    提供统一的条件评估功能，支持多种内置条件类型和自定义条件。
    """
    
    def __init__(self) -> None:
        """初始化条件评估器"""
        self._condition_functions: Dict[ConditionType, Callable] = {
            ConditionType.HAS_TOOL_CALLS: self._has_tool_calls,
            ConditionType.NO_TOOL_CALLS: self._no_tool_calls,
            ConditionType.HAS_TOOL_RESULTS: self._has_tool_results,
            ConditionType.MAX_ITERATIONS_REACHED: self._max_iterations_reached,
            ConditionType.HAS_ERRORS: self._has_errors,
            ConditionType.NO_ERRORS: self._no_errors,
            ConditionType.MESSAGE_CONTAINS: self._message_contains,
            ConditionType.ITERATION_COUNT_EQUALS: self._iteration_count_equals,
            ConditionType.ITERATION_COUNT_GREATER_THAN: self._iteration_count_greater_than,
            ConditionType.CUSTOM: self._custom_condition,
        }
    
    def evaluate(self, condition_type: ConditionType, state: IState, 
                 parameters: Optional[Dict[str, Any]] = None,
                 config: Optional[Dict[str, Any]] = None) -> bool:
        """评估条件是否满足
        
        Args:
            condition_type: 条件类型
            state: 当前工作流状态
            parameters: 条件参数
            config: 额外配置信息（用于自定义条件）
            
        Returns:
            bool: 条件是否满足
        """
        if condition_type not in self._condition_functions:
            raise ValueError(f"未知的条件类型: {condition_type}")
        
        condition_func = self._condition_functions[condition_type]
        parameters = parameters or {}
        config = config or {}
        
        result = condition_func(state, parameters, config)
        return bool(result)
    
    def register_condition_function(self, condition_type: ConditionType, 
                                   func: Callable) -> None:
        """注册自定义条件函数
        
        Args:
            condition_type: 条件类型
            func: 条件函数，签名为 (state, parameters, config) -> bool
        """
        self._condition_functions[condition_type] = func
    
    def list_condition_types(self) -> list[ConditionType]:
        """列出所有可用的条件类型
        
        Returns:
            List[ConditionType]: 条件类型列表
        """
        return list(self._condition_functions.keys())
    
    # 内置条件函数实现
    def _has_tool_calls(self, state: IState, parameters: Dict[str, Any],
                       config: Dict[str, Any]) -> bool:
        """检查是否有工具调用（使用类型安全的接口）"""
        messages = state.get_data("messages", [])
        if not messages:
            return False

        last_message = messages[-1]
        
        # 使用类型安全的接口方法
        from src.interfaces.messages import IBaseMessage
        if isinstance(last_message, IBaseMessage):
            return last_message.has_tool_calls()
        
        # 对于非接口消息，使用消息转换器转换为接口类型
        try:
            from src.infrastructure.messages.converters import MessageConverter
            converter = MessageConverter()
            base_message = converter.to_base_message(last_message)
            return base_message.has_tool_calls()
        except Exception:
            # 转换失败，使用后备方案
            return self._fallback_tool_call_check(last_message)
    
    def _fallback_tool_call_check(self, message: Any) -> bool:
        """后备工具调用检查（用于兼容性）"""
        # 检查消息的metadata中的tool_calls
        if hasattr(message, 'metadata'):
            metadata = getattr(message, 'metadata', {})
            if isinstance(metadata, dict) and metadata.get("tool_calls"):
                return True

        # 检查消息内容
        if hasattr(message, 'content'):
            content = str(getattr(message, 'content', ''))
            return "tool_call" in content.lower() or "调用工具" in content

        return False

    def _no_tool_calls(self, state: IState, parameters: Dict[str, Any], 
                      config: Dict[str, Any]) -> bool:
        """检查是否没有工具调用"""
        return not self._has_tool_calls(state, parameters, config)

    def _has_tool_results(self, state: IState, parameters: Dict[str, Any], 
                         config: Dict[str, Any]) -> bool:
        """检查是否有工具执行结果"""
        return len(state.get_data("tool_results", [])) > 0

    def _max_iterations_reached(self, state: IState, parameters: Dict[str, Any],
                               config: Dict[str, Any]) -> bool:
        """检查是否达到最大迭代次数"""
        # 优先使用工作流级别的迭代计数
        workflow_iteration_count = state.get_data("workflow_iteration_count")
        workflow_max_iterations = state.get_data("workflow_max_iterations")
        
        # 如果没有工作流级别的计数，使用旧的字段
        if workflow_iteration_count is None:
            workflow_iteration_count = state.get_data("iteration_count", 0)
        if workflow_max_iterations is None:
            workflow_max_iterations = state.get_data("max_iterations", 10)
            
        return bool(workflow_iteration_count >= workflow_max_iterations)

    def _has_errors(self, state: IState, parameters: Dict[str, Any],
                   config: Dict[str, Any]) -> bool:
        """检查是否有错误"""
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

    def _no_errors(self, state: IState, parameters: Dict[str, Any], 
                  config: Dict[str, Any]) -> bool:
        """检查是否没有错误"""
        return not self._has_errors(state, parameters, config)

    def _message_contains(self, state: IState, parameters: Dict[str, Any], 
                         config: Dict[str, Any]) -> bool:
        """检查消息是否包含指定内容"""
        messages = state.get_data("messages", [])
        if not messages or "text" not in parameters:
            return False
        
        search_text = parameters["text"].lower()
        case_sensitive = parameters.get("case_sensitive", False)
        
        for message in messages:
            if hasattr(message, 'content'):
                content = str(getattr(message, 'content', ''))
                if not case_sensitive:
                    content = content.lower()
                if search_text in content:
                    return True
        
        return False

    def _iteration_count_equals(self, state: IState, parameters: Dict[str, Any], 
                               config: Dict[str, Any]) -> bool:
        """检查迭代次数是否等于指定值"""
        if "count" not in parameters:
            return False
        
        iteration_count = state.get_data("iteration_count", 0)
        count = parameters["count"]
        return bool(iteration_count == count)

    def _iteration_count_greater_than(self, state: IState, parameters: Dict[str, Any], 
                                    config: Dict[str, Any]) -> bool:
        """检查迭代次数是否大于指定值"""
        if "count" not in parameters:
            return False
        
        iteration_count = state.get_data("iteration_count", 0)
        count = parameters["count"]
        return bool(iteration_count > count)

    def _custom_condition(self, state: IState, parameters: Dict[str, Any], 
                         config: Dict[str, Any]) -> bool:
        """执行自定义条件"""
        # 首先尝试从参数中获取代码
        code = parameters.get("custom_condition_code") or parameters.get("expression")
        
        if not code:
            raise ValueError("自定义条件需要提供 custom_condition_code 或 expression 参数")
        
        try:
            # 创建安全的执行环境
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "any": any,
                    "all": all,
                },
                "state": state,
                "parameters": parameters,
                "config": config,
            }
            
            # 执行自定义代码
            result = eval(code, safe_globals)
            return bool(result)
            
        except Exception as e:
            # 记录错误但不中断执行
            print(f"自定义条件执行失败: {e}")
            return False


# 全局条件评估器实例
_global_evaluator = ConditionEvaluator()


def get_condition_evaluator() -> ConditionEvaluator:
    """获取全局条件评估器实例
    
    Returns:
        ConditionEvaluator: 条件评估器实例
    """
    return _global_evaluator


def evaluate_condition(condition_type: ConditionType, state: IWorkflowState, 
                      parameters: Optional[Dict[str, Any]] = None,
                      config: Optional[Dict[str, Any]] = None) -> bool:
    """便捷函数：评估条件
    
    Args:
        condition_type: 条件类型
        state: 当前工作流状态
        parameters: 条件参数
        config: 额外配置信息
        
    Returns:
        bool: 条件是否满足
    """
    return _global_evaluator.evaluate(condition_type, state, parameters, config)