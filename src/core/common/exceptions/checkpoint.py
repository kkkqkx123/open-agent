"""Checkpoint模块异常定义

定义checkpoint操作相关的异常类型。
"""


class CheckpointError(Exception):
    """Checkpoint操作基础异常"""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint未找到异常"""
    pass


class CheckpointStorageError(CheckpointError):
    """Checkpoint存储异常"""
    pass


class CheckpointValidationError(CheckpointError):
    """Checkpoint验证异常"""
    pass