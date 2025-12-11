"""状态模块错误处理器

为状态管理系统提供专门的错误处理和恢复策略。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional

from src.infrastructure.error_management import (
    BaseErrorHandler, ErrorCategory, ErrorSeverity, 
    register_error_handler, operation_with_retry
)
from src.interfaces.state.exceptions import (
    StateError, StateValidationError, StateNotFoundError,
    StateTimeoutError, StateCapacityError
)
from src.interfaces.history.exceptions import HistoryError

logger = get_logger(__name__)


class StateErrorHandler(BaseErrorHandler):
    """状态模块错误处理器"""
    
    def __init__(self):
        """初始化状态错误处理器"""
        super().__init__(ErrorCategory.STATE, ErrorSeverity.HIGH)
        self._recovery_strategies = {
            StateValidationError: self._handle_validation_error,
            StateNotFoundError: self._handle_not_found_error,
            StateTimeoutError: self._handle_timeout_error,
            StateCapacityError: self._handle_capacity_error,
            HistoryError: self._handle_history_error,
        }
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误"""
        return isinstance(error, (StateError, StateValidationError, StateNotFoundError,
                                StateTimeoutError, StateCapacityError, HistoryError))
    
    def handle(self, error: Exception, context: Optional[Dict] = None) -> None:
        """处理状态错误"""
        try:
            # 记录错误日志
            self._log_error(error, context)
            
            # 根据错误类型选择恢复策略
            error_type = type(error)
            if error_type in self._recovery_strategies:
                self._recovery_strategies[error_type](error, context)
            else:
                # 通用状态错误处理
                self._handle_generic_state_error(error, context)
                
        except Exception as handler_error:
            # 错误处理器本身出错，记录但不抛出异常
            logger.error(f"状态错误处理器内部错误: {handler_error}")
    
    def _handle_validation_error(self, error: StateValidationError, context: Optional[Dict] = None) -> None:
        """处理状态验证错误"""
        logger.warning(f"状态验证失败: {error}")
        
        # 提供修复建议
        if context:
            if 'state_id' in context:
                logger.info(f"建议检查状态ID: {context['state_id']}")
            if 'operation' in context:
                logger.info(f"建议检查操作: {context['operation']}")
        
        # 提供通用验证建议
        logger.info("常见验证问题: 状态数据类型、必需字段缺失、数据格式错误")
    
    def _handle_not_found_error(self, error: StateNotFoundError, context: Optional[Dict] = None) -> None:
        """处理状态未找到错误"""
        logger.error(f"状态未找到: {error}")
        
        # 建议检查状态存储
        if context and 'state_id' in context:
            logger.info(f"建议检查状态ID是否正确: {context['state_id']}")
            logger.info("建议检查状态是否已被删除或从未创建")
        
        logger.info("建议检查状态存储后端的连接状态")
    
    def _handle_timeout_error(self, error: StateTimeoutError, context: Optional[Dict] = None) -> None:
        """处理状态超时错误"""
        logger.error(f"状态操作超时: {error}")
        
        # 提供超时处理建议
        logger.info("建议检查网络连接和服务器响应时间")
        logger.info("考虑增加超时时间或优化操作性能")
        
        if context and 'operation' in context:
            logger.info(f"超时操作: {context['operation']}")
    
    def _handle_capacity_error(self, error: StateCapacityError, context: Optional[Dict] = None) -> None:
        """处理状态容量错误"""
        logger.error(f"状态容量超限: {error}")
        
        # 提供容量管理建议
        if hasattr(error, 'required_size') and hasattr(error, 'available_size'):
            logger.info(f"所需大小: {error.required_size}, 可用大小: {error.available_size}")
        
        logger.info("建议清理旧状态数据或增加存储容量")
        logger.info("考虑实施状态数据压缩或归档策略")
    
    def _handle_history_error(self, error: HistoryError, context: Optional[Dict] = None) -> None:
        """处理历史记录错误"""
        logger.error(f"历史记录错误: {error}")
        
        # 提供历史记录修复建议
        if context and 'state_id' in context:
            logger.info(f"建议检查状态 {context['state_id']} 的历史记录存储")
        
        logger.info("建议检查历史记录存储后端的可用空间")
        logger.info("考虑清理或压缩历史记录数据")
    
    def _handle_generic_state_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """处理通用状态错误"""
        logger.error(f"状态错误: {error}")
        
        # 提供通用建议
        if context and 'state_id' in context:
            logger.info(f"建议检查状态: {context['state_id']}")
        
        logger.info("建议检查状态管理系统的配置和依赖")
        logger.info("考虑重启相关服务或检查系统资源")
    
    def _log_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """记录状态错误日志"""
        error_info = {
            "category": self.error_category.value,
            "severity": self.error_severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        # 添加状态特定的错误信息
        if isinstance(error, StateError):
            if hasattr(error, 'details') and error.details:
                error_info["error_details"] = error.details
        
        # 添加历史记录特定的错误信息
        if isinstance(error, HistoryError):
            if hasattr(error, 'error_code') and error.error_code:
                error_info["error_code"] = error.error_code
            if hasattr(error, 'details') and error.details:
                error_info["error_details"] = error.details
        
        # 根据严重度选择日志级别
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"状态错误: {error_info}")
        elif self.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"状态警告: {error_info}")
        else:
            logger.info(f"状态信息: {error_info}")


class StateErrorRecovery:
    """状态错误恢复策略"""
    
    @staticmethod
    def retry_state_operation(state_operation_func, max_retries: int = 3):
        """重试状态操作"""
        return operation_with_retry(
            state_operation_func,
            max_retries=max_retries,
            retryable_exceptions=(StateTimeoutError, ConnectionError, IOError),
            context={"operation": "state_operation"}
        )
    
    @staticmethod
    def fallback_to_default_state(primary_state_func, default_state_func):
        """降级到默认状态"""
        try:
            return primary_state_func()
        except Exception as e:
            logger.warning(f"主状态创建失败，使用默认状态: {e}")
            return default_state_func()
    
    @staticmethod
    def validate_state_before_operation(state, operation: str) -> bool:
        """操作前验证状态"""
        try:
            if state is None:
                raise StateValidationError("状态对象不能为None")
            
            # 检查状态的基本功能
            if not hasattr(state, 'to_dict'):
                raise StateValidationError("状态对象缺少 to_dict 方法")
            
            if not hasattr(state, 'get_id'):
                raise StateValidationError("状态对象缺少 get_id 方法")
            
            # 测试状态序列化
            try:
                state_dict = state.to_dict()
                import json
                json.dumps(state_dict)
            except Exception as e:
                raise StateValidationError(f"状态数据无法序列化: {e}")
            
            return True
        except Exception as e:
            logger.error(f"状态验证失败 (操作: {operation}): {e}")
            return False
    
    @staticmethod
    def cleanup_old_states(state_manager, max_age_seconds: int = 3600):
        """清理旧状态"""
        try:
            # 这里应该实现具体的清理逻辑
            # 例如：删除超过指定时间的状态
            logger.info(f"开始清理超过 {max_age_seconds} 秒的旧状态")
            # 实际实现取决于具体的状态管理器接口
        except Exception as e:
            logger.error(f"清理旧状态失败: {e}")


class StateConsistencyChecker:
    """状态一致性检查器"""
    
    @staticmethod
    def check_state_consistency(state) -> Dict[str, Any]:
        """检查状态一致性"""
        issues = []
        
        try:
            # 检查状态ID
            if hasattr(state, 'get_id'):
                state_id = state.get_id()
                if not state_id:
                    issues.append("状态ID为空")
            else:
                issues.append("状态对象缺少 get_id 方法")
            
            # 检查状态数据
            if hasattr(state, 'to_dict'):
                state_dict = state.to_dict()
                if not isinstance(state_dict, dict):
                    issues.append("状态数据不是字典类型")
                elif 'data' not in state_dict:
                    issues.append("状态数据缺少 'data' 字段")
            else:
                issues.append("状态对象缺少 to_dict 方法")
            
            # 检查时间戳
            if hasattr(state, 'get_created_at') and hasattr(state, 'get_updated_at'):
                created_at = state.get_created_at()
                updated_at = state.get_updated_at()
                if created_at and updated_at and updated_at < created_at:
                    issues.append("更新时间早于创建时间")
            
            return {
                "consistent": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "consistent": False,
                "issues": [f"一致性检查失败: {e}"]
            }


# 注册状态错误处理器
def register_state_error_handler():
    """注册状态错误处理器到全局注册表"""
    state_handler = StateErrorHandler()
    
    # 注册各种状态异常的处理器
    register_error_handler(StateError, state_handler)
    register_error_handler(StateValidationError, state_handler)
    register_error_handler(StateNotFoundError, state_handler)
    register_error_handler(StateTimeoutError, state_handler)
    register_error_handler(StateCapacityError, state_handler)
    register_error_handler(HistoryError, state_handler)
    
    logger.info("状态错误处理器已注册到全局注册表")


# 自动注册
register_state_error_handler()