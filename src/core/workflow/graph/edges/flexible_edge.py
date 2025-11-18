"""灵活条件边

实现基于路由函数的条件边，支持条件逻辑与路由目标的解耦。
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import logging

from src.core.workflow.graph.route_functions import RouteFunctionManager
from src.core.workflow.states.workflow import WorkflowState
from src.core.workflow.config.config import EdgeConfig, EdgeType

logger = logging.getLogger(__name__)


@dataclass
class FlexibleConditionalEdge:
    """灵活条件边
    
    只定义路由函数，具体指向的节点在工作流中定义。
    """
    from_node: str
    route_function: str  # 路由函数名称
    route_parameters: Dict[str, Any]  # 路由函数参数
    description: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        self._route_function_manager: Optional[RouteFunctionManager] = None
        self._cached_route_function: Optional[Callable] = None
    
    def set_route_function_manager(self, manager: RouteFunctionManager) -> None:
        """设置路由函数管理器
        
        Args:
            manager: 路由函数管理器
        """
        self._route_function_manager = manager
        # 清除缓存，因为管理器可能已更改
        self._cached_route_function = None
    
    def validate(self, route_function_manager: Optional[RouteFunctionManager] = None) -> List[str]:
        """验证边配置
        
        Args:
            route_function_manager: 路由函数管理器，如果为None则使用内部管理器
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        manager = route_function_manager or self._route_function_manager
        
        if not manager:
            errors.append("路由函数管理器未设置")
            return errors
        
        # 验证路由函数是否存在
        if not manager.get_route_function(self.route_function):
            errors.append(f"路由函数不存在: {self.route_function}")
        
        # 验证路由函数参数
        param_errors = manager.validate_route_function(
            self.route_function, 
            self.route_parameters
        )
        errors.extend(param_errors)
        
        return errors
    
    def create_route_function(self, route_function_manager: Optional[RouteFunctionManager] = None) -> Callable:
        """创建实际的路由函数
        
        Args:
            route_function_manager: 路由函数管理器，如果为None则使用内部管理器
            
        Returns:
            Callable: 路由函数
            
        Raises:
            ValueError: 路由函数不存在
        """
        # 使用缓存的函数
        if self._cached_route_function:
            return self._cached_route_function
        
        manager = route_function_manager or self._route_function_manager
        if not manager:
            raise ValueError("路由函数管理器未设置")
        
        base_route_function = manager.get_route_function(self.route_function)
        if not base_route_function:
            raise ValueError(f"路由函数不存在: {self.route_function}")
        
        # 创建包装函数，注入参数
        def wrapped_route_function(state: WorkflowState) -> str:
            # 将路由参数注入到状态中
            state_dict = dict(state) if isinstance(state, dict) else state.__dict__
            enhanced_state = {
                **state_dict,
                "_route_parameters": self.route_parameters
            }
            return base_route_function(enhanced_state)
        
        # 缓存函数
        self._cached_route_function = wrapped_route_function
        return wrapped_route_function
    
    @classmethod
    def from_config(cls, config: EdgeConfig, route_function_manager: Optional[RouteFunctionManager] = None) -> "FlexibleConditionalEdge":
        """从配置创建灵活条件边
        
        Args:
            config: 边配置
            route_function_manager: 路由函数管理器
            
        Returns:
            FlexibleConditionalEdge: 灵活条件边实例
            
        Raises:
            ValueError: 配置类型不匹配或缺少必要字段
        """
        
        if config.type != EdgeType.CONDITIONAL:
            raise ValueError(f"配置类型不匹配，期望 conditional，实际 {config.type.value}")
        
        # 检查是否包含路由函数（新格式）
        if hasattr(config, 'route_function') and config.route_function:
            route_function = config.route_function
            route_parameters = getattr(config, 'route_parameters', {})
        else:
            # 尝试从条件字符串解析（兼容旧格式）
            if not config.condition:
                raise ValueError("条件边必须指定路由函数或条件表达式")
            
            route_function, route_parameters = cls._parse_condition(config.condition)
        
        edge = cls(
            from_node=config.from_node,
            route_function=route_function,
            route_parameters=route_parameters,
            description=config.description
        )
        
        if route_function_manager:
            edge.set_route_function_manager(route_function_manager)
        
        return edge
    
    def to_config(self) -> EdgeConfig:
        """转换为配置
        
        Returns:
            EdgeConfig: 边配置
        """
        return EdgeConfig(
            from_node=self.from_node,
            to_node="",  # 灵活条件边不指定目标节点
            type=EdgeType.CONDITIONAL,
            condition="",  # 使用路由函数替代条件表达式
            description=self.description,
            path_map=None  # 路径映射在工作流中定义
        )
    
    @classmethod
    def _parse_condition(cls, condition_str: str) -> tuple[str, Dict[str, Any]]:
        """解析条件字符串，提取路由函数和参数
        
        Args:
            condition_str: 条件字符串
            
        Returns:
            tuple[str, Dict[str, Any]]: 路由函数名称和参数
        """
        # 内置条件映射
        condition_mapping = {
            "has_tool_call": "has_tool_calls",
            "no_tool_call": "no_tool_calls",
            "has_tool_calls": "has_tool_calls",
            "no_tool_calls": "no_tool_calls",
            "has_tool_result": "has_tool_results",
            "has_tool_results": "has_tool_results",
            "max_iterations": "max_iterations_reached",
            "max_iterations_reached": "max_iterations_reached",
            "has_error": "has_errors",
            "has_errors": "has_errors",
            "no_error": "no_errors",
            "no_errors": "no_errors",
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
                route_function = condition_mapping[condition_name]
                # 简单参数解析
                if route_function in ["iteration_count_equals", "iteration_count_greater_than"]:
                    try:
                        count = int(params_str)
                        if route_function == "iteration_count_equals":
                            return "iteration_count_equals", {"count": count}
                        else:
                            return "iteration_count_greater_than", {"threshold": count}
                    except ValueError:
                        pass
                elif route_function == "message_contains_error":
                    return "keyword_match", {"keywords": [params_str]}
        
        # 默认为自定义条件
        return "custom_condition", {"expression": condition_str}
    
    def get_route_info(self, route_function_manager: Optional[RouteFunctionManager] = None) -> Optional[Dict[str, Any]]:
        """获取路由函数信息
        
        Args:
            route_function_manager: 路由函数管理器
            
        Returns:
            Optional[Dict[str, Any]]: 路由函数信息
        """
        manager = route_function_manager or self._route_function_manager
        if not manager:
            return None
        
        return manager.get_route_info(self.route_function)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"FlexibleConditionalEdge({self.from_node} -> [{self.route_function}])"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        params = f" params={self.route_parameters}" if self.route_parameters else ""
        return f"FlexibleConditionalEdge(from_node='{self.from_node}', route_function='{self.route_function}'{params}{desc})"


class FlexibleConditionalEdgeFactory:
    """灵活条件边工厂
    
    提供创建灵活条件边的工厂方法。
    """
    
    def __init__(self, route_function_manager: RouteFunctionManager):
        self.route_function_manager = route_function_manager
    
    def create_edge(
        self,
        from_node: str,
        route_function: str,
        route_parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> FlexibleConditionalEdge:
        """创建灵活条件边
        
        Args:
            from_node: 起始节点
            route_function: 路由函数名称
            route_parameters: 路由函数参数
            description: 描述
            
        Returns:
            FlexibleConditionalEdge: 灵活条件边实例
        """
        edge = FlexibleConditionalEdge(
            from_node=from_node,
            route_function=route_function,
            route_parameters=route_parameters or {},
            description=description
        )
        edge.set_route_function_manager(self.route_function_manager)
        
        # 验证边配置
        errors = edge.validate()
        if errors:
            raise ValueError(f"灵活条件边配置错误: {', '.join(errors)}")
        
        return edge
    
    def create_from_config(self, config: EdgeConfig) -> FlexibleConditionalEdge:
        """从配置创建灵活条件边
        
        Args:
            config: 边配置
            
        Returns:
            FlexibleConditionalEdge: 灵活条件边实例
        """
        return FlexibleConditionalEdge.from_config(config, self.route_function_manager)
    
    def create_batch(self, edge_configs: List[EdgeConfig]) -> List[FlexibleConditionalEdge]:
        """批量创建灵活条件边
        
        Args:
            edge_configs: 边配置列表
            
        Returns:
            List[FlexibleConditionalEdge]: 灵活条件边列表
        """
        edges = []
        errors = []
        
        for i, config in enumerate(edge_configs):
            try:
                edge = self.create_from_config(config)
                edges.append(edge)
            except Exception as e:
                errors.append(f"边 {i}: {e}")
        
        if errors:
            raise ValueError(f"批量创建灵活条件边失败:\n" + "\n".join(errors))
        
        return edges