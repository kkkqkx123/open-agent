"""Hook系统模块

提供独立的Hook执行功能，从插件系统中分离出来。
"""

from .executor import HookExecutor

__all__ = ["HookExecutor"]