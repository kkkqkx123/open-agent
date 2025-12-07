"""条件边定义

表示基于条件判断的节点连接，支持多种条件类型。
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from dataclasses import dataclass

from src.interfaces.workflow.config import IEdgeConfig
if TYPE_CHECKING:
    from src.interfaces.state import IWorkflowState


@dataclass
class ConditionalEdge:
    """条件边
    
    表示基于条件判断的节点连接，根据条件决定是否走这条边。
    """
    
    from_node: str
    to_node: str
    condition: str
    condition_type: Any
    condition_parameters: Dict[str, Any]
    description: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        self._evaluator = None  # 延迟初始化
    
    def _get_evaluator(self) -> Any:
        """获取条件评估器"""
        if self._evaluator is None:
            from src.infrastructure.graph.conditions import ConditionEvaluator
            self._evaluator = ConditionEvaluator()
        return self._evaluator
    
    @classmethod
    def from_config(cls, config: IEdgeConfig) -> "ConditionalEdge":
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
    
    def to_config(self) -> IEdgeConfig:
        """转换为配置
        
        Returns:
            IEdgeConfig: 边配置
        """
        from src.core.workflow.config import EdgeConfig, EdgeType
        return EdgeConfig(
            from_node=self.from_node,
            to_node=self.to_node,
            type=EdgeType(EdgeType.CONDITIONAL.value),
            condition=self.condition,
            description=self.description
        )
    
    def evaluate(self, state: "IWorkflowState") -> bool:
        """评估条件是否满足
        
        Args:
            state: 当前工作流状态
            
        Returns:
            bool: 条件是否满足
        """
        evaluator = self._get_evaluator()
        return evaluator.evaluate(
            self.condition_type,
            state,
            self.condition_parameters,
            {}  # 传递空的config字典
        )
    
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
        from src.infrastructure.graph.conditions import ConditionType
        if self.condition_type == ConditionType.MESSAGE_CONTAINS:
            if "text" not in self.condition_parameters:
                errors.append("message_contains 条件需要指定 text 参数")
        elif self.condition_type in [ConditionType.ITERATION_COUNT_EQUALS, ConditionType.ITERATION_COUNT_GREATER_THAN]:
            if "count" not in self.condition_parameters:
                errors.append(f"{self.condition_type.value} 条件需要指定 count 参数")
        
        return errors
    
    @classmethod
    def _parse_condition(cls, condition_str: str) -> tuple[Any, Dict[str, Any]]:
        """解析条件字符串
        
        Args:
            condition_str: 条件字符串
            
        Returns:
            tuple[Any, Dict[str, Any]]: 条件类型和参数
        """
        from src.infrastructure.graph.conditions import ConditionType
        
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
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"ConditionalEdge({self.from_node} -> {self.to_node} [{self.condition}])"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        return f"ConditionalEdge(from_node='{self.from_node}', to_node='{self.to_node}', condition='{self.condition}'{desc})"