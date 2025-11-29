"""错误恢复插件

提供节点执行过程中的错误恢复和重试机制。
"""

import logging
import time
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.plugins import IHookPlugin, PluginMetadata, PluginContext, HookContext, HookPoint, HookExecutionResult, PluginType


logger = logging.getLogger(__name__)


class ErrorRecoveryPlugin(IHookPlugin):
    """错误恢复插件
    
    提供节点执行过程中的错误恢复和重试机制。
    """
    
    def __init__(self):
        """初始化错误恢复插件"""
        self._config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="error_recovery",
            version="1.0.0",
            description="提供节点执行过程中的错误恢复和重试机制",
            author="system",
            plugin_type=PluginType.HOOK,
            supported_hook_points=[HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR],
            config_schema={
                "type": "object",
                "properties": {
                    "max_retries": {
                        "type": "integer",
                        "description": "最大重试次数",
                        "default": 3,
                        "minimum": 0
                    },
                    "fallback_node": {
                        "type": "string",
                        "description": "回退节点名称",
                        "default": "error_handler"
                    },
                    "retry_delay": {
                        "type": "number",
                        "description": "重试延迟（秒）",
                        "default": 1.0,
                        "minimum": 0.0
                    },
                    "exponential_backoff": {
                        "type": "boolean",
                        "description": "是否使用指数退避",
                        "default": True
                    },
                    "retry_on_exceptions": {
                        "type": "array",
                        "description": "需要重试的异常类型",
                        "default": ["Exception"]
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
            "max_retries": config.get("max_retries", 3),
            "fallback_node": config.get("fallback_node", "error_handler"),
            "retry_delay": config.get("retry_delay", 1.0),
            "exponential_backoff": config.get("exponential_backoff", True),
            "retry_on_exceptions": config.get("retry_on_exceptions", ["Exception"])
        }
        
        logger.debug("错误恢复插件初始化完成")
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
        """检查重试次数"""
        if not context.metadata:
            context.metadata = {}
        
        retry_count = context.metadata.get("retry_count", 0)
        
        if retry_count >= self._config["max_retries"]:
            logger.error(
                f"节点 {context.node_type} 重试次数已达上限: {retry_count}/{self._config['max_retries']}"
            )
            return HookExecutionResult(
                should_continue=False,
                force_next_node=self._config["fallback_node"],
                metadata={
                    "max_retries_exceeded": True,
                    "retry_count": retry_count
                }
            )
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """成功执行后重置重试计数"""
        if context.metadata and "retry_count" in context.metadata:
            context.metadata["retry_count"] = 0
        
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理和重试逻辑"""
        if not context.metadata:
            context.metadata = {}
        
        error = context.error
        if not error:
            return HookExecutionResult(should_continue=True)
        
        # 检查是否是需要重试的异常类型
        should_retry = any(
            error.__class__.__name__ in exception_types 
            for exception_types in self._config["retry_on_exceptions"]
            if isinstance(exception_types, list)
        ) or any(
            error.__class__.__name__ == exception_type
            for exception_type in self._config["retry_on_exceptions"]
            if isinstance(exception_type, str)
        )
        
        if not should_retry:
            logger.error(f"节点 {context.node_type} 发生不可重试错误: {error}")
            return HookExecutionResult(
                should_continue=False,
                force_next_node=self._config["fallback_node"],
                metadata={"unrecoverable_error": True, "error": str(error)}
            )
        
        # 增加重试计数
        retry_count = context.metadata.get("retry_count", 0) + 1
        context.metadata["retry_count"] = retry_count
        
        if retry_count >= self._config["max_retries"]:
            logger.error(
                f"节点 {context.node_type} 重试次数已达上限: {retry_count}/{self._config['max_retries']}"
            )
            return HookExecutionResult(
                should_continue=False,
                force_next_node=self._config["fallback_node"],
                metadata={
                    "max_retries_exceeded": True,
                    "retry_count": retry_count,
                    "last_error": str(error)
                }
            )
        
        # 计算延迟时间
        if self._config["exponential_backoff"]:
            delay = self._config["retry_delay"] * (2 ** (retry_count - 1))
        else:
            delay = self._config["retry_delay"]
        
        logger.warning(
            f"节点 {context.node_type} 第 {retry_count} 次重试，"
            f"延迟 {delay:.1f}s，错误: {error}"
        )
        
        # 等待延迟时间
        time.sleep(delay)
        
        return HookExecutionResult(
            should_continue=True,
            metadata={
                "retry_scheduled": True,
                "retry_count": retry_count,
                "retry_delay": delay
            }
        )
    
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
        pass  # ErrorRecovery插件不需要执行服务