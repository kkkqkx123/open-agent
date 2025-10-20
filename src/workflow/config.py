"""工作流配置模型

定义工作流配置的数据结构，支持YAML序列化和反序列化。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class EdgeType(Enum):
    """边类型枚举"""
    SIMPLE = "simple"
    CONDITIONAL = "conditional"


@dataclass
class StateSchemaConfig:
    """状态模式配置"""
    messages: str = "List[BaseMessage]"
    tool_calls: str = "List[ToolCall]"
    tool_results: str = "List[ToolResult]"
    iteration_count: str = "int"
    max_iterations: str = "int"
    additional_fields: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "messages": self.messages,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
        }
        if self.additional_fields:
            result.update(self.additional_fields)
        return result


@dataclass
class NodeConfig:
    """节点配置"""
    type: str
    config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        """从字典创建节点配置"""
        return cls(
            type=data["type"],
            config=data.get("config", {}),
            description=data.get("description")
        )


@dataclass
class EdgeConfig:
    """边配置"""
    from_node: str
    to_node: str
    type: EdgeType
    condition: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EdgeConfig":
        """从字典创建边配置"""
        edge_type = EdgeType(data["type"])
        return cls(
            from_node=data["from"],
            to_node=data["to"],
            type=edge_type,
            condition=data.get("condition"),
            description=data.get("description")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.type.value,
        }
        if self.condition:
            result["condition"] = self.condition
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class WorkflowConfig:
    """工作流配置"""
    name: str
    description: str
    version: str = "1.0"
    state_schema: StateSchemaConfig = field(default_factory=StateSchemaConfig)
    nodes: Dict[str, NodeConfig] = field(default_factory=dict)
    edges: List[EdgeConfig] = field(default_factory=list)
    entry_point: Optional[str] = None
    additional_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """从字典创建工作流配置"""
        # 处理状态模式配置
        state_schema_data = data.get("state_schema", {})
        state_schema = StateSchemaConfig(
            messages=state_schema_data.get("messages", "List[BaseMessage]"),
            tool_calls=state_schema_data.get("tool_calls", "List[ToolCall]"),
            tool_results=state_schema_data.get("tool_results", "List[ToolResult]"),
            iteration_count=state_schema_data.get("iteration_count", "int"),
            max_iterations=state_schema_data.get("max_iterations", "int"),
            additional_fields={
                k: v for k, v in state_schema_data.items()
                if k not in ["messages", "tool_calls", "tool_results", "iteration_count", "max_iterations"]
            }
        )

        # 处理节点配置
        nodes = {}
        for node_name, node_data in data.get("nodes", {}).items():
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
            additional_config={
                k: v for k, v in data.items()
                if k not in ["name", "description", "version", "state_schema", "nodes", "edges", "entry_point"]
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "state_schema": self.state_schema.to_dict(),
            "nodes": {
                name: {
                    "type": node.type,
                    "config": node.config,
                }
                for name, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
        }

        # 添加节点描述（如果有）
        for name, node in self.nodes.items():
            if node.description:
                result["nodes"][name]["description"] = node.description

        if self.entry_point:
            result["entry_point"] = self.entry_point

        if self.additional_config:
            result.update(self.additional_config)

        return result

    def validate(self) -> List[str]:
        """验证配置的有效性"""
        errors = []

        # 检查基本字段
        if not self.name:
            errors.append("工作流名称不能为空")
        if not self.description:
            errors.append("工作流描述不能为空")

        # 检查节点配置
        if not self.nodes:
            errors.append("工作流必须至少包含一个节点")

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

        return errors