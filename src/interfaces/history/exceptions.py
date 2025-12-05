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
        token_count: Optional[int] = None,
        **kwargs: Any
    ):
        """
        初始化Token计算异常
        
        Args:
            message: 错误消息
            model: 模型名称
            provider: 提供商名称
            token_count: Token数量
            **kwargs: 其他参数
        """
        super().__init__(message, "TOKEN_CALCULATION_ERROR", kwargs)
        self.model = model
        self.provider = provider
        self.token_count = token_count
        
        if model:
            self.details["model"] = model
        if provider:
            self.details["provider"] = provider
        if token_count is not None:
            self.details["token_count"] = token_count


class CostCalculationError(HistoryError):
    """成本计算异常
    
    当成本计算失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        pricing_info: Optional[Dict[str, Any]] = None,
        cost_amount: Optional[float] = None,
        **kwargs: Any
    ):
        """
        初始化成本计算异常
        
        Args:
            message: 错误消息
            model: 模型名称
            pricing_info: 定价信息
            cost_amount: 成本金额
            **kwargs: 其他参数
        """
        super().__init__(message, "COST_CALCULATION_ERROR", kwargs)
        self.model = model
        self.pricing_info = pricing_info or {}
        self.cost_amount = cost_amount
        
        if model:
            self.details["model"] = model
        if pricing_info:
            self.details["pricing_info"] = pricing_info
        if cost_amount is not None:
            self.details["cost_amount"] = cost_amount


class StatisticsError(HistoryError):
    """统计异常
    
    当统计操作失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        statistic_type: Optional[str] = None,
        time_range: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """
        初始化统计异常
        
        Args:
            message: 错误消息
            workflow_id: 工作流ID
            statistic_type: 统计类型
            time_range: 时间范围
            **kwargs: 其他参数
        """
        super().__init__(message, "STATISTICS_ERROR", kwargs)
        self.workflow_id = workflow_id
        self.statistic_type = statistic_type
        self.time_range = time_range or {}
        
        if workflow_id:
            self.details["workflow_id"] = workflow_id
        if statistic_type:
            self.details["statistic_type"] = statistic_type
        if time_range:
            self.details["time_range"] = time_range


class RecordNotFoundError(HistoryError):
    """记录未找到异常
    
    当请求的历史记录不存在时抛出。
    """
    
    def __init__(
        self,
        message: str,
        record_id: Optional[str] = None,
        record_type: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """
        初始化记录未找到异常
        
        Args:
            message: 错误消息
            record_id: 记录ID
            record_type: 记录类型
            query_params: 查询参数
            **kwargs: 其他参数
        """
        super().__init__(message, "RECORD_NOT_FOUND_ERROR", kwargs)
        self.record_id = record_id
        self.record_type = record_type
        self.query_params = query_params or {}
        
        if record_id:
            self.details["record_id"] = record_id
        if record_type:
            self.details["record_type"] = record_type
        if query_params:
            self.details["query_params"] = query_params


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
        reset_time: Optional[str] = None,
        **kwargs: Any
    ):
        """
        初始化配额超限异常
        
        Args:
            message: 错误消息
            quota_type: 配额类型
            current_usage: 当前使用量
            quota_limit: 配额限制
            reset_time: 重置时间
            **kwargs: 其他参数
        """
        super().__init__(message, "QUOTA_EXCEEDED_ERROR", kwargs)
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        self.reset_time = reset_time
        
        if quota_type:
            self.details["quota_type"] = quota_type
        if current_usage is not None:
            self.details["current_usage"] = current_usage
        if quota_limit is not None:
            self.details["quota_limit"] = quota_limit
        if reset_time:
            self.details["reset_time"] = reset_time


class HistoryQueryError(HistoryError):
    """历史查询异常
    
    当历史查询操作失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        query_type: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """
        初始化历史查询异常
        
        Args:
            message: 错误消息
            query_type: 查询类型
            query_params: 查询参数
            **kwargs: 其他参数
        """
        super().__init__(message, "HISTORY_QUERY_ERROR", kwargs)
        self.query_type = query_type
        self.query_params = query_params or {}
        
        if query_type:
            self.details["query_type"] = query_type
        if query_params:
            self.details["query_params"] = query_params


class HistoryStorageError(HistoryError):
    """历史存储异常
    
    当历史存储操作失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        storage_operation: Optional[str] = None,
        storage_backend: Optional[str] = None,
        **kwargs: Any
    ):
        """
        初始化历史存储异常
        
        Args:
            message: 错误消息
            storage_operation: 存储操作类型
            storage_backend: 存储后端
            **kwargs: 其他参数
        """
        super().__init__(message, "HISTORY_STORAGE_ERROR", kwargs)
        self.storage_operation = storage_operation
        self.storage_backend = storage_backend
        
        if storage_operation:
            self.details["storage_operation"] = storage_operation
        if storage_backend:
            self.details["storage_backend"] = storage_backend


class HistoryValidationError(HistoryError):
    """历史验证异常
    
    当历史数据验证失败时抛出。
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[list] = None,
        data_type: Optional[str] = None,
        **kwargs: Any
    ):
        """
        初始化历史验证异常
        
        Args:
            message: 错误消息
            validation_errors: 验证错误列表
            data_type: 数据类型
            **kwargs: 其他参数
        """
        super().__init__(message, "HISTORY_VALIDATION_ERROR", kwargs)
        self.validation_errors = validation_errors or []
        self.data_type = data_type
        
        if validation_errors:
            self.details["validation_errors"] = validation_errors
        if data_type:
            self.details["data_type"] = data_type


# 导出所有异常
__all__ = [
    "HistoryError",
    "TokenCalculationError",
    "CostCalculationError",
    "StatisticsError",
    "RecordNotFoundError",
    "QuotaExceededError",
    "HistoryQueryError",
    "HistoryStorageError",
    "HistoryValidationError",
]