"""UI消息系统接口模块

提供UI消息系统的所有接口定义。
"""

from .messages import (
    IUIMessage,
    IUIMessageRenderer,
    IUIMessageAdapter,
    IUIMessageManager,
    IUIMessageController
)

__all__ = [
    "IUIMessage",
    "IUIMessageRenderer", 
    "IUIMessageAdapter",
    "IUIMessageManager",
    "IUIMessageController"
]