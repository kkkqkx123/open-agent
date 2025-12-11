"""Logger依赖注入空实现

提供Logger服务的空实现，避免循环依赖。
"""

import sys
from typing import Optional

from src.interfaces.logger import ILogger


class _StubLogger(ILogger):
    """临时 logger 实现（用于极端情况）"""
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        print(f"[DEBUG] {message}", file=sys.stdout)
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        print(f"[INFO] {message}", file=sys.stdout)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        print(f"[WARNING] {message}", file=sys.stderr)
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        print(f"[CRITICAL] {message}", file=sys.stderr)
    
    def set_level(self, level) -> None:
        """设置日志级别"""
        pass
    
    def add_handler(self, handler) -> None:
        """添加日志处理器"""
        pass
    
    def remove_handler(self, handler) -> None:
        """移除日志处理器"""
        pass
    
    def set_redactor(self, redactor) -> None:
        """设置日志脱敏器"""
        pass


# 全局日志实例
_global_logger: Optional[ILogger] = None


def get_logger(module_name: str | None = None) -> ILogger:
    """获取日志记录器实例"""
    global _global_logger
    if _global_logger is not None:
        return _global_logger
    
    # 返回临时实现
    return _StubLogger()


def set_logger_instance(logger: ILogger) -> None:
    """设置全局logger实例"""
    global _global_logger
    _global_logger = logger


def clear_logger_instance() -> None:
    """清除全局logger实例"""
    global _global_logger
    _global_logger = None


def get_logger_status() -> dict:
    """获取日志注入状态"""
    return {
        "has_global_logger": _global_logger is not None,
        "logger_type": type(_global_logger).__name__ if _global_logger else None
    }


__all__ = [
    "get_logger",
    "set_logger_instance",
    "clear_logger_instance",
    "get_logger_status",
]