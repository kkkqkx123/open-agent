"""统一注册表模块

提供节点、边、函数等的统一注册管理功能。
"""

# 从基础设施层导入基础注册表
from src.infrastructure.graph.registry import (
    NodeRegistry as InfraNodeRegistry,
    EdgeRegistry as InfraEdgeRegistry
)
from .function_registry import FunctionRegistry

# 为了向后兼容，重新导出基础设施层的注册表
NodeRegistry = InfraNodeRegistry
EdgeRegistry = InfraEdgeRegistry

__all__ = [
    "NodeRegistry",
    "EdgeRegistry",
    "FunctionRegistry"
]