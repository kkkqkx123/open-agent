"""降级配置"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FallbackConfig:
    """降级配置"""
    
    # 基础配置
    enabled: bool = True
    max_attempts: int = 3
    
    # 降级模型列表
    fallback_models: List[str] = field(default_factory=list)
    
    # 降级策略配置
    strategy_type: str = "sequential"  # sequential, priority, random
    
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
    
    # 其他配置
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
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "FallbackConfig":
        """从字典创建配置"""
        return cls(
            enabled=config_dict.get("enabled", True),
            max_attempts=config_dict.get("max_attempts", 3),
            fallback_models=config_dict.get("fallback_models", []),
            strategy_type=config_dict.get("strategy_type", "sequential"),
            error_mappings=config_dict.get("error_mappings", {}),
            base_delay=config_dict.get("base_delay", 1.0),
            max_delay=config_dict.get("max_delay", 60.0),
            exponential_base=config_dict.get("exponential_base", 2.0),
            jitter=config_dict.get("jitter", True),
            fallback_on_status_codes=config_dict.get("fallback_on_status_codes", [429, 500, 502, 503, 504]),
            fallback_on_errors=config_dict.get("fallback_on_errors", [
                "timeout", "rate_limit", "service_unavailable", "overloaded_error"
            ]),
            provider_config=config_dict.get("provider_config", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "max_attempts": self.max_attempts,
            "fallback_models": self.fallback_models,
            "strategy_type": self.strategy_type,
            "error_mappings": self.error_mappings,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
            "fallback_on_status_codes": self.fallback_on_status_codes,
            "fallback_on_errors": self.fallback_on_errors,
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
    
    def get_duration(self) -> Optional[float]:
        """获取尝试持续时间（如果有的话）"""
        # 这里可以扩展以记录开始和结束时间
        return None
    
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
        import time
        self.success = True
        self.final_response = response
        self.end_time = time.time()
    
    def mark_failure(self, error: Exception) -> None:
        """标记会话失败"""
        import time
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "primary_model": self.primary_model,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.get_total_duration(),
            "total_attempts": self.get_total_attempts(),
            "success": self.success,
            "final_error": str(self.final_error) if self.final_error else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }