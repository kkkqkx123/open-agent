"""
基础设施层配置处理器模块

提供配置继承、环境变量、引用、验证和转换等处理功能。
"""

# 基础处理器
from .base_processor import BaseConfigProcessor, IConfigProcessor

# 具体处理器实现
from .environment_processor import EnvironmentProcessor
from .inheritance_processor import InheritanceProcessor
from .reference_processor import ReferenceProcessor
from .validation_processor import ValidationProcessor, SchemaRegistry
from .transformation_processor import TransformationProcessor, TypeConverter

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
    "TypeConverter"
]