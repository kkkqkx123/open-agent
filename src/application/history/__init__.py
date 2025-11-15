"""历史管理应用层模块

提供历史记录管理、Token使用追踪、成本计算等功能。
"""

from .manager import HistoryManager
from ...infrastructure.history.token_tracker import TokenUsageTracker
from ...infrastructure.history.session_context import (
    SessionContext,
    get_current_session,
    set_current_session,
    clear_current_session,
    session_context,
    generate_session_id,
    SessionContextManager,
    get_session_context_manager
)
from .di_config import (
    register_history_services,
    register_history_services_with_dependencies,
    register_test_history_services
)

__all__ = [
    "HistoryManager",
    "TokenUsageTracker",
    "SessionContext",
    "get_current_session",
    "set_current_session",
    "clear_current_session",
    "session_context",
    "generate_session_id",
    "SessionContextManager",
    "get_session_context_manager",
    "register_history_services",
    "register_history_services_with_dependencies",
    "register_test_history_services"
]