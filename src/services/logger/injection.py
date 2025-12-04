"""日志依赖注入便利层

使用通用依赖注入框架提供简洁的日志获取方式。
"""

import sys
from typing import Optional

from src.interfaces.logger import ILogger
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


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


def _create_fallback_logger() -> ILogger:
    """创建fallback logger"""
    return _StubLogger()


# 注册日志注入
_logger_injection = get_global_injection_registry().register(ILogger, _create_fallback_logger)


@injectable(ILogger, _create_fallback_logger)
def get_logger(module_name: str | None = None) -> ILogger:
    """获取日志记录器实例
    
    获取策略（按优先级）：
    1. 使用全局 logger 实例（由容器设置）
    2. 尝试从容器获取
    3. 降级到临时实现（防止崩溃）
    
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
    return _logger_injection.get_instance()


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
    _logger_injection.set_instance(logger)


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
    _logger_injection.clear_instance()


def get_logger_status() -> dict:
    """获取日志注入状态
    
    Returns:
        状态信息字典
    """
    return _logger_injection.get_status()


def disable_container_fallback() -> None:
    """禁用容器降级（主要用于测试）"""
    _logger_injection.disable_container_fallback()


def enable_container_fallback() -> None:
    """启用容器降级"""
    _logger_injection.enable_container_fallback()


# 导出的公共接口
__all__ = [
    "get_logger",
    "set_logger_instance",
    "clear_logger_instance",
    "get_logger_status",
    "disable_container_fallback",
    "enable_container_fallback",
]