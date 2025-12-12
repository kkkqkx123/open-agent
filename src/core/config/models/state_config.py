"""状态管理配置模型"""

from typing import Dict, Any, List
from pydantic import Field, field_validator

from .base import BaseConfig


class StateCoreConfig(BaseConfig):
    """状态管理核心配置"""
    
    default_ttl: int = Field(default=3600, description="默认TTL（秒）")
    max_states: int = Field(default=10000, description="最大状态数")
    cleanup_interval: int = Field(default=300, description="清理间隔（秒）")
    
    @field_validator("default_ttl", "max_states", "cleanup_interval")
    @classmethod
    def validate_positive_integer(cls, v: int) -> int:
        """验证正整数"""
        if v <= 0:
            raise ValueError("必须为正整数")
        return v


class SerializerConfig(BaseConfig):
    """序列化配置"""
    
    format: str = Field(default="json", description="序列化格式")
    compression: bool = Field(default=True, description="是否启用压缩")
    compression_threshold: int = Field(default=1024, description="压缩阈值（字节）")
    
    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """验证序列化格式"""
        allowed_formats = ["json", "pickle", "msgpack"]
        if v not in allowed_formats:
            raise ValueError(f"序列化格式必须是以下之一: {allowed_formats}")
        return v


class CacheConfig(BaseConfig):
    """缓存配置"""
    
    enabled: bool = Field(default=True, description="是否启用缓存")
    max_size: int = Field(default=1000, description="缓存最大大小")
    ttl: int = Field(default=300, description="缓存TTL（秒）")
    eviction_policy: str = Field(default="lru", description="缓存驱逐策略")
    enable_serialization: bool = Field(default=False, description="是否启用序列化")
    serialization_format: str = Field(default="json", description="序列化格式")
    
    @field_validator("eviction_policy")
    @classmethod
    def validate_eviction_policy(cls, v: str) -> str:
        """验证缓存驱逐策略"""
        allowed_policies = ["lru", "lfu", "fifo"]
        if v not in allowed_policies:
            raise ValueError(f"缓存驱逐策略必须是以下之一: {allowed_policies}")
        return v


class StorageTypeConfig(BaseConfig):
    """存储类型配置"""
    
    default_type: str = Field(default="memory", description="默认存储类型")
    
    @field_validator("default_type")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        """验证存储类型"""
        allowed_types = ["memory", "sqlite", "file"]
        if v not in allowed_types:
            raise ValueError(f"存储类型必须是以下之一: {allowed_types}")
        return v


class MemoryStorageConfig(BaseConfig):
    """内存存储配置"""
    
    max_size: int = Field(default=10000, description="最大大小")


class SQLiteStorageConfig(BaseConfig):
    """SQLite存储配置"""
    
    database_path: str = Field(default="data/states.db", description="数据库路径")
    connection_pool_size: int = Field(default=10, description="连接池大小")
    compression: bool = Field(default=True, description="是否启用压缩")
    compression_threshold: int = Field(default=1024, description="压缩阈值")


class FileStorageConfig(BaseConfig):
    """文件存储配置"""
    
    base_path: str = Field(default="data/states", description="基础路径")
    format: str = Field(default="json", description="文件格式")
    compression: bool = Field(default=False, description="是否启用压缩")
    create_subdirs: bool = Field(default=True, description="是否创建子目录")


class StorageConfig(BaseConfig):
    """存储配置"""
    
    default_type: str = Field(default="memory", description="默认存储类型")
    memory: MemoryStorageConfig = Field(default_factory=MemoryStorageConfig)
    sqlite: SQLiteStorageConfig = Field(default_factory=SQLiteStorageConfig)
    file: FileStorageConfig = Field(default_factory=FileStorageConfig)


class ValidationConfig(BaseConfig):
    """验证配置"""
    
    enabled: bool = Field(default=True, description="是否启用验证")
    strict_mode: bool = Field(default=False, description="严格模式")
    custom_validators: List[str] = Field(default_factory=list, description="自定义验证器")


class LifecycleConfig(BaseConfig):
    """生命周期配置"""
    
    auto_cleanup: bool = Field(default=True, description="自动清理")
    cleanup_interval: int = Field(default=300, description="清理间隔")
    event_handlers: List[str] = Field(default_factory=list, description="事件处理器")


class WorkflowConfig(BaseConfig):
    """工作流配置"""
    
    max_iterations: int = Field(default=100, description="最大迭代次数")
    message_history_limit: int = Field(default=1000, description="消息历史限制")
    auto_save: bool = Field(default=True, description="自动保存")


class ToolsConfig(BaseConfig):
    """工具配置"""
    
    context_isolation: bool = Field(default=True, description="上下文隔离")
    auto_expiration: bool = Field(default=True, description="自动过期")
    default_ttl: int = Field(default=1800, description="默认TTL")


class SessionsConfig(BaseConfig):
    """会话配置"""
    
    auto_cleanup: bool = Field(default=True, description="自动清理")
    max_inactive_duration: int = Field(default=3600, description="最大非活动时长")


class ThreadsConfig(BaseConfig):
    """线程配置"""
    
    auto_cleanup: bool = Field(default=True, description="自动清理")
    max_inactive_duration: int = Field(default=7200, description="最大非活动时长")


class CheckpointsConfig(BaseConfig):
    """检查点配置"""
    
    auto_cleanup: bool = Field(default=True, description="自动清理")
    max_checkpoints_per_thread: int = Field(default=50, description="每个线程最大检查点数")
    cleanup_interval: int = Field(default=600, description="清理间隔")


class SpecializedConfig(BaseConfig):
    """特化配置"""
    
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    sessions: SessionsConfig = Field(default_factory=SessionsConfig)
    threads: ThreadsConfig = Field(default_factory=ThreadsConfig)
    checkpoints: CheckpointsConfig = Field(default_factory=CheckpointsConfig)


class MonitoringConfig(BaseConfig):
    """监控配置"""
    
    enabled: bool = Field(default=True, description="是否启用监控")
    statistics_interval: int = Field(default=60, description="统计间隔")
    performance_tracking: bool = Field(default=True, description="性能跟踪")
    memory_tracking: bool = Field(default=True, description="内存跟踪")


class ErrorHandlingConfig(BaseConfig):
    """错误处理配置"""
    
    retry_attempts: int = Field(default=3, description="重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟")
    fallback_to_memory: bool = Field(default=True, description="回退到内存")
    log_errors: bool = Field(default=True, description="记录错误")


class DevelopmentConfig(BaseConfig):
    """开发配置"""
    
    debug_mode: bool = Field(default=False, description="调试模式")
    verbose_logging: bool = Field(default=False, description="详细日志")
    enable_profiling: bool = Field(default=False, description="启用性能分析")
    mock_storage: bool = Field(default=False, description="模拟存储")


class StateConfig(BaseConfig):
    """状态管理配置"""
    
    core: StateCoreConfig = Field(default_factory=StateCoreConfig)
    serializer: SerializerConfig = Field(default_factory=SerializerConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    lifecycle: LifecycleConfig = Field(default_factory=LifecycleConfig)
    specialized: SpecializedConfig = Field(default_factory=SpecializedConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置字典"""
        return self.to_dict()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.to_dict()
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default