"""重试配置基础设施模块

提供统一的重试配置管理功能，支持多种重试策略和条件判断。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Type
from enum import Enum
import time


class RetryStrategy(Enum):
    """重试策略枚举"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    ADAPTIVE = "adaptive"


@dataclass
class RetryConfig:
    """重试配置
    
    提供完整的重试配置管理，包括策略、延迟、条件等。
    """
    
    # 基础配置
    enabled: bool = True
    max_attempts: int = 3
    
    # 延迟配置
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    # 重试条件
    retry_on_status_codes: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})
    retry_on_errors: List[str] = field(default_factory=lambda: [
        "timeout", "rate_limit", "service_unavailable", "overloaded_error",
        "connection_error", "read_timeout", "write_timeout"
    ])
    retryable_exceptions: List[Type[Exception]] = field(default_factory=list)
    
    # 策略配置
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    
    # 超时配置
    total_timeout: Optional[float] = None  # 总超时时间（秒）
    per_attempt_timeout: Optional[float] = None  # 每次尝试超时时间（秒）
    
    # 提供商特定配置
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    def is_enabled(self) -> bool:
        """检查重试是否启用"""
        return self.enabled
    
    def get_max_attempts(self) -> int:
        """获取最大尝试次数"""
        return self.max_attempts
    
    def should_retry_on_error(self, error: Exception) -> bool:
        """
        判断是否应该对特定错误进行重试
        
        Args:
            error: 错误对象
            
        Returns:
            是否应该重试
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 检查异常类型
        for exception_type in self.retryable_exceptions:
            if isinstance(error, exception_type):
                return True
        
        # 检查错误字符串模式
        for error_pattern in self.retry_on_errors:
            if error_pattern in error_str or error_pattern in error_type:
                return True
        
        # 检查HTTP状态码
        response = getattr(error, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)
            if status_code is not None and status_code in self.retry_on_status_codes:
                return True
        
        # 默认情况下允许重试（向后兼容）
        return True
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间
        
        Args:
            attempt: 尝试次数
            
        Returns:
            延迟时间（秒）
        """
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.ADAPTIVE:
            # 自适应策略：根据错误类型调整延迟
            delay = self.base_delay * (self.exponential_base ** (attempt - 1))
            # 可以根据错误类型进一步调整
        else:
            delay = self.base_delay
        
        # 限制最大延迟
        delay = min(delay, self.max_delay)
        
        # 添加抖动
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_continue_retry(self, attempt: int, start_time: float) -> bool:
        """
        判断是否应该继续重试
        
        Args:
            attempt: 当前尝试次数
            start_time: 开始时间
            
        Returns:
            是否应该继续重试
        """
        # 检查尝试次数
        if attempt >= self.max_attempts:
            return False
        
        # 检查总超时时间
        if self.total_timeout is not None:
            elapsed = time.time() - start_time
            if elapsed >= self.total_timeout:
                return False
        
        return True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RetryConfig":
        """从字典创建配置"""
        strategy_str = config_dict.get("strategy", "exponential_backoff")
        try:
            strategy = RetryStrategy(strategy_str)
        except ValueError:
            strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        
        return cls(
            enabled=config_dict.get("enabled", True),
            max_attempts=config_dict.get("max_attempts", 3),
            base_delay=config_dict.get("base_delay", 1.0),
            max_delay=config_dict.get("max_delay", 60.0),
            exponential_base=config_dict.get("exponential_base", 2.0),
            jitter=config_dict.get("jitter", True),
            retry_on_status_codes=set(config_dict.get("retry_on_status_codes", [429, 500, 502, 503, 504])),
            retry_on_errors=config_dict.get("retry_on_errors", [
                "timeout", "rate_limit", "service_unavailable", "overloaded_error",
                "connection_error", "read_timeout", "write_timeout"
            ]),
            retryable_exceptions=config_dict.get("retryable_exceptions", []),
            strategy=strategy,
            total_timeout=config_dict.get("total_timeout"),
            per_attempt_timeout=config_dict.get("per_attempt_timeout"),
            provider_config=config_dict.get("provider_config", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "max_attempts": self.max_attempts,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
            "retry_on_status_codes": list(self.retry_on_status_codes),
            "retry_on_errors": self.retry_on_errors,
            "retryable_exceptions": [exc.__name__ for exc in self.retryable_exceptions],
            "strategy": self.strategy.value,
            "total_timeout": self.total_timeout,
            "per_attempt_timeout": self.per_attempt_timeout,
            "provider_config": self.provider_config,
        }


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    
    attempt_number: int
    error: Optional[Exception]
    timestamp: float
    delay: float = 0.0
    success: bool = False
    result: Optional[Any] = None
    duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "attempt_number": self.attempt_number,
            "error": str(self.error) if self.error else None,
            "error_type": type(self.error).__name__ if self.error else None,
            "timestamp": self.timestamp,
            "delay": self.delay,
            "success": self.success,
            "duration": self.duration,
        }


@dataclass
class RetrySession:
    """重试会话记录"""
    
    func_name: str
    start_time: float
    end_time: Optional[float] = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    success: bool = False
    final_result: Optional[Any] = None
    final_error: Optional[Exception] = None
    
    def add_attempt(self, attempt: RetryAttempt) -> None:
        """添加尝试记录"""
        self.attempts.append(attempt)
    
    def mark_success(self, result: Any) -> None:
        """标记会话成功"""
        self.success = True
        self.final_result = result
        self.end_time = time.time()
    
    def mark_failure(self, error: Exception) -> None:
        """标记会话失败"""
        self.success = False
        self.final_error = error
        self.end_time = time.time()
    
    def get_total_duration(self) -> Optional[float]:
        """获取总持续时间"""
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    def get_total_attempts(self) -> int:
        """获取总尝试次数"""
        return len(self.attempts)
    
    def get_successful_attempt(self) -> Optional[RetryAttempt]:
        """获取成功的尝试"""
        for attempt in self.attempts:
            if attempt.success:
                return attempt
        return None
    
    def get_total_delay(self) -> float:
        """获取总延迟时间"""
        return sum(attempt.delay for attempt in self.attempts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "func_name": self.func_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.get_total_duration(),
            "total_attempts": self.get_total_attempts(),
            "total_delay": self.get_total_delay(),
            "success": self.success,
            "final_error": str(self.final_error) if self.final_error else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass
class RetryStats:
    """重试统计信息"""
    
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    total_attempts: int = 0
    total_delay: float = 0.0
    average_attempts: float = 0.0
    success_rate: float = 0.0
    
    def update(self, session: RetrySession) -> None:
        """更新统计信息"""
        self.total_sessions += 1
        if session.success:
            self.successful_sessions += 1
        else:
            self.failed_sessions += 1
        
        self.total_attempts += session.get_total_attempts()
        self.total_delay += session.get_total_delay()
        
        # 重新计算平均值
        self.average_attempts = self.total_attempts / self.total_sessions
        self.success_rate = self.successful_sessions / self.total_sessions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "failed_sessions": self.failed_sessions,
            "total_attempts": self.total_attempts,
            "total_delay": self.total_delay,
            "average_attempts": self.average_attempts,
            "success_rate": self.success_rate,
        }