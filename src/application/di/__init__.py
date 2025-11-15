"""应用层依赖注入配置

提供应用层服务的依赖注入配置。
"""

from .application_module import ApplicationModule
from .application_config import ApplicationConfig

__all__ = [
    "ApplicationModule",
    "ApplicationConfig"
]