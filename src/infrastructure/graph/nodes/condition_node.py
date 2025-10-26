"""条件判断节点

负责根据状态信息进行条件判断，决定工作流的分支走向。
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.prompts.agent_state import AgentState


@node("condition_node")
class ConditionNode(BaseNode):
    """条件判断节点"""

    def __init__(self) -> None:
        """初始化条件节点"""
        self._condition_functions: Dict[str, Callable] = {
            "has_tool_calls": self._has_tool_calls,
            "no_tool_calls": self._no_tool_calls,
            "has_tool_results": self._has_tool_results,
            "max_iterations_reached": self._max_iterations_reached,
            "has_errors": self._has_errors,
            "no_errors": self._no_errors,
            "message_contains": self._message_contains,
            "iteration_count_equals": self._iteration_count_equals,
            "iteration_count_greater_than": self._iteration_count_greater_than,
            "custom": self._custom_condition,
        }

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "condition_node"

    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行条件判断逻辑

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 获取条件配置
        conditions = config.get("conditions", [])
        if not conditions:
            # 如果没有配置条件，使用默认条件
            conditions = [{"type": "has_tool_calls", "next_node": "execute_tool"}]
        
        # 评估条件
        for condition_config in conditions:
            if self._evaluate_condition(condition_config, state):
                next_node = condition_config.get("next_node")
                return NodeExecutionResult(
                    state=state,
                    next_node=next_node,
                    metadata={
                        "condition_met": condition_config.get("type"),
                        "condition_config": condition_config
                    }
                )
        
        # 如果没有条件满足，使用默认节点
        default_next = config.get("default_next_node")
        return NodeExecutionResult(
            state=state,
            next_node=default_next,
            metadata={
                "condition_met": None,
                "message": "没有条件满足，使用默认节点"
            }
        )

    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "conditions": {
                    "type": "array",
                    "description": "条件列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "条件类型"
                            },
                            "next_node": {
                                "type": "string",
                                "description": "满足条件时的下一个节点"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "条件参数"
                            }
                        },
                        "required": ["type", "next_node"]
                    }
                },
                "default_next_node": {
                    "type": "string",
                    "description": "默认下一个节点（没有条件满足时）"
                },
                "custom_condition_code": {
                    "type": "string",
                    "description": "自定义条件代码（当条件类型为custom时使用）"
                }
            },
            "required": []
        }

    def _evaluate_condition(self, condition_config: Dict[str, Any], state: AgentState) -> bool:
        """评估单个条件

        Args:
            condition_config: 条件配置
            state: 当前Agent状态

        Returns:
            bool: 条件是否满足
        """
        condition_type = condition_config.get("type")
        parameters = condition_config.get("parameters", {})
        
        if condition_type not in self._condition_functions:
            raise ValueError(f"未知的条件类型: {condition_type}")
        
        condition_func = self._condition_functions[condition_type]
        return condition_func(state, parameters, condition_config)  # type: ignore

    # 内置条件函数
    def _has_tool_calls(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查是否有工具调用"""
        if not state.messages:
            return False

        last_message = state.messages[-1]
        # 检查是否有tool_calls属性
        if hasattr(last_message, 'tool_calls'):
            tool_calls = getattr(last_message, 'tool_calls', None)
            if tool_calls:
                return True

        # 检查消息内容
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', ''))
            return "tool_call" in content.lower() or "调用工具" in content

        return False

    def _no_tool_calls(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查是否没有工具调用"""
        return not self._has_tool_calls(state, parameters, config)

    def _has_tool_results(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查是否有工具执行结果"""
        return len(state.tool_results) > 0

    def _max_iterations_reached(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查是否达到最大迭代次数"""
        # 假设状态中有迭代计数
        iteration_count = getattr(state, 'iteration_count', 0)
        max_iterations = getattr(state, 'max_iterations', 10)
        return iteration_count >= max_iterations

    def _has_errors(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查是否有错误"""
        # 检查工具结果中的错误
        for result in state.tool_results:
            if not result.success:
                return True
        return False

    def _no_errors(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查是否没有错误"""
        return not self._has_errors(state, parameters, config)

    def _message_contains(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查消息是否包含指定内容"""
        if not state.messages or "text" not in parameters:
            return False
        
        search_text = parameters["text"].lower()
        case_sensitive = parameters.get("case_sensitive", False)
        
        for message in state.messages:
            if hasattr(message, 'content'):
                content = str(getattr(message, 'content', ''))
                if not case_sensitive:
                    content = content.lower()
                if search_text in content:
                    return True
        
        return False

    def _iteration_count_equals(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查迭代次数是否等于指定值"""
        if "count" not in parameters:
            return False
        
        iteration_count = getattr(state, 'iteration_count', 0)
        count = parameters["count"]
        return bool(iteration_count == count)

    def _iteration_count_greater_than(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """检查迭代次数是否大于指定值"""
        if "count" not in parameters:
            return False
        
        iteration_count = getattr(state, 'iteration_count', 0)
        count = parameters["count"]
        return bool(iteration_count > count)

    def _custom_condition(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """执行自定义条件"""
        # 首先尝试从条件配置的参数中获取代码
        code = parameters.get("custom_condition_code")
        
        # 如果没有找到，尝试从整个节点配置中获取
        if not code:
            # 这里需要获取整个节点配置，但我们只有条件配置
            # 为了解决这个问题，我们需要修改方法签名或传递方式
            raise ValueError("自定义条件需要提供 custom_condition_code")
        
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
            }
            
            # 执行自定义代码
            result = eval(code, safe_globals)
            return bool(result)
            
        except Exception as e:
            # 记录错误但不中断执行
            print(f"自定义条件执行失败: {e}")
            return False  # type: ignore

    def register_condition_function(self, name: str, func: Callable) -> None:
        """注册自定义条件函数

        Args:
            name: 条件函数名称
            func: 条件函数，签名为 (state, parameters, config) -> bool
        """
        self._condition_functions[name] = func

    def list_condition_types(self) -> List[str]:
        """列出所有可用的条件类型

        Returns:
            List[str]: 条件类型列表
        """
        return list(self._condition_functions.keys())