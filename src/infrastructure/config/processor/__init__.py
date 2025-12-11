"""
基础设施层配置处理器模块

提供配置继承、环境变量、引用、验证、转换、发现和Provider管理等处理功能。
"""

# 基础处理器
from .base_processor import BaseConfigProcessor, IConfigProcessor

# 具体处理器实现
from .environment_processor import EnvironmentProcessor
from .inheritance_processor import InheritanceProcessor
from .reference_processor import ReferenceProcessor
from .validation_processor import ValidationProcessor, SchemaRegistry
from .transformation_processor import TransformationProcessor, TypeConverter
from .discovery_processor import DiscoveryProcessor

# 配置发现策略
from .strategies import (
    LLMConfigDiscoveryStrategy,
    WorkflowConfigDiscoveryStrategy,
    ToolsConfigDiscoveryStrategy,
    ProviderManagementStrategy,
    DefaultProviderManagementStrategy,
    ProviderManager,
    ProviderInfo
)

__all__ = [
    # 基础处理器
    "BaseConfigProcessor",
    "IConfigProcessor",
    
    # 具体处理器实现
    "EnvironmentProcessor",
    "InheritanceProcessor",
    "ReferenceProcessor",
    "ValidationProcessor",
    "SchemaRegistry",
    "TransformationProcessor",
    "TypeConverter",
    "DiscoveryProcessor",
    
    # 数据类
    "ProviderInfo",
    
    # 配置发现策略
    "LLMConfigDiscoveryStrategy",
    "WorkflowConfigDiscoveryStrategy",
    "ToolsConfigDiscoveryStrategy",
    "ProviderManagementStrategy",
    "DefaultProviderManagementStrategy",
    "ProviderManager"
]