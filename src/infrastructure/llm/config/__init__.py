"""配置管理模块

提供LLM客户端的配置发现、加载、验证和管理功能。
"""

from .config_discovery import ConfigDiscovery, ConfigInfo

__all__ = [
    "ConfigDiscovery",
    "ConfigInfo",
]