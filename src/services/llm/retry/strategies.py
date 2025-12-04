"""服务层重试策略实现

这个模块提供服务层特有的重试策略功能，包括日志记录器和条件检查器。
基础的重试策略已经迁移到基础设施层。
"""

from typing import Optional, List, Callable, Any

from src.interfaces.llm import IRetryLogger


class DefaultRetryLogger(IRetryLogger):
    """默认重试日志记录器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化默认重试日志记录器
        
        Args:
            enabled: 是否启用日志记录
        """
        self.enabled = enabled
    
    def log_retry_attempt(self, func_name: str, error: Exception, attempt: int, delay: float) -> None:
        """
        记录重试尝试
        
        Args:
            func_name: 函数名称
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        if not self.enabled:
            return
        
        print(f"[Retry] {func_name} 尝试 {attempt} 失败: {error}, {delay:.2f}秒后重试")
    
    def log_retry_success(self, func_name: str, result: Any, attempt: int) -> None:
        """
        记录重试成功
        
        Args:
            func_name: 函数名称
            result: 结果
            attempt: 尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Retry] {func_name} 在第 {attempt} 次尝试后成功")
    
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """
        记录重试失败
        
        Args:
            func_name: 函数名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        if not self.enabled:
            return
        
        print(f"[Retry] {func_name} 在 {total_attempts} 次尝试后失败: {error}")


def create_status_code_checker(retry_status_codes: List[int]) -> Callable[[Exception, int], bool]:
    """创建状态码重试条件检查器"""
    def checker(error: Exception, attempt: int) -> bool:
        if hasattr(error, "response"):
            response = getattr(error, "response")
            if hasattr(response, "status_code"):
                return response.status_code in retry_status_codes
        return False
    return checker


def create_error_type_checker(retry_error_types: List[str], block_error_types: Optional[List[str]] = None) -> Callable[[Exception, int], bool]:
    """创建错误类型重试条件检查器"""
    def checker(error: Exception, attempt: int) -> bool:
        error_type = type(error).__name__
        error_str = str(error).lower()
        
        # 检查是否在阻塞列表中
        for block_type in block_error_types or []:
            if block_type in error_type or block_type in error_str:
                return False
        
        # 如果有重试列表，只允许重试列表中的错误类型
        if retry_error_types:
            for retry_type in retry_error_types:
                # 检查错误类型名称或错误消息是否包含重试类型
                if retry_type.lower() in error_type.lower() or retry_type.lower() in error_str:
                    return True
            return False  # 不在重试列表中，不应重试
        else:
            # 如果没有重试列表，默认允许重试（除非被阻塞）
            return True
    return checker