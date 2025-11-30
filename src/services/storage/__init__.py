"""存储服务模块

提供存储相关的业务编排和配置管理功能。
"""

from .orchestrator import (
    StorageOrchestrator,
    ThreadStorageService
)

from .config_manager import (
    StorageConfigManager,
    StorageType
)

# 保留原有的manager以兼容现有代码，但标记为废弃
from .manager import StorageManager

__all__ = [
    # 新的服务类
    "StorageOrchestrator",
    "ThreadStorageService",
    "StorageConfigManager",
    "StorageType",
    
    # 兼容性（废弃）
    "StorageManager",
]