"""
配置管理模块

提供 LLM 配置发现、加载和验证功能
"""

from .config_discovery import ConfigDiscovery, ConfigLocation, get_config_discovery, ConfigInfo, ProviderInfo
from .config_loader import ConfigLoader, LoadOptions, get_config_loader
from .config_validator import (
    ConfigValidator,
    ValidationResult,
    ValidationReport,
    ValidationSeverity,
    get_config_validator
)
from .models import LLMClientConfig, OpenAIConfig, MockConfig, GeminiConfig, AnthropicConfig, HumanRelayConfig

__all__ = [
    # 核心类
    "ConfigDiscovery",
    "ConfigLoader",
    "ConfigValidator",
    
    # 数据类
    "ConfigLocation",
    "LoadOptions",
    "ValidationResult",
    "ValidationReport",
    "ValidationSeverity",
    
    # 配置模型
    "LLMClientConfig",
    "OpenAIConfig",
    "MockConfig",
    "GeminiConfig",
    "AnthropicConfig",
    "HumanRelayConfig",
    
    # 全局函数
    "get_config_discovery",
    "get_config_loader",
    "get_config_validator",
]