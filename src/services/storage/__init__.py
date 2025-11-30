"""存储服务模块

提供存储相关的业务编排功能。
配置管理已移至src.core.storage模块。
"""

from .orchestrator import (
    StorageOrchestrator,
    ThreadStorageService
)

# 从core.storage导入配置管理（已迁移至基础设施层）
from src.core.storage import (
    StorageConfigManager,
    StorageType,
    StorageConfig
)

# 保留原有的manager以兼容现有代码，但标记为废弃
from .manager import StorageManager

__all__ = [
    # 新的服务类
    "StorageOrchestrator",
    "ThreadStorageService",
    
    # 从core.storage导入的配置管理
    "StorageConfigManager",
    "StorageType",
    "StorageConfig",
    
    # 兼容性（废弃）
    "StorageManager",
]