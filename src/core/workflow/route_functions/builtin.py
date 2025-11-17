"""内置路由函数

提供系统内置的常用路由函数。
"""

from typing import Dict, Any

from ..states.workflow import WorkflowState


class BuiltinRouteFunctions:
    """内置路由函数集合"""
    
    @staticmethod
    def has_tool_calls(state: WorkflowState) -> str:
        """检查是否有工具调用
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        messages = state.get("messages", [])
        if not messages:
            return "end"
        
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            return "continue"
        
        return "end"
    
    @staticmethod
    def no_tool_calls(state: WorkflowState) -> str:
        """检查是否没有工具调用
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        return "continue" if BuiltinRouteFunctions.has_tool_calls(state) == "end" else "end"
    
    @staticmethod
    def has_tool_results(state: WorkflowState) -> str:
        """检查是否有工具结果
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        return "continue" if len(state.get("tool_results", [])) > 0 else "end"
    
    @staticmethod
    def max_iterations_reached(state: WorkflowState) -> str:
        """检查是否达到最大迭代次数
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 10)
        return "end" if iteration_count >= max_iterations else "continue"
    
    @staticmethod
    def has_errors(state: WorkflowState) -> str:
        """检查是否有错误
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        for result in state.get("tool_results", []):
            if isinstance(result, dict) and not result.get("success", True):
                return "error"
        return "continue"
    
    @staticmethod
    def no_errors(state: WorkflowState) -> str:
        """检查是否没有错误
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        return "continue" if BuiltinRouteFunctions.has_errors(state) == "continue" else "error"
    
    @staticmethod
    def tool_call_count(state: WorkflowState) -> str:
        """基于工具调用数量的路由
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        messages = state.get("messages", [])
        if not messages:
            return "none"
        
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            tool_calls = getattr(last_message, 'tool_calls', [])
            if len(tool_calls) == 1:
                return "single"
            elif len(tool_calls) > 1:
                return "multiple"
        
        return "none"
    
    @staticmethod
    def message_contains_error(state: WorkflowState) -> str:
        """检查消息是否包含错误关键词
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        messages = state.get("messages", [])
        if not messages:
            return "no_error"
        
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', '')).lower()
            error_keywords = ["error", "exception", "failed", "failure", "错误", "异常", "失败"]
            
            if any(keyword in content for keyword in error_keywords):
                return "has_error"
        
        return "no_error"
    
    @staticmethod
    def iteration_count_equals(state: WorkflowState) -> str:
        """检查迭代次数是否等于指定值
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        iteration_count = state.get("iteration_count", 0)
        route_params = state.get("_route_parameters", {})
        target_count = route_params.get("count", 1)
        
        return "equals" if iteration_count == target_count else "not_equals"
    
    @staticmethod
    def iteration_count_greater_than(state: WorkflowState) -> str:
        """检查迭代次数是否大于指定值
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        iteration_count = state.get("iteration_count", 0)
        route_params = state.get("_route_parameters", {})
        threshold = route_params.get("threshold", 1)
        
        return "greater" if iteration_count > threshold else "not_greater"
    
    @staticmethod
    def status_check(state: WorkflowState) -> str:
        """基于状态值的路由
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        route_params = state.get("_route_parameters", {})
        state_key = route_params.get("state_key", "status")
        value_mapping = route_params.get("value_mapping", {})
        default_route = route_params.get("default_route", "default")
        
        state_value = state.get(state_key)
        return value_mapping.get(str(state_value), default_route)
    
    @staticmethod
    def keyword_match(state: WorkflowState) -> str:
        """基于关键词匹配的路由
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        route_params = state.get("_route_parameters", {})
        keywords = route_params.get("keywords", [])
        case_sensitive = route_params.get("case_sensitive", False)
        message_index = route_params.get("message_index", -1)
        
        messages = state.get("messages", [])
        if not messages or not keywords:
            return "not_matched"
        
        # 获取指定索引的消息
        if message_index < 0:
            message_index = len(messages) + message_index
        
        if message_index < 0 or message_index >= len(messages):
            return "not_matched"
        
        message = messages[message_index]
        if hasattr(message, 'content'):
            content = str(getattr(message, 'content', ''))
            if not case_sensitive:
                content = content.lower()
                search_keywords = [kw.lower() for kw in keywords]
            else:
                search_keywords = keywords
            
            if any(keyword in content for keyword in search_keywords):
                return "matched"
        
        return "not_matched"
    
    @staticmethod
    def threshold_check(state: WorkflowState) -> str:
        """基于阈值的路由
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 路由决策
        """
        route_params = state.get("_route_parameters", {})
        state_key = route_params.get("state_key", "value")
        threshold = route_params.get("threshold", 0)
        comparison = route_params.get("comparison", "greater_than")
        
        state_value = state.get(state_key, 0)
        
        try:
            if comparison == "greater_than":
                return "above" if state_value > threshold else "below"
            elif comparison == "less_than":
                return "below" if state_value < threshold else "above"
            elif comparison == "equals":
                return "equals" if state_value == threshold else "not_equals"
            elif comparison == "greater_equal":
                return "above" if state_value >= threshold else "below"
            elif comparison == "less_equal":
                return "below" if state_value <= threshold else "above"
        except (TypeError, ValueError):
            pass
        
        return "error"
    
    @classmethod
    def get_all_functions(cls) -> Dict[str, Any]:
        """获取所有内置路由函数
        
        Returns:
            Dict[str, Any]: 路由函数字典
        """
        return {
            "has_tool_calls": cls.has_tool_calls,
            "no_tool_calls": cls.no_tool_calls,
            "has_tool_results": cls.has_tool_results,
            "max_iterations_reached": cls.max_iterations_reached,
            "has_errors": cls.has_errors,
            "no_errors": cls.no_errors,
            "tool_call_count": cls.tool_call_count,
            "message_contains_error": cls.message_contains_error,
            "iteration_count_equals": cls.iteration_count_equals,
            "iteration_count_greater_than": cls.iteration_count_greater_than,
            "status_check": cls.status_check,
            "keyword_match": cls.keyword_match,
            "threshold_check": cls.threshold_check,
        }