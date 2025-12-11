"""Token计数器配置数据模型

提供Token计数器所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class TokenCounterCacheClientConfig(BaseModel):
    """Token计数器缓存配置数据模型"""
    
    ttl_seconds: int = Field(default=3600, description="缓存TTL（秒）")
    max_size: int = Field(default=1000, description="最大缓存条目数")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenCounterCacheClientConfig":
        """从字典创建配置"""
        return cls(**data)


class TokenCounterCalibrationClientConfig(BaseModel):
    """Token计数器校准配置数据模型"""
    
    min_data_points: int = Field(default=3, description="最小校准数据点数")
    max_data_points: int = Field(default=100, description="最大校准数据点数")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenCounterCalibrationClientConfig":
        """从字典创建配置"""
        return cls(**data)


class TokenCounterMonitoringClientConfig(BaseModel):
    """Token计数器监控配置数据模型"""
    
    enabled: bool = Field(default=True, description="是否启用监控")
    stats_interval: int = Field(default=300, description="统计信息记录间隔（秒）")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenCounterMonitoringClientConfig":
        """从字典创建配置"""
        return cls(**data)


class TokenCounterClientConfig(BaseModel):
    """Token计数器配置数据模型
    
    包含Token计数器所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """
    
    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称：gpt-4, gemini-pro等")
    enhanced: bool = Field(default=False, description="是否使用增强版计数器")
    
    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")
    
    # 缓存配置
    cache: Optional[Union[TokenCounterCacheClientConfig, Dict[str, Any], str]] = Field(default=None, description="缓存配置")
    
    # 校准配置
    calibration: Optional[Union[TokenCounterCalibrationClientConfig, Dict[str, Any], str]] = Field(default=None, description="校准配置")
    
    # 监控配置
    monitoring: Optional[Union[TokenCounterMonitoringClientConfig, Dict[str, Any], str]] = Field(default=None, description="监控配置")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenCounterClientConfig":
        """从字典创建配置"""
        # 处理cache字段
        if "cache" in data and isinstance(data["cache"], dict):
            data["cache"] = TokenCounterCacheClientConfig(**data["cache"])
        
        # 处理calibration字段
        if "calibration" in data and isinstance(data["calibration"], dict):
            data["calibration"] = TokenCounterCalibrationClientConfig(**data["calibration"])
        
        # 处理monitoring字段
        if "monitoring" in data and isinstance(data["monitoring"], dict):
            data["monitoring"] = TokenCounterMonitoringClientConfig(**data["monitoring"])
        
        return cls(**data)


__all__ = [
    "TokenCounterCacheClientConfig",
    "TokenCounterCalibrationClientConfig",
    "TokenCounterMonitoringClientConfig",
    "TokenCounterClientConfig"
]