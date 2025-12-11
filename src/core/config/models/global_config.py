"""全局配置模型"""

from typing import List, Optional
from pydantic import Field, field_validator

from .base import BaseConfig


class LogOutputConfig(BaseConfig):
    """日志输出配置"""

    type: str = Field(..., description="输出类型：console, file")
    level: str = Field("INFO", description="日志级别")
    format: str = Field("text", description="日志格式：text, json")
    path: Optional[str] = Field(None, description="文件路径（仅文件输出）")

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


class GlobalConfig(BaseConfig):
    """全局配置模型"""

    # 日志配置
    log_level: str = Field("INFO", description="全局日志级别")
    log_outputs: List[LogOutputConfig] = Field(
        default_factory=list, description="日志输出配置列表"
    )

    # 环境配置
    env: str = Field("development", description="运行环境")
    debug: bool = Field(False, description="调试模式")

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