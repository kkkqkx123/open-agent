"""
验证基础设施模块
"""

from .cache import (
    ValidationCache,
    ValidationCacheKeyGenerator,
)

from .result import ValidationResult

__all__ = [
    # 缓存
    "ValidationCache",
    "ValidationCacheKeyGenerator",
    
    # 验证结果
    "ValidationResult",
    
]