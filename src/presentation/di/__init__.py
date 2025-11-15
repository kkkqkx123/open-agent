"""表示层依赖注入配置

提供表示层服务的依赖注入配置。
"""

from .presentation_module import PresentationModule
from .presentation_config import PresentationConfig

__all__ = [
    "PresentationModule",
    "PresentationConfig"
]