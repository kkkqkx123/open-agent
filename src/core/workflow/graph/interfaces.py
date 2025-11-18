"""图接口定义

提供图系统的核心接口，包括节点、边和图的抽象定义。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from src.state.interfaces import IState


@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    state: 'IState'
    next_node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


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
    def execute(self, state: 'IState', config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        pass

    @abstractmethod
    async def execute_async(self, state: 'IState', config: Dict[str, Any]) -> NodeExecutionResult:
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
        """获取节点配置Schema

        Returns:
            Dict[str, Any]: 配置Schema
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置

        Args:
            config: 节点配置

        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
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


class IEdge(ABC):
    """边接口"""

    @property
    @abstractmethod
    def edge_id(self) -> str:
        """边ID"""
        pass

    @property
    @abstractmethod
    def from_node(self) -> str:
        """起始节点ID"""
        pass

    @property
    @abstractmethod
    def to_node(self) -> str:
        """目标节点ID"""
        pass

    @abstractmethod
    def can_traverse(self, state: 'IState', config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边

        Args:
            state: 当前工作流状态
            config: 边配置

        Returns:
            bool: 是否可以遍历
        """
        pass

    @abstractmethod
    def get_next_nodes(self, state: 'IState', config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表

        Args:
            state: 当前工作流状态
            config: 边配置

        Returns:
            List[str]: 下一个节点ID列表
        """
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
        """添加节点

        Args:
            node: 节点实例
        """
        pass

    @abstractmethod
    def add_edge(self, edge: IEdge) -> None:
        """添加边

        Args:
            edge: 边实例
        """
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[INode]:
        """获取节点

        Args:
            node_id: 节点ID

        Returns:
            Optional[INode]: 节点实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[IEdge]:
        """获取边

        Args:
            edge_id: 边ID

        Returns:
            Optional[IEdge]: 边实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def get_outgoing_edges(self, node_id: str) -> List[IEdge]:
        """获取节点的出边

        Args:
            node_id: 节点ID

        Returns:
            List[IEdge]: 出边列表
        """
        pass

    @abstractmethod
    def get_incoming_edges(self, node_id: str) -> List[IEdge]:
        """获取节点的入边

        Args:
            node_id: 节点ID

        Returns:
            List[IEdge]: 入边列表
        """
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """验证图结构

        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        pass


class IGraphBuilder(ABC):
    """图构建器接口"""

    @abstractmethod
    def create_node(self, node_type: str, node_id: str, config: Dict[str, Any]) -> INode:
        """创建节点

        Args:
            node_type: 节点类型
            node_id: 节点ID
            config: 节点配置

        Returns:
            INode: 节点实例
        """
        pass

    @abstractmethod
    def create_edge(self, edge_type: str, edge_id: str, from_node: str, to_node: str, 
                   config: Dict[str, Any]) -> IEdge:
        """创建边

        Args:
            edge_type: 边类型
            edge_id: 边ID
            from_node: 起始节点ID
            to_node: 目标节点ID
            config: 边配置

        Returns:
            IEdge: 边实例
        """
        pass

    @abstractmethod
    def build(self) -> IGraph:
        """构建图

        Returns:
            IGraph: 图实例
        """
        pass


class INodeRegistry(ABC):
    """节点注册表接口"""

    @abstractmethod
    def register_node(self, node_class: Type[INode]) -> None:
        """注册节点类型

        Args:
            node_class: 节点类
        """
        pass

    @abstractmethod
    def register_node_instance(self, node: INode) -> None:
        """注册节点实例

        Args:
            node: 节点实例
        """
        pass

    @abstractmethod
    def get_node_class(self, node_type: str) -> Type[INode]:
        """获取节点类型

        Args:
            node_type: 节点类型

        Returns:
            Type[INode]: 节点类
        """
        pass

    @abstractmethod
    def get_node_instance(self, node_type: str) -> INode:
        """获取节点实例

        Args:
            node_type: 节点类型

        Returns:
            INode: 节点实例
        """
        pass

    @abstractmethod
    def list_nodes(self) -> List[str]:
        """列出所有注册的节点类型

        Returns:
            List[str]: 节点类型列表
        """
        pass

    @abstractmethod
    def get_node_schema(self, node_type: str) -> Dict[str, Any]:
        """获取节点配置Schema

        Args:
            node_type: 节点类型

        Returns:
            Dict[str, Any]: 配置Schema
        """
        pass

    @abstractmethod
    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """验证节点配置

        Args:
            node_type: 节点类型
            config: 节点配置

        Returns:
            List[str]: 验证错误列表
        """
        pass


class IRoutingFunction(ABC):
    """路由函数接口"""

    @abstractmethod
    def route(self, state: 'IState', config: Dict[str, Any]) -> List[str]:
        """路由函数

        Args:
            state: 当前工作流状态
            config: 路由配置

        Returns:
            List[str]: 下一个节点ID列表
        """
        pass


class IRoutingRegistry(ABC):
    """路由注册表接口"""

    @abstractmethod
    def register_function(self, name: str, function: IRoutingFunction) -> None:
        """注册路由函数

        Args:
            name: 函数名称
            function: 路由函数
        """
        pass

    @abstractmethod
    def get_function(self, name: str) -> Optional[IRoutingFunction]:
        """获取路由函数

        Args:
            name: 函数名称

        Returns:
            Optional[IRoutingFunction]: 路由函数，如果不存在则返回None
        """
        pass

    @abstractmethod
    def list_functions(self) -> List[str]:
        """列出所有注册的路由函数

        Returns:
            List[str]: 函数名称列表
        """
        pass