"""统一注册表模块

提供节点、边、函数等的统一注册管理功能。

注册器类型：
├─ NodeRegistry: 节点注册器（来自基础设施层）
├─ EdgeRegistry: 边注册器（核心层实现）
└─ FunctionRegistry: 函数注册器（节点函数和路由函数）

使用方式：
1. 通过依赖注入获取注册器实例
2. 注册相应的类型或实例
3. 通过注册器查询和管理已注册的项目
"""

# 从基础设施层导入基础注册表
from src.infrastructure.graph.registry import (
    NodeRegistry as InfraNodeRegistry,
    EdgeRegistry as InfraEdgeRegistry
)
from .function_registry import FunctionRegistry, IFunction, node_function, route_function
from .edge_registry import EdgeRegistry as CoreEdgeRegistry, edge

# 为了向后兼容，重新导出基础设施层的注册表
NodeRegistry = InfraNodeRegistry
InfraEdgeRegistryInstance = InfraEdgeRegistry  # 保留基础设施层的实例

# 使用核心层的EdgeRegistry作为主要实现
EdgeRegistry = CoreEdgeRegistry

__all__ = [
    "NodeRegistry",
    "EdgeRegistry",
    "InfraEdgeRegistryInstance",  # 基础设施层边注册器实例
    "FunctionRegistry",
    "IFunction",
    "node_function",
    "route_function",
    "edge",
]