"""Repository基类

提供所有Repository实现的通用基类和功能。
"""

from src.services.logger import get_logger
from abc import ABC
from typing import Dict, Any, Optional

from src.core.common.exceptions import RepositoryError

logger = get_logger(__name__)


class BaseRepository(ABC):
    """Repository基类，包含通用功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化基类
        
        Args:
            config: 配置参数
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    def _log_operation(self, operation: str, success: bool, details: str = "") -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            success: 是否成功
            details: 详细信息
        """
        status = "成功" if success else "失败"
        message = f"{operation}{status}"
        if details:
            message += f": {details}"
        
        if success:
            self.logger.debug(message)
        else:
            self.logger.error(message)
    
    def _handle_exception(self, operation: str, exception: Exception) -> None:
        """处理异常
        
        Args:
            operation: 操作名称
            exception: 异常对象
        """
        error_msg = f"{operation}失败: {exception}"
        self.logger.error(error_msg)
        raise RepositoryError(error_msg) from exception