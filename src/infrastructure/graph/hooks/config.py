"""Hook配置模型

定义Hook系统的配置数据结构和验证逻辑。
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class HookType(str, Enum):
    """Hook类型枚举"""
    DEAD_LOOP_DETECTION = "dead_loop_detection"
    PERFORMANCE_MONITORING = "performance_monitoring"
    ERROR_RECOVERY = "error_recovery"
    LOGGING = "logging"
    METRICS_COLLECTION = "metrics_collection"
    CUSTOM = "custom"


class HookConfig(BaseModel):
    """Hook配置模型"""
    
    type: HookType = Field(..., description="Hook类型")
    enabled: bool = Field(True, description="是否启用")
    config: Dict[str, Any] = Field(default_factory=dict, description="Hook特定配置")
    node_types: Optional[List[str]] = Field(None, description="适用的节点类型列表")
    priority: int = Field(0, description="Hook执行优先级，数值越大优先级越高")
    
    class Config:
        """Pydantic配置"""
        use_enum_values = True
    
    @validator('config')
    def validate_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """验证Hook配置"""
        return v
    
    @validator('priority')
    def validate_priority(cls, v: int) -> int:
        """验证优先级"""
        if v < 0:
            raise ValueError("优先级不能为负数")
        return v


class NodeHookConfig(BaseModel):
    """节点Hook配置"""
    
    node_type: str = Field(..., description="节点类型")
    hooks: List[HookConfig] = Field(default_factory=list, description="Hook配置列表")
    inherit_global: bool = Field(True, description="是否继承全局Hook配置")
    
    @validator('hooks')
    def validate_hooks(cls, v: List[HookConfig]) -> List[HookConfig]:
        """验证Hook列表"""
        # 检查是否有重复类型的Hook
        hook_types = [hook.type for hook in v]
        if len(hook_types) != len(set(hook_types)):
            raise ValueError("节点配置中不能有重复类型的Hook")
        return v


class GlobalHookConfig(BaseModel):
    """全局Hook配置"""
    
    hooks: List[HookConfig] = Field(default_factory=list, description="全局Hook配置列表")
    
    @validator('hooks')
    def validate_hooks(cls, v: List[HookConfig]) -> List[HookConfig]:
        """验证Hook列表"""
        # 检查是否有重复类型的Hook
        hook_types = [hook.type for hook in v]
        if len(hook_types) != len(set(hook_types)):
            raise ValueError("全局配置中不能有重复类型的Hook")
        return v


class HookGroupConfig(BaseModel):
    """Hook组配置"""
    
    enabled: bool = Field(True, description="是否启用")
    config: Dict[str, Any] = Field(default_factory=dict, description="组配置")


class DeadLoopDetectionConfig(HookGroupConfig):
    """死循环检测Hook配置"""
    
    config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_iterations": 20,
            "fallback_node": "dead_loop_check",
            "log_level": "WARNING",
            "check_interval": 1,
            "reset_on_success": True
        },
        description="死循环检测配置"
    )


class PerformanceMonitoringConfig(HookGroupConfig):
    """性能监控Hook配置"""
    
    config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timeout_threshold": 10.0,
            "log_slow_executions": True,
            "metrics_collection": True,
            "slow_execution_threshold": 5.0,
            "enable_profiling": False
        },
        description="性能监控配置"
    )


class ErrorRecoveryConfig(HookGroupConfig):
    """错误恢复Hook配置"""
    
    config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_retries": 3,
            "fallback_node": "error_handler",
            "retry_delay": 1.0,
            "exponential_backoff": True,
            "retry_on_exceptions": ["Exception"]
        },
        description="错误恢复配置"
    )


class LoggingConfig(HookGroupConfig):
    """日志Hook配置"""
    
    config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "log_level": "INFO",
            "structured_logging": True,
            "log_execution_time": True,
            "log_state_changes": False,
            "log_format": "json"
        },
        description="日志配置"
    )


class MetricsCollectionConfig(HookGroupConfig):
    """指标收集Hook配置"""
    
    config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enable_performance_metrics": True,
            "enable_business_metrics": True,
            "enable_system_metrics": False,
            "metrics_endpoint": None,
            "collection_interval": 60
        },
        description="指标收集配置"
    )


# Hook类型到配置类的映射
HOOK_CONFIG_MAPPING = {
    HookType.DEAD_LOOP_DETECTION: DeadLoopDetectionConfig,
    HookType.PERFORMANCE_MONITORING: PerformanceMonitoringConfig,
    HookType.ERROR_RECOVERY: ErrorRecoveryConfig,
    HookType.LOGGING: LoggingConfig,
    HookType.METRICS_COLLECTION: MetricsCollectionConfig,
}


def create_hook_config(hook_type: HookType, **kwargs) -> HookConfig:
    """创建Hook配置
    
    Args:
        hook_type: Hook类型
        **kwargs: 配置参数
        
    Returns:
        HookConfig: Hook配置实例
    """
    # 获取默认配置
    config_class = HOOK_CONFIG_MAPPING.get(hook_type, HookGroupConfig)
    default_config = config_class().config
    
    # 合并用户配置
    merged_config = {**default_config, **kwargs.get('config', {})}
    
    return HookConfig(
        type=hook_type,
        enabled=kwargs.get('enabled', True),
        config=merged_config,
        node_types=kwargs.get('node_types'),
        priority=kwargs.get('priority', 0)
    )


def validate_hook_config(config: Dict[str, Any]) -> List[str]:
    """验证Hook配置
    
    Args:
        config: Hook配置字典
        
    Returns:
        List[str]: 验证错误列表
    """
    errors = []
    
    try:
        HookConfig(**config)
    except Exception as e:
        errors.append(f"Hook配置验证失败: {str(e)}")
    
    return errors


def merge_hook_configs(
    global_config: GlobalHookConfig,
    node_config: NodeHookConfig
) -> List[HookConfig]:
    """合并全局和节点Hook配置
    
    Args:
        global_config: 全局Hook配置
        node_config: 节点Hook配置
        
    Returns:
        List[HookConfig]: 合并后的Hook配置列表
    """
    if not node_config.inherit_global:
        return node_config.hooks.copy()
    
    # 创建Hook类型到配置的映射
    global_hooks = {hook.type: hook for hook in global_config.hooks}
    node_hooks = {hook.type: hook for hook in node_config.hooks}
    
    # 合并配置，节点配置优先级更高
    merged_hooks = {}
    
    # 添加全局Hook
    for hook_type, hook in global_hooks.items():
        if hook_type not in node_hooks:
            merged_hooks[hook_type] = hook
    
    # 添加节点Hook（覆盖全局Hook）
    for hook_type, hook in node_hooks.items():
        merged_hooks[hook_type] = hook
    
    # 按优先级排序
    return sorted(merged_hooks.values(), key=lambda x: x.priority, reverse=True)