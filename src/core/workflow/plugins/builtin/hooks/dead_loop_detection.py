"""死循环检测插件

检测节点执行过程中的死循环情况。
"""

import logging
from typing import Dict, Any, List, Optional

from src.interfaces.workflow.plugins import IHookPlugin, PluginMetadata, PluginContext, HookContext, HookPoint, HookExecutionResult, PluginType


logger = logging.getLogger(__name__)


class DeadLoopDetectionPlugin(IHookPlugin):
    """死循环检测插件
    
    检测节点执行过程中的死循环情况，防止无限循环。
    """
    
    def __init__(self):
        """初始化死循环检测插件"""
        self._config = {}
        self._execution_service = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return PluginMetadata(
            name="dead_loop_detection",
            version="1.0.0",
            description="检测节点执行过程中的死循环情况，防止无限循环",
            author="system",
            plugin_type=PluginType.HOOK,
            supported_hook_points=[HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR],
            config_schema={
                "type": "object",
                "properties": {
                    "max_iterations": {
                        "type": "integer",
                        "description": "最大迭代次数",
                        "default": 20,
                        "minimum": 1
                    },
                    "fallback_node": {
                        "type": "string",
                        "description": "回退节点名称",
                        "default": "dead_loop_check"
                    },
                    "log_level": {
                        "type": "string",
                        "description": "日志级别",
                        "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                        "default": "WARNING"
                    },
                    "check_interval": {
                        "type": "integer",
                        "description": "检查间隔",
                        "default": 1,
                        "minimum": 1
                    },
                    "reset_on_success": {
                        "type": "boolean",
                        "description": "成功时重置计数",
                        "default": True
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
            "max_iterations": config.get("max_iterations", 20),
            "fallback_node": config.get("fallback_node", "dead_loop_check"),
            "log_level": config.get("log_level", "WARNING"),
            "check_interval": config.get("check_interval", 1),
            "reset_on_success": config.get("reset_on_success", True)
        }
        
        logger.debug("死循环检测插件初始化完成")
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
        """节点执行前检查死循环"""
        # 获取执行服务中的执行计数
        if not self._execution_service:
            return HookExecutionResult(should_continue=True)

        execution_count = self._execution_service.get_execution_count(context.node_type)
        
        # 每隔一定间隔检查一次
        if execution_count % self._config["check_interval"] == 0 and execution_count > 0:
            if execution_count >= self._config["max_iterations"]:
                log_message = (
                    f"节点 {context.node_type} 可能陷入死循环，"
                    f"执行次数: {execution_count}, 最大允许: {self._config['max_iterations']}"
                )
                
                log_level = self._config["log_level"]
                if log_level == "WARNING":
                    logger.warning(log_message)
                elif log_level == "ERROR":
                    logger.error(log_message)
                else:
                    logger.info(log_message)
                
                # 强制切换到回退节点
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node=self._config["fallback_node"],
                    metadata={
                        "dead_loop_detected": True,
                        "execution_count": execution_count,
                        "max_iterations": self._config["max_iterations"]
                    }
                )
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后更新计数"""
        if self._execution_service:
            self._execution_service.increment_execution_count(context.node_type)
        
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误时不重置计数"""
        return HookExecutionResult(should_continue=True)
    
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
        self._execution_service = service