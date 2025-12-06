"""优化模块

提供动态编译、资源管理、消息路由和全局检查节点管理功能。
"""

from .dynamic_compiler import (
    GraphChanges,
    EdgeConfig,
    OptimizedGraph,
    DynamicCompiler,
)

from .message_router import (
    RouteRule,
    MessageTypeRule,
    SenderRule,
    RecipientRule,
    MetadataRule,
    MessageRouter,
)

from .global_check_nodes import (
    InjectionPoint,
    GlobalCheckNode,
    InjectionRule,
    ConditionalInjection,
    InjectionContext,
    GlobalCheckNodeManager,
)

from .resource_manager import (
    ResourceLimits,
    GraphResource,
    ResourceUsage,
    ResourceUsageMonitor,
    ResourceManager,
)

__all__ = [
    # 动态编译器
    "GraphChanges",
    "EdgeConfig",
    "OptimizedGraph",
    "DynamicCompiler",
    
    # 消息路由器
    "RouteRule",
    "MessageTypeRule",
    "SenderRule",
    "RecipientRule",
    "MetadataRule",
    "MessageRouter",
    
    # 全局检查节点管理
    "InjectionPoint",
    "GlobalCheckNode",
    "InjectionRule",
    "ConditionalInjection",
    "InjectionContext",
    "GlobalCheckNodeManager",
    
    # 资源管理
    "ResourceLimits",
    "GraphResource",
    "ResourceUsage",
    "ResourceUsageMonitor",
    "ResourceManager",
]