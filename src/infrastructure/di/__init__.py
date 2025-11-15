"""基础设施层依赖注入配置

提供基础设施相关服务的依赖注入配置。
"""

from .infrastructure_module import InfrastructureModule
from .infrastructure_config import InfrastructureConfig

__all__ = [
    "InfrastructureModule",
    "InfrastructureConfig"
]