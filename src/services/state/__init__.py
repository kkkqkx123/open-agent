"""状态管理服务模块

提供简化的状态管理服务实现，直接整合状态管理、历史记录、快照和持久化功能。
"""

# 核心管理器
from .manager import StateManager, StateWrapper

# 特化管理器
from .session_manager import SessionStateManager
from .workflow_manager import WorkflowStateManager

# 配置和初始化
from .config import get_state_service_config, validate_state_configuration, configure_state_services
from .init import (
    initialize_state_services,
    get_state_manager,
    get_session_manager,
    shutdown_state_services,
    get_service_status,
    ensure_state_services_initialized
)

# 持久化服务（保留用于备份功能）
from .persistence import StatePersistenceService, StateBackupService

__all__ = [
    # 核心状态管理
    "StateManager",
    "StateWrapper",
    
    # 特化管理器
    "SessionStateManager",
    "WorkflowStateManager",
    
    # 配置和初始化
    "get_state_service_config",
    "validate_state_configuration",
    "configure_state_services",
    "initialize_state_services",
    "get_state_manager",
    "get_session_manager",
    "shutdown_state_services",
    "get_service_status",
    "ensure_state_services_initialized",
    
    # 持久化服务
    "StatePersistenceService",
    "StateBackupService"
]