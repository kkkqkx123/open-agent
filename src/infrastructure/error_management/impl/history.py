"""历史模块错误处理器

为历史记录管理系统提供专门的错误处理和恢复策略。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional

from src.infrastructure.error_management import (
    BaseErrorHandler, ErrorCategory, ErrorSeverity, 
    register_error_handler, operation_with_retry
)
from src.interfaces.history.exceptions import (
    HistoryError, TokenCalculationError, CostCalculationError, 
    StatisticsError, RecordNotFoundError, QuotaExceededError
)

logger = get_logger(__name__)


class HistoryErrorHandler(BaseErrorHandler):
    """历史模块错误处理器"""
    
    def __init__(self):
        """初始化历史错误处理器"""
        super().__init__(ErrorCategory.EXECUTION, ErrorSeverity.MEDIUM)
        self._recovery_strategies = {
            TokenCalculationError: self._handle_token_calculation_error,
            CostCalculationError: self._handle_cost_calculation_error,
            StatisticsError: self._handle_statistics_error,
            RecordNotFoundError: self._handle_record_not_found_error,
            QuotaExceededError: self._handle_quota_exceeded_error,
        }
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误"""
        return isinstance(error, (HistoryError, TokenCalculationError, CostCalculationError,
                                StatisticsError, RecordNotFoundError, QuotaExceededError))
    
    def handle(self, error: Exception, context: Optional[Dict] = None) -> None:
         """处理历史错误"""
         try:
             # 记录错误日志
             self._log_error(error, context)
             
             # 根据错误类型选择恢复策略
             error_type = type(error)
             if error_type in self._recovery_strategies:
                 self._recovery_strategies[error_type](error, context)
             else:
                 # 通用历史错误处理
                 if isinstance(error, HistoryError):
                     self._handle_generic_history_error(error, context)
                 
         except Exception as handler_error:
             # 错误处理器本身出错，记录但不抛出异常
             logger.error(f"历史错误处理器内部错误: {handler_error}")
    
    def _handle_token_calculation_error(self, error: TokenCalculationError, context: Optional[Dict] = None) -> None:
        """处理Token计算错误"""
        logger.warning(f"Token计算失败: {error}")
        
        # 提供修复建议
        if hasattr(error, 'model') and error.model:
            logger.info(f"建议检查模型 {error.model} 的Token计算配置")
        
        if hasattr(error, 'provider') and error.provider:
            logger.info(f"建议检查提供商 {error.provider} 的API响应格式")
        
        logger.info("常见Token计算问题: API响应格式变化、编码问题、特殊字符处理")
    
    def _handle_cost_calculation_error(self, error: CostCalculationError, context: Optional[Dict] = None) -> None:
        """处理成本计算错误"""
        logger.warning(f"成本计算失败: {error}")
        
        # 提供修复建议
        if hasattr(error, 'model') and error.model:
            logger.info(f"建议检查模型 {error.model} 的定价配置")
        
        if hasattr(error, 'pricing_info') and error.pricing_info:
            logger.info(f"定价信息: {error.pricing_info}")
        
        logger.info("常见成本计算问题: 定价信息缺失、货币转换错误、除零错误")
    
    def _handle_statistics_error(self, error: StatisticsError, context: Optional[Dict] = None) -> None:
        """处理统计错误"""
        logger.warning(f"统计计算失败: {error}")
        
        # 提供修复建议
        if hasattr(error, 'workflow_id') and error.workflow_id:
            logger.info(f"建议检查工作流 {error.workflow_id} 的历史数据完整性")
        
        if hasattr(error, 'statistic_type') and error.statistic_type:
            logger.info(f"统计类型: {error.statistic_type}")
        
        logger.info("常见统计问题: 数据不一致、聚合错误、时间范围问题")
    
    def _handle_record_not_found_error(self, error: RecordNotFoundError, context: Optional[Dict] = None) -> None:
        """处理记录未找到错误"""
        logger.warning(f"历史记录未找到: {error}")
        
        # 提供修复建议
        if hasattr(error, 'record_id') and error.record_id:
            logger.info(f"建议检查记录ID: {error.record_id}")
        
        if hasattr(error, 'record_type') and error.record_type:
            logger.info(f"记录类型: {error.record_type}")
        
        logger.info("常见原因: 记录已被删除、ID错误、权限问题")
    
    def _handle_quota_exceeded_error(self, error: QuotaExceededError, context: Optional[Dict] = None) -> None:
        """处理配额超限错误"""
        logger.error(f"历史记录配额超限: {error}")
        
        # 提供配额管理建议
        if hasattr(error, 'quota_type') and error.quota_type:
            logger.info(f"配额类型: {error.quota_type}")
        
        if hasattr(error, 'current_usage') and hasattr(error, 'quota_limit'):
            logger.info(f"当前使用量: {error.current_usage}, 限制: {error.quota_limit}")
        
        logger.info("建议清理旧历史记录或升级存储配额")
    
    def _handle_generic_history_error(self, error: HistoryError, context: Optional[Dict] = None) -> None:
        """处理通用历史错误"""
        logger.error(f"历史记录错误: {error}")
        
        # 提供通用建议
        if context and 'operation' in context:
            logger.info(f"失败的操作: {context['operation']}")
        
        logger.info("建议检查历史存储后端的状态和配置")
    
    def _log_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """记录历史错误日志"""
        error_info = {
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # 添加历史特定的错误信息
        if isinstance(error, HistoryError):
            if hasattr(error, 'error_code') and error.error_code:
                error_info["error_code"] = error.error_code
            if hasattr(error, 'details') and error.details:
                error_info["error_details"] = error.details
        
        # 添加Token计算特定的错误信息
        if isinstance(error, TokenCalculationError):
            if hasattr(error, 'model') and error.model:
                error_info["model"] = error.model
            if hasattr(error, 'provider') and error.provider:
                error_info["provider"] = error.provider
        
        # 添加成本计算特定的错误信息
        if isinstance(error, CostCalculationError):
            if hasattr(error, 'model') and error.model:
                error_info["model"] = error.model
            if hasattr(error, 'pricing_info') and error.pricing_info:
                error_info["pricing_info"] = error.pricing_info
        
        # 添加统计特定的错误信息
        if isinstance(error, StatisticsError):
            if hasattr(error, 'workflow_id') and error.workflow_id:
                error_info["workflow_id"] = error.workflow_id
            if hasattr(error, 'statistic_type') and error.statistic_type:
                error_info["statistic_type"] = error.statistic_type
        
        # 根据严重度选择日志级别
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"历史错误: {error_info}")
        elif self.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"历史警告: {error_info}")
        else:
            logger.info(f"历史信息: {error_info}")


class HistoryErrorRecovery:
    """历史错误恢复策略"""
    
    @staticmethod
    def retry_history_operation(history_operation_func, max_retries: int = 3):
        """重试历史操作"""
        return operation_with_retry(
            history_operation_func,
            max_retries=max_retries,
            retryable_exceptions=(IOError, TimeoutError, ConnectionError),
            context={"operation": "history_operation"}
        )
    
    @staticmethod
    def fallback_to_estimated_tokens(primary_calculation_func, fallback_estimation_func):
        """降级到估算Token"""
        try:
            return primary_calculation_func()
        except TokenCalculationError as e:
            logger.warning(f"精确Token计算失败，使用估算: {e}")
            return fallback_estimation_func()
    
    @staticmethod
    def validate_history_data_before_storage(record) -> bool:
        """存储前验证历史数据"""
        try:
            if record is None:
                raise HistoryError("历史记录不能为None")
            
            # 检查记录的基本功能
            if not hasattr(record, 'to_dict'):
                raise HistoryError("历史记录缺少 to_dict 方法")
            
            if not hasattr(record, 'record_id'):
                raise HistoryError("历史记录缺少 record_id 属性")
            
            # 测试记录序列化
            try:
                record_dict = record.to_dict()
                import json
                json.dumps(record_dict)
            except Exception as e:
                raise HistoryError(f"历史记录数据无法序列化: {e}")
            
            return True
        except Exception as e:
            logger.error(f"历史记录验证失败: {e}")
            return False
    
    @staticmethod
    def cleanup_old_history_records(history_manager, max_age_days: int = 30):
        """清理旧历史记录"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            logger.info(f"开始清理超过 {max_age_days} 天的历史记录")
            # 实际实现取决于具体的历史管理器接口
            # deleted_count = await history_manager.delete_records(older_than=cutoff_date)
            # logger.info(f"清理完成，删除了 {deleted_count} 条记录")
        except Exception as e:
            logger.error(f"清理旧历史记录失败: {e}")


class HistoryDataConsistencyChecker:
    """历史数据一致性检查器"""
    
    @staticmethod
    def check_token_usage_consistency(token_record) -> Dict[str, Any]:
        """检查Token使用记录的一致性"""
        issues = []
        
        try:
            # 检查Token数量关系
            if hasattr(token_record, 'prompt_tokens') and hasattr(token_record, 'completion_tokens'):
                calculated_total = token_record.prompt_tokens + token_record.completion_tokens
                if hasattr(token_record, 'total_tokens'):
                    if token_record.total_tokens != calculated_total:
                        issues.append(f"Token总数不一致: {token_record.total_tokens} vs {calculated_total}")
            
            # 检查负数
            if hasattr(token_record, 'prompt_tokens') and token_record.prompt_tokens < 0:
                issues.append("Prompt token数量为负数")
            
            if hasattr(token_record, 'completion_tokens') and token_record.completion_tokens < 0:
                issues.append("Completion token数量为负数")
            
            # 检查置信度
            if hasattr(token_record, 'confidence'):
                if not (0.0 <= token_record.confidence <= 1.0):
                    issues.append(f"置信度超出范围: {token_record.confidence}")
            
            return {
                "consistent": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "consistent": False,
                "issues": [f"一致性检查失败: {e}"]
            }
    
    @staticmethod
    def check_cost_record_consistency(cost_record) -> Dict[str, Any]:
        """检查成本记录的一致性"""
        issues = []
        
        try:
            # 检查成本关系
            if hasattr(cost_record, 'prompt_cost') and hasattr(cost_record, 'completion_cost'):
                calculated_total = cost_record.prompt_cost + cost_record.completion_cost
                if hasattr(cost_record, 'total_cost'):
                    if abs(cost_record.total_cost - calculated_total) > 0.0001:
                        issues.append(f"总成本不一致: {cost_record.total_cost} vs {calculated_total}")
            
            # 检查负数
            if hasattr(cost_record, 'prompt_cost') and cost_record.prompt_cost < 0:
                issues.append("Prompt成本为负数")
            
            if hasattr(cost_record, 'completion_cost') and cost_record.completion_cost < 0:
                issues.append("Completion成本为负数")
            
            return {
                "consistent": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "consistent": False,
                "issues": [f"成本一致性检查失败: {e}"]
            }


# 注册历史错误处理器
def register_history_error_handler():
    """注册历史错误处理器到全局注册表"""
    history_handler = HistoryErrorHandler()
    
    # 注册各种历史异常的处理器
    register_error_handler(HistoryError, history_handler)
    register_error_handler(TokenCalculationError, history_handler)
    register_error_handler(CostCalculationError, history_handler)
    register_error_handler(StatisticsError, history_handler)
    register_error_handler(RecordNotFoundError, history_handler)
    register_error_handler(QuotaExceededError, history_handler)
    
    logger.info("历史错误处理器已注册到全局注册表")


# 自动注册
register_history_error_handler()