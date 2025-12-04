"""降级配置基础设施模块

提供统一的降级配置管理功能，支持多种降级策略和条件判断。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time


class FallbackStrategy(Enum):
    """降级策略枚举"""
    SEQUENTIAL = "sequential"
    PRIORITY = "priority"
    RANDOM = "random"
    PARALLEL = "parallel"


@dataclass
class FallbackConfig:
    """降级配置
    
    提供完整的降级配置管理，包括策略、延迟、条件等。
    """
    
    # 基础配置
    enabled: bool = True
    max_attempts: int = 3
    
    # 降级模型列表
    fallback_models: List[str] = field(default_factory=list)
    
    # 降级策略配置
    strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL
    
    # 错误类型映射
    error_mappings: Dict[str, List[str]] = field(default_factory=dict)
    
    # 延迟配置
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    # 条件配置
    fallback_on_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    fallback_on_errors: List[str] = field(default_factory=lambda: [
        "timeout", "rate_limit", "service_unavailable", "overloaded_error"
    ])
    
    # 并行降级配置
    parallel_timeout: Optional[float] = None  # 并行降级超时时间
    parallel_success_threshold: int = 1  # 并行降级成功阈值
    
    # 提供商特定配置
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    def is_enabled(self) -> bool:
        """检查降级是否启用"""
        return self.enabled and len(self.fallback_models) > 0
    
    def get_max_attempts(self) -> int:
        """获取最大尝试次数"""
        return self.max_attempts
    
    def get_fallback_models(self) -> List[str]:
        """获取降级模型列表"""
        return self.fallback_models.copy()
    
    def should_fallback_on_error(self, error: Exception) -> bool:
        """
        判断是否应该对特定错误进行降级
        
        Args:
            error: 错误对象
            
        Returns:
            是否应该降级
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 检查错误类型
        for error_pattern in self.fallback_on_errors:
            if error_pattern in error_str or error_pattern in error_type:
                return True
        
        # 检查状态码
        response = getattr(error, 'response', None)
        if response is not None:
            status_code = getattr(response, 'status_code', None)
            if status_code is not None and status_code in self.fallback_on_status_codes:
                return True
        
        # 默认情况下，对于任何错误都允许降级
        return True
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算降级延迟时间
        
        Args:
            attempt: 尝试次数
            
        Returns:
            延迟时间（秒）
        """
        # 指数退避
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        
        # 限制最大延迟
        delay = min(delay, self.max_delay)
        
        # 添加抖动
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        根据策略获取降级目标
        
        Args:
            error: 错误对象
            attempt: 尝试次数
            
        Returns:
            降级目标模型名称
        """
        if not self.fallback_models:
            return None
        
        if self.strategy == FallbackStrategy.SEQUENTIAL:
            # 顺序策略：按列表顺序选择
            index = min(attempt - 1, len(self.fallback_models) - 1)
            return self.fallback_models[index]
        
        elif self.strategy == FallbackStrategy.PRIORITY:
            # 优先级策略：根据错误类型选择
            error_str = str(error).lower()
            for error_pattern, models in self.error_mappings.items():
                if error_pattern in error_str:
                    if models:
                        return models[0]
            # 如果没有匹配的错误映射，使用第一个模型
            return self.fallback_models[0]
        
        elif self.strategy == FallbackStrategy.RANDOM:
            # 随机策略：随机选择一个模型
            import random
            return random.choice(self.fallback_models)
        
        elif self.strategy == FallbackStrategy.PARALLEL:
            # 并行策略：返回特殊标记
            return "parallel_fallback"
        
        return None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "FallbackConfig":
        """从字典创建配置"""
        strategy_str = config_dict.get("strategy", "sequential")
        try:
            strategy = FallbackStrategy(strategy_str)
        except ValueError:
            strategy = FallbackStrategy.SEQUENTIAL
        
        return cls(
            enabled=config_dict.get("enabled", True),
            max_attempts=config_dict.get("max_attempts", 3),
            fallback_models=config_dict.get("fallback_models", []),
            strategy=strategy,
            error_mappings=config_dict.get("error_mappings", {}),
            base_delay=config_dict.get("base_delay", 1.0),
            max_delay=config_dict.get("max_delay", 60.0),
            exponential_base=config_dict.get("exponential_base", 2.0),
            jitter=config_dict.get("jitter", True),
            fallback_on_status_codes=config_dict.get("fallback_on_status_codes", [429, 500, 502, 503, 504]),
            fallback_on_errors=config_dict.get("fallback_on_errors", [
                "timeout", "rate_limit", "service_unavailable", "overloaded_error"
            ]),
            parallel_timeout=config_dict.get("parallel_timeout"),
            parallel_success_threshold=config_dict.get("parallel_success_threshold", 1),
            provider_config=config_dict.get("provider_config", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "max_attempts": self.max_attempts,
            "fallback_models": self.fallback_models,
            "strategy": self.strategy.value,
            "error_mappings": self.error_mappings,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
            "fallback_on_status_codes": self.fallback_on_status_codes,
            "fallback_on_errors": self.fallback_on_errors,
            "parallel_timeout": self.parallel_timeout,
            "parallel_success_threshold": self.parallel_success_threshold,
            "provider_config": self.provider_config,
        }


@dataclass
class FallbackAttempt:
    """降级尝试记录"""
    
    primary_model: str
    fallback_model: Optional[str]
    error: Optional[Exception]
    attempt_number: int
    timestamp: float
    success: bool
    response: Optional[Any] = None
    delay: float = 0.0
    duration: Optional[float] = None
    
    def get_duration(self) -> Optional[float]:
        """获取尝试持续时间（如果有的话）"""
        return self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "error": str(self.error) if self.error else None,
            "error_type": type(self.error).__name__ if self.error else None,
            "attempt_number": self.attempt_number,
            "timestamp": self.timestamp,
            "success": self.success,
            "delay": self.delay,
            "duration": self.duration,
        }


@dataclass
class FallbackSession:
    """降级会话记录"""
    
    primary_model: str
    start_time: float
    end_time: Optional[float] = None
    attempts: List[FallbackAttempt] = field(default_factory=list)
    success: bool = False
    final_response: Optional[Any] = None
    final_error: Optional[Exception] = None
    
    def add_attempt(self, attempt: FallbackAttempt) -> None:
        """添加尝试记录"""
        self.attempts.append(attempt)
    
    def mark_success(self, response: Any) -> None:
        """标记会话成功"""
        self.success = True
        self.final_response = response
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
    
    def get_successful_attempt(self) -> Optional[FallbackAttempt]:
        """获取成功的尝试"""
        for attempt in self.attempts:
            if attempt.success:
                return attempt
        return None
    
    def get_fallback_usage(self) -> bool:
        """是否使用了降级"""
        return len(self.attempts) > 1 or (
            len(self.attempts) == 1 and self.attempts[0].fallback_model is not None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "primary_model": self.primary_model,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.get_total_duration(),
            "total_attempts": self.get_total_attempts(),
            "success": self.success,
            "fallback_used": self.get_fallback_usage(),
            "final_error": str(self.final_error) if self.final_error else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass
class FallbackStats:
    """降级统计信息"""
    
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    fallback_usage_count: int = 0
    total_attempts: int = 0
    average_attempts: float = 0.0
    fallback_rate: float = 0.0
    success_rate: float = 0.0
    
    def update(self, session: FallbackSession) -> None:
        """更新统计信息"""
        self.total_sessions += 1
        if session.success:
            self.successful_sessions += 1
        else:
            self.failed_sessions += 1
        
        if session.get_fallback_usage():
            self.fallback_usage_count += 1
        
        self.total_attempts += session.get_total_attempts()
        
        # 重新计算平均值
        self.average_attempts = self.total_attempts / self.total_sessions
        self.fallback_rate = self.fallback_usage_count / self.total_sessions
        self.success_rate = self.successful_sessions / self.total_sessions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "failed_sessions": self.failed_sessions,
            "fallback_usage_count": self.fallback_usage_count,
            "total_attempts": self.total_attempts,
            "average_attempts": self.average_attempts,
            "fallback_rate": self.fallback_rate,
            "success_rate": self.success_rate,
        }