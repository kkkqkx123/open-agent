"""依赖注入接口模块

提供所有服务的依赖注入接口，避免循环依赖。
"""

from .core import (
    set_logger_provider,
    set_token_calculator,
    get_logger,
    calculate_messages_tokens,
    clear_providers,
)
from .fallback_logger import FallbackLogger
from .config import *
from .history import *
from .logger import *

__all__ = [
    # Core依赖注入
    "set_logger_provider",
    "set_token_calculator",
    "get_logger",
    "calculate_messages_tokens",
    "clear_providers",
    "FallbackLogger",
    
    # Config服务
    "get_config_loader",
    "get_config_manager",
    "get_config_validator",
    "get_config_processor_chain",
    "get_inheritance_processor",
    "get_environment_variable_processor",
    "get_reference_processor",
    "get_adapter_factory",
    "set_config_loader_instance",
    "set_config_manager_instance",
    "set_config_validator_instance",
    "set_config_processor_chain_instance",
    "set_inheritance_processor_instance",
    "set_environment_variable_processor_instance",
    "set_reference_processor_instance",
    "set_adapter_factory_instance",
    "clear_config_loader_instance",
    "clear_config_manager_instance",
    "clear_config_validator_instance",
    "clear_config_processor_chain_instance",
    "clear_inheritance_processor_instance",
    "clear_environment_variable_processor_instance",
    "clear_reference_processor_instance",
    "clear_adapter_factory_instance",
    "get_config_loader_status",
    "get_config_manager_status",
    "get_config_validator_status",
    "get_config_processor_chain_status",
    "get_inheritance_processor_status",
    "get_environment_variable_processor_status",
    "get_reference_processor_status",
    "get_adapter_factory_status",
    
    # History服务
    "get_history_manager",
    "get_cost_calculator",
    "get_token_tracker",
    "get_history_repository",
    "set_history_manager_instance",
    "set_cost_calculator_instance",
    "set_token_tracker_instance",
    "set_history_repository_instance",
    "clear_history_manager_instance",
    "clear_cost_calculator_instance",
    "clear_token_tracker_instance",
    "clear_history_repository_instance",
    "get_history_manager_status",
    "get_cost_calculator_status",
    "get_token_tracker_status",
    "get_history_repository_status",
    
    # Logger服务
    "get_logger",
    "set_logger_instance",
    "clear_logger_instance",
    "get_logger_status",
]