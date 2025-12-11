"""配置映射器

负责在配置数据和业务实体之间进行转换。

📍 位置决策：
经过架构分析，此映射器应该位于 `src/core/workflow/mappers/` 目录。

📋 决策理由：
1. 职责分离：配置系统专注于配置处理，映射器专注于数据转换
2. 架构清晰：避免配置层反向依赖业务层，符合分层架构原则
3. 领域一致性：映射逻辑属于领域知识，与业务实体紧密相关
4. 维护便利：修改实体结构影响范围小，模块自治性强

🏗️ 架构原则：
- 单一职责原则：映射器专注于数据转换
- 依赖倒置原则：避免反向依赖
- 领域驱动设计：映射逻辑属于领域层

📚 相关文档：
- docs/plan/workflow/refactor/config_mapper_location_decision.md
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from ..graph_entities import (
    Graph, Node, Edge, StateField, GraphState, EdgeType
)


class ConfigMapper:
    """配置映射器
    
    负责在配置数据和业务实体之间进行转换。
    """

    def dict_to_graph(self, data: Dict[str, Any]) -> Graph:
        """将字典数据转换为图实体
        
        Args:
            data: 图配置字典数据
            
        Returns:
            Graph: 图实体
        """
        # 创建图状态
        state_schema_data = data.get("state_schema", {})
        state = self._dict_to_graph_state(state_schema_data)

        # 创建节点
        nodes = {}
        for node_name, node_data in data.get("nodes", {}).items():
            node = self._dict_to_node(node_data)
            nodes[node.node_id] = node

        # 创建边
        edges = []
        for edge_data in data.get("edges", []):
            edge = self._dict_to_edge(edge_data)
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

    def graph_to_dict(self, graph: Graph) -> Dict[str, Any]:
        """将图实体转换为字典数据
        
        Args:
            graph: 图实体
            
        Returns:
            Dict[str, Any]: 图配置字典数据
        """
        result = {
            "name": graph.name,
            "id": graph.graph_id,
            "description": graph.description,
            "version": graph.version,
        }

        # 状态模式
        if graph.state:
            result["state_schema"] = self._graph_state_to_dict(graph.state)

        # 节点
        if graph.nodes:
            result["nodes"] = {
                node_id: self._node_to_dict(node)
                for node_id, node in graph.nodes.items()
            }

        # 边
        if graph.edges:
            result["edges"] = [self._edge_to_dict(edge) for edge in graph.edges]

        # 其他配置
        if graph.entry_point:
            result["entry_point"] = graph.entry_point

        return result

    def _dict_to_graph_state(self, data: Dict[str, Any]) -> GraphState:
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

    def _graph_state_to_dict(self, state: GraphState) -> Dict[str, Any]:
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

    def _dict_to_node(self, data: Dict[str, Any]) -> Node:
        """将字典数据转换为节点实体"""
        return Node(
            node_id=data.get("id", data.get("name", str(uuid.uuid4()))),
            name=data["name"],
            function_name=data["function_name"],
            description=data.get("description"),
            parameters=data.get("config", {}),
            node_type=data.get("type", "default")
        )

    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        """将节点实体转换为字典数据"""
        result = {
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

    def _dict_to_edge(self, data: Dict[str, Any]) -> Edge:
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

    def _edge_to_dict(self, edge: Edge) -> Dict[str, Any]:
        """将边实体转换为字典数据"""
        result = {
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


# 全局映射器实例
_config_mapper = ConfigMapper()


def get_config_mapper() -> ConfigMapper:
    """获取配置映射器实例
    
    Returns:
        ConfigMapper: 配置映射器实例
    """
    return _config_mapper


def dict_to_graph(data: Dict[str, Any]) -> Graph:
    """便捷函数：将字典转换为图实体
    
    Args:
        data: 图配置字典数据
        
    Returns:
        Graph: 图实体
    """
    return _config_mapper.dict_to_graph(data)


def graph_to_dict(graph: Graph) -> Dict[str, Any]:
    """便捷函数：将图实体转换为字典
    
    Args:
        graph: 图实体
        
    Returns:
        Dict[str, Any]: 图配置字典数据
    """
    return _config_mapper.graph_to_dict(graph)