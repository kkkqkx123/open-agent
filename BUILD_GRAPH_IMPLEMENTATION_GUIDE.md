# build_graph方法实现指南

## 概述

`build_graph` 方法应将配置字典转换为 `IGraph` 对象，支持从配置创建图结构。

## 现状分析

### 关键接口

**IGraph 接口** (`src/interfaces/workflow/graph.py`):
```python
class IGraph(ABC):
    @property
    def graph_id(self) -> str: ...
    
    def add_node(self, node: INode) -> None: ...
    def add_edge(self, edge: IEdge) -> None: ...
    
    def get_node(self, node_id: str) -> Optional[INode]: ...
    def get_edge(self, edge_id: str) -> Optional[IEdge]: ...
    
    def get_nodes(self) -> Dict[str, INode]: ...
    def get_edges(self) -> Dict[str, IEdge]: ...
    
    def validate(self) -> List[str]: ...
    def get_entry_points(self) -> List[str]: ...
    def get_exit_points(self) -> List[str]: ...
```

**INode 接口** (`src/interfaces/workflow/graph.py`):
```python
class INode(ABC):
    @property
    def node_id(self) -> str: ...
    @property
    def node_type(self) -> str: ...
    
    def execute(self, state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult: ...
    async def execute_async(self, state: IWorkflowState, config: Dict[str, Any]) -> NodeExecutionResult: ...
    
    def get_config_schema(self) -> Dict[str, Any]: ...
    def validate(self) -> List[str]: ...
```

**IEdge 接口** (`src/interfaces/workflow/graph.py`):
```python
class IEdge(ABC):
    @property
    def edge_id(self) -> str: ...
    @property
    def source_node(self) -> str: ...
    @property
    def target_node(self) -> str: ...
    @property
    def edge_type(self) -> str: ...
    
    def can_traverse(self, state: IState) -> bool: ...
    def can_traverse_with_config(self, state: IState, config: Dict[str, Any]) -> bool: ...
    def get_next_nodes(self, state: IState, config: Dict[str, Any]) -> List[str]: ...
    
    def validate(self) -> List[str]: ...
```

### 现有实现

**SimpleNode** 和 **SimpleEdge** 提供了最小化的实现：
- 可用于快速创建节点和边
- 支持基本的配置存储
- 验证方法已实现

## 实现方案

### 方案1: 创建简单的Graph实现类（推荐）

首先需要创建 `Graph` 类实现 `IGraph` 接口：

```python
# src/core/workflow/graph/graph.py

from typing import Dict, List, Optional
from uuid import uuid4

from src.interfaces.workflow.graph import IGraph, INode, IEdge


class Graph(IGraph):
    """图实现类"""
    
    def __init__(self, graph_id: Optional[str] = None):
        """初始化图
        
        Args:
            graph_id: 图ID，如果为None则自动生成
        """
        self._graph_id = graph_id or str(uuid4())
        self._nodes: Dict[str, INode] = {}
        self._edges: Dict[str, IEdge] = {}
    
    @property
    def graph_id(self) -> str:
        """图ID"""
        return self._graph_id
    
    def add_node(self, node: INode) -> None:
        """添加节点"""
        if node.node_id in self._nodes:
            raise ValueError(f"节点 {node.node_id} 已存在")
        self._nodes[node.node_id] = node
    
    def add_edge(self, edge: IEdge) -> None:
        """添加边"""
        if edge.edge_id in self._edges:
            raise ValueError(f"边 {edge.edge_id} 已存在")
        
        # 验证源节点和目标节点存在
        if edge.source_node not in self._nodes:
            raise ValueError(f"源节点 {edge.source_node} 不存在")
        if edge.target_node not in self._nodes:
            raise ValueError(f"目标节点 {edge.target_node} 不存在")
        
        self._edges[edge.edge_id] = edge
    
    def get_node(self, node_id: str) -> Optional[INode]:
        """获取节点"""
        return self._nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[IEdge]:
        """获取边"""
        return self._edges.get(edge_id)
    
    def get_nodes(self) -> Dict[str, INode]:
        """获取所有节点"""
        return self._nodes.copy()
    
    def get_edges(self) -> Dict[str, IEdge]:
        """获取所有边"""
        return self._edges.copy()
    
    def validate(self) -> List[str]:
        """验证图结构"""
        errors = []
        
        # 验证至少有一个节点
        if not self._nodes:
            errors.append("图必须至少有一个节点")
        
        # 验证所有节点
        for node in self._nodes.values():
            errors.extend(node.validate())
        
        # 验证所有边
        for edge in self._edges.values():
            errors.extend(edge.validate())
            
            # 验证边的源和目标节点存在
            if edge.source_node not in self._nodes:
                errors.append(f"边 {edge.edge_id} 的源节点不存在")
            if edge.target_node not in self._nodes:
                errors.append(f"边 {edge.edge_id} 的目标节点不存在")
        
        return errors
    
    def get_entry_points(self) -> List[str]:
        """获取入口节点列表"""
        # 入口节点是没有入站边的节点
        nodes_with_incoming = set()
        for edge in self._edges.values():
            nodes_with_incoming.add(edge.target_node)
        
        entry_points = [
            node_id for node_id in self._nodes.keys()
            if node_id not in nodes_with_incoming
        ]
        
        return entry_points or list(self._nodes.keys())[:1]
    
    def get_exit_points(self) -> List[str]:
        """获取出口节点列表"""
        # 出口节点是没有出站边的节点
        nodes_with_outgoing = set()
        for edge in self._edges.values():
            nodes_with_outgoing.add(edge.source_node)
        
        exit_points = [
            node_id for node_id in self._nodes.keys()
            if node_id not in nodes_with_outgoing
        ]
        
        return exit_points or list(self._nodes.keys())[-1:]
```

### 方案2: 实现build_graph方法

```python
# 在 src/core/workflow/graph/service.py 中

from .graph import Graph  # 导入上面创建的Graph类


class GraphService(IGraphService):
    """图服务实现"""
    
    def build_graph(self, config: Dict[str, Any]) -> IGraph:
        """从配置构建图
        
        Args:
            config: 图配置，格式为:
                {
                    "graph_id": "graph_1",  # 可选
                    "nodes": [
                        {
                            "id": "node_1",
                            "type": "registered_node_type",  # 必须是已注册的节点类型
                            "name": "Start Node",
                            "description": "Entry point",
                            "config": {}
                        },
                        ...
                    ],
                    "edges": [
                        {
                            "id": "edge_1",
                            "from": "node_1",
                            "to": "node_2",
                            "type": "registered_edge_type",  # 必须是已注册的边类型
                            "config": {}
                        },
                        ...
                    ]
                }
            
        Returns:
            IGraph: 构建的图
            
        Raises:
            ValueError: 配置无效、未注册的节点/边类型或图构建失败
        """
        # 创建图
        graph_id = config.get("graph_id")
        graph = Graph(graph_id)
        
        # 添加节点
        nodes_config = config.get("nodes", [])
        created_nodes: Dict[str, INode] = {}
        
        for node_config in nodes_config:
            node_id = node_config.get("id")
            node_type = node_config.get("type")
            
            if not node_id:
                raise ValueError("节点必须有ID")
            
            if not node_type:
                raise ValueError(f"节点 {node_id} 必须指定type")
            
            try:
                # 从注册表获取节点类（必须已注册）
                node_class = self._global_registry.node_registry.get_node_class(node_type)
                if not node_class:
                    raise ValueError(f"未注册的节点类型: {node_type}")
                
                node = node_class()
                graph.add_node(node)
                created_nodes[node_id] = node
                
            except ValueError as ve:
                # 直接重新抛出ValueError（更清晰的错误消息）
                raise ve
            except Exception as e:
                raise ValueError(f"创建节点 {node_id} (type={node_type}) 失败: {str(e)}")
        
        # 添加边
        edges_config = config.get("edges", [])
        
        for edge_config in edges_config:
            edge_id = edge_config.get("id")
            source_node = edge_config.get("from")
            target_node = edge_config.get("to")
            edge_type = edge_config.get("type")
            
            if not all([edge_id, source_node, target_node]):
                raise ValueError("边必须有id、from和to")
            
            if not edge_type:
                raise ValueError(f"边 {edge_id} 必须指定type")
            
            if source_node not in created_nodes:
                raise ValueError(f"源节点 {source_node} 不存在")
            if target_node not in created_nodes:
                raise ValueError(f"目标节点 {target_node} 不存在")
            
            try:
                # 从注册表获取边类（必须已注册）
                edge_class = self._global_registry.edge_registry.get_edge_class(edge_type)
                if not edge_class:
                    raise ValueError(f"未注册的边类型: {edge_type}")
                
                # 尝试用标准方式创建边
                edge = edge_class(source_node, target_node)
                graph.add_edge(edge)
                
            except ValueError as ve:
                # 直接重新抛出ValueError（更清晰的错误消息）
                raise ve
            except Exception as e:
                raise ValueError(f"创建边 {edge_id} (type={edge_type}) 失败: {str(e)}")
        
        # 验证图
        validation_errors = graph.validate()
        if validation_errors:
            raise ValueError(f"图验证失败: {', '.join(validation_errors)}")
        
        return graph
```

## 配置格式示例

```json
{
    "graph_id": "workflow_graph_1",
    "nodes": [
        {
            "id": "start",
            "type": "start_node",
            "name": "Start",
            "description": "Workflow entry point",
            "config": {}
        },
        {
            "id": "task_1",
            "type": "llm_node",
            "name": "LLM Task",
            "description": "Execute LLM query",
            "config": {
                "model": "gpt-4",
                "temperature": 0.7
            }
        },
        {
            "id": "end",
            "type": "end_node",
            "name": "End",
            "description": "Workflow exit point",
            "config": {}
        }
    ],
    "edges": [
        {
            "id": "edge_1",
            "from": "start",
            "to": "task_1",
            "type": "simple",
            "config": {}
        },
        {
            "id": "edge_2",
            "from": "task_1",
            "to": "end",
            "type": "simple",
            "config": {}
        }
    ]
}
```

## YAML配置示例

```yaml
graph_id: workflow_graph_1

nodes:
  - id: start
    type: start_node
    name: Start
    description: Workflow entry point
    config: {}
  
  - id: task_1
    type: llm_node
    name: LLM Task
    description: Execute LLM query
    config:
      model: gpt-4
      temperature: 0.7
  
  - id: end
    type: end_node
    name: End
    description: Workflow exit point
    config: {}

edges:
  - id: edge_1
    from: start
    to: task_1
    type: simple
    config: {}
  
  - id: edge_2
    from: task_1
    to: end
    type: simple
    config: {}
```

## 实现步骤

1. **创建Graph类**
   - 在 `src/core/workflow/graph/graph.py` 中实现 `Graph` 类
   - 实现所有 `IGraph` 接口方法
   - 添加节点和边的验证逻辑

2. **更新build_graph方法**
   - 替换 `NotImplementedError` 的占位符
   - 实现配置解析逻辑
   - 添加节点和边的创建逻辑
   - 实现错误处理和验证

3. **更新__init__.py**
   - 导出 `Graph` 类到 `src/core/workflow/graph/__init__.py`

4. **测试**
   - 创建单元测试验证图的创建
   - 测试各种配置格式
   - 测试错误情况

## 高级特性（可选）

### 1. 支持节点工厂

```python
class INodeFactory(ABC):
    """节点工厂接口"""
    
    @abstractmethod
    def create_node(self, config: Dict[str, Any]) -> INode:
        """从配置创建节点"""
        pass
```

### 2. 支持边的条件和路由

```python
# 在建图时处理条件边
if edge_type == "conditional":
    condition_func = self._global_registry.routing_registry.get(edge_config.get("condition"))
    edge = ConditionalEdge(source, target, condition_func)
```

### 3. 支持子图

```python
# 在配置中支持嵌套的子图
if node_type == "subgraph":
    subgraph_config = node_config.get("subgraph_config")
    node = SubgraphNode(self.build_graph(subgraph_config))
```

## 最佳实践

1. **验证**: 总是在构建完图后调用 `validate()`
2. **错误处理**: 提供清晰的错误消息
3. **配置默认值**: 为可选配置提供合理的默认值
4. **文档**: 记录配置格式和支持的节点/边类型
5. **扩展性**: 使用注册表模式支持自定义节点和边类型
