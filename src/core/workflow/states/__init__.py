"""工作流状态模块

提供状态管理的核心功能，保持向后兼容性。
"""

# 核心状态类和消息类
from .workflow_state import (
    WorkflowState,
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    MessageRole,
    MessageManager
)

# 状态构建器
from .state_builder import (
    WorkflowStateBuilder,
    create_empty_state,
    create_state_from_dict,
    create_state_with_messages,
    create_state_with_conversation,
    builder,
    from_dict,
    with_messages,
    conversation
)

# 工厂类和函数
from .state_factory import WorkflowStateFactory
from .state_factory import (
    create_empty,
    from_config,
    with_messages as factory_with_messages,
    conversation as factory_conversation,
    from_dict as factory_from_dict
)

# 导出核心符号
__all__ = [
    # 核心类
    "WorkflowState",
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "MessageRole",
    "MessageManager",
    
    # 构建器
    "WorkflowStateBuilder",
    
    # 工厂类
    "WorkflowStateFactory",
    
    # 创建函数
    "create_empty_state",
    "create_state_from_dict",
    "create_state_with_messages",
    "create_state_with_conversation",
    "builder",
    "from_dict",
    "with_messages",
    "conversation",
    
    # 工厂函数
    "create_empty",
    "from_config",
    "factory_with_messages",
    "factory_conversation",
    "factory_from_dict"
]