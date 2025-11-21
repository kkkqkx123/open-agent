"""提示词管理模块数据模型

从接口层导入模型定义（避免循环依赖）。
"""

# 从接口层导入模型定义
from ...interfaces.prompts import PromptMeta, PromptConfig

__all__ = [
    "PromptMeta",
    "PromptConfig",
]
