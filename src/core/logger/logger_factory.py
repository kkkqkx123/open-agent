"""Core 层日志工厂

为 Core 层提供统一的日志记录器获取接口，避免直接依赖 Services 层。
"""

from typing import Any, Dict, Optional
from ...interfaces.common_infra import ILogger


def get_core_logger(name: str, config: Optional[Dict[str, Any]] = None) -> ILogger:
    """为 Core 层提供统一的日志记录器
    
    Args:
        name: 日志记录器名称
        config: 可选的配置参数
        
    Returns:
        实现 ILogger 接口的日志记录器实例
    """
    # 延迟导入避免循环依赖
    from ...services.logger import get_logger
    return get_logger(name, config)


# 为了保持向后兼容性，提供一个简单的获取函数
def get_logger(name: str) -> ILogger:
    """获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        实现 ILogger 接口的日志记录器实例
    """
    return get_core_logger(name)