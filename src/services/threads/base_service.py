"""线程服务基类"""

from src.interfaces.dependency_injection import get_logger
from abc import ABC
from typing import Optional

from src.core.threads.entities import Thread
from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.storage.exceptions import StorageValidationError as ValidationError, StorageNotFoundError as EntityNotFoundError

logger = get_logger(__name__)


class BaseThreadService(ABC):
    """线程服务基类，提供通用功能"""
    
    def __init__(self, thread_repository: IThreadRepository):
        """初始化基类服务
        
        Args:
            thread_repository: 线程仓储接口
        """
        self._thread_repository = thread_repository
    
    def _handle_exception(self, e: Exception, operation: str) -> None:
        """统一异常处理
        
        Args:
            e: 异常对象
            operation: 操作名称
        """
        logger.error(f"Failed to {operation}: {str(e)}")
        if isinstance(e, (ValidationError, EntityNotFoundError)):
            raise
        raise ValidationError(f"Failed to {operation}: {str(e)}")
    
    async def _validate_thread_exists(self, thread_id: str) -> Thread:
        """验证线程存在性
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程对象
            
        Raises:
            EntityNotFoundError: 线程不存在
        """
        thread = await self._thread_repository.get(thread_id)
        if not thread:
            raise EntityNotFoundError(f"Thread {thread_id} not found")
        return thread
    
    def _log_operation(self, operation: str, thread_id: Optional[str] = None, **kwargs) -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            thread_id: 线程ID（可选）
            **kwargs: 其他参数
        """
        message = f"Thread operation: {operation}"
        if thread_id:
            message += f" for thread {thread_id}"
        if kwargs:
            message += f" with params: {kwargs}"
        logger.info(message)