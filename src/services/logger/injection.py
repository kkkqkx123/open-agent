"""日志依赖注入便利层

简化实现避免循环依赖，提供基本的日志获取方式。
"""

import sys
from typing import Optional

from src.interfaces.logger import ILogger


class _StubLogger(ILogger):
    """临时 logger 实现（用于极端情况）
    
    当日志系统初始化失败时使用此实现，确保代码不会因为
    缺少 logger 而直接崩溃。
    """
    
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


# 全局日志实例（简化实现）
_global_logger: Optional[ILogger] = None


def get_logger(module_name: str | None = None) -> ILogger:
    """获取日志记录器实例
    
    简化实现：直接返回全局实例或临时实现
    
    Args:
        module_name: 模块名称，用于标识日志来源（当前版本中未使用，保留兼容性）
        
    Returns:
        ILogger: 日志记录器实例
        
    Example:
        ```python
        # 模块级别使用（推荐）
        logger = get_logger(__name__)
        
        logger.info("应用启动")
        logger.error("发生错误", exc_info=True)
        ```
    """
    global _global_logger
    if _global_logger is not None:
        return _global_logger
    
    # 返回临时实现
    return _StubLogger()


def set_logger_instance(logger: ILogger) -> None:
    """在应用启动时设置全局 logger 实例
    
    这个函数由容器的 logger_bindings 在服务注册后调用。
    
    Args:
        logger: ILogger 实例
        
    Example:
        ```python
        # 在 logger_bindings.py 中
        logger_instance = container.get(ILogger)
        set_logger_instance(logger_instance)
        ```
    """
    global _global_logger
    _global_logger = logger


def clear_logger_instance() -> None:
    """清除全局 logger 实例
    
    主要用于测试环境重置。
    
    Example:
        ```python
        # 在测试清理中
        def teardown():
            clear_logger_instance()
        ```
    """
    global _global_logger
    _global_logger = None


def get_logger_status() -> dict:
    """获取日志注入状态
    
    Returns:
        状态信息字典
    """
    return {
        "has_global_logger": _global_logger is not None,
        "logger_type": type(_global_logger).__name__ if _global_logger else None
    }


# 导出的公共接口
__all__ = [
    "get_logger",
    "set_logger_instance",
    "clear_logger_instance",
    "get_logger_status",
]