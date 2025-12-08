"""
核心模块

提供转换器的核心接口、基础类和上下文管理。
"""

from .interfaces import (
    IProvider,
    IConverter,
    IMultimodalAdapter,
    IStreamAdapter,
    IToolsAdapter,
    IValidationAdapter,
)
from .base_converter import BaseConverter
from .conversion_context import ConversionContext
from .conversion_pipeline import ConversionPipeline

__all__ = [
    "IProvider",
    "IConverter", 
    "IMultimodalAdapter",
    "IStreamAdapter",
    "IToolsAdapter",
    "IValidationAdapter",
    "BaseConverter",
    "ConversionContext",
    "ConversionPipeline",
]