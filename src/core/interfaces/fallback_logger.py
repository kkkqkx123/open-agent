"""回退日志实现

当没有设置依赖容器时使用的简单日志实现。
"""

import sys
from typing import Any, Optional

from src.interfaces.logger import ILogger, IBaseHandler, ILogRedactor


class FallbackLogger(ILogger):
    """回退日志记录器
    
    当没有设置依赖容器时使用的简单日志实现，确保系统不会因为缺少日志服务而崩溃。
    """
    
    def __init__(self, name: Optional[str] = None):
        """初始化回退日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self._name = name or "fallback"
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        print(f"[DEBUG] [{self._name}] {message}", file=sys.stdout)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        print(f"[INFO] [{self._name}] {message}", file=sys.stdout)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        print(f"[WARNING] [{self._name}] {message}", file=sys.stderr)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        print(f"[ERROR] [{self._name}] {message}", file=sys.stderr)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        print(f"[CRITICAL] [{self._name}] {message}", file=sys.stderr)
    
    def set_level(self, level: Any) -> None:
        """设置日志级别"""
        # 回退实现不支持设置日志级别
        pass
    
    def add_handler(self, handler: IBaseHandler) -> None:
        """添加日志处理器"""
        # 回退实现不支持添加处理器
        pass
    
    def remove_handler(self, handler: IBaseHandler) -> None:
        """移除日志处理器"""
        # 回退实现不支持移除处理器
        pass
    
    def set_redactor(self, redactor: ILogRedactor) -> None:
        """设置日志脱敏器"""
        # 回退实现不支持设置脱敏器
        pass


__all__ = [
    "FallbackLogger",
]