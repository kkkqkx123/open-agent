"""依赖注入容器

提供服务的依赖注入和管理功能。
"""

from .core.container import DependencyContainer, get_global_container, reset_global_container

from .bindings.storage_bindings import StorageServiceBindings
from .bindings.history_bindings import HistoryServiceBindings
from .bindings.session_bindings import SessionServiceBindings
from .bindings.thread_bindings import ThreadServiceBindings
from .bindings.llm_bindings import LLMServiceBindings
from .bindings.logger_bindings import LoggerServiceBindings
from .bindings.config_bindings import ConfigServiceBindings

__all__ = [
    # 核心容器
    "DependencyContainer",
    "get_global_container",
    "reset_global_container",
    
    # 日志服务绑定
    "LoggerServiceBindings",
    "ConfigServiceBindings",
    
    # 存储服务绑定
    "StorageServiceBindings",
    
    # History服务绑定
    "HistoryServiceBindings",
    "SessionServiceBindings",
    "ThreadServiceBindings",
    "LLMServiceBindings",
]