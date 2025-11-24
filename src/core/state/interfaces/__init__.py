"""统一状态管理接口模块

提供所有状态管理相关的接口定义。
"""

# 基础接口
from .base import (
    IState,
    IStateManager,
    IStateSerializer,
    IStateValidator,
    IStateLifecycleManager,
    IStateCache,
    IStateStorageAdapter
)

# 工作流状态接口
from .workflow import (
    IWorkflowState,
    IWorkflowStateBuilder
)

# 工具状态接口
from .tools import (
    IToolState,
    IToolStateManager,
    IToolStateBuilder,
    StateType
)

# 会话状态接口
from .sessions import (
    ISessionState,
    ISessionStateManager
)

# 线程状态接口
from .threads import (
    IThreadState,
    IThreadStateManager
)

# 检查点状态接口
from .checkpoints import (
    ICheckpointState,
    ICheckpointStateManager
)

__all__ = [
    # 基础接口
    "IState",
    "IStateManager",
    "IStateSerializer",
    "IStateValidator",
    "IStateLifecycleManager",
    "IStateCache",
    "IStateStorageAdapter",
    
    # 工作流状态接口
    "IWorkflowState",
    "IWorkflowStateBuilder",
    
    # 工具状态接口
    "IToolState",
    "IToolStateManager",
    "IToolStateBuilder",
    "StateType",
    
    # 会话状态接口
    "ISessionState",
    "ISessionStateManager",
    
    # 线程状态接口
    "IThreadState",
    "IThreadStateManager",
    
    # 检查点状态接口
    "ICheckpointState",
    "ICheckpointStateManager"
]