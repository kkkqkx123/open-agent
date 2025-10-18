"""全局配置模型"""

from typing import List, Dict, Any, Optional
from pydantic import Field, validator

from .base import BaseConfig


class LogOutputConfig(BaseConfig):
    """日志输出配置"""
    type: str = Field(..., description="输出类型：console, file")
    level: str = Field("INFO", description="日志级别")
    format: str = Field("text", description="日志格式：text, json")
    path: Optional[str] = Field(None, description="文件路径（仅文件输出）")
    rotation: Optional[str] = Field(None, description="轮转策略：daily, weekly, size")
    max_size: Optional[str] = Field(None, description="最大文件大小")
    
    @validator('type')
    def validate_type(cls, v):
        """验证输出类型"""
        allowed_types = ['console', 'file']
        if v not in allowed_types:
            raise ValueError(f'输出类型必须是以下之一: {allowed_types}')
        return v
    
    @validator('level')
    def validate_level(cls, v):
        """验证日志级别"""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'日志级别必须是以下之一: {allowed_levels}')
        return v.upper()
    
    @validator('format')
    def validate_format(cls, v):
        """验证日志格式"""
        allowed_formats = ['text', 'json']
        if v not in allowed_formats:
            raise ValueError(f'日志格式必须是以下之一: {allowed_formats}')
        return v


class GlobalConfig(BaseConfig):
    """全局配置模型"""
    
    # 日志配置
    log_level: str = Field("INFO", description="全局日志级别")
    log_outputs: List[LogOutputConfig] = Field(default_factory=list, description="日志输出配置列表")
    
    # 安全配置
    secret_patterns: List[str] = Field(default_factory=list, description="敏感信息正则表达式模式")
    
    # 环境配置
    env: str = Field("development", description="运行环境")
    debug: bool = Field(False, description="调试模式")
    env_prefix: str = Field("AGENT_", description="环境变量前缀")
    
    # 热重载配置
    hot_reload: bool = Field(True, description="是否启用热重载")
    watch_interval: int = Field(5, description="配置监听间隔（秒）")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """验证日志级别"""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'日志级别必须是以下之一: {allowed_levels}')
        return v.upper()
    
    @validator('env')
    def validate_env(cls, v):
        """验证环境名称"""
        allowed_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in allowed_envs:
            raise ValueError(f'环境必须是以下之一: {allowed_envs}')
        return v.lower()
    
    @validator('watch_interval')
    def validate_watch_interval(cls, v):
        """验证监听间隔"""
        if v < 1:
            raise ValueError('监听间隔必须大于0秒')
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