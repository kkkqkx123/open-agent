"""图领域实体

定义工作流图的领域实体，包含业务逻辑和行为，
不包含配置数据处理等基础设施功能。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from datetime import datetime

from src.infrastructure.validation.result import ValidationResult


class EdgeType(Enum):
    """边类型枚举"""
    SIMPLE = "simple"
    CONDITIONAL = "conditional"


@dataclass
class StateField:
    """状态字段领域实体"""
    name: str
    field_type: str
    default_value: Any = None
    reducer_function: Optional[str] = None
    description: Optional[str] = None

    # 业务方法
    def has_default_value(self) -> bool:
        """检查是否有默认值"""
        return self.default_value is not None

    def has_reducer(self) -> bool:
        """检查是否有reducer函数"""
        return self.reducer_function is not None

    def validate_value(self, value: Any) -> bool:
        """验证值是否符合字段类型"""
        # 简单的类型验证，实际实现可能更复杂
        if self.field_type == "str":
            return isinstance(value, str)
        elif self.field_type == "int":
            return isinstance(value, int)
        elif self.field_type == "float":
            return isinstance(value, (int, float))
        elif self.field_type == "bool":
            return isinstance(value, bool)
        elif self.field_type == "dict":
            return isinstance(value, dict)
        elif self.field_type == "list":
            return isinstance(value, list)
        return True


@dataclass
class GraphState:
    """图状态领域实体"""
    name: str
    fields: Dict[str, StateField] = field(default_factory=dict)

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

    def get_field(self, field_name: str) -> Optional[StateField]:
        """获取指定字段"""
        return self.fields.get(field_name)

    def add_field(self, field: StateField) -> None:
        """添加字段"""
        self.fields[field.name] = field

    def remove_field(self, field_name: str) -> bool:
        """移除字段"""
        if field_name in self.fields:
            del self.fields[field_name]
            return True
        return False

    def validate_state_data(self, state_data: Dict[str, Any]) -> ValidationResult:
        """验证状态数据"""
        errors = []
        
        for field_name, field in self.fields.items():
            if field_name in state_data:
                if not field.validate_value(state_data[field_name]):
                    errors.append(f"字段 {field_name} 的值类型不匹配")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])


@dataclass
class Node:
    """节点领域实体"""
    node_id: str
    name: str
    function_name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    node_type: str = "default"
    
    # 运行时状态
    status: str = "inactive"
    execution_count: int = 0
    last_execution_time: Optional[datetime] = None
    execution_history: List[Dict[str, Any]] = field(default_factory=list)

    # 业务方法
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        # 记录执行
        self.execution_count += 1
        self.last_execution_time = datetime.now()
        
        execution_record = {
            "execution_id": f"{self.node_id}_{self.execution_count}",
            "timestamp": self.last_execution_time,
            "input_data": input_data,
            "context": context
        }
        self.execution_history.append(execution_record)
        
        # 这里应该调用实际的函数执行逻辑
        # 暂时返回基本结果
        return {
            "node_id": self.node_id,
            "status": "completed",
            "result": f"Node {self.name} executed successfully"
        }

    def can_execute(self) -> bool:
        """检查节点是否可以执行"""
        return self.status != "disabled"

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history[-limit:]

    def reset_execution_history(self) -> None:
        """重置执行历史"""
        self.execution_history.clear()
        self.execution_count = 0
        self.last_execution_time = None

    def is_llm_node(self) -> bool:
        """检查是否为LLM节点"""
        return "llm" in self.name.lower() or "agent" in self.name.lower()

    def is_tool_node(self) -> bool:
        """检查是否为工具节点"""
        return "tool" in self.name.lower()

    def is_condition_node(self) -> bool:
        """检查是否为条件节点"""
        return "condition" in self.name.lower() or "decide" in self.name.lower()

    def validate_parameters(self) -> ValidationResult:
        """验证节点参数"""
        errors = []
        
        if not self.function_name:
            errors.append("节点必须指定函数名称")
        
        if not self.node_id:
            errors.append("节点必须指定ID")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])


@dataclass
class Edge:
    """边领域实体"""
    edge_id: str
    from_node_id: str
    to_node_id: str
    edge_type: EdgeType
    condition: Optional[str] = None
    description: Optional[str] = None
    path_map: Optional[Dict[str, Any]] = None
    route_function: Optional[str] = None
    route_parameters: Dict[str, Any] = field(default_factory=dict)

    # 业务方法
    def is_simple_edge(self) -> bool:
        """检查是否为简单边"""
        return self.edge_type == EdgeType.SIMPLE

    def is_conditional_edge(self) -> bool:
        """检查是否为条件边"""
        return self.edge_type == EdgeType.CONDITIONAL

    def is_flexible_conditional(self) -> bool:
        """检查是否为灵活条件边"""
        return (
            self.edge_type == EdgeType.CONDITIONAL and
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
            return [self.to_node_id] if self.to_node_id else []
        elif self.has_path_map() and isinstance(self.path_map, dict):
            return list(self.path_map.values())
        elif self.has_path_map() and isinstance(self.path_map, list):
            return self.path_map
        else:
            return []

    def can_traverse(self, context: Dict[str, Any]) -> bool:
        """检查是否可以遍历这条边"""
        if self.is_simple_edge():
            return True
        
        if self.is_conditional_edge():
            # 这里应该评估条件表达式
            # 暂时返回True
            return True
        
        return False

    def evaluate_condition(self, context: Dict[str, Any]) -> Optional[str]:
        """评估条件，返回目标节点ID"""
        if self.is_simple_edge():
            return self.to_node_id
        
        if self.has_path_map():
            # 根据条件评估结果选择路径
            # 这里应该实现实际的逻辑
            return self.to_node_id
        
        return None

    def validate(self) -> ValidationResult:
        """验证边配置"""
        errors = []
        
        if not self.from_node_id:
            errors.append("起始节点ID不能为空")
        
        if not self.to_node_id and self.is_simple_edge():
            errors.append("简单边必须指定目标节点ID")
        
        if self.is_conditional_edge():
            if self.is_flexible_conditional():
                if not self.route_function:
                    errors.append("灵活条件边必须指定路由函数")
            else:
                if not self.condition:
                    errors.append("条件边必须指定条件表达式")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])


@dataclass
class Graph:
    """图领域实体"""
    graph_id: str
    name: str
    description: str = ""
    version: str = "1.0"
    state: GraphState = field(default_factory=lambda: GraphState(name="GraphState"))
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    entry_point: Optional[str] = None
    
    # 运行时状态
    status: str = "initialized"
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    last_execution_time: Optional[datetime] = None

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

    def has_node(self, node_id: str) -> bool:
        """检查是否包含指定节点"""
        return node_id in self.nodes

    def get_node(self, node_id: str) -> Optional[Node]:
        """获取指定节点"""
        return self.nodes.get(node_id)

    def add_node(self, node: Node) -> None:
        """添加节点"""
        self.nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # 同时移除相关的边
            self.edges = [
                edge for edge in self.edges
                if edge.from_node_id != node_id and edge.to_node_id != node_id
            ]
            return True
        return False

    def get_edges_from_node(self, node_id: str) -> List[Edge]:
        """获取从指定节点出发的边"""
        return [edge for edge in self.edges if edge.from_node_id == node_id]

    def get_edges_to_node(self, node_id: str) -> List[Edge]:
        """获取指向指定节点的边"""
        return [edge for edge in self.edges if edge.to_node_id == node_id]

    def get_connected_nodes(self, node_id: str) -> Set[str]:
        """获取与指定节点相连的节点"""
        connected = set()
        for edge in self.edges:
            if edge.from_node_id == node_id and edge.to_node_id:
                connected.add(edge.to_node_id)
            elif edge.to_node_id == node_id:
                connected.add(edge.from_node_id)
        return connected

    def has_entry_point(self) -> bool:
        """检查是否有入口点"""
        return self.entry_point is not None

    def is_entry_point(self, node_id: str) -> bool:
        """检查指定节点是否为入口点"""
        return self.entry_point == node_id

    def get_next_nodes(self, current_node_id: str, context: Dict[str, Any]) -> List[str]:
        """获取下一个可执行的节点"""
        next_nodes = []
        
        for edge in self.get_edges_from_node(current_node_id):
            if edge.can_traverse(context):
                target_node = edge.evaluate_condition(context)
                if target_node:
                    next_nodes.append(target_node)
        
        return next_nodes

    def validate_structure(self) -> ValidationResult:
        """验证图结构"""
        errors = []
        
        # 验证基本字段
        if not self.name:
            errors.append("图名称不能为空")
        
        if not self.graph_id:
            errors.append("图ID不能为空")
        
        # 验证节点
        node_ids = set(self.nodes.keys())
        for node_id, node in self.nodes.items():
            node_validation = node.validate_parameters()
            if not node_validation.is_valid:
                errors.extend([f"节点 {node_id}: {error}" for error in node_validation.errors])
        
        # 验证边
        for edge in self.edges:
            edge_validation = edge.validate()
            if not edge_validation.is_valid:
                errors.extend([f"边 {edge.edge_id}: {error}" for error in edge_validation.errors])
            
            # 验证节点存在性
            if edge.from_node_id not in node_ids:
                errors.append(f"边起始节点不存在: {edge.from_node_id}")
            
            if edge.to_node_id not in node_ids and edge.is_simple_edge():
                errors.append(f"边目标节点不存在: {edge.to_node_id}")
        
        # 验证入口点
        if self.entry_point and self.entry_point not in node_ids:
            errors.append(f"入口点节点不存在: {self.entry_point}")
        
        # 验证连通性
        if self.entry_point and node_ids:
            reachable_nodes = self._get_reachable_nodes(self.entry_point)
            unreachable_nodes = node_ids - reachable_nodes
            if unreachable_nodes:
                errors.append(f"以下节点无法从入口点到达: {', '.join(unreachable_nodes)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])

    def _get_reachable_nodes(self, start_node_id: str) -> Set[str]:
        """获取从指定节点可达的所有节点"""
        reachable = set()
        to_visit = [start_node_id]
        
        while to_visit:
            current = to_visit.pop()
            if current not in reachable:
                reachable.add(current)
                # 获取所有相连的节点
                for edge in self.get_edges_from_node(current):
                    if edge.to_node_id:
                        to_visit.append(edge.to_node_id)
        
        return reachable

    def execute(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行图"""
        if not self.entry_point:
            raise ValueError("图没有设置入口点")
        
        self.status = "running"
        self.execution_count += 1
        self.last_execution_time = datetime.now()
        
        current_node_id = self.entry_point
        execution_context = initial_context.copy()
        execution_path = [current_node_id]
        
        while current_node_id:
            current_node = self.get_node(current_node_id)
            if not current_node:
                break
            
            # 执行当前节点
            node_result = current_node.execute(execution_context, {"execution_path": execution_path})
            execution_context.update(node_result)
            
            # 获取下一个节点
            next_nodes = self.get_next_nodes(current_node_id, execution_context)
            
            if not next_nodes:
                break
            
            # 简单选择第一个下一个节点（实际可能需要更复杂的路由逻辑）
            current_node_id = next_nodes[0]
            execution_path.append(current_node_id)
        
        self.status = "completed"
        
        return {
            "status": self.status,
            "execution_path": execution_path,
            "final_context": execution_context,
            "execution_count": self.execution_count
        }

    def reset(self) -> None:
        """重置图状态"""
        self.status = "initialized"
        for node in self.nodes.values():
            node.reset_execution_history()
        self.execution_count = 0
        self.last_execution_time = None

