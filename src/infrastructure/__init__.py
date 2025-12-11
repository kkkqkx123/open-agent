"""
基础设施层模块

提供系统的基础设施实现，包括配置、存储、容器、缓存、日志等核心组件。
这些实现为整个系统提供技术支撑。

使用方式：
- 配置相关：from src.infrastructure.config import ConfigLoader
- 存储相关：from src.infrastructure.storage import BaseStorage
- 容器相关：from src.infrastructure.container import DependencyContainer
- 验证相关：from src.infrastructure.validation import ValidationCache
"""

# 导出验证模块
from .validation import (
    ValidationCache,
    ValidationCacheKeyGenerator,
)