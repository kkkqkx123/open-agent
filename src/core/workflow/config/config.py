"""图配置系统

定义工作流图的结构和配置。
"""

from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, field, asdict
from enum import Enum


@dataclass
class WorkflowConfig:
    """工作流配置 - 用于状态机工作流"""
    name: str
    description: str = ""
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """从字典创建工作流配置
        
        Args:
            data: 配置字典
            
        Returns:
            WorkflowConfig: 工作流配置实例
        """
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            additional_config=data.get("additional_config", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class EdgeType(Enum):
    """边类型枚举"""
    SIMPLE = "simple"
    CONDITIONAL = "conditional"


@dataclass
class EdgeConfig:
    """边配置 - 符合LangGraph边模式"""
    from_node: str
    to_node: str
    type: EdgeType
    condition: Optional[str] = None  # 条件函数名（兼容旧格式）
    description: Optional[str] = None
    path_map: Optional[Dict[str, Any]] = None  # 条件边的路径映射
    
    # 新增灵活条件边支持
    route_function: Optional[str] = None  # 路由函数名称
    route_parameters: Optional[Dict[str, Any]] = None  # 路由函数参数

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EdgeConfig":
        """从字典创建边配置"""
        edge_type = EdgeType(data["type"])
        return cls(
            from_node=data["from"],
            to_node=data["to"],
            type=edge_type,
            condition=data.get("condition"),
            description=data.get("description"),
            path_map=data.get("path_map"),
            route_function=data.get("route_function"),
            route_parameters=data.get("route_parameters", {})
        )

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

    def is_flexible_conditional(self) -> bool:
        """检查是否为灵活条件边
        
        Returns:
            bool: 是否为灵活条件边
        """
        return (
            self.type == EdgeType.CONDITIONAL and 
            self.route_function is not None
        )

    def validate(self) -> List[str]:
        """验证边配置
        
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
class StateFieldConfig:
    """状态字段配置"""
    name: str
    type: str
    default: Any = None
    reducer: Optional[str] = None
    description: Optional[str] = None


@dataclass
class GraphStateConfig:
    """图状态配置"""
    name: str
    fields: Dict[str, StateFieldConfig] = field(default_factory=dict)


@dataclass
class NodeConfig:
    """节点配置"""
    name: str
    function_name: str
    description: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 新增：支持节点内部函数组合
    composition_name: Optional[str] = None  # 节点内部函数组合名称
    function_sequence: List[str] = field(default_factory=list)  # 函数执行序列

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        """从字典创建节点配置"""
        return cls(
            name=data["name"],
            function_name=data["function_name"],
            description=data.get("description"),
            config=data.get("config", {}),
            composition_name=data.get("composition_name"),
            function_sequence=data.get("function_sequence", [])
        )

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


@dataclass
class GraphConfig:
    """图配置 - 符合LangGraph StateGraph模式"""
    name: str
    description: str
    version: str = "1.0"
    state_schema: GraphStateConfig = field(default_factory=lambda: GraphStateConfig("GraphState"))
    nodes: Dict[str, NodeConfig] = field(default_factory=dict)
    edges: List[EdgeConfig] = field(default_factory=list)
    entry_point: Optional[str] = None
    checkpointer: Optional[str] = None  # 检查点配置
    interrupt_before: Optional[List[str]] = None  # 中断配置
    interrupt_after: Optional[List[str]] = None   # 中断配置
    state_overrides: Dict[str, Any] = field(default_factory=dict)  # 状态覆盖
    additional_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphConfig":
        """从字典创建图配置"""
        # 处理状态模式配置
        state_schema_data = data.get("state_schema", {})
        state_fields = {}
        
        for field_name, field_config in state_schema_data.get("fields", {}).items():
            state_fields[field_name] = StateFieldConfig(
                name=field_name,
                type=field_config.get("type", "str"),
                default=field_config.get("default"),
                reducer=field_config.get("reducer"),
                description=field_config.get("description")
            )
        
        state_schema = GraphStateConfig(
            name=state_schema_data.get("name", "GraphState"),
            fields=state_fields
        )

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
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0"),
            state_schema=state_schema,
            nodes=nodes,
            edges=edges,
            entry_point=data.get("entry_point"),
            checkpointer=data.get("checkpointer"),
            interrupt_before=data.get("interrupt_before"),
            interrupt_after=data.get("interrupt_after"),
            state_overrides=data.get("state_overrides", {}),
            additional_config=data.get("additional_config", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }
        
        # 状态模式
        if self.state_schema:
            state_fields: Dict[str, Any] = {}
            for field_name, field_config in self.state_schema.fields.items():
                field_data: Dict[str, Any] = {
                    "type": field_config.type,
                }
                if field_config.default is not None:
                    field_data["default"] = field_config.default
                if field_config.reducer:
                    field_data["reducer"] = field_config.reducer
                if field_config.description:
                    field_data["description"] = field_config.description
                state_fields[field_name] = field_data
            
            result["state_schema"] = {
                "name": self.state_schema.name,
                "fields": state_fields
            }
        
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

    def validate(self) -> List[str]:
        """验证图配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证基本字段
        if not self.name:
            errors.append("图名称不能为空")
        
        if not self.description:
            errors.append("图描述不能为空")
        
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
        from ..states.factory import StateFactory
        return StateFactory.create_state_class_from_config(self.state_schema)