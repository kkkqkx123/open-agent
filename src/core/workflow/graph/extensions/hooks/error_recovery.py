"""错误恢复Hook

提供错误处理和恢复功能。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult
from .base import ConfigurableHook

logger = get_logger(__name__)


class ErrorRecoveryHook(ConfigurableHook):
    """错误恢复Hook
    
    提供错误处理和恢复功能，包括错误分类、重试机制和恢复策略。
    """
    
    def __init__(self):
        """初始化错误恢复Hook"""
        super().__init__(
            hook_id="error_recovery",
            name="错误恢复Hook",
            description="提供错误处理和恢复功能，包括错误分类、重试机制和恢复策略",
            version="1.0.0"
        )
        
        # 设置默认配置
        self.set_default_config({
            "enable_retry": True,
            "max_retry_count": 3,
            "retry_delay": 1.0,
            "retry_backoff_factor": 2.0,
            "enable_error_classification": True,
            "enable_auto_recovery": True,
            "recovery_strategies": {}
        })
        
        self._retry_counts: Dict[str, int] = {}
        self._error_history: List[Dict[str, Any]] = []
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点"""
        return [HookPoint.ON_ERROR]
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """处理错误并尝试恢复"""
        if not context.error:
            return HookExecutionResult(should_continue=True)
        
        error_info = self._classify_error(context.error)
        node_type = context.node_type or "unknown"
        
        # 记录错误
        self._record_error(context, error_info)
        
        # 尝试自动恢复
        if self.get_config_value("enable_auto_recovery"):
            recovery_result = self._attempt_recovery(context, error_info)
            if recovery_result:
                self._log_execution(HookPoint.ON_ERROR, error=context.error)
                return recovery_result
        
        # 检查是否应该重试
        if self.get_config_value("enable_retry") and self._should_retry(node_type, error_info):
            retry_count = self._retry_counts.get(node_type, 0) + 1
            self._retry_counts[node_type] = retry_count
            
            if retry_count <= self.get_config_value("max_retry_count", 3):
                logger.info(f"准备重试节点 {node_type}，第 {retry_count} 次重试")
                
                # 计算重试延迟
                delay = self._calculate_retry_delay(retry_count)
                
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node=node_type,  # 重试同一个节点
                    metadata={
                        "retry_requested": True,
                        "retry_count": retry_count,
                        "retry_delay": delay,
                        "error_info": error_info
                    }
                )
        
        # 无法恢复，传递到错误处理器
        self._log_execution(HookPoint.ON_ERROR, error=context.error)
        return HookExecutionResult(
            should_continue=False,
            force_next_node="error_handler",
            metadata={
                "error_recovery_failed": True,
                "error_info": error_info,
                "retry_count": self._retry_counts.get(node_type, 0)
            }
        )
    
    def _classify_error(self, error: Exception) -> Dict[str, Any]:
        """分类错误
        
        Args:
            error: 错误对象
            
        Returns:
            Dict[str, Any]: 错误分类信息
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 基本分类
        classification = {
            "type": error_type,
            "message": error_message,
            "category": "unknown",
            "severity": "medium",
            "recoverable": False,
            "retryable": False
        }
        
        # 根据错误类型进行分类
        if self.get_config_value("enable_error_classification", True):
            if "timeout" in error_type.lower() or "timeout" in error_message.lower():
                classification.update({
                    "category": "timeout",
                    "severity": "high",
                    "recoverable": True,
                    "retryable": True
                })
            elif "connection" in error_type.lower() or "network" in error_message.lower():
                classification.update({
                    "category": "network",
                    "severity": "high",
                    "recoverable": True,
                    "retryable": True
                })
            elif "permission" in error_type.lower() or "access" in error_message.lower():
                classification.update({
                    "category": "permission",
                    "severity": "high",
                    "recoverable": False,
                    "retryable": False
                })
            elif "value" in error_type.lower() or "key" in error_message.lower():
                classification.update({
                    "category": "data",
                    "severity": "medium",
                    "recoverable": True,
                    "retryable": False
                })
            elif "memory" in error_type.lower() or "memory" in error_message.lower():
                classification.update({
                    "category": "resource",
                    "severity": "high",
                    "recoverable": True,
                    "retryable": True
                })
        
        return classification
    
    def _record_error(self, context: HookContext, error_info: Dict[str, Any]) -> None:
        """记录错误信息
        
        Args:
            context: Hook执行上下文
            error_info: 错误分类信息
        """
        error_record = {
            "timestamp": context.metadata.get("timestamp") if context.metadata else None,
            "node_type": context.node_type,
            "error_type": error_info["type"],
            "error_message": error_info["message"],
            "category": error_info["category"],
            "severity": error_info["severity"],
            "state_summary": self._get_state_summary(context.state)
        }
        
        self._error_history.append(error_record)
        
        # 限制历史记录长度
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-500:]
    
    def _attempt_recovery(self, context: HookContext, error_info: Dict[str, Any]) -> Optional[HookExecutionResult]:
        """尝试自动恢复
        
        Args:
            context: Hook执行上下文
            error_info: 错误分类信息
            
        Returns:
            Optional[HookExecutionResult]: 恢复结果，如果无法恢复则返回None
        """
        recovery_strategies = self.get_config_value("recovery_strategies", {})
        category = error_info["category"]
        
        if category in recovery_strategies:
            strategy = recovery_strategies[category]
            action = strategy.get("action")
            
            if action == "retry":
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node=context.node_type,
                    metadata={
                        "recovery_action": "retry",
                        "strategy": strategy
                    }
                )
            elif action == "skip":
                return HookExecutionResult(
                    should_continue=True,
                    force_next_node=strategy.get("next_node", "next"),
                    metadata={
                        "recovery_action": "skip",
                        "strategy": strategy
                    }
                )
            elif action == "fallback":
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node=strategy.get("fallback_node", "fallback"),
                    metadata={
                        "recovery_action": "fallback",
                        "strategy": strategy
                    }
                )
        
        return None
    
    def _should_retry(self, node_type: str, error_info: Dict[str, Any]) -> bool:
        """判断是否应该重试
        
        Args:
            node_type: 节点类型
            error_info: 错误分类信息
            
        Returns:
            bool: 是否应该重试
        """
        # 检查错误是否可重试
        if not error_info.get("retryable", False):
            return False
        
        # 检查重试次数
        current_retry_count = self._retry_counts.get(node_type, 0)
        max_retry_count = self.get_config_value("max_retry_count", 3)
        
        return current_retry_count < max_retry_count
    
    def _calculate_retry_delay(self, retry_count: int) -> float:
        """计算重试延迟
        
        Args:
            retry_count: 重试次数
            
        Returns:
            float: 重试延迟（秒）
        """
        base_delay = self.get_config_value("retry_delay", 1.0)
        backoff_factor = self.get_config_value("retry_backoff_factor", 2.0)
        
        return base_delay * (backoff_factor ** (retry_count - 1))
    
    def _get_state_summary(self, state: Any) -> Dict[str, Any]:
        """获取状态摘要"""
        try:
            if state is None:
                return {"type": "None"}
            
            summary = {"type": type(state).__name__}
            
            if hasattr(state, 'messages'):
                summary["message_count"] = str(len(state.messages))
            
            if hasattr(state, 'iteration_count'):
                summary["iteration_count"] = str(state.iteration_count)
            
            return summary
        except Exception:
            return {"error": "Failed to summarize state"}
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            Dict[str, Any]: 错误统计信息
        """
        if not self._error_history:
            return {"total_errors": 0}
        
        # 统计错误类型
        error_types = {}
        error_categories = {}
        error_severities = {}
        
        for record in self._error_history:
            # 统计错误类型
            error_type = record["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # 统计错误类别
            category = record["category"]
            error_categories[category] = error_categories.get(category, 0) + 1
            
            # 统计错误严重程度
            severity = record["severity"]
            error_severities[severity] = error_severities.get(severity, 0) + 1
        
        return {
            "total_errors": len(self._error_history),
            "error_types": error_types,
            "error_categories": error_categories,
            "error_severities": error_severities,
            "retry_counts": self._retry_counts.copy()
        }
    
    def clear_error_history(self) -> None:
        """清空错误历史"""
        self._error_history.clear()
        self._retry_counts.clear()
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置"""
        errors = super().validate_config(config)
        
        # 验证max_retry_count
        max_retry = config.get("max_retry_count")
        if max_retry is not None and (not isinstance(max_retry, int) or max_retry < 0):
            errors.append("max_retry_count必须是非负整数")
        
        # 验证retry_delay
        retry_delay = config.get("retry_delay")
        if retry_delay is not None and (not isinstance(retry_delay, (int, float)) or retry_delay < 0):
            errors.append("retry_delay必须是非负数字")
        
        # 验证retry_backoff_factor
        backoff_factor = config.get("retry_backoff_factor")
        if backoff_factor is not None and (not isinstance(backoff_factor, (int, float)) or backoff_factor < 1):
            errors.append("retry_backoff_factor必须是大于等于1的数字")
        
        return errors