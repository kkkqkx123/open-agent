"""工作流配置映射器

负责在基础设施层配置数据和Core层工作流实体之间进行转换。
"""

from typing import Dict, Any, Optional
import uuid

from src.infrastructure.config.models.base import ConfigData
from src.core.workflow.graph_entities import (
    Graph, Node, Edge, StateField, GraphState, EdgeType
)


class WorkflowConfigMapper:
    """工作流配置映射器
    
    负责在基础设施层配置数据和Core层工作流实体之间进行转换。
    """

    @staticmethod
    def config_data_to_graph(config_data: ConfigData) -> Graph:
        """将配置数据转换为图实体
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Graph: 图实体
        """
        data = config_data.data
        
        # 创建图状态
        state_schema_data = data.get("state_schema", {})
        state = WorkflowConfigMapper._dict_to_graph_state(state_schema_data)

        # 创建节点
        nodes = {}
        for node_name, node_data in data.get("nodes", {}).items():
            node = WorkflowConfigMapper._dict_to_node(node_data)
            nodes[node.node_id] = node

        # 创建边
        edges = []
        for edge_data in data.get("edges", []):
            edge = WorkflowConfigMapper._dict_to_edge(edge_data)
            edges.append(edge)

        # 创建图
        graph = Graph(
            graph_id=data.get("id", data.get("name", str(uuid.uuid4()))),
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            state=state,
            nodes=nodes,
            edges=edges,
            entry_point=data.get("entry_point")
        )

        return graph

    @staticmethod
    def graph_to_config_data(graph: Graph) -> ConfigData:
        """将图实体转换为配置数据
        
        Args:
            graph: 图实体
            
        Returns:
            ConfigData: 基础配置数据
        """
        data = WorkflowConfigMapper._graph_to_dict(graph)
        return ConfigData(data)

    @staticmethod
    def _dict_to_graph_state(data: Dict[str, Any]) -> GraphState:
        """将字典数据转换为图状态"""
        fields = {}
        for field_name, field_data in data.get("fields", {}).items():
            field = StateField(
                name=field_name,
                field_type=field_data.get("type", "str"),
                default_value=field_data.get("default"),
                reducer_function=field_data.get("reducer"),
                description=field_data.get("description")
            )
            fields[field_name] = field

        return GraphState(
            name=data.get("name", "GraphState"),
            fields=fields
        )

    @staticmethod
    def _graph_state_to_dict(state: GraphState) -> Dict[str, Any]:
        """将图状态转换为字典数据"""
        return {
            "name": state.name,
            "fields": {
                field_name: {
                    "name": field.name,
                    "type": field.field_type,
                    "default": field.default_value,
                    "reducer": field.reducer_function,
                    "description": field.description
                }
                for field_name, field in state.fields.items()
            }
        }

    @staticmethod
    def _dict_to_node(data: Dict[str, Any]) -> Node:
        """将字典数据转换为节点实体"""
        return Node(
            node_id=data.get("id", data.get("name", str(uuid.uuid4()))),
            name=data["name"],
            function_name=data["function_name"],
            description=data.get("description"),
            parameters=data.get("config", {}),
            node_type=data.get("type", "default")
        )

    @staticmethod
    def _node_to_dict(node: Node) -> Dict[str, Any]:
        """将节点实体转换为字典数据"""
        result: Dict[str, Any] = {
            "id": node.node_id,
            "name": node.name,
            "function_name": node.function_name,
        }
        if node.description:
            result["description"] = node.description
        if node.parameters:
            result["config"] = node.parameters
        if node.node_type != "default":
            result["type"] = node.node_type
        return result

    @staticmethod
    def _dict_to_edge(data: Dict[str, Any]) -> Edge:
        """将字典数据转换为边实体"""
        edge_type = EdgeType(data["type"])
        return Edge(
            edge_id=data.get("id", str(uuid.uuid4())),
            from_node_id=data["from"],
            to_node_id=data["to"],
            edge_type=edge_type,
            condition=data.get("condition"),
            description=data.get("description"),
            path_map=data.get("path_map"),
            route_function=data.get("route_function"),
            route_parameters=data.get("route_parameters", {})
        )

    @staticmethod
    def _edge_to_dict(edge: Edge) -> Dict[str, Any]:
        """将边实体转换为字典数据"""
        result: Dict[str, Any] = {
            "id": edge.edge_id,
            "from": edge.from_node_id,
            "to": edge.to_node_id,
            "type": edge.edge_type.value,
        }
        if edge.condition:
            result["condition"] = edge.condition
        if edge.description:
            result["description"] = edge.description
        if edge.path_map:
            result["path_map"] = edge.path_map
        if edge.route_function:
            result["route_function"] = edge.route_function
        if edge.route_parameters:
            result["route_parameters"] = edge.route_parameters
        return result

    @staticmethod
    def _graph_to_dict(graph: Graph) -> Dict[str, Any]:
        """将图实体转换为字典数据"""
        result: Dict[str, Any] = {
            "name": graph.name,
            "id": graph.graph_id,
            "description": graph.description,
            "version": graph.version,
        }

        # 状态模式
        if graph.state:
            result["state_schema"] = WorkflowConfigMapper._graph_state_to_dict(graph.state)

        # 节点
        if graph.nodes:
            result["nodes"] = {
                node_id: WorkflowConfigMapper._node_to_dict(node)
                for node_id, node in graph.nodes.items()
            }

        # 边
        if graph.edges:
            result["edges"] = [WorkflowConfigMapper._edge_to_dict(edge) for edge in graph.edges]

        # 其他配置
        if graph.entry_point:
            result["entry_point"] = graph.entry_point

        return result