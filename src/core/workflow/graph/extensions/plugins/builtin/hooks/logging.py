"""日志插件

提供节点执行过程中的日志记录功能。
"""

from src.services.logger.injection import get_logger
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.workflow.plugins import IHookPlugin, PluginMetadata, PluginContext, HookContext, HookPoint, HookExecutionResult, PluginType


logger = get_logger(__name__)


class LoggingPlugin(IHookPlugin):
    """日志插件
    
    提供节点执行过程中的日志记录功能，支持结构化日志和多种格式。
    """
    
    def __init__(self):
        """初始化日志插件"""
        self._config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="logging",
            version="1.0.0",
            description="提供节点执行过程中的日志记录功能，支持结构化日志和多种格式",
            author="system",
            plugin_type=PluginType.HOOK,
            supported_hook_points=[HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR],
            config_schema={
                "type": "object",
                "properties": {
                    "log_level": {
                        "type": "string",
                        "description": "日志级别",
                        "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                        "default": "INFO"
                    },
                    "structured_logging": {
                        "type": "boolean",
                        "description": "是否使用结构化日志",
                        "default": True
                    },
                    "log_execution_time": {
                        "type": "boolean",
                        "description": "是否记录执行时间",
                        "default": True
                    },
                    "log_state_changes": {
                        "type": "boolean",
                        "description": "是否记录状态变化",
                        "default": False
                    },
                    "log_format": {
                        "type": "string",
                        "description": "日志格式",
                        "enum": ["json", "key_value"],
                        "default": "json"
                    }
                },
                "required": []
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        self._config = {
            "log_level": config.get("log_level", "INFO"),
            "structured_logging": config.get("structured_logging", True),
            "log_execution_time": config.get("log_execution_time", True),
            "log_state_changes": config.get("log_state_changes", False),
            "log_format": config.get("log_format", "json")
        }
        
        logger.debug("日志插件初始化完成")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        """执行插件逻辑（Hook插件通常不使用此方法）
        
        Args:
            state: 当前工作流状态
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        return state
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行开始日志"""
        log_data: Dict[str, Any] = {
            "event": "node_execution_started",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self._config["log_state_changes"]:
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data)
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行完成日志"""
        log_data: Dict[str, Any] = {
            "event": "node_execution_completed",
            "node_type": context.node_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self._config["log_execution_time"] and context.metadata:
            execution_time = context.metadata.get("execution_time")
            if execution_time:
                log_data["execution_time"] = execution_time

        if context.execution_result and context.execution_result.next_node:
            log_data["next_node"] = context.execution_result.next_node

        if self._config["log_state_changes"]:
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data)
        
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

        if self._config["log_state_changes"]:
            log_data["state_summary"] = self._get_state_summary(context.state)
        
        self._log(log_data, level="ERROR")
        
        return HookExecutionResult(should_continue=True)
    
    def _get_state_summary(self, state) -> Dict[str, Any]:
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
        log_level = level or self._config["log_level"]
        
        if self._config["structured_logging"]:
            if self._config["log_format"] == "json":
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
    
    def cleanup(self) -> bool:
        """清理插件资源
        
        Returns:
            bool: 清理是否成功
        """
        self._config.clear()
        return True
    
    def set_execution_service(self, service) -> None:
        """设置执行服务
        
        Args:
            service: Hook执行服务实例
        """
        pass  # Logging插件不需要执行服务