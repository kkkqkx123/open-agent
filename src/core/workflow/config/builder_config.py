"""构建器配置系统

提供统一的构建器配置管理，支持灵活的配置选项和环境适配。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum


class ErrorHandlingStrategy(Enum):
    """错误处理策略"""
    FAIL_FAST = "fail_fast"
    LOG_AND_CONTINUE = "log_and_continue"
    RETRY = "retry"
    IGNORE = "ignore"


class BuildStrategy(Enum):
    """构建策略"""
    LAZY = "lazy"
    EAGER = "eager"
    CACHED = "cached"
    PARALLEL = "parallel"


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationConfig:
    """验证配置"""
    enabled: bool = True
    strict_mode: bool = False
    fail_on_warning: bool = False
    disabled_rules: List[str] = field(default_factory=list)
    custom_rules: Dict[str, str] = field(default_factory=dict)  # rule_name -> rule_class_path


@dataclass
class CachingConfig:
    """缓存配置"""
    enabled: bool = True
    max_size: int = 1000
    ttl_seconds: Optional[int] = None
    cache_key_func: Optional[str] = None  # function_path
    clear_on_error: bool = True


@dataclass
class RetryConfig:
    """重试配置"""
    enabled: bool = False
    max_attempts: int = 3
    delay_seconds: float = 0.1
    backoff_factor: float = 2.0
    retry_on_exceptions: List[str] = field(default_factory=lambda: ["Exception"])


@dataclass
class LoggingConfig:
    """日志配置"""
    enabled: bool = True
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_build_details: bool = True
    log_performance_metrics: bool = False
    custom_handlers: List[str] = field(default_factory=list)


@dataclass
class PerformanceConfig:
    """性能配置"""
    parallel_building: bool = False
    max_workers: int = 4
    timeout_seconds: Optional[int] = None
    memory_limit_mb: Optional[int] = None
    enable_profiling: bool = False


@dataclass
class BuilderConfig:
    """统一构建器配置
    
    包含所有构建器相关的配置选项。
    """
    
    # 基础配置
    name: str = "default"
    description: str = ""
    environment: str = "development"  # development, testing, production
    
    # 功能开关
    enable_validation: bool = True
    enable_caching: bool = True
    enable_logging: bool = True
    enable_monitoring: bool = False
    enable_retry: bool = False
    
    # 构建策略
    build_strategy: BuildStrategy = BuildStrategy.LAZY
    error_handling: ErrorHandlingStrategy = ErrorHandlingStrategy.LOG_AND_CONTINUE
    
    # 子配置
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # 扩展配置
    custom_builders: Dict[str, str] = field(default_factory=dict)  # element_type -> builder_class_path
    plugin_directories: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    # 函数解析配置
    function_resolution_order: List[str] = field(default_factory=lambda: [
        "function_registry", "node_registry", "builtin_functions"
    ])
    function_fallback_enabled: bool = True
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuilderConfig":
        """从字典创建配置
        
        Args:
            data: 配置字典
            
        Returns:
            BuilderConfig: 构建器配置实例
        """
        # 处理子配置
        validation_data = data.get("validation", {})
        caching_data = data.get("caching", {})
        retry_data = data.get("retry", {})
        logging_data = data.get("logging", {})
        performance_data = data.get("performance", {})
        
        # 处理枚举类型
        build_strategy = BuildStrategy(data.get("build_strategy", "lazy"))
        error_handling = ErrorHandlingStrategy(data.get("error_handling", "log_and_continue"))
        log_level = LogLevel(logging_data.get("level", "info"))
        
        return cls(
            # 基础配置
            name=data.get("name", "default"),
            description=data.get("description", ""),
            environment=data.get("environment", "development"),
            
            # 功能开关
            enable_validation=data.get("enable_validation", True),
            enable_caching=data.get("enable_caching", True),
            enable_logging=data.get("enable_logging", True),
            enable_monitoring=data.get("enable_monitoring", False),
            enable_retry=data.get("enable_retry", False),
            
            # 构建策略
            build_strategy=build_strategy,
            error_handling=error_handling,
            
            # 子配置
            validation=ValidationConfig(**validation_data),
            caching=CachingConfig(**caching_data),
            retry=RetryConfig(**retry_data),
            logging=LoggingConfig(
                enabled=logging_data.get("enabled", True),
                level=log_level,
                format=logging_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                log_build_details=logging_data.get("log_build_details", True),
                log_performance_metrics=logging_data.get("log_performance_metrics", False),
                custom_handlers=logging_data.get("custom_handlers", [])
            ),
            performance=PerformanceConfig(**performance_data),
            
            # 扩展配置
            custom_builders=data.get("custom_builders", {}),
            plugin_directories=data.get("plugin_directories", []),
            environment_variables=data.get("environment_variables", {}),
            
            # 函数解析配置
            function_resolution_order=data.get("function_resolution_order", [
                "function_registry", "node_registry", "builtin_functions"
            ]),
            function_fallback_enabled=data.get("function_fallback_enabled", True),
            
            # 元数据
            metadata=data.get("metadata", {}),
            tags=data.get("tags", [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            # 基础配置
            "name": self.name,
            "description": self.description,
            "environment": self.environment,
            
            # 功能开关
            "enable_validation": self.enable_validation,
            "enable_caching": self.enable_caching,
            "enable_logging": self.enable_logging,
            "enable_monitoring": self.enable_monitoring,
            "enable_retry": self.enable_retry,
            
            # 构建策略
            "build_strategy": self.build_strategy.value,
            "error_handling": self.error_handling.value,
            
            # 子配置
            "validation": {
                "enabled": self.validation.enabled,
                "strict_mode": self.validation.strict_mode,
                "fail_on_warning": self.validation.fail_on_warning,
                "disabled_rules": self.validation.disabled_rules,
                "custom_rules": self.validation.custom_rules,
            },
            "caching": {
                "enabled": self.caching.enabled,
                "max_size": self.caching.max_size,
                "ttl_seconds": self.caching.ttl_seconds,
                "cache_key_func": self.caching.cache_key_func,
                "clear_on_error": self.caching.clear_on_error,
            },
            "retry": {
                "enabled": self.retry.enabled,
                "max_attempts": self.retry.max_attempts,
                "delay_seconds": self.retry.delay_seconds,
                "backoff_factor": self.retry.backoff_factor,
                "retry_on_exceptions": self.retry.retry_on_exceptions,
            },
            "logging": {
                "enabled": self.logging.enabled,
                "level": self.logging.level.value,
                "format": self.logging.format,
                "log_build_details": self.logging.log_build_details,
                "log_performance_metrics": self.logging.log_performance_metrics,
                "custom_handlers": self.logging.custom_handlers,
            },
            "performance": {
                "parallel_building": self.performance.parallel_building,
                "max_workers": self.performance.max_workers,
                "timeout_seconds": self.performance.timeout_seconds,
                "memory_limit_mb": self.performance.memory_limit_mb,
                "enable_profiling": self.performance.enable_profiling,
            },
            
            # 扩展配置
            "custom_builders": self.custom_builders,
            "plugin_directories": self.plugin_directories,
            "environment_variables": self.environment_variables,
            
            # 函数解析配置
            "function_resolution_order": self.function_resolution_order,
            "function_fallback_enabled": self.function_fallback_enabled,
            
            # 元数据
            "metadata": self.metadata,
            "tags": self.tags,
        }
    
    def merge(self, other: "BuilderConfig") -> "BuilderConfig":
        """合并配置
        
        Args:
            other: 另一个配置实例
            
        Returns:
            BuilderConfig: 合并后的配置
        """
        # 创建新的配置实例
        merged = BuilderConfig()
        
        # 合并基础字段
        for field_name in self.__dataclass_fields__:
            current_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            
            if isinstance(current_value, dict) and isinstance(other_value, dict):
                # 合并字典
                merged_value = {**current_value, **other_value}
            elif isinstance(current_value, list) and isinstance(other_value, list):
                # 合并列表
                merged_value = list(set(current_value + other_value))
            else:
                # 使用其他配置的值（如果非空）
                merged_value = other_value if other_value is not None else current_value
            
            setattr(merged, field_name, merged_value)
        
        return merged
    
    def override_with_environment_variables(self) -> None:
        """使用环境变量覆盖配置"""
        import os
        
        # 定义环境变量映射
        env_mappings = {
            "BUILDER_NAME": ("name", str),
            "BUILDER_ENVIRONMENT": ("environment", str),
            "BUILDER_ENABLE_VALIDATION": ("enable_validation", bool),
            "BUILDER_ENABLE_CACHING": ("enable_caching", bool),
            "BUILDER_ENABLE_LOGGING": ("enable_logging", bool),
            "BUILDER_BUILD_STRATEGY": ("build_strategy", BuildStrategy),
            "BUILDER_ERROR_HANDLING": ("error_handling", ErrorHandlingStrategy),
            "BUILDER_LOG_LEVEL": ("logging.level", LogLevel),
            "BUILDER_CACHE_MAX_SIZE": ("caching.max_size", int),
            "BUILDER_RETRY_MAX_ATTEMPTS": ("retry.max_attempts", int),
            "BUILDER_PERFORMANCE_MAX_WORKERS": ("performance.max_workers", int),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 转换值类型
                if value_type == bool:
                    converted_value = env_value.lower() in ("true", "1", "yes", "on")
                elif value_type == int:
                    converted_value = int(env_value)
                elif value_type == BuildStrategy:
                    converted_value = BuildStrategy(env_value.lower())
                elif value_type == ErrorHandlingStrategy:
                    converted_value = ErrorHandlingStrategy(env_value.lower())
                elif value_type == LogLevel:
                    converted_value = LogLevel(env_value.lower())
                else:
                    converted_value = env_value
                
                # 设置配置值
                self._set_nested_value(config_path, converted_value)
    
    def _set_nested_value(self, path: str, value: Any) -> None:
        """设置嵌套配置值
        
        Args:
            path: 配置路径，如 "logging.level"
            value: 配置值
        """
        parts = path.split(".")
        current = self
        
        for part in parts[:-1]:
            current = getattr(current, part)
        
        setattr(current, parts[-1], value)
    
    def validate(self) -> List[str]:
        """验证配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证基础配置
        if not self.name:
            errors.append("构建器名称不能为空")
        
        if self.environment not in ["development", "testing", "production"]:
            errors.append(f"无效的环境: {self.environment}")
        
        # 验证性能配置
        if self.performance.max_workers <= 0:
            errors.append("最大工作线程数必须大于0")
        
        if self.performance.memory_limit_mb is not None and self.performance.memory_limit_mb <= 0:
            errors.append("内存限制必须大于0")
        
        # 验证重试配置
        if self.retry.max_attempts <= 0:
            errors.append("最大重试次数必须大于0")
        
        if self.retry.delay_seconds < 0:
            errors.append("重试延迟不能为负数")
        
        # 验证缓存配置
        if self.caching.max_size <= 0:
            errors.append("缓存大小必须大于0")
        
        return errors
    
    def create_for_environment(self, environment: str) -> "BuilderConfig":
        """为特定环境创建配置
        
        Args:
            environment: 环境名称
            
        Returns:
            BuilderConfig: 环境特定的配置
        """
        # 创建配置副本
        env_config = BuilderConfig(
            name=f"{self.name}_{environment}",
            environment=environment
        )
        
        # 根据环境调整配置
        if environment == "production":
            env_config.enable_validation = True
            env_config.validation.strict_mode = True
            env_config.enable_logging = True
            env_config.logging.level = LogLevel.WARNING
            env_config.enable_monitoring = True
            env_config.performance.parallel_building = True
        elif environment == "testing":
            env_config.enable_validation = True
            env_config.validation.strict_mode = False
            env_config.enable_logging = True
            env_config.logging.level = LogLevel.DEBUG
            env_config.enable_caching = False
            env_config.enable_retry = False
        else:  # development
            env_config.enable_validation = True
            env_config.validation.strict_mode = False
            env_config.enable_logging = True
            env_config.logging.level = LogLevel.DEBUG
            env_config.logging.log_build_details = True
        
        return env_config


# 预定义配置
DEVELOPMENT_CONFIG = BuilderConfig(
    name="development",
    environment="development",
    enable_validation=True,
    enable_caching=True,
    enable_logging=True,
    logging=LoggingConfig(level=LogLevel.DEBUG, log_build_details=True),
    performance=PerformanceConfig(parallel_building=False)
)

TESTING_CONFIG = BuilderConfig(
    name="testing",
    environment="testing",
    enable_validation=True,
    enable_caching=False,
    enable_logging=True,
    logging=LoggingConfig(level=LogLevel.DEBUG),
    performance=PerformanceConfig(parallel_building=False),
    retry=RetryConfig(enabled=False)
)

PRODUCTION_CONFIG = BuilderConfig(
    name="production",
    environment="production",
    enable_validation=True,
    enable_caching=True,
    enable_logging=True,
    logging=LoggingConfig(level=LogLevel.WARNING),
    performance=PerformanceConfig(parallel_building=True, max_workers=8),
    validation=ValidationConfig(strict_mode=True),
    enable_monitoring=True
)


def get_config_for_environment(environment: str) -> BuilderConfig:
    """获取环境特定的配置
    
    Args:
        environment: 环境名称
        
    Returns:
        BuilderConfig: 环境特定的配置
    """
    configs = {
        "development": DEVELOPMENT_CONFIG,
        "testing": TESTING_CONFIG,
        "production": PRODUCTION_CONFIG,
    }
    
    base_config = configs.get(environment, DEVELOPMENT_CONFIG)
    return base_config.create_for_environment(environment)