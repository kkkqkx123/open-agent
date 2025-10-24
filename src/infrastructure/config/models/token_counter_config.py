"""Token计数器配置模型"""

from typing import Dict, Any, Optional, Union
from pydantic import Field, field_validator, model_validator

from .base import BaseConfig


class TokenCounterCacheConfig(BaseConfig):
    """Token计数器缓存配置"""
    
    ttl_seconds: int = Field(default=3600, description="缓存TTL（秒）")
    max_size: int = Field(default=1000, description="最大缓存条目数")
    
    @field_validator("ttl_seconds")
    @classmethod
    def validate_ttl_seconds(cls, v: int) -> int:
        """验证TTL秒数"""
        if v <= 0:
            raise ValueError("缓存TTL必须大于0")
        return v
    
    @field_validator("max_size")
    @classmethod
    def validate_max_size(cls, v: int) -> int:
        """验证最大缓存大小"""
        if v <= 0:
            raise ValueError("最大缓存大小必须大于0")
        return v


class TokenCounterCalibrationConfig(BaseConfig):
    """Token计数器校准配置"""
    
    min_data_points: int = Field(default=3, description="最小校准数据点数")
    max_data_points: int = Field(default=100, description="最大校准数据点数")
    
    @field_validator("min_data_points")
    @classmethod
    def validate_min_data_points(cls, v: int) -> int:
        """验证最小数据点数"""
        if v <= 0:
            raise ValueError("最小校准数据点数必须大于0")
        return v
    
    @field_validator("max_data_points")
    @classmethod
    def validate_max_data_points(cls, v: int) -> int:
        """验证最大数据点数"""
        if v <= 0:
            raise ValueError("最大校准数据点数必须大于0")
        return v


class TokenCounterMonitoringConfig(BaseConfig):
    """Token计数器监控配置"""
    
    enabled: bool = Field(default=True, description="是否启用监控")
    stats_interval: int = Field(default=300, description="统计信息记录间隔（秒）")
    
    @field_validator("stats_interval")
    @classmethod
    def validate_stats_interval(cls, v: int) -> int:
        """验证统计间隔"""
        if v <= 0:
            raise ValueError("统计信息记录间隔必须大于0")
        return v


class TokenCounterConfig(BaseConfig):
    """Token计数器配置模型"""
    
    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称：gpt-4, gemini-pro等")
    enhanced: bool = Field(default=False, description="是否使用增强版计数器")
    
    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")
    
    # 缓存配置
    cache: Optional[Union[TokenCounterCacheConfig, Dict[str, Any], str]] = Field(default=None, description="缓存配置")
    
    # 校准配置
    calibration: Optional[Union[TokenCounterCalibrationConfig, Dict[str, Any], str]] = Field(default=None, description="校准配置")
    
    # 监控配置
    monitoring: Optional[Union[TokenCounterMonitoringConfig, Dict[str, Any], str]] = Field(default=None, description="监控配置")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """验证模型类型"""
        allowed_types = ["openai", "gemini", "anthropic", "claude", "local"]
        if v.lower() not in allowed_types:
            raise ValueError(f"模型类型必须是以下之一: {allowed_types}")
        return v.lower()
    
    
    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证并转换字段"""
        # 转换cache字段
        cache_value = data.get("cache")
        if isinstance(cache_value, dict):
            data["cache"] = TokenCounterCacheConfig(**cache_value)
        elif isinstance(cache_value, str):
            # 如果是引用字符串，保持原样，在配置系统中处理继承
            pass
        
        # 转换calibration字段
        calibration_value = data.get("calibration")
        if isinstance(calibration_value, dict):
            data["calibration"] = TokenCounterCalibrationConfig(**calibration_value)
        elif isinstance(calibration_value, str):
            # 如果是引用字符串，保持原样，在配置系统中处理继承
            pass
        
        # 转换monitoring字段
        monitoring_value = data.get("monitoring")
        if isinstance(monitoring_value, dict):
            data["monitoring"] = TokenCounterMonitoringConfig(**monitoring_value)
        elif isinstance(monitoring_value, str):
            # 如果是引用字符串，保持原样，在配置系统中处理继承
            pass
        
        return data

    def get_cache_config(self) -> TokenCounterCacheConfig:
        """获取缓存配置，如果未设置则返回默认配置"""
        if self.cache is None:
            return TokenCounterCacheConfig()
        elif isinstance(self.cache, dict):
            return TokenCounterCacheConfig(**self.cache)
        elif isinstance(self.cache, str):
            # 如果是引用字符串，返回默认配置
            # 在实际使用中，配置系统会解析引用
            return TokenCounterCacheConfig()
        # 当self.cache已经是TokenCounterCacheConfig实例时
        return self.cache
    
    def get_calibration_config(self) -> TokenCounterCalibrationConfig:
        """获取校准配置，如果未设置则返回默认配置"""
        if self.calibration is None:
            return TokenCounterCalibrationConfig()
        elif isinstance(self.calibration, dict):
            return TokenCounterCalibrationConfig(**self.calibration)
        elif isinstance(self.calibration, str):
            # 如果是引用字符串，返回默认配置
            # 在实际使用中，配置系统会解析引用
            return TokenCounterCalibrationConfig()
        # 当self.calibration已经是TokenCounterCalibrationConfig实例时
        return self.calibration
    
    def get_monitoring_config(self) -> TokenCounterMonitoringConfig:
        """获取监控配置，如果未设置则返回默认配置"""
        if self.monitoring is None:
            return TokenCounterMonitoringConfig()
        elif isinstance(self.monitoring, dict):
            return TokenCounterMonitoringConfig(**self.monitoring)
        elif isinstance(self.monitoring, str):
            # 如果是引用字符串，返回默认配置
            # 在实际使用中，配置系统会解析引用
            return TokenCounterMonitoringConfig()
        # 当self.monitoring已经是TokenCounterMonitoringConfig实例时
        return self.monitoring