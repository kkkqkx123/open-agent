"""
通用基础设施接口重新导出模块

此模块提供向后兼容性，建议直接从专门的接口模块导入。
将在未来版本中废弃。
"""

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# 废弃警告
def _deprecation_warning(name: str, new_location: str):
    warnings.warn(
        f"Import '{name}' from src.interfaces.common_infra is deprecated. "
        f"Please import from '{new_location}' instead.",
        DeprecationWarning,
        stacklevel=3
    )

# 重新导出 ServiceLifetime
from src.interfaces.container.core import ServiceLifetime

# 重新导出 IStorage
from src.interfaces.storage.base import IStorage

# 重新导出 IDependencyContainer
from src.interfaces.container.core import IDependencyContainer

# 重新导出配置接口
from src.interfaces.config.interfaces import IConfigLoader, IConfigInheritanceHandler

# 更新 __all__ 列表
__all__ = [
    "ServiceLifetime",
    "IStorage",
    "IDependencyContainer",
    "IConfigLoader",
    "IConfigInheritanceHandler"
]

