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
from src.interfaces.prompts.models import PromptConfig, PromptMeta
from src.interfaces.prompts.cache import IPromptCache
from src.interfaces.prompts.injector import (
    IPromptInjector,
    IPromptLoader,
)

# 从上级目录的 prompts.py 导入 IPromptRegistry
# 注意：这里使用相对导入避免循环依赖
import sys
import os
from pathlib import Path

# 手动加载上级 prompts.py 中的 IPromptRegistry
_prompts_file = Path(__file__).parent.parent / "prompts.py"
if _prompts_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_prompts_module", str(_prompts_file))
    if spec and spec.loader:
        _module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_module)
        IPromptRegistry = getattr(_module, "IPromptRegistry", None)
    else:
        IPromptRegistry = None
else:
    IPromptRegistry = None

__all__ = [
    "IPromptType",
    "IPromptTypeRegistry",
    "PromptType",
    "PromptTypeConfig",
    "create_prompt_type_config",
    "get_default_prompt_type_configs",
    "PromptConfig",
    "PromptMeta",
    "IPromptCache",
    "IPromptInjector",
    "IPromptLoader",
    "IPromptRegistry",
]
