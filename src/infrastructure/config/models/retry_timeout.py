"""重试和超时配置数据模型

提供重试和超时所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from typing import List
from pydantic import BaseModel, Field


class RetryTimeoutClientConfig(BaseModel):
    """重试配置数据模型
    
    包含重试所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """

    max_retries: int = Field(3, description="最大重试次数", ge=0, le=10)
    base_delay: float = Field(1.0, description="基础延迟时间（秒）", ge=0.1, le=300.0)
    max_delay: float = Field(60.0, description="最大延迟时间（秒）", ge=1.0, le=600.0)
    jitter: bool = Field(True, description="是否添加随机抖动")
    exponential_base: float = Field(2.0, description="指数退避基数", ge=1.1, le=5.0)
    retry_on_status_codes: List[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504],
        description="需要重试的HTTP状态码"
    )
    retry_on_errors: List[str] = Field(
        default_factory=lambda: ["timeout", "rate_limit", "service_unavailable"],
        description="需要重试的错误类型"
    )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "RetryTimeoutClientConfig":
        """从字典创建配置"""
        return cls(**data)


class TimeoutClientConfig(BaseModel):
    """超时配置数据模型
    
    包含超时所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """

    request_timeout: int = Field(30, description="请求超时时间（秒）", ge=1, le=300)
    connect_timeout: int = Field(10, description="连接超时时间（秒）", ge=1, le=60)
    read_timeout: int = Field(30, description="读取超时时间（秒）", ge=1, le=300)
    write_timeout: int = Field(30, description="写入超时时间（秒）", ge=1, le=300)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TimeoutClientConfig":
        """从字典创建配置"""
        return cls(**data)


__all__ = [
    "RetryTimeoutClientConfig",
    "TimeoutClientConfig"
]