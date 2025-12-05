"""依赖注入容器

提供服务的依赖注入和管理功能。
"""

from .core.container import DependencyContainer, get_global_container, reset_global_container

from .bindings.storage_bindings import StorageServiceBindings
from .bindings.thread_checkpoint_bindings import ThreadCheckpointServiceBindings
from .bindings.history_bindings import HistoryServiceBindings
from .bindings.session_bindings import SessionServiceBindings
from .bindings.thread_bindings import ThreadServiceBindings
from .bindings.llm_bindings import LLMServiceBindings
from .bindings.logger_bindings import (
    register_logger_services,
    register_test_logger_services,
    register_production_logger_services,
    register_development_logger_services,
    setup_global_logger_services,
    shutdown_logger_services,
    get_logger_service_status,
    isolated_test_logger,
    reset_test_logger_services,
    get_logger_lifecycle_manager,
    validate_logger_config,
    get_logger_service_config
)

__all__ = [
    # 核心容器
    "DependencyContainer",
    "DependencyContainer",
    "get_global_container",
    "reset_global_container",
    
    # 日志服务绑定（优化后的全局日志依赖注入容器）
    "register_logger_services",
    "register_test_logger_services",
    "register_production_logger_services",
    "register_development_logger_services",
    "setup_global_logger_services",
    "shutdown_logger_services",
    "get_logger_service_status",
    "isolated_test_logger",
    "reset_test_logger_services",
    "get_logger_lifecycle_manager",
    "validate_logger_config",
    "get_logger_service_config",
    
    # 存储服务绑定
    "StorageServiceBindings",
    
    # Thread检查点服务绑定
    "ThreadCheckpointServiceBindings",
    
    # History服务绑定
    "HistoryServiceBindings",
    "SessionServiceBindings",
    "ThreadServiceBindings",
    "LLMServiceBindings",
]