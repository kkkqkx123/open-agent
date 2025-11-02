"""条件边定义

表示基于条件判断的节点连接，支持多种条件类型。
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

from ..config import EdgeConfig
from ..state import WorkflowState


class ConditionType(Enum):
    """条件类型枚举"""
    HAS_TOOL_CALLS = "has_tool_calls"
    NO_TOOL_CALLS = "no_tool_calls"
    HAS_TOOL_RESULTS = "has_tool_results"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    HAS_ERRORS = "has_errors"
    NO_ERRORS = "no_errors"
    MESSAGE_CONTAINS = "message_contains"
    ITERATION_COUNT_EQUALS = "iteration_count_equals"
    ITERATION_COUNT_GREATER_THAN = "iteration_count_greater_than"
    CUSTOM = "custom"


@dataclass
class ConditionalEdge:
    """条件边
    
    表示基于条件判断的节点连接，根据条件决定是否走这条边。
    """
    
    from_node: str
    to_node: str
    condition: str
    condition_type: ConditionType
    condition_parameters: Dict[str, Any]
    description: Optional[str] = None
    
    @classmethod
    def from_config(cls, config: EdgeConfig) -> "ConditionalEdge":
        """从配置创建条件边
        
        Args:
            config: 边配置
            
        Returns:
            ConditionalEdge: 条件边实例
        """
        if config.type.value != "conditional":
            raise ValueError(f"配置类型不匹配，期望 conditional，实际 {config.type.value}")
        
        if not config.condition:
            raise ValueError("条件边必须指定条件表达式")
        
        # 解析条件类型和参数
        condition_type, condition_parameters = cls._parse_condition(config.condition)
        
        return cls(
            from_node=config.from_node,
            to_node=config.to_node,
            condition=config.condition,
            condition_type=condition_type,
            condition_parameters=condition_parameters,
            description=config.description
        )
    
    def to_config(self) -> EdgeConfig:
        """转换为配置
        
        Returns:
            EdgeConfig: 边配置
        """
        from ..config import EdgeType
        return EdgeConfig(
            from_node=self.from_node,
            to_node=self.to_node,
            type=EdgeType.CONDITIONAL,
            condition=self.condition,
            description=self.description
        )
    
    def evaluate(self, state: WorkflowState) -> bool:
        """评估条件是否满足
        
        Args:
            state: 当前工作流状态
            
        Returns:
            bool: 条件是否满足
        """
        if self.condition_type == ConditionType.HAS_TOOL_CALLS:
            return self._has_tool_calls(state)
        elif self.condition_type == ConditionType.NO_TOOL_CALLS:
            return self._no_tool_calls(state)
        elif self.condition_type == ConditionType.HAS_TOOL_RESULTS:
            return self._has_tool_results(state)
        elif self.condition_type == ConditionType.MAX_ITERATIONS_REACHED:
            return self._max_iterations_reached(state)
        elif self.condition_type == ConditionType.HAS_ERRORS:
            return self._has_errors(state)
        elif self.condition_type == ConditionType.NO_ERRORS:
            return self._no_errors(state)
        elif self.condition_type == ConditionType.MESSAGE_CONTAINS:
            return self._message_contains(state)
        elif self.condition_type == ConditionType.ITERATION_COUNT_EQUALS:
            return self._iteration_count_equals(state)
        elif self.condition_type == ConditionType.ITERATION_COUNT_GREATER_THAN:
            return self._iteration_count_greater_than(state)
        elif self.condition_type == ConditionType.CUSTOM:
            return self._custom_condition(state)
        else:
            raise ValueError(f"未知的条件类型: {self.condition_type}")
    
    def validate(self, node_names: set) -> List[str]:
        """验证边的有效性
        
        Args:
            node_names: 可用节点名称集合
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if self.from_node not in node_names:
            errors.append(f"起始节点 '{self.from_node}' 不存在")
        
        if self.to_node not in node_names:
            errors.append(f"目标节点 '{self.to_node}' 不存在")
        
        if self.from_node == self.to_node:
            errors.append("不允许节点自循环")
        
        # 验证条件参数
        if self.condition_type == ConditionType.MESSAGE_CONTAINS:
            if "text" not in self.condition_parameters:
                errors.append("message_contains 条件需要指定 text 参数")
        elif self.condition_type in [ConditionType.ITERATION_COUNT_EQUALS, ConditionType.ITERATION_COUNT_GREATER_THAN]:
            if "count" not in self.condition_parameters:
                errors.append(f"{self.condition_type.value} 条件需要指定 count 参数")
        
        return errors
    
    @classmethod
    def _parse_condition(cls, condition_str: str) -> tuple[ConditionType, Dict[str, Any]]:
        """解析条件字符串
        
        Args:
            condition_str: 条件字符串
            
        Returns:
            tuple[ConditionType, Dict[str, Any]]: 条件类型和参数
        """
        # 内置条件映射
        condition_mapping = {
            "has_tool_call": ConditionType.HAS_TOOL_CALLS,
            "no_tool_call": ConditionType.NO_TOOL_CALLS,
            "has_tool_calls": ConditionType.HAS_TOOL_CALLS,
            "no_tool_calls": ConditionType.NO_TOOL_CALLS,
            "has_tool_result": ConditionType.HAS_TOOL_RESULTS,
            "has_tool_results": ConditionType.HAS_TOOL_RESULTS,
            "max_iterations": ConditionType.MAX_ITERATIONS_REACHED,
            "max_iterations_reached": ConditionType.MAX_ITERATIONS_REACHED,
            "has_error": ConditionType.HAS_ERRORS,
            "has_errors": ConditionType.HAS_ERRORS,
            "no_error": ConditionType.NO_ERRORS,
            "no_errors": ConditionType.NO_ERRORS,
            "message_contains": ConditionType.MESSAGE_CONTAINS,
            "iteration_count_equals": ConditionType.ITERATION_COUNT_EQUALS,
            "iteration_count_greater_than": ConditionType.ITERATION_COUNT_GREATER_THAN,
        }
        
        # 检查是否为内置条件
        if condition_str in condition_mapping:
            return condition_mapping[condition_str], {}
        
        # 检查是否为带参数的条件
        if ":" in condition_str:
            parts = condition_str.split(":", 1)
            condition_name = parts[0]
            params_str = parts[1]
            
            if condition_name in condition_mapping:
                condition_type = condition_mapping[condition_name]
                # 简单参数解析
                if condition_type == ConditionType.MESSAGE_CONTAINS:
                    return condition_type, {"text": params_str}
                elif condition_type in [ConditionType.ITERATION_COUNT_EQUALS, ConditionType.ITERATION_COUNT_GREATER_THAN]:
                    try:
                        count = int(params_str)
                        return condition_type, {"count": count}
                    except ValueError:
                        pass
        
        # 默认为自定义条件
        return ConditionType.CUSTOM, {"expression": condition_str}
    
    # 条件评估方法
    def _has_tool_calls(self, state: WorkflowState) -> bool:
        """检查是否有工具调用"""
        if not state.get("messages"):
            return False
        
        messages = state.get("messages", [])
        if not messages:
            return False
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            return True
        
        # 检查消息内容
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', ''))
            return "tool_call" in content.lower() or "调用工具" in content
        
        return False
    
    def _no_tool_calls(self, state: WorkflowState) -> bool:
        """检查是否没有工具调用"""
        return not self._has_tool_calls(state)
    
    def _has_tool_results(self, state: WorkflowState) -> bool:
        """检查是否有工具执行结果"""
        return len(state.get("tool_results", [])) > 0
    
    def _max_iterations_reached(self, state: WorkflowState) -> bool:
        """检查是否达到最大迭代次数"""
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 10)
        return iteration_count >= max_iterations
    
    def _has_errors(self, state: WorkflowState) -> bool:
        """检查是否有错误"""
        for result in state.get("tool_results", []):
            if not result.get("success", True):
                return True
        return False
    
    def _no_errors(self, state: WorkflowState) -> bool:
        """检查是否没有错误"""
        return not self._has_errors(state)
    
    def _message_contains(self, state: WorkflowState) -> bool:
        """检查消息是否包含指定内容"""
        if "text" not in self.condition_parameters:
            return False
        
        search_text = self.condition_parameters["text"].lower()
        
        for message in state.get("messages", []):
            if hasattr(message, 'content'):
                content = str(getattr(message, 'content', '')).lower()
                if search_text in content:
                    return True
        
        return False
    
    def _iteration_count_equals(self, state: WorkflowState) -> bool:
        """检查迭代次数是否等于指定值"""
        if "count" not in self.condition_parameters:
            return False
        
        iteration_count = state.get("iteration_count", 0)
        count = self.condition_parameters["count"]
        return bool(iteration_count == count)
    
    def _iteration_count_greater_than(self, state: WorkflowState) -> bool:
        """检查迭代次数是否大于指定值"""
        if "count" not in self.condition_parameters:
            return False
        
        iteration_count = state.get("iteration_count", 0)
        count = self.condition_parameters["count"]
        return bool(iteration_count > count)
    
    def _custom_condition(self, state: WorkflowState) -> bool:
        """执行自定义条件"""
        if "expression" not in self.condition_parameters:
            return False
        
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
            }
            
            # 执行自定义表达式
            expression = self.condition_parameters["expression"]
            result = eval(expression, safe_globals)
            return bool(result)
            
        except Exception:
            # 如果执行失败，返回False
            return False
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"ConditionalEdge({self.from_node} -> {self.to_node} [{self.condition}])"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        return f"ConditionalEdge(from_node='{self.from_node}', to_node='{self.to_node}', condition='{self.condition}'{desc})"