"""历史管理异常定义

定义历史记录管理相关的异常类型。
"""

from typing import Optional, Dict, Any


class HistoryError(Exception):
    """历史管理基础异常
    
    所有历史管理相关异常的基类。
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class TokenCalculationError(HistoryError):
    """Token计算异常
    
    当Token计算失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs: Any
    ):
        """
        初始化Token计算异常
        
        Args:
            message: 错误消息
            model: 模型名称
            provider: 提供商名称
            **kwargs: 其他参数
        """
        super().__init__(message, **kwargs)
        self.model = model
        self.provider = provider
        
        if model:
            self.details["model"] = model
        if provider:
            self.details["provider"] = provider


class CostCalculationError(HistoryError):
    """成本计算异常
    
    当成本计算失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        pricing_info: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """
        初始化成本计算异常
        
        Args:
            message: 错误消息
            model: 模型名称
            pricing_info: 定价信息
            **kwargs: 其他参数
        """
        super().__init__(message, **kwargs)
        self.model = model
        self.pricing_info = pricing_info or {}
        
        if model:
            self.details["model"] = model
        if pricing_info:
            self.details["pricing_info"] = pricing_info


class StatisticsError(HistoryError):
    """统计异常
    
    当统计操作失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        statistic_type: Optional[str] = None,
        **kwargs: Any
    ):
        """
        初始化统计异常
        
        Args:
            message: 错误消息
            workflow_id: 工作流ID
            statistic_type: 统计类型
            **kwargs: 其他参数
        """
        super().__init__(message, **kwargs)
        self.workflow_id = workflow_id
        self.statistic_type = statistic_type
        
        if workflow_id:
            self.details["workflow_id"] = workflow_id
        if statistic_type:
            self.details["statistic_type"] = statistic_type


class RecordNotFoundError(HistoryError):
    """记录未找到异常
    
    当请求的历史记录不存在时抛出。
    """
    
    def __init__(
        self,
        message: str,
        record_id: Optional[str] = None,
        record_type: Optional[str] = None,
        **kwargs: Any
    ):
        """
        初始化记录未找到异常
        
        Args:
            message: 错误消息
            record_id: 记录ID
            record_type: 记录类型
            **kwargs: 其他参数
        """
        super().__init__(message, **kwargs)
        self.record_id = record_id
        self.record_type = record_type
        
        if record_id:
            self.details["record_id"] = record_id
        if record_type:
            self.details["record_type"] = record_type


class QuotaExceededError(HistoryError):
    """配额超限异常
    
    当超过存储或使用配额时抛出。
    """
    
    def __init__(
        self,
        message: str,
        quota_type: Optional[str] = None,
        current_usage: Optional[int] = None,
        quota_limit: Optional[int] = None,
        **kwargs: Any
    ):
        """
        初始化配额超限异常
        
        Args:
            message: 错误消息
            quota_type: 配额类型
            current_usage: 当前使用量
            quota_limit: 配额限制
            **kwargs: 其他参数
        """
        super().__init__(message, **kwargs)
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        
        if quota_type:
            self.details["quota_type"] = quota_type
        if current_usage is not None:
            self.details["current_usage"] = current_usage
        if quota_limit is not None:
            self.details["quota_limit"] = quota_limit
