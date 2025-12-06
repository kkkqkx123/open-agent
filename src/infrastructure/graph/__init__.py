"""基础设施层图模块

提供LangGraph功能的自主实现，包括状态图引擎、执行引擎、检查点管理、
Hook系统、动态编译、消息传递和全局检查节点管理等功能。
"""

# 核心引擎
from .engine.state_graph import StateGraphEngine
from .engine.compiler import GraphCompiler
from .execution.engine import ExecutionEngine
from .execution.scheduler import TaskScheduler
from .execution.state_manager import StateManager
from .execution.stream_processor import StreamProcessor

# 通道系统
from .channels.base import BaseChannel
from .channels.last_value import LastValue, LastValueAfterFinish
from .channels.topic import Topic
from .channels.binop import BinaryOperatorAggregate

# 类型定义
from .types import (
    # 核心类型
    Send,
    Command,
    Interrupt,
    StateSnapshot,
    StateUpdate,
    PregelTask,
    PregelExecutableTask,
    
    # 配置和策略
    Durability,
    Checkpointer,
    StreamMode,
    StreamWriter,
    RetryPolicy,
    CachePolicy,
    
    # 错误类型
    GraphInterrupt,
    GraphRecursionError,
    GraphValueError,
    GraphTypeError,
    EmptyChannelError,
    InvalidUpdateError,
    NodeNotFoundError,
    EdgeNotFoundError,
    InvalidGraphError,
    CheckpointNotFoundError,
    CheckpointError,
    DeliveryFailedError,
    InvalidConfigurationError,
)

# Hook系统
from .hooks.hook_system import HookSystem, HookRegistration, HookContext, HookExecutionResult
from .hooks.hook_points import HookPoint
from .hooks.hook_chains import HookChain, ExecutionMode
from .hooks.conditional_hooks import ConditionalHook

# 优化功能
from .optimization.dynamic_compiler import DynamicCompiler, GraphChanges, EdgeConfig, OptimizedGraph
from .optimization.message_router import MessageRouter, RouteRule, MessageTypeRule, SenderRule, RecipientRule, MetadataRule
from .optimization.global_check_nodes import (
    GlobalCheckNodeManager,
    GlobalCheckNode,
    InjectionPoint,
    InjectionRule,
    ConditionalInjection,
    InjectionContext,
)
from .optimization.resource_manager import ResourceManager, ResourceLimits, GraphResource, ResourceUsage

# 消息传递
from .messaging import (
    Message,
    MessageProcessor,
    MessageReliability,
    MessagePassingManager,
    MessagePassingMode,
)

__all__ = [
    # 核心引擎
    "StateGraphEngine",
    "GraphCompiler",
    "ExecutionEngine",
    "TaskScheduler",
    "StateManager",
    "StreamProcessor",
    
    # 通道系统
    "BaseChannel",
    "LastValue",
    "LastValueAfterFinish",
    "Topic",
    "BinaryOperatorAggregate",
    
    # 类型定义
    "Send",
    "Command",
    "Interrupt",
    "StateSnapshot",
    "StateUpdate",
    "PregelTask",
    "PregelExecutableTask",
    "Durability",
    "Checkpointer",
    "StreamMode",
    "StreamWriter",
    "RetryPolicy",
    "CachePolicy",
    "GraphInterrupt",
    "GraphRecursionError",
    "GraphValueError",
    "GraphTypeError",
    "EmptyChannelError",
    "InvalidUpdateError",
    "NodeNotFoundError",
    "EdgeNotFoundError",
    "InvalidGraphError",
    "CheckpointNotFoundError",
    "CheckpointError",
    "DeliveryFailedError",
    "InvalidConfigurationError",
    
    # Hook系统
    "HookSystem",
    "HookRegistration",
    "HookContext",
    "HookExecutionResult",
    "HookPoint",
    "HookChain",
    "ExecutionMode",
    "ConditionalHook",
    
    # 优化功能
    "DynamicCompiler",
    "GraphChanges",
    "EdgeConfig",
    "OptimizedGraph",
    "MessageRouter",
    "RouteRule",
    "MessageTypeRule",
    "SenderRule",
    "RecipientRule",
    "MetadataRule",
    "GlobalCheckNodeManager",
    "GlobalCheckNode",
    "InjectionPoint",
    "InjectionRule",
    "ConditionalInjection",
    "InjectionContext",
    "ResourceManager",
    "ResourceLimits",
    "GraphResource",
    "ResourceUsage",
    
    # 消息传递
    "Message",
    "MessageProcessor",
    "MessageReliability",
    "MessagePassingManager",
    "MessagePassingMode",
]