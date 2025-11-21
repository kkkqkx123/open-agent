"""
提示词管理模块（已弃用）

本模块已迁移到新的扁平化架构。
此文件仅为向后兼容性保留。

新位置：
  - 接口: src.interfaces.prompts
  - 实现: src.services.prompts
  
迁移计划见: docs/PROMPTS_MIGRATION_PLAN.md
"""

import warnings
from typing import TYPE_CHECKING

# 发出弃用警告
warnings.warn(
    "src.domain.prompts is deprecated and will be removed in version 2.0. "
    "Use src.interfaces.prompts and src.services.prompts instead. "
    "See docs/PROMPTS_MIGRATION_PLAN.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# 为向后兼容性重定向
if TYPE_CHECKING:
    from ..interfaces.prompts import (
        IPromptRegistry,
        IPromptLoader,
        IPromptInjector,
        PromptMeta,
        PromptConfig,
    )
    from ..services.prompts import (
        PromptRegistry,
        PromptLoader,
        PromptInjector,
        create_agent_workflow,
        create_simple_workflow,
    )

# 运行时导入（触发警告）
def __getattr__(name: str):
    """动态导入以支持向后兼容性"""
    
    # 接口
    if name == "IPromptRegistry":
        from ...interfaces.prompts import IPromptRegistry
        return IPromptRegistry
    elif name == "IPromptLoader":
        from ...interfaces.prompts import IPromptLoader
        return IPromptLoader
    elif name == "IPromptInjector":
        from ...interfaces.prompts import IPromptInjector
        return IPromptInjector
    
    # 模型
    elif name == "PromptMeta":
        from ...interfaces.prompts import PromptMeta
        return PromptMeta
    elif name == "PromptConfig":
        from ...interfaces.prompts import PromptConfig
        return PromptConfig
    
    # 实现
    elif name == "PromptRegistry":
        from ...services.prompts import PromptRegistry
        return PromptRegistry
    elif name == "PromptLoader":
        from ...services.prompts import PromptLoader
        return PromptLoader
    elif name == "PromptInjector":
        from ...services.prompts import PromptInjector
        return PromptInjector
    
    # LangGraph集成
    elif name == "create_agent_workflow":
        from ...services.prompts import create_agent_workflow
        return create_agent_workflow
    elif name == "create_simple_workflow":
        from ...services.prompts import create_simple_workflow
        return create_simple_workflow
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "IPromptRegistry",
    "IPromptLoader",
    "IPromptInjector",
    "PromptMeta",
    "PromptConfig",
    "PromptRegistry",
    "PromptLoader",
    "PromptInjector",
    "create_agent_workflow",
    "create_simple_workflow",
]
