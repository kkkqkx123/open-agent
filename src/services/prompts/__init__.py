"""提示词管理服务层

提供提示词系统的具体实现和服务。
"""

from .registry import PromptRegistry
from .loader import PromptLoader
from .injector import PromptInjector
from .config import PromptConfigManager, get_global_config_manager

# 重新导出提示词工厂的便捷函数
from .prompt_factory import (
    create_prompt_system,
    create_prompt_registry,
    create_prompt_loader,
    create_prompt_injector,
    PromptSystemFactory
)

__all__ = [
    # 核心服务
    "PromptRegistry",
    "PromptLoader",
    "PromptInjector",
    "PromptConfigManager",
    "get_global_config_manager",
    
    # 提示词工厂
    "PromptSystemFactory",
    
    # 提示词工厂便捷函数
    "create_prompt_system",
    "create_prompt_registry",
    "create_prompt_loader",
    "create_prompt_injector",
]
