"""任务组配置模型"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, field_validator, model_validator
from dataclasses import dataclass, field
from enum import Enum

from .base import BaseConfig
from .retry_timeout_config import RetryTimeoutConfig, TimeoutConfig


class FallbackStrategy(str, Enum):
    """降级策略枚举"""
    ECHELON_DOWN = "echelon_down"  # 层级降级
    MODEL_ROTATE = "model_rotate"  # 模型轮询
    PROVIDER_FAILOVER = "provider_failover"  # 提供商故障转移
    TASK_GROUP_SWITCH = "task_group_switch"  # 任务组切换


class RotationStrategy(str, Enum):
    """轮询策略枚举"""
    ROUND_ROBIN = "round_robin"  # 轮询
    LEAST_RECENTLY_USED = "least_recently_used"  # 最少使用
    WEIGHTED = "weighted"  # 加权


class RateLimitingAlgorithm(str, Enum):
    """限流算法枚举"""
    TOKEN_BUCKET = "token_bucket"  # 令牌桶
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_time: int = 60
    half_open_requests: int = 1
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "CircuitBreakerConfig":
        """从字典创建配置"""
        return cls(
            failure_threshold=config_dict.get("failure_threshold", 5),
            recovery_time=config_dict.get("recovery_time", 60),
            half_open_requests=config_dict.get("half_open_requests", 1)
        )


@dataclass
class ThinkingConfig:
    """思考配置"""
    enabled: bool = True
    budget_tokens: int = 2000
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ThinkingConfig":
        """从字典创建配置"""
        return cls(
            enabled=config_dict.get("enabled", True),
            budget_tokens=config_dict.get("budget_tokens", 2000)
        )


@dataclass
class EchelonConfig:
    """层级配置"""
    models: List[str]
    concurrency_limit: int
    rpm_limit: int
    priority: int
    timeout: int
    max_retries: int
    temperature: float = 0.7
    max_tokens: int = 2000
    function_calling: Optional[str] = None
    response_format: Optional[str] = None
    thinking_config: Optional[ThinkingConfig] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "EchelonConfig":
        """从字典创建配置"""
        thinking_config = None
        if "thinking_config" in config_dict:
            thinking_config = ThinkingConfig.from_dict(config_dict["thinking_config"])
        
        return cls(
            models=config_dict.get("models", []),
            concurrency_limit=config_dict.get("concurrency_limit", 0),
            rpm_limit=config_dict.get("rpm_limit", 0),
            priority=config_dict.get("priority", 0),
            timeout=config_dict.get("timeout", 0),
            max_retries=config_dict.get("max_retries", 0),
            temperature=config_dict.get("temperature", 0.7),
            max_tokens=config_dict.get("max_tokens", 2000),
            function_calling=config_dict.get("function_calling"),
            response_format=config_dict.get("response_format"),
            thinking_config=thinking_config
        )


@dataclass
class FallbackConfig:
    """任务组降级配置"""
    strategy: FallbackStrategy = FallbackStrategy.ECHELON_DOWN
    fallback_groups: List[str] = field(default_factory=list)
    max_attempts: int = 3
    retry_delay: float = 1.0
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "FallbackConfig":
        """从字典创建配置"""
        circuit_breaker = None
        if "circuit_breaker" in config_dict:
            circuit_breaker = CircuitBreakerConfig.from_dict(config_dict["circuit_breaker"])
        
        return cls(
            strategy=FallbackStrategy(config_dict.get("strategy", "echelon_down")),
            fallback_groups=config_dict.get("fallback_groups", []),
            max_attempts=config_dict.get("max_attempts", 3),
            retry_delay=config_dict.get("retry_delay", 1.0),
            circuit_breaker=circuit_breaker
        )


@dataclass
class TaskGroupConfig:
    """任务组配置"""
    name: str
    description: str
    echelons: Dict[str, EchelonConfig]
    fallback_strategy: FallbackStrategy = FallbackStrategy.ECHELON_DOWN
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    fallback_config: Optional[FallbackConfig] = None
    
    @classmethod
    def from_dict(cls, name: str, config_dict: Dict[str, Any]) -> "TaskGroupConfig":
        """从字典创建配置"""
        echelons = {}
        
        # 解析层级配置
        for key, value in config_dict.items():
            if key.startswith("echelon") and isinstance(value, dict):
                echelons[key] = EchelonConfig.from_dict(value)
            elif key in ["translation", "analysis", "execute", "thinking", "high_payload"]:
                # 小模型组的任务类型
                echelons[key] = EchelonConfig.from_dict(value)
        
        # 解析熔断器配置
        circuit_breaker = None
        if "circuit_breaker" in config_dict:
            circuit_breaker = CircuitBreakerConfig.from_dict(config_dict["circuit_breaker"])
        
        # 解析降级配置
        fallback_config = None
        if "fallback_config" in config_dict:
            fallback_config = FallbackConfig.from_dict(config_dict["fallback_config"])
        
        return cls(
            name=name,
            description=config_dict.get("description", ""),
            echelons=echelons,
            fallback_strategy=FallbackStrategy(config_dict.get("fallback_strategy", "echelon_down")),
            circuit_breaker=circuit_breaker,
            fallback_config=fallback_config
        )


@dataclass
class RateLimitingConfig:
    """限流配置"""
    enabled: bool = True
    algorithm: RateLimitingAlgorithm = RateLimitingAlgorithm.TOKEN_BUCKET
    token_bucket: Optional[Dict[str, Any]] = None
    sliding_window: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RateLimitingConfig":
        """从字典创建配置"""
        return cls(
            enabled=config_dict.get("enabled", True),
            algorithm=RateLimitingAlgorithm(config_dict.get("algorithm", "token_bucket")),
            token_bucket=config_dict.get("token_bucket"),
            sliding_window=config_dict.get("sliding_window")
        )


@dataclass
class PollingPoolFallbackConfig:
    """轮询池降级配置"""
    strategy: str = "instance_rotation"  # instance_rotation, simple_retry
    max_instance_attempts: int = 2
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PollingPoolFallbackConfig":
        """从字典创建配置"""
        return cls(
            strategy=config_dict.get("strategy", "instance_rotation"),
            max_instance_attempts=config_dict.get("max_instance_attempts", 2)
        )


@dataclass
class PollingPoolConfig:
    """轮询池配置"""
    name: str
    description: str
    task_groups: List[str]
    rotation_strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN
    health_check_interval: int = 30
    failure_threshold: int = 3
    recovery_time: int = 60
    rate_limiting: Optional[RateLimitingConfig] = None
    fallback_config: Optional[PollingPoolFallbackConfig] = None
    
    @classmethod
    def from_dict(cls, name: str, config_dict: Dict[str, Any]) -> "PollingPoolConfig":
        """从字典创建配置"""
        rate_limiting = None
        if "rate_limiting" in config_dict:
            rate_limiting = RateLimitingConfig.from_dict(config_dict["rate_limiting"])
        
        # 解析降级配置
        fallback_config = None
        if "fallback_config" in config_dict:
            fallback_config = PollingPoolFallbackConfig.from_dict(config_dict["fallback_config"])
        
        return cls(
            name=name,
            description=config_dict.get("description", ""),
            task_groups=config_dict["task_groups"],
            rotation_strategy=RotationStrategy(config_dict.get("rotation_strategy", "round_robin")),
            health_check_interval=config_dict.get("health_check_interval", 30),
            failure_threshold=config_dict.get("failure_threshold", 3),
            recovery_time=config_dict.get("recovery_time", 60),
            rate_limiting=rate_limiting,
            fallback_config=fallback_config
        )


@dataclass
class ConcurrencyControlConfig:
    """并发控制配置"""
    enabled: bool = True
    levels: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConcurrencyControlConfig":
        """从字典创建配置"""
        return cls(
            enabled=config_dict.get("enabled", True),
            levels=config_dict.get("levels", [])
        )


@dataclass
class GlobalFallbackConfig:
    """全局降级配置"""
    enabled: bool = True
    max_attempts: int = 3
    retry_delay: float = 1.0
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "GlobalFallbackConfig":
        """从字典创建配置"""
        circuit_breaker = None
        if "circuit_breaker" in config_dict:
            circuit_breaker = CircuitBreakerConfig.from_dict(config_dict["circuit_breaker"])
        
        return cls(
            enabled=config_dict.get("enabled", True),
            max_attempts=config_dict.get("max_attempts", 3),
            retry_delay=config_dict.get("retry_delay", 1.0),
            circuit_breaker=circuit_breaker
        )


@dataclass
class TaskGroupsConfig:
    """任务组总配置"""
    task_groups: Dict[str, TaskGroupConfig]
    polling_pools: Dict[str, PollingPoolConfig]
    global_fallback: GlobalFallbackConfig
    concurrency_control: ConcurrencyControlConfig
    rate_limiting: RateLimitingConfig
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TaskGroupsConfig":
        """从字典创建配置"""
        # 解析任务组
        task_groups = {}
        if "task_groups" in config_dict:
            for name, group_config in config_dict["task_groups"].items():
                task_groups[name] = TaskGroupConfig.from_dict(name, group_config)
        
        # 解析轮询池
        polling_pools = {}
        if "polling_pools" in config_dict:
            for name, pool_config in config_dict["polling_pools"].items():
                polling_pools[name] = PollingPoolConfig.from_dict(name, pool_config)
        
        # 解析全局降级配置
        global_fallback = GlobalFallbackConfig.from_dict(
            config_dict.get("global_fallback", {})
        )
        
        # 解析并发控制配置
        concurrency_control = ConcurrencyControlConfig.from_dict(
            config_dict.get("concurrency_control", {})
        )
        
        # 解析限流配置
        rate_limiting = RateLimitingConfig.from_dict(
            config_dict.get("rate_limiting", {})
        )
        
        return cls(
            task_groups=task_groups,
            polling_pools=polling_pools,
            global_fallback=global_fallback,
            concurrency_control=concurrency_control,
            rate_limiting=rate_limiting
        )
    
    def get_task_group(self, name: str) -> Optional[TaskGroupConfig]:
        """获取任务组配置"""
        return self.task_groups.get(name)
    
    def get_polling_pool(self, name: str) -> Optional[PollingPoolConfig]:
        """获取轮询池配置"""
        return self.polling_pools.get(name)
    
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[EchelonConfig]:
        """获取层级配置"""
        task_group = self.get_task_group(group_name)
        if task_group:
            return task_group.echelons.get(echelon_name)
        return None