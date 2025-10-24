"""节点注册系统

提供节点类型的注册、获取和管理功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional, Callable
from dataclasses import dataclass

from src.domain.prompts.agent_state import AgentState


@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    state: AgentState
    next_node: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class BaseNode(ABC):
    """节点基类"""

    @property
    @abstractmethod
    def node_type(self) -> str:
        """节点类型标识"""
        pass

    @abstractmethod
    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑

        Args:
            state: 当前Agent状态
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


class NodeRegistry:
    """节点注册表"""

    def __init__(self) -> None:
        self._nodes: Dict[str, Type[BaseNode]] = {}
        self._node_instances: Dict[str, BaseNode] = {}

    def register_node(self, node_class: Type[BaseNode]) -> None:
        """注册节点类型

        Args:
            node_class: 节点类

        Raises:
            ValueError: 节点类型已存在
        """
        if node_class is None:
            raise ValueError("节点类不能为None")
        
        # 尝试获取节点类型，如果失败则抛出明确的错误
        try:
            # 创建临时实例来获取 node_type 属性值
            temp_instance = node_class()
            node_type = temp_instance.node_type
        except AttributeError as e:
            raise ValueError(f"节点类缺少 node_type 属性: {e}")
        except Exception as e:
            raise ValueError(f"获取节点类型失败: {e}")
        
        if node_type in self._nodes:
            raise ValueError(f"节点类型 '{node_type}' 已存在")
        
        self._nodes[node_type] = node_class

    def register_node_instance(self, node: BaseNode) -> None:
        """注册节点实例

        Args:
            node: 节点实例

        Raises:
            ValueError: 节点类型已存在
        """
        if node is None:
            raise ValueError("节点实例不能为None")
        
        # 尝试获取节点类型，如果失败则抛出明确的错误
        try:
            node_type = node.node_type
        except AttributeError as e:
            raise ValueError(f"节点实例缺少 node_type 属性: {e}")
        except Exception as e:
            raise ValueError(f"获取节点类型失败: {e}")
        
        if node_type in self._node_instances:
            raise ValueError(f"节点实例 '{node_type}' 已存在")
        
        self._node_instances[node_type] = node

    def get_node_class(self, node_type: str) -> Type[BaseNode]:
        """获取节点类型

        Args:
            node_type: 节点类型

        Returns:
            Type[BaseNode]: 节点类

        Raises:
            ValueError: 节点类型不存在
        """
        if node_type not in self._nodes:
            raise ValueError(f"未知的节点类型: {node_type}")
        return self._nodes[node_type]

    def get_node_instance(self, node_type: str) -> BaseNode:
        """获取节点实例

        Args:
            node_type: 节点类型

        Returns:
            BaseNode: 节点实例

        Raises:
            ValueError: 节点类型不存在
        """
        # 优先返回已注册的实例
        if node_type in self._node_instances:
            return self._node_instances[node_type]
        
        # 如果没有实例，创建新实例
        node_class = self.get_node_class(node_type)
        return node_class()

    def list_nodes(self) -> List[str]:
        """列出所有注册的节点类型

        Returns:
            List[str]: 节点类型列表
        """
        # 合并节点类和节点实例的类型
        all_nodes = set(self._nodes.keys())
        all_nodes.update(self._node_instances.keys())
        return list(all_nodes)

    def get_node_schema(self, node_type: str) -> Dict[str, Any]:
        """获取节点配置Schema

        Args:
            node_type: 节点类型

        Returns:
            Dict[str, Any]: 配置Schema

        Raises:
            ValueError: 节点类型不存在
        """
        node = self.get_node_instance(node_type)
        return node.get_config_schema()

    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """验证节点配置

        Args:
            node_type: 节点类型
            config: 节点配置

        Returns:
            List[str]: 验证错误列表
        """
        try:
            node = self.get_node_instance(node_type)
            return node.validate_config(config)
        except ValueError as e:
            return [str(e)]

    def clear(self) -> None:
        """清除所有注册的节点"""
        self._nodes.clear()
        self._node_instances.clear()


# 全局节点注册表实例
_global_registry: Optional[NodeRegistry] = None


def get_global_registry() -> NodeRegistry:
    """获取全局节点注册表

    Returns:
        NodeRegistry: 全局节点注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = NodeRegistry()
    return _global_registry


def register_node(node_class: Type[BaseNode]) -> None:
    """注册节点类型到全局注册表

    Args:
        node_class: 节点类
    """
    if node_class is None:
        raise ValueError("节点类不能为None")
    
    get_global_registry().register_node(node_class)


def register_node_instance(node: BaseNode) -> None:
    """注册节点实例到全局注册表

    Args:
        node: 节点实例
    """
    if node is None:
        raise ValueError("节点实例不能为None")
    
    get_global_registry().register_node_instance(node)


def get_node(node_type: str) -> BaseNode:
    """从全局注册表获取节点实例

    Args:
        node_type: 节点类型

    Returns:
        BaseNode: 节点实例
    """
    return get_global_registry().get_node_instance(node_type)


# 装饰器版本，用于自动注册节点
def node(node_type: str) -> Callable:
    """节点注册装饰器

    Args:
        node_type: 节点类型

    Returns:
        Callable: 装饰器函数
    """
    def decorator(node_class: Type[BaseNode]) -> Type[BaseNode]:
        # 创建一个新的类，覆盖 node_type 属性
        class WrappedNode(node_class):  # type: ignore
            @property
            def node_type(self) -> str:
                return node_type
        
        # 保持原始类的名称和文档
        WrappedNode.__name__ = node_class.__name__
        WrappedNode.__qualname__ = node_class.__qualname__
        if hasattr(node_class, '__doc__'):
            WrappedNode.__doc__ = node_class.__doc__
        
        # 注册到全局注册表
        register_node(WrappedNode)
        
        return WrappedNode
    
    return decorator