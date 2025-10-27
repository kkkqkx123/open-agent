"""LangGraph配置模型

定义符合LangGraph最佳实践的图配置数据结构，支持YAML序列化和反序列化。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Annotated, Callable, Union, Literal
from enum import Enum
import operator
import types
from typing_extensions import TypedDict


class EdgeType(Enum):
    """边类型枚举"""
    SIMPLE = "simple"
    CONDITIONAL = "conditional"


@dataclass
class StateFieldConfig:
    """状态字段配置"""
    type: str
    default: Any = None
    reducer: Optional[str] = None  # reducer函数名，如 "operator.add"
    description: Optional[str] = None


@dataclass
class GraphStateConfig:
    """图状态配置 - 符合LangGraph TypedDict模式"""
    name: str
    fields: Dict[str, StateFieldConfig] = field(default_factory=dict)
    
    def to_typed_dict_class(self) -> type:
        """转换为TypedDict类"""
        # 创建字段字典
        field_annotations = {}
        field_defaults = {}
        
        for field_name, field_config in self.fields.items():
            # 解析类型字符串
            field_type = self._parse_type_string(field_config.type)
            
            # 如果有reducer，添加Annotated
            if field_config.reducer:
                reducer_func = self._get_reducer_function(field_config.reducer)
                field_type = Annotated[field_type, reducer_func]
            
            field_annotations[field_name] = field_type
            if field_config.default is not None:
                field_defaults[field_name] = field_config.default
        
        # 创建TypedDict类
        namespace = {"__annotations__": field_annotations}
        if field_defaults:
            namespace.update(field_defaults)
        
        # 使用 types.new_class 替代 type() 来避免 MRO 解析错误
        DynamicState = types.new_class(self.name, (TypedDict,), {}, lambda ns: ns.update(namespace))
        return DynamicState
    
    def _parse_type_string(self, type_str: str) -> type:
        """解析类型字符串为实际类型"""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "List[str]": List[str],
            "List[int]": List[int],
            "List[dict]": List[Dict[str, Any]],
            "Dict[str, Any]": Dict[str, Any],
        }
        return type_map.get(type_str, str)
    
    def _get_reducer_function(self, reducer_str: str) -> Callable:
        """获取reducer函数"""
        reducer_map = {
            "operator.add": operator.add,
            "operator.or_": operator.or_,
            "operator.and_": operator.and_,
            "append": lambda x, y: (x or []) + (y or []),
            "extend": lambda x, y: (x or []) + (y or []),
            "replace": lambda x, y: y,
        }
        return reducer_map.get(reducer_str, operator.add)


@dataclass
class NodeConfig:
    """节点配置 - 符合LangGraph节点模式"""
    name: str
    function_name: str  # 对应的函数名
    config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    input_state: Optional[str] = None  # 可选的输入状态类型
    output_state: Optional[str] = None  # 可选的输出状态类型

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        """从字典创建节点配置"""
        return cls(
            name=data.get("name", ""),
            function_name=data.get("function", data.get("type", "")),
            config=data.get("config", {}),
            description=data.get("description"),
            input_state=data.get("input_state"),
            output_state=data.get("output_state")
        )


@dataclass
class EdgeConfig:
    """边配置 - 符合LangGraph边模式"""
    from_node: str
    to_node: str
    type: EdgeType
    condition: Optional[str] = None  # 条件函数名
    description: Optional[str] = None
    path_map: Optional[List[str]] = None  # 条件边的路径映射

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
            path_map=data.get("path_map")
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
    additional_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphConfig":
        """从字典创建图配置"""
        # 处理状态模式配置
        state_schema_data = data.get("state_schema", {})
        state_fields = {}
        
        for field_name, field_config in state_schema_data.get("fields", {}).items():
            state_fields[field_name] = StateFieldConfig(
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
            additional_config={
                k: v for k, v in data.items()
                if k not in ["name", "description", "version", "state_schema", "nodes", "edges", 
                           "entry_point", "checkpointer", "interrupt_before", "interrupt_after"]
            }
        )

    def model_dump(self) -> Dict[str, Any]:
        """转换为字典（Pydantic兼容方法）"""
        return self.to_dict()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "state_schema": {
                "name": self.state_schema.name,
                "fields": {
                    name: {
                        "type": config.type,
                        "default": config.default,
                        "reducer": config.reducer,
                        "description": config.description
                    }
                    for name, config in self.state_schema.fields.items()
                }
            },
            "nodes": {
                name: {
                    "function": node.function_name,
                    "config": node.config,
                    "description": node.description,
                    "input_state": node.input_state,
                    "output_state": node.output_state
                }
                for name, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
        }

        if self.entry_point:
            result["entry_point"] = self.entry_point
        if self.checkpointer:
            result["checkpointer"] = self.checkpointer
        if self.interrupt_before:
            result["interrupt_before"] = self.interrupt_before
        if self.interrupt_after:
            result["interrupt_after"] = self.interrupt_after
        if self.additional_config:
            result.update(self.additional_config)

        return result

    def validate(self) -> List[str]:
        """验证配置的有效性"""
        errors = []

        # 检查基本字段
        if not self.name:
            errors.append("图名称不能为空")
        if not self.description:
            errors.append("图描述不能为空")

        # 检查节点配置
        if not self.nodes:
            errors.append("图必须至少包含一个节点")

        # 检查边配置
        node_names = set(self.nodes.keys())
        for edge in self.edges:
            if edge.from_node not in node_names:
                errors.append(f"边的起始节点 '{edge.from_node}' 不存在")
            if edge.to_node not in node_names:
                errors.append(f"边的目标节点 '{edge.to_node}' 不存在")
            if edge.type == EdgeType.CONDITIONAL and not edge.condition:
                errors.append(f"条件边 '{edge.from_node}' -> '{edge.to_node}' 缺少条件表达式")

        # 检查入口点
        if self.entry_point and self.entry_point not in node_names:
            errors.append(f"入口节点 '{self.entry_point}' 不存在")

        # 检查状态配置
        if not self.state_schema.fields:
            errors.append("图必须定义状态模式")

        return errors

    def get_state_class(self) -> type:
        """获取状态类"""
        return self.state_schema.to_typed_dict_class()


# 为了向后兼容，保留旧的类名
WorkflowConfig = GraphConfig
StateSchemaConfig = GraphStateConfig