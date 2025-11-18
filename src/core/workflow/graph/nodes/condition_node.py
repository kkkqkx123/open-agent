"""条件判断节点

负责根据状态信息进行条件判断，决定工作流的分支走向。
"""

from typing import Dict, Any, Optional, List, Callable

from .registry import BaseNode, NodeExecutionResult, node
from ...states import WorkflowState
from ...edges.conditions import ConditionType, ConditionEvaluator


@node("condition_node")
class ConditionNode(BaseNode):
    """条件判断节点"""

    def __init__(self) -> None:
        """初始化条件节点"""
        self._evaluator = ConditionEvaluator()

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "condition_node"

    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行条件判断逻辑

        Args:
            state: 当前工作流状态
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
            if self._evaluate_condition(condition_config, state, config):
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
                                "description": "条件类型",
                                "enum": [ct.value for ct in ConditionType]
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

    def _evaluate_condition(self, condition_config: Dict[str, Any], state: WorkflowState, 
                           node_config: Dict[str, Any]) -> bool:
        """评估单个条件

        Args:
            condition_config: 条件配置
            state: 当前工作流状态
            node_config: 节点配置

        Returns:
            bool: 条件是否满足
        """
        condition_type_str = condition_config.get("type")
        parameters = condition_config.get("parameters", {})
        
        # 对于自定义条件，尝试从节点配置中获取代码
        if condition_type_str == "custom" and "custom_condition_code" not in parameters:
            custom_code = node_config.get("custom_condition_code")
            if custom_code:
                parameters["custom_condition_code"] = custom_code
        
        try:
            condition_type = ConditionType(condition_type_str)
        except ValueError:
            raise ValueError(f"未知的条件类型: {condition_type_str}")
        
        return self._evaluator.evaluate(condition_type, state, parameters, node_config)

    def register_condition_function(self, condition_type: ConditionType, func: Callable) -> None:
        """注册自定义条件函数

        Args:
            condition_type: 条件类型
            func: 条件函数，签名为 (state, parameters, config) -> bool
        """
        self._evaluator.register_condition_function(condition_type, func)

    def list_condition_types(self) -> List[str]:
        """列出所有可用的条件类型

        Returns:
            List[str]: 条件类型列表
        """
        return [ct.value for ct in self._evaluator.list_condition_types()]