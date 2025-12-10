"""图配置领域实体

定义工作流图配置的领域实体，只包含业务逻辑和数据结构，
不包含配置处理、验证等基础设施功能。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Type
from enum import Enum

from src.interfaces.workflow.config import (
    EdgeType as InterfaceEdgeType,
    INodeConfig,
    IEdgeConfig,
    IStateFieldConfig,
    IGraphStateConfig,
    IGraphConfig
)


# 直接使用接口层的 EdgeType，不继承（Enum final 类）
EdgeType = InterfaceEdgeType


@dataclass
class StateFieldConfig(IStateFieldConfig):
    """状态字段配置领域实体"""
    _name: str
    _type: str
    default: Any = None
    _reducer: Optional[str] = None
    _description: Optional[str] = None

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def type(self) -> str:
        return self._type
    
    @property
    def reducer(self) -> Optional[str]:
        return self._reducer
    
    @property
    def description(self) -> Optional[str]:
        return self._description

    # 业务方法
    def has_default(self) -> bool:
        """检查是否有默认值"""
        return self.default is not None

    def has_reducer(self) -> bool:
        """检查是否有reducer"""
        return self.reducer is not None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.reducer:
            result["reducer"] = self.reducer
        if self.description:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateFieldConfig":
        """从字典创建状态字段配置"""
        return cls(
            _name=data.get("name", ""),
            _type=data.get("type", "str"),
            default=data.get("default"),
            _reducer=data.get("reducer"),
            _description=data.get("description")
        )


@dataclass
class GraphStateConfig(IGraphStateConfig):
    """图状态配置领域实体"""
    _name: str
    _fields: Dict[str, StateFieldConfig] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def fields(self) -> Dict[str, StateFieldConfig]:
        return self._fields

    # 业务方法
    def get_field_count(self) -> int:
        """获取字段数量"""
        return len(self.fields)

    def get_field_names(self) -> List[str]:
        """获取字段名称列表"""
        return list(self.fields.keys())

    def has_field(self, field_name: str) -> bool:
        """检查是否包含指定字段"""
        return field_name in self.fields

    def get_field(self, field_name: str) -> Optional[StateFieldConfig]:
        """获取指定字段配置"""
        return self.fields.get(field_name)

    def add_field(self, field: StateFieldConfig) -> None:
        """添加字段"""
        self._fields[field.name] = field

    def remove_field(self, field_name: str) -> bool:
        """移除字段"""
        if field_name in self._fields:
            del self._fields[field_name]
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "fields": {
                name: config.to_dict()
                for name, config in self._fields.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphStateConfig":
        """从字典创建图状态配置"""
        fields = {}
        for field_name, field_config in data.get("fields", {}).items():
            if isinstance(field_config, StateFieldConfig):
                fields[field_name] = field_config
            else:
                fields[field_name] = StateFieldConfig.from_dict(field_config)
        
        return cls(
            _name=data.get("name", "GraphState"),
            _fields=fields
        )


@dataclass
class NodeConfig(INodeConfig):
    """节点配置领域实体"""
    _name: str
    _function_name: str
    _description: Optional[str] = None
    _config: Dict[str, Any] = field(default_factory=dict)
    
    # 新增：支持节点内部函数组合
    _composition_name: Optional[str] = None  # 节点内部函数组合名称
    _function_sequence: List[str] = field(default_factory=list)  # 函数执行序列

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def function_name(self) -> str:
        return self._function_name
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config
    
    @property
    def composition_name(self) -> Optional[str]:
        return self._composition_name
    
    @property
    def function_sequence(self) -> List[str]:
        return self._function_sequence

    # 业务方法
    def has_composition(self) -> bool:
        """检查是否有函数组合"""
        return self.composition_name is not None

    def get_function_count(self) -> int:
        """获取函数序列数量"""
        return len(self.function_sequence)

    def has_config(self, key: str) -> bool:
        """检查是否包含指定配置"""
        return key in self.config

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value

    def is_llm_node(self) -> bool:
        """检查是否为LLM节点"""
        return "llm" in self.name.lower() or "agent" in self.name.lower()

    def is_tool_node(self) -> bool:
        """检查是否为工具节点"""
        return "tool" in self.name.lower()

    def is_condition_node(self) -> bool:
        """检查是否为条件节点"""
        return "condition" in self.name.lower() or "decide" in self.name.lower()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result: Dict[str, Any] = {
            "name": self.name,
            "function_name": self.function_name,
        }
        if self.description:
            result["description"] = self.description
        if self.config:
            result["config"] = self.config
        if self.composition_name:
            result["composition_name"] = self.composition_name
        if self.function_sequence:
            result["function_sequence"] = self.function_sequence
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        """从字典创建节点配置"""
        return cls(
            _name=data["name"],
            _function_name=data["function_name"],
            _description=data.get("description"),
            _config=data.get("config", {}),
            _composition_name=data.get("composition_name"),
            _function_sequence=data.get("function_sequence", [])
        )


@dataclass
class EdgeConfig(IEdgeConfig):
    """边配置领域实体"""
    _from_node: str
    _to_node: str
    _type: InterfaceEdgeType
    _condition: Optional[str] = None  # 条件函数名（兼容旧格式）
    _description: Optional[str] = None
    _path_map: Optional[Dict[str, Any]] = None  # 条件边的路径映射
    
    # 新增灵活条件边支持
    _route_function: Optional[str] = None  # 路由函数名称
    _route_parameters: Optional[Dict[str, Any]] = None  # 路由函数参数

    @property
    def from_node(self) -> str:
        return self._from_node
    
    @property
    def to_node(self) -> str:
        return self._to_node
    
    @property
    def type(self) -> InterfaceEdgeType:
        return self._type
    
    @property
    def condition(self) -> Optional[str]:
        return self._condition
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def path_map(self) -> Optional[Dict[str, Any]]:
        return self._path_map
    
    @property
    def route_function(self) -> Optional[str]:
        return self._route_function
    
    @property
    def route_parameters(self) -> Optional[Dict[str, Any]]:
        return self._route_parameters

    # 业务方法
    def is_simple_edge(self) -> bool:
        """检查是否为简单边"""
        return self.type == EdgeType.SIMPLE

    def is_conditional_edge(self) -> bool:
        """检查是否为条件边"""
        return self.type == EdgeType.CONDITIONAL

    def is_flexible_conditional(self) -> bool:
        """检查是否为灵活条件边"""
        return (
            self.type == EdgeType.CONDITIONAL and 
            self.route_function is not None
        )

    def has_condition(self) -> bool:
        """检查是否有条件"""
        return self.condition is not None

    def has_path_map(self) -> bool:
        """检查是否有路径映射"""
        return self.path_map is not None

    def has_route_function(self) -> bool:
        """检查是否有路由函数"""
        return self.route_function is not None

    def get_target_nodes(self) -> List[str]:
        """获取目标节点列表"""
        if self.is_simple_edge():
            return [self.to_node] if self.to_node else []
        elif self.has_path_map() and isinstance(self.path_map, dict):
            return list(self.path_map.values())
        elif self.has_path_map() and isinstance(self.path_map, list):
            return self.path_map
        else:
            return []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result: Dict[str, Any] = {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.type.value,
        }
        if self.condition:
            result["condition"] = self.condition
        if self.description:
            result["description"] = self.description
        if self.path_map:
            result["path_map"] = self.path_map
        if self.route_function:
            result["route_function"] = self.route_function
        if self.route_parameters:
            result["route_parameters"] = self.route_parameters
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EdgeConfig":
        """从字典创建边配置"""
        edge_type = EdgeType(data["type"])
        return cls(
            _from_node=data["from"],
            _to_node=data["to"],
            _type=edge_type,
            _condition=data.get("condition"),
            _description=data.get("description"),
            _path_map=data.get("path_map"),
            _route_function=data.get("route_function"),
            _route_parameters=data.get("route_parameters", {})
        )

    def validate(self) -> List[str]:
        """验证边配置（基础业务验证）
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not self.from_node:
            errors.append("起始节点不能为空")
        
        if not self.to_node and self.type == EdgeType.SIMPLE:
            errors.append("简单边必须指定目标节点")
        
        if self.type == EdgeType.CONDITIONAL:
            # 检查是否为灵活条件边
            if self.is_flexible_conditional():
                if not self.route_function:
                    errors.append("灵活条件边必须指定路由函数")
            else:
                # 传统条件边
                if not self.condition:
                    errors.append("条件边必须指定条件表达式")
        
        return errors


@dataclass
class GraphConfig(IGraphConfig):
    """图配置领域实体"""
    _name: str
    _id: str = ""  # 添加 id 属性
    _description: str = ""
    _version: str = "1.0"
    _state_schema: GraphStateConfig = field(default_factory=lambda: GraphStateConfig(_name="GraphState"))
    _nodes: Dict[str, NodeConfig] = field(default_factory=dict)
    _edges: List[EdgeConfig] = field(default_factory=list)
    _entry_point: Optional[str] = None
    _checkpointer: Optional[str] = None  # 检查点配置
    _interrupt_before: Optional[List[str]] = None  # 中断配置
    _interrupt_after: Optional[List[str]] = None   # 中断配置
    _state_overrides: Dict[str, Any] = field(default_factory=dict)  # 状态覆盖
    _additional_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def state_schema(self) -> GraphStateConfig:
        return self._state_schema
    
    @property
    def nodes(self) -> Dict[str, NodeConfig]:
        return self._nodes
    
    @property
    def entry_point(self) -> Optional[str]:
        return self._entry_point
    
    @property
    def checkpointer(self) -> Optional[str]:
        return self._checkpointer
    
    @property
    def interrupt_before(self) -> Optional[List[str]]:
        return self._interrupt_before
    
    @property
    def interrupt_after(self) -> Optional[List[str]]:
        return self._interrupt_after
    
    @property
    def state_overrides(self) -> Dict[str, Any]:
        return self._state_overrides
    
    @property
    def additional_config(self) -> Dict[str, Any]:
        return self._additional_config
    
    @property
    def edges(self) -> List[EdgeConfig]:
        return self._edges

    # 业务方法
    def get_node_count(self) -> int:
        """获取节点数量"""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """获取边数量"""
        return len(self.edges)

    def get_node_names(self) -> List[str]:
        """获取节点名称列表"""
        return list(self.nodes.keys())

    def has_node(self, node_name: str) -> bool:
        """检查是否包含指定节点"""
        return node_name in self.nodes

    def get_node(self, node_name: str) -> Optional[NodeConfig]:
        """获取指定节点配置"""
        return self.nodes.get(node_name)

    def add_node(self, node: NodeConfig) -> None:
        """添加节点"""
        self._nodes[node.name] = node

    def remove_node(self, node_name: str) -> bool:
        """移除节点"""
        if node_name in self._nodes:
            del self._nodes[node_name]
            # 同时移除相关的边
            self._edges = [edge for edge in self._edges 
                        if edge.from_node != node_name and edge.to_node != node_name]
            return True
        return False

    def get_edges_from_node(self, node_name: str) -> List[EdgeConfig]:
        """获取从指定节点出发的边"""
        return [edge for edge in self.edges if edge.from_node == node_name]

    def get_edges_to_node(self, node_name: str) -> List[EdgeConfig]:
        """获取指向指定节点的边"""
        return [edge for edge in self.edges if edge.to_node == node_name]

    def get_connected_nodes(self, node_name: str) -> List[str]:
        """获取与指定节点相连的节点"""
        connected = set()
        for edge in self.edges:
            if edge.from_node == node_name and edge.to_node:
                connected.add(edge.to_node)
            elif edge.to_node == node_name:
                connected.add(edge.from_node)
        return list(connected)

    def has_entry_point(self) -> bool:
        """检查是否有入口点"""
        return self.entry_point is not None

    def is_entry_point(self, node_name: str) -> bool:
        """检查指定节点是否为入口点"""
        return self.entry_point == node_name

    def get_state_field_count(self) -> int:
        """获取状态字段数量"""
        return self.state_schema.get_field_count()

    def has_checkpointer(self) -> bool:
        """检查是否有检查点配置"""
        return self.checkpointer is not None

    def has_interrupts(self) -> bool:
        """检查是否有中断配置"""
        return (self.interrupt_before is not None and len(self.interrupt_before) > 0) or \
               (self.interrupt_after is not None and len(self.interrupt_after) > 0)

    def get_additional_config(self, key: str, default: Any = None) -> Any:
        """获取额外配置值"""
        return self.additional_config.get(key, default)

    def set_additional_config(self, key: str, value: Any) -> None:
        """设置额外配置值"""
        self.additional_config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result: Dict[str, Any] = {
            "name": self.name,
            "id": self.id or self.name,  # 如果id为空，使用name
            "description": self.description,
            "version": self.version,
        }
        
        # 状态模式
        if self.state_schema:
            result["state_schema"] = self.state_schema.to_dict()
        
        # 节点
        if self.nodes:
            result["nodes"] = {
                name: config.to_dict()
                for name, config in self.nodes.items()
            }
        
        # 边
        if self.edges:
            result["edges"] = [edge.to_dict() for edge in self.edges]
        
        # 其他配置
        if self.entry_point:
            result["entry_point"] = self.entry_point
        if self.checkpointer:
            result["checkpointer"] = self.checkpointer
        if self.interrupt_before:
            result["interrupt_before"] = self.interrupt_before
        if self.interrupt_after:
            result["interrupt_after"] = self.interrupt_after
        if self.state_overrides:
            result["state_overrides"] = self.state_overrides
        if self.additional_config:
            result["additional_config"] = self.additional_config
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphConfig":
        """从字典创建图配置"""
        # 处理状态模式配置
        state_schema_data = data.get("state_schema", {})
        state_schema = GraphStateConfig.from_dict(state_schema_data)

        # 处理节点配置
        nodes = {}
        for node_name, node_data in data.get("nodes", {}).items():
            node_data["name"] = node_name  # 确保节点名称正确
            nodes[node_name] = NodeConfig.from_dict(node_data)

        # 处理边配置
        edges = []
        for edge_data in data.get("edges", []):
            edges.append(EdgeConfig.from_dict(edge_data))

        return cls(
            _name=data["name"],
            _id=data.get("id", data.get("name", "")),  # 使用name作为默认id
            _description=data.get("description", ""),
            _version=data.get("version", "1.0"),
            _state_schema=state_schema,
            _nodes=nodes,
            _edges=edges,
            _entry_point=data.get("entry_point"),
            _checkpointer=data.get("checkpointer"),
            _interrupt_before=data.get("interrupt_before"),
            _interrupt_after=data.get("interrupt_after"),
            _state_overrides=data.get("state_overrides", {}),
            _additional_config=data.get("additional_config", {})
        )

    def validate(self) -> List[str]:
        """验证图配置（基础业务验证）
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证基本字段
        if not self.name:
            errors.append("图名称不能为空")
        
        # 验证节点
        node_names = set(self.nodes.keys())
        for node_name, node_config in self.nodes.items():
            if not node_config.function_name:
                errors.append(f"节点 {node_name} 缺少函数名称")
        
        # 验证边
        for edge in self.edges:
            edge_errors = edge.validate()
            for error in edge_errors:
                errors.append(f"边 {edge.from_node} -> {edge.to_node}: {error}")
            
            # 验证节点存在性
            if edge.from_node not in node_names and edge.from_node not in ["__start__"]:
                errors.append(f"边起始节点不存在: {edge.from_node}")
            
            if edge.to_node not in node_names and edge.to_node not in ["__end__"] and edge.type == EdgeType.SIMPLE:
                errors.append(f"边目标节点不存在: {edge.to_node}")
        
        # 验证入口点
        if self.entry_point and self.entry_point not in node_names:
            errors.append(f"入口点节点不存在: {self.entry_point}")
        
        return errors

    def get_state_class(self) -> Type[Dict[str, Any]]:
        """获取状态类"""
        # TODO: 实现状态工厂或使用接口
        # from ..states.factory import WorkflowStateFactory
        # return WorkflowStateFactory.create_state_class_from_config(self.state_schema)
        
        # 临时返回基本字典类型
        return Dict[str, Any]


@dataclass
class WorkflowConfig:
    """工作流配置领域实体 - 用于状态机工作流"""
    name: str
    description: str = ""
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    # 业务方法
    def has_additional_config(self, key: str) -> bool:
        """检查是否有额外配置"""
        return key in self.additional_config
    
    def get_additional_config(self, key: str, default: Any = None) -> Any:
        """获取额外配置值"""
        return self.additional_config.get(key, default)
    
    def set_additional_config(self, key: str, value: Any) -> None:
        """设置额外配置值"""
        self.additional_config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """从字典创建工作流配置"""
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            additional_config=data.get("additional_config", {})
        )