"""
提示词系统接口层

提供提示词相关的接口定义
"""

from src.interfaces.prompts.types import (
    IPromptType,
    IPromptTypeRegistry,
    PromptType,
    PromptTypeConfig,
    create_prompt_type_config,
    get_default_prompt_type_configs,
)

__all__ = [
    "IPromptType",
    "IPromptTypeRegistry",
    "PromptType",
    "PromptTypeConfig",
    "create_prompt_type_config",
    "get_default_prompt_type_configs",
]
