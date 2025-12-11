"""工作流配置映射器

负责在配置数据和业务实体之间进行转换，实现IConfigMapper接口。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from src.interfaces.config import IConfigMapper, ValidationResult
from src.interfaces.common_domain import ValidationResult as CommonValidationResult
from ..graph_entities import (
    Graph, Node, Edge, StateField, GraphState, EdgeType
)


class WorkflowConfigMapper(IConfigMapper):
    """工作流配置映射器
    
    负责在配置数据和业务实体之间进行转换。
    """

    def dict_to_entity(self, config_data: Dict[str, Any]) -> Graph:
        """将配置字典转换为业务实体
        
        Args:
            config_data: 配置字典数据
            
        Returns:
            Graph: 图实体
        """
        return self._dict_to_graph(config_data)
    
    def _dict_to_graph(self, data: Dict[str, Any]) -> Graph:
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

    def entity_to_dict(self, entity: Graph) -> Dict[str, Any]:
        """将业务实体转换为配置字典
        
        Args:
            entity: 图实体
            
        Returns:
            Dict[str, Any]: 图配置字典数据
        """
        return self._graph_to_dict(entity)
    
    def _graph_to_dict(self, graph: Graph) -> Dict[str, Any]:
        """将图实体转换为字典数据
        
        Args:
            graph: 图实体
            
        Returns:
            Dict[str, Any]: 图配置字典数据
        """
        result: Dict[str, Any] = {
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


    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证配置数据
        
        Args:
            config_data: 配置字典数据
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        # 验证必需字段
        if "name" not in config_data:
            errors.append("缺少必需字段: name")
        
        # 验证节点
        if "nodes" in config_data:
            for node_name, node_data in config_data["nodes"].items():
                if not node_data:
                    errors.append(f"节点 '{node_name}' 配置不能为空")
                    continue
                
                if "function_name" not in node_data:
                    errors.append(f"节点 '{node_name}' 缺少function_name字段")
        
        # 验证边
        if "edges" in config_data:
            node_names = set(config_data.get("nodes", {}).keys())
            for i, edge_data in enumerate(config_data["edges"]):
                if not edge_data:
                    errors.append(f"边 {i} 配置不能为空")
                    continue
                
                from_node = edge_data.get("from")
                to_node = edge_data.get("to")
                
                if from_node and from_node not in node_names:
                    errors.append(f"边 {i} 的源节点 '{from_node}' 不存在")
                
                if to_node and to_node not in node_names:
                    errors.append(f"边 {i} 的目标节点 '{to_node}' 不存在")
        
        # 验证入口点
        if "entry_point" in config_data:
            entry_point = config_data["entry_point"]
            node_names = set(config_data.get("nodes", {}).keys())
            if entry_point and entry_point not in node_names:
                errors.append(f"入口点节点 '{entry_point}' 不存在")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


# 全局映射器实例
_workflow_config_mapper = WorkflowConfigMapper()


def get_workflow_config_mapper() -> WorkflowConfigMapper:
    """获取工作流配置映射器实例
    
    Returns:
        WorkflowConfigMapper: 工作流配置映射器实例
    """
    return _workflow_config_mapper


def dict_to_graph(data: Dict[str, Any]) -> Graph:
    """便捷函数：将字典转换为图实体
    
    Args:
        data: 图配置字典数据
        
    Returns:
        Graph: 图实体
    """
    return _workflow_config_mapper.dict_to_entity(data)


def graph_to_dict(graph: Graph) -> Dict[str, Any]:
    """便捷函数：将图实体转换为字典
    
    Args:
        graph: 图实体
        
    Returns:
        Dict[str, Any]: 图配置字典数据
    """
    return _workflow_config_mapper.entity_to_dict(graph)
