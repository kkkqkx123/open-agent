"""日志Hook

提供节点执行过程中的日志记录功能。
"""

from src.interfaces.dependency_injection import get_logger
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult
from .base import ConfigurableHook

logger = get_logger(__name__)


class LoggingHook(ConfigurableHook):
    """日志Hook
    
    提供节点执行过程中的日志记录功能，支持结构化日志和多种格式。
    """
    
    def __init__(self):
        """初始化日志Hook"""
        super().__init__(
            hook_id="logging",
            name="日志Hook",
            description="提供节点执行过程中的日志记录功能，支持结构化日志和多种格式",
            version="1.0.0"
        )
        
        # 设置默认配置
        self.set_default_config({
            "log_level": "INFO",
            "structured_logging": True,
            "log_execution_time": True,
            "log_state_changes": False,
            "log_format": "json"
        })
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点"""
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行开始日志"""
        log_data: Dict[str, Any] = {
            "event": "node_execution_started",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.get_config_value("log_state_changes"):
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data)
        
        self._log_execution(HookPoint.BEFORE_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行完成日志"""
        log_data: Dict[str, Any] = {
            "event": "node_execution_completed",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.get_config_value("log_execution_time") and context.metadata:
            execution_time = context.metadata.get("execution_time")
            if execution_time:
                log_data["execution_time"] = execution_time

        if context.execution_result and context.execution_result.next_node:
            log_data["next_node"] = context.execution_result.next_node

        if self.get_config_value("log_state_changes"):
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data)
        
        self._log_execution(HookPoint.AFTER_EXECUTE)
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误日志"""
        log_data: Dict[str, Any] = {
            "event": "node_execution_error",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(context.error) if context.error else "Unknown error",
            "error_type": context.error.__class__.__name__ if context.error else "Unknown"
        }

        if self.get_config_value("log_state_changes"):
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data, level="ERROR")
        
        self._log_execution(HookPoint.ON_ERROR, error=context.error)
        return HookExecutionResult(should_continue=True)
    
    def _get_state_summary(self, state: Any) -> Dict[str, Any]:
        """获取状态摘要"""
        try:
            summary = {
                "message_count": len(getattr(state, 'messages', [])),
                "iteration_count": getattr(state, 'iteration_count', 0),
                "has_errors": bool(getattr(state, 'errors', []))
            }
            
            if hasattr(state, 'context') and state.context:
                summary["context_keys"] = list(state.context.keys())
            
            return summary
        except Exception:
            return {"error": "Failed to summarize state"}
    
    def _log(self, log_data: Dict[str, Any], level: Optional[str] = None) -> None:
        """记录日志"""
        log_level = level or self.get_config_value("log_level", "INFO")
        
        if self.get_config_value("structured_logging", True):
            if self.get_config_value("log_format", "json") == "json":
                message = json.dumps(log_data, ensure_ascii=False)
            else:
                message = " | ".join([f"{k}={v}" for k, v in log_data.items()])
        else:
            message = f"{log_data.get('event', 'unknown')} - {log_data.get('node_type', 'unknown')}"
        
        if log_level == "DEBUG":
            logger.debug(message)
        elif log_level == "INFO":
            logger.info(message)
        elif log_level == "WARNING":
            logger.warning(message)
        elif log_level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置"""
        errors = super().validate_config(config)
        
        # 验证log_level
        log_level = config.get("log_level")
        if log_level is not None and log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            errors.append("log_level必须是DEBUG、INFO、WARNING或ERROR之一")
        
        # 验证log_format
        log_format = config.get("log_format")
        if log_format is not None and log_format not in ["json", "key_value"]:
            errors.append("log_format必须是json或key_value之一")
        
        return errors