"""build_graph方法使用示例

演示如何使用GraphService.build_graph()方法从配置创建图。
"""

from src.core.workflow.graph import GraphService, Graph, SimpleNode, SimpleEdge


def example_simple_graph():
    """示例1: 创建一个简单的线性图"""
    print("=" * 60)
    print("示例1: 创建简单线性图")
    print("=" * 60)
    
    # 创建图服务
    service = GraphService()
    
    # 定义图配置
    config = {
        "graph_id": "simple_linear_graph",
        "nodes": [
            {
                "id": "start",
                "type": "simple_node",
                "name": "Start Node",
                "description": "Workflow entry point"
            },
            {
                "id": "process",
                "type": "simple_node",
                "name": "Process Node",
                "description": "Main processing"
            },
            {
                "id": "end",
                "type": "simple_node",
                "name": "End Node",
                "description": "Workflow exit point"
            }
        ],
        "edges": [
            {
                "id": "edge_1",
                "from": "start",
                "to": "process",
                "type": "simple"
            },
            {
                "id": "edge_2",
                "from": "process",
                "to": "end",
                "type": "simple"
            }
        ]
    }
    
    # 构建图
    graph = service.build_graph(config)
    
    # 验证图
    print(f"\n图ID: {graph.graph_id}")
    print(f"节点数: {len(graph.get_nodes())}")
    print(f"边数: {len(graph.get_edges())}")
    print(f"入口节点: {graph.get_entry_points()}")
    print(f"出口节点: {graph.get_exit_points()}")
    
    # 列出所有节点
    print("\n节点列表:")
    for node_id, node in graph.get_nodes().items():
        print(f"  - {node_id}: {node.node_type}")
    
    # 列出所有边
    print("\nEdges:")
    for edge_id, edge in graph.get_edges().items():
        print(f"  - {edge_id}: {edge.source_node} -> {edge.target_node}")


def example_branching_graph():
    """示例2: 创建一个有分支的图"""
    print("\n" + "=" * 60)
    print("示例2: 创建有分支的图")
    print("=" * 60)
    
    service = GraphService()
    
    # 定义有分支的图配置
    config = {
        "graph_id": "branching_graph",
        "nodes": [
            {
                "id": "start",
                "type": "simple_node",
                "name": "Start",
                "description": "Entry point"
            },
            {
                "id": "decision",
                "type": "simple_node",
                "name": "Decision",
                "description": "Branching decision"
            },
            {
                "id": "branch_a",
                "type": "simple_node",
                "name": "Branch A",
                "description": "First branch"
            },
            {
                "id": "branch_b",
                "type": "simple_node",
                "name": "Branch B",
                "description": "Second branch"
            },
            {
                "id": "merge",
                "type": "simple_node",
                "name": "Merge",
                "description": "Merge branches"
            },
            {
                "id": "end",
                "type": "simple_node",
                "name": "End",
                "description": "Exit point"
            }
        ],
        "edges": [
            {
                "id": "e1",
                "from": "start",
                "to": "decision",
                "type": "simple"
            },
            {
                "id": "e2",
                "from": "decision",
                "to": "branch_a",
                "type": "simple"
            },
            {
                "id": "e3",
                "from": "decision",
                "to": "branch_b",
                "type": "simple"
            },
            {
                "id": "e4",
                "from": "branch_a",
                "to": "merge",
                "type": "simple"
            },
            {
                "id": "e5",
                "from": "branch_b",
                "to": "merge",
                "type": "simple"
            },
            {
                "id": "e6",
                "from": "merge",
                "to": "end",
                "type": "simple"
            }
        ]
    }
    
    # 构建图
    graph = service.build_graph(config)
    
    print(f"\n图ID: {graph.graph_id}")
    print(f"节点数: {len(graph.get_nodes())}")
    print(f"边数: {len(graph.get_edges())}")
    print(f"入口节点: {graph.get_entry_points()}")
    print(f"出口节点: {graph.get_exit_points()}")
    
    # 展示图结构
    print("\n图结构:")
    for node_id in graph.get_entry_points():
        _print_graph_structure(graph, node_id, indent="")


def example_with_config():
    """示例3: 创建带配置的节点"""
    print("\n" + "=" * 60)
    print("示例3: 创建带配置的节点")
    print("=" * 60)
    
    service = GraphService()
    
    # 定义带配置的图
    config = {
        "graph_id": "configured_graph",
        "nodes": [
            {
                "id": "input",
                "type": "simple_node",
                "name": "Input",
                "description": "Input processing",
                "config": {
                    "timeout": 30,
                    "retries": 3
                }
            },
            {
                "id": "llm",
                "type": "simple_node",
                "name": "LLM",
                "description": "LLM processing",
                "config": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            {
                "id": "output",
                "type": "simple_node",
                "name": "Output",
                "description": "Output processing"
            }
        ],
        "edges": [
            {
                "id": "input_to_llm",
                "from": "input",
                "to": "llm",
                "type": "simple"
            },
            {
                "id": "llm_to_output",
                "from": "llm",
                "to": "output",
                "type": "simple"
            }
        ]
    }
    
    # 构建图
    graph = service.build_graph(config)
    
    print(f"\n图ID: {graph.graph_id}")
    
    # 展示节点配置
    print("\n节点配置:")
    for node_id, node in graph.get_nodes().items():
        if hasattr(node, 'config') and node.config:
            print(f"  {node_id}: {node.config}")
        else:
            print(f"  {node_id}: (无配置)")


def example_error_handling():
    """示例4: 错误处理示例"""
    print("\n" + "=" * 60)
    print("示例4: 错误处理")
    print("=" * 60)
    
    service = GraphService()
    
    # 示例1: 缺少节点ID
    print("\n测试1: 节点缺少ID")
    try:
        config = {
            "nodes": [
                {
                    "type": "simple_node",
                    "name": "No ID"
                }
            ]
        }
        service.build_graph(config)
    except ValueError as e:
        print(f"  ✓ 捕获错误: {e}")
    
    # 示例2: 边引用不存在的节点
    print("\nTest 2: 边引用不存在的节点")
    try:
        config = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "simple_node",
                    "name": "Node 1"
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "from": "node1",
                    "to": "nonexistent",
                    "type": "simple"
                }
            ]
        }
        service.build_graph(config)
    except ValueError as e:
        print(f"  ✓ 捕获错误: {e}")
    
    # 示例3: 边缺少必要字段
    print("\nTest 3: 边缺少必要字段")
    try:
        config = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "simple_node",
                    "name": "Node 1"
                },
                {
                    "id": "node2",
                    "type": "simple_node",
                    "name": "Node 2"
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "from": "node1"
                    # 缺少 'to' 字段
                }
            ]
        }
        service.build_graph(config)
    except ValueError as e:
        print(f"  ✓ 捕获错误: {e}")


def _print_graph_structure(graph, node_id, indent="", visited=None):
    """递归打印图结构（用于可视化有向图）"""
    if visited is None:
        visited = set()
    
    if node_id in visited:
        print(f"{indent}└── {node_id} (循环引用)")
        return
    
    visited.add(node_id)
    
    node = graph.get_node(node_id)
    print(f"{indent}├── {node_id}")
    
    # 找出所有出站边
    outgoing_edges = [
        edge for edge in graph.get_edges().values()
        if edge.source_node == node_id
    ]
    
    for i, edge in enumerate(outgoing_edges):
        is_last = i == len(outgoing_edges) - 1
        next_indent = indent + ("    " if is_last else "│   ")
        _print_graph_structure(graph, edge.target_node, next_indent, visited)


if __name__ == "__main__":
    example_simple_graph()
    example_branching_graph()
    example_with_config()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("=" * 60)
