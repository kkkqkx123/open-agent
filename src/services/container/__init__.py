"""依赖注入容器

提供服务的依赖注入和管理功能。
"""

from .container import DependencyContainer, get_global_container, reset_global_container

# 向后兼容别名
Container = DependencyContainer
from .storage_bindings import (
    register_all_storage_services,
    register_session_storage_only,
    register_thread_storage_only
)
from .thread_checkpoint_bindings import (
    register_thread_checkpoint_services,
    register_thread_checkpoint_services_with_custom_backend,
    register_thread_checkpoint_test_services,
    get_thread_checkpoint_service_config
)
from .history_bindings import (
    register_history_services,
    register_history_test_services,
    get_history_service_config,
    validate_history_config
)

__all__ = [
    # 核心容器
    "Container",
    "DependencyContainer",
    "get_global_container",
    "reset_global_container",
    
    # 存储服务绑定
    "register_all_storage_services",
    "register_session_storage_only",
    "register_thread_storage_only",
    
    # Thread检查点服务绑定
    "register_thread_checkpoint_services",
    "register_thread_checkpoint_services_with_custom_backend",
    "register_thread_checkpoint_test_services",
    "get_thread_checkpoint_service_config",
    
    # History服务绑定
    "register_history_services",
    "register_history_test_services",
    "get_history_service_config",
    "validate_history_config",
]