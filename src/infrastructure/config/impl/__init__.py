"""配置实现层

提供各模块配置的具体实现，负责配置的加载、处理和转换。
"""

from .base_impl import BaseConfigImpl, IConfigImpl

__all__ = [
    "BaseConfigImpl",
    "IConfigImpl",
]