"""领域层依赖注入配置

提供领域层服务的依赖注入配置。
"""

from .domain_module import DomainModule
from .domain_config import DomainConfig

__all__ = [
    "DomainModule",
    "DomainConfig"
]