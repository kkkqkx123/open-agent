"""全局配置模型"""

from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator

from ..base import BaseConfig
from .checkpoint_config import CheckpointConfig


class LogOutputConfig(BaseConfig):
    """日志输出配置"""

    type: str = Field(..., description="输出类型：console, file")
    level: str = Field("INFO", description="日志级别")
    format: str = Field("text", description="日志格式：text, json")
    path: Optional[str] = Field(None, description="文件路径（仅文件输出）")
    rotation: Optional[str] = Field(None, description="轮转策略：daily, weekly, size")
    max_size: Optional[str] = Field(None, description="最大文件大小")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """验证输出类型"""
        allowed_types = ["console", "file"]
        if v not in allowed_types:
            raise ValueError(f"输出类型必须是以下之一: {allowed_types}")
        return v

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"日志级别必须是以下之一: {allowed_levels}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """验证日志格式"""
        allowed_formats = ["text", "json"]
        if v not in allowed_formats:
            raise ValueError(f"日志格式必须是以下之一: {allowed_formats}")
        return v


class LLMGlobalConfig(BaseConfig):
    """LLM全局配置"""

    # 默认超时和重试配置
    default_timeout: int = Field(30, description="默认超时时间（秒）", ge=1, le=300)
    default_max_retries: int = Field(3, description="默认最大重试次数", ge=0, le=10)
    
    # 全局重试配置
    retry_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "base_delay": 1.0,
            "max_delay": 60.0,
            "jitter": True,
            "exponential_base": 2.0,
            "retry_on_status_codes": [429, 500, 502, 503, 504],
            "retry_on_errors": ["timeout", "rate_limit", "service_unavailable"],
        },
        description="全局重试配置"
    )
    
    # 全局超时配置
    timeout_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "request_timeout": 30,
            "connect_timeout": 10,
            "read_timeout": 30,
            "write_timeout": 30,
        },
        description="全局超时配置"
    )
    
    # 性能优化配置
    performance: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_concurrent_requests": 10,
            "request_queue_size": 100,
            "connection_pool_size": 20,
            "connection_keep_alive": True,
        },
        description="性能优化配置"
    )

    @field_validator("retry_config")
    @classmethod
    def validate_retry_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """验证重试配置"""
        if not isinstance(v, dict):
            raise ValueError("retry_config必须是字典")
        
        # 验证基础延迟时间
        if "base_delay" in v:
            base_delay = v["base_delay"]
            if not isinstance(base_delay, (int, float)) or base_delay <= 0:
                raise ValueError("retry_config.base_delay必须是正数")
        
        # 验证最大延迟时间
        if "max_delay" in v:
            max_delay = v["max_delay"]
            if not isinstance(max_delay, (int, float)) or max_delay <= 0:
                raise ValueError("retry_config.max_delay必须是正数")
        
        # 验证指数退避基数
        if "exponential_base" in v:
            exponential_base = v["exponential_base"]
            if not isinstance(exponential_base, (int, float)) or exponential_base <= 1:
                raise ValueError("retry_config.exponential_base必须大于1")
        
        return v

    @field_validator("timeout_config")
    @classmethod
    def validate_timeout_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """验证超时配置"""
        if not isinstance(v, dict):
            raise ValueError("timeout_config必须是字典")
        
        # 验证请求超时时间
        if "request_timeout" in v:
            request_timeout = v["request_timeout"]
            if not isinstance(request_timeout, int) or request_timeout <= 0:
                raise ValueError("timeout_config.request_timeout必须是正整数")
        
        return v


class GlobalConfig(BaseConfig):
    """全局配置模型"""

    # 日志配置
    log_level: str = Field("INFO", description="全局日志级别")
    log_outputs: List[LogOutputConfig] = Field(
        default_factory=list, description="日志输出配置列表"
    )

    # 安全配置
    secret_patterns: List[str] = Field(
        default_factory=list, description="敏感信息正则表达式模式"
    )

    # 环境配置
    env: str = Field("development", description="运行环境")
    debug: bool = Field(False, description="调试模式")
    env_prefix: str = Field("CONFIG_", description="环境变量前缀")

    # 热重载配置
    hot_reload: bool = Field(True, description="是否启用热重载")
    watch_interval: int = Field(5, description="配置监听间隔（秒）")
    
    # LLM全局配置
    llm: LLMGlobalConfig = Field(
        default_factory=lambda: LLMGlobalConfig(
            default_timeout=30,
            default_max_retries=3
        ), description="LLM全局配置"
    )
    
    # Checkpoint配置
    checkpoint: CheckpointConfig = Field(
        default_factory=lambda: CheckpointConfig(
            enabled=True,
            storage_type="sqlite",
            auto_save=True,
            save_interval=5,
            max_checkpoints=100,
            retention_days=30,
            db_path=None,
            compression=False
        ), description="Checkpoint配置"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"日志级别必须是以下之一: {allowed_levels}")
        return v.upper()

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """验证环境名称"""
        allowed_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed_envs:
            raise ValueError(f"环境必须是以下之一: {allowed_envs}")
        return v.lower()

    @field_validator("watch_interval")
    @classmethod
    def validate_watch_interval(cls, v: int) -> int:
        """验证监听间隔"""
        if v < 1:
            raise ValueError("监听间隔必须大于0秒")
        return v

    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return self.env == "production"

    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return self.env == "development"

    def get_log_output_config(self, output_type: str) -> Optional[LogOutputConfig]:
        """获取指定类型的日志输出配置"""
        for output_config in self.log_outputs:
            if output_config.type == output_type:
                return output_config
        return None
    
    def get_llm_config(self) -> LLMGlobalConfig:
        """获取LLM全局配置"""
        return self.llm