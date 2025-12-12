"""重试和超时配置模型"""

from typing import List
from pydantic import Field, field_validator

from .base import BaseConfig


class RetryTimeoutConfig(BaseConfig):
    """重试配置模型"""

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

    @field_validator("retry_on_status_codes")
    @classmethod
    def validate_status_codes(cls, v: List[int]) -> List[int]:
        """验证HTTP状态码"""
        if not v:
            return v
        
        for code in v:
            if not isinstance(code, int) or code < 100 or code > 599:
                raise ValueError(f"无效的HTTP状态码: {code}")
        
        return v

    @field_validator("retry_on_errors")
    @classmethod
    def validate_error_types(cls, v: List[str]) -> List[str]:
        """验证错误类型"""
        if not v:
            return v
        
        allowed_errors = {
            "timeout", "rate_limit", "service_unavailable", 
            "insufficient_quota", "overloaded_error", "temporary_error"
        }
        
        for error in v:
            if error not in allowed_errors:
                raise ValueError(f"不支持的错误类型: {error}。允许的值为: {allowed_errors}")
        
        return v

    def get_retry_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        import random
        
        # 指数退避
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        
        # 添加随机抖动
        if self.jitter:
            jitter_factor = 0.8 + random.random() * 0.4  # 0.8-1.2倍抖动
            delay *= jitter_factor
        
        return delay

    def should_retry_on_status_code(self, status_code: int) -> bool:
        """检查是否应该基于状态码重试"""
        return status_code in self.retry_on_status_codes

    def should_retry_on_error_type(self, error_type: str) -> bool:
        """检查是否应该基于错误类型重试"""
        return error_type in self.retry_on_errors


class TimeoutConfig(BaseConfig):
    """超时配置模型"""

    request_timeout: int = Field(30, description="请求超时时间（秒）", ge=1, le=300)
    connect_timeout: int = Field(10, description="连接超时时间（秒）", ge=1, le=60)
    read_timeout: int = Field(30, description="读取超时时间（秒）", ge=1, le=300)
    write_timeout: int = Field(30, description="写入超时时间（秒）", ge=1, le=300)

    @field_validator("connect_timeout")
    @classmethod
    def validate_connect_timeout(cls, v: int, values) -> int:
        """验证连接超时时间"""
        request_timeout = values.data.get("request_timeout", 30)
        if v > request_timeout:
            raise ValueError("连接超时时间不能超过请求超时时间")
        return v

    @field_validator("read_timeout")
    @classmethod
    def validate_read_timeout(cls, v: int, values) -> int:
        """验证读取超时时间"""
        request_timeout = values.data.get("request_timeout", 30)
        if v > request_timeout:
            raise ValueError("读取超时时间不能超过请求超时时间")
        return v

    @field_validator("write_timeout")
    @classmethod
    def validate_write_timeout(cls, v: int, values) -> int:
        """验证写入超时时间"""
        request_timeout = values.data.get("request_timeout", 30)
        if v > request_timeout:
            raise ValueError("写入超时时间不能超过请求超时时间")
        return v

    def get_total_timeout(self) -> int:
        """获取总超时时间"""
        return self.request_timeout

    def get_client_timeout_kwargs(self) -> dict:
        """获取客户端超时参数字典"""
        return {
            "timeout": self.request_timeout,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "write_timeout": self.write_timeout,
        }
