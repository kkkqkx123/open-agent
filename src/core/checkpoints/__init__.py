"""Checkpoint核心模块

提供Checkpoint相关的核心功能，包括实体定义、接口和错误处理。
"""

from .interfaces import IInternalCheckpointStorage
from .entities import CheckpointData, CheckpointConfig
from .error_handler import CheckpointErrorHandler, CheckpointOperationHandler

# 导出错误处理相关
def register_checkpoint_error_handler():
    """注册Checkpoint错误处理器到统一错误处理框架"""
    from src.core.common.error_management import register_error_handler
    from src.core.common.exceptions.checkpoint import (
        CheckpointError,
        CheckpointNotFoundError,
        CheckpointStorageError,
        CheckpointValidationError
    )
    
    # 注册Checkpoint错误处理器
    checkpoint_handler = CheckpointErrorHandler()
    
    register_error_handler(CheckpointError, checkpoint_handler)
    register_error_handler(CheckpointNotFoundError, checkpoint_handler)
    register_error_handler(CheckpointStorageError, checkpoint_handler)
    register_error_handler(CheckpointValidationError, checkpoint_handler)

__all__ = [
    # 核心接口和实体
    "IInternalCheckpointStorage",
    "CheckpointData", 
    "CheckpointConfig",
    
    # 错误处理
    "CheckpointErrorHandler",
    "CheckpointOperationHandler",
    "register_checkpoint_error_handler"
]