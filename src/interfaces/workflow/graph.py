"""Graph interfaces for workflow.

This module contains interfaces related to workflow graphs, nodes, and edges.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..state.base import IState
    from ..state.workflow import IWorkflowState


@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    state: 'IState'
    next_node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class IGraphBuilder(ABC):
    """图构建器接口"""
    
    @abstractmethod
    def add_node(self, node: 'INode') -> 'IGraphBuilder':
        """添加节点"""
        pass
    
    @abstractmethod
    def add_edge(self, edge: 'IEdge') -> 'IGraphBuilder':
        """添加边"""
        pass
    
    @abstractmethod
    def build(self) -> 'IGraph':
        """构建图"""
        pass


class INodeRegistry(ABC):
    """节点注册表接口"""
    
    @abstractmethod
    def register(self, node_type: str, node_class: Type['INode']) -> None:
        """注册节点类型"""
        pass
    
    @abstractmethod
    def get(self, node_type: str) -> Optional[Type['INode']]:
        """获取节点类型"""
        pass
    
    @abstractmethod
    def list_types(self) -> List[str]:
        """列出所有注册的节点类型"""
        pass


class IRoutingFunction(ABC):
    """路由函数接口"""
    
    @abstractmethod
    def __call__(self, state: Any) -> str:
        """执行路由逻辑"""
        pass


class IRoutingRegistry(ABC):
    """路由注册表接口"""
    
    @abstractmethod
    def register(self, name: str, routing_func: IRoutingFunction) -> None:
        """注册路由函数"""
        pass
    
    @abstractmethod
    def get(self, name: str) -> Optional[IRoutingFunction]:
        """获取路由函数"""
        pass


class INode(ABC):
    """节点接口"""

    @property
    @abstractmethod
    def node_id(self) -> str:
        """节点ID"""
        pass

    @property
    @abstractmethod
    def node_type(self) -> str:
        """节点类型标识"""
        pass

    @abstractmethod
    def execute(self, state: 'IWorkflowState', config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        pass

    @abstractmethod
    async def execute_async(self, state: 'IWorkflowState', config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        pass

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置"""
        errors = []
        schema = self.get_config_schema()
        
        # 检查必需字段
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        properties = schema.get("properties", {})
        for field_name, field_config in properties.items():
            if field_name in config:
                expected_type = field_config.get("type")
                if expected_type == "string" and not isinstance(config[field_name], str):
                    errors.append(f"字段 {field_name} 应为字符串类型")
                elif expected_type == "integer" and not isinstance(config[field_name], int):
                    errors.append(f"字段 {field_name} 应为整数类型")
                elif expected_type == "boolean" and not isinstance(config[field_name], bool):
                    errors.append(f"字段 {field_name} 应为布尔类型")
                elif expected_type == "array" and not isinstance(config[field_name], list):
                    errors.append(f"字段 {field_name} 应为数组类型")
                elif expected_type == "object" and not isinstance(config[field_name], dict):
                    errors.append(f"字段 {field_name} 应为对象类型")
        
        return errors

    @abstractmethod
    def validate(self) -> List[str]:
        """验证节点配置"""
        pass


class IEdge(ABC):
    """边接口"""

    @property
    @abstractmethod
    def edge_id(self) -> str:
        """边ID"""
        pass

    @property
    @abstractmethod
    def source_node(self) -> str:
        """源节点ID"""
        pass

    @property
    @abstractmethod
    def target_node(self) -> str:
        """目标节点ID"""
        pass

    # 兼容旧接口的属性
    @property
    @abstractmethod
    def from_node(self) -> str:
        """起始节点ID（兼容旧接口）"""
        pass

    @property
    @abstractmethod
    def to_node(self) -> str:
        """目标节点ID（兼容旧接口）"""
        pass

    @property
    @abstractmethod
    def edge_type(self) -> str:
        """边类型（simple, conditional, flexible）"""
        pass

    @abstractmethod
    def can_traverse(self, state: 'IState') -> bool:
        """判断是否可以遍历此边"""
        pass

    @abstractmethod
    def can_traverse_with_config(self, state: 'IState', config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边（带配置）"""
        pass

    @abstractmethod
    def get_next_nodes(self, state: 'IState', config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表"""
        pass

    async def can_traverse_async(self, state: 'IState', config: Dict[str, Any]) -> bool:
        """异步判断是否可以遍历此边"""
        return self.can_traverse_with_config(state, config)

    async def get_next_nodes_async(self, state: 'IState', config: Dict[str, Any]) -> List[str]:
        """异步获取下一个节点列表"""
        return self.get_next_nodes(state, config)

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取边配置Schema"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证边配置"""
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """验证边配置"""
        pass


class IGraph(ABC):
    """图接口"""

    @property
    @abstractmethod
    def graph_id(self) -> str:
        """图ID"""
        pass

    @abstractmethod
    def add_node(self, node: INode) -> None:
        """添加节点"""
        pass

    @abstractmethod
    def add_edge(self, edge: IEdge) -> None:
        """添加边"""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[INode]:
        """获取节点"""
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[IEdge]:
        """获取边"""
        pass

    @abstractmethod
    def get_nodes(self) -> Dict[str, INode]:
        """获取所有节点"""
        pass

    @abstractmethod
    def get_edges(self) -> Dict[str, IEdge]:
        """获取所有边"""
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """验证图结构"""
        pass

    @abstractmethod
    def get_entry_points(self) -> List[str]:
        """获取入口节点列表"""
        pass

    @abstractmethod
    def get_exit_points(self) -> List[str]:
        """获取出口节点列表"""
        pass

    @abstractmethod
    def get_engine(self) -> Any:
        """获取图引擎"""
        pass


class INodeFunctionConfig(ABC):
    """节点函数配置接口"""
    
    @property
    @abstractmethod
    def function_type(self) -> str:
        """函数类型（llm, tool, analysis, condition, custom）"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """函数参数配置"""
        pass
    
    @property
    @abstractmethod
    def return_type(self) -> str:
        """返回值类型"""
        pass


class INodeCompositionConfig(ABC):
    """节点组合配置接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """组合名称"""
        pass
    
    @property
    @abstractmethod
    def function_sequence(self) -> List[str]:
        """函数执行序列"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """组合描述"""
        pass


class IRouteFunctionConfig(ABC):
    """路由函数配置接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """路由函数名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """路由函数描述"""
        pass
    
    @property
    @abstractmethod
    def return_values(self) -> List[str]:
        """可能的返回值列表"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """路由函数分类"""
        pass


# 保持向后兼容性
__all__ = [
    "INode",
    "IEdge",
    "IGraph", 
    "NodeExecutionResult",
    "IGraphBuilder",
    "INodeRegistry",
    "IRoutingFunction",
    "IRoutingRegistry",
    "INodeFunctionConfig",
    "INodeCompositionConfig",
    "IRouteFunctionConfig"
]