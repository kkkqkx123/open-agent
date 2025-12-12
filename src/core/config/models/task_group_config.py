"""任务组配置模型"""

from typing import Dict, Any, Optional, List, Union
from pydantic import Field, field_validator, model_validator
from enum import Enum

from .base import BaseConfig


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


class CircuitBreakerConfig(BaseConfig):
    """熔断器配置"""
    failure_threshold: int = Field(5, description="失败阈值", ge=1, le=100)
    recovery_time: int = Field(60, description="恢复时间（秒）", ge=1, le=3600)
    half_open_requests: int = Field(1, description="半开状态请求数", ge=1, le=10)


class ThinkingConfig(BaseConfig):
    """思考配置"""
    enabled: bool = Field(True, description="是否启用思考")
    budget_tokens: int = Field(2000, description="思考令牌预算", ge=100, le=10000)


class EchelonConfig(BaseConfig):
    """层级配置
    
    定义单个层级中的模型及其参数配置。
    """
    models: List[str] = Field(..., description="模型列表", min_length=1)
    concurrency_limit: int = Field(0, description="并发限制", ge=0, le=1000)
    rpm_limit: int = Field(0, description="每分钟请求限制", ge=0, le=10000)
    priority: int = Field(0, description="优先级", ge=0, le=100)
    timeout: int = Field(0, description="超时时间（秒）", ge=0, le=300)
    max_retries: int = Field(0, description="最大重试次数", ge=0, le=10)
    temperature: float = Field(0.7, description="温度参数", ge=0.0, le=2.0)
    max_tokens: int = Field(2000, description="最大令牌数", ge=1, le=100000)
    function_calling: Optional[str] = Field(None, description="函数调用模式")
    response_format: Optional[str] = Field(None, description="响应格式")
    thinking_config: Optional[ThinkingConfig] = Field(None, description="思考配置")
    
    @field_validator("models")
    @classmethod
    def validate_models_not_empty(cls, v: List[str]) -> List[str]:
        """验证模型列表不包含空字符串"""
        if any(not m.strip() for m in v):
            raise ValueError("模型名称不能为空字符串")
        return v


class FallbackConfig(BaseConfig):
    """任务组降级配置"""
    strategy: FallbackStrategy = Field(FallbackStrategy.ECHELON_DOWN, description="降级策略")
    fallback_groups: List[str] = Field(default_factory=list, description="降级组列表")
    max_attempts: int = Field(3, description="最大尝试次数", ge=1, le=10)
    retry_delay: float = Field(1.0, description="重试延迟（秒）", ge=0.1, le=60.0)
    circuit_breaker: Optional[CircuitBreakerConfig] = Field(None, description="熔断器配置")


class TaskGroupConfig(BaseConfig):
    """任务组配置
    
    定义一个任务组，支持多层级降级、熔断器和故障转移。
    
    示例：
        ```python
        config = TaskGroupConfig(
            name="gpt4_group",
            description="高精度任务组",
            echelons={
                "echelon_1": EchelonConfig(
                    models=["gpt-4"],
                    priority=100,
                    max_retries=3
                ),
                "echelon_2": EchelonConfig(
                    models=["gpt-3.5-turbo"],
                    priority=50
                )
            }
        )
        ```
    """
    name: str = Field(..., description="任务组名称", min_length=1)
    description: str = Field("", description="任务组描述")
    echelons: Dict[str, EchelonConfig] = Field(default_factory=dict, description="层级配置字典")
    fallback_strategy: FallbackStrategy = Field(FallbackStrategy.ECHELON_DOWN, description="降级策略")
    circuit_breaker: Optional[CircuitBreakerConfig] = Field(None, description="熔断器配置")
    fallback_config: Optional[FallbackConfig] = Field(None, description="降级配置")
    
    @model_validator(mode="after")
    def validate_echelon_consistency(self) -> "TaskGroupConfig":
        """验证层级配置的一致性"""
        if self.fallback_strategy == FallbackStrategy.ECHELON_DOWN:
            if not self.echelons:
                raise ValueError("层级降级策略要求至少配置一个层级")
        return self
    
    # === 业务方法 ===
    
    def get_sorted_echelons(self) -> List[tuple[str, EchelonConfig]]:
        """按优先级排序获取所有层级
        
        Returns:
            按优先级降序排列的 (名称, 配置) 元组列表
        """
        return sorted(
            self.echelons.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
    
    def get_first_echelon(self) -> Optional[tuple[str, EchelonConfig]]:
        """获取优先级最高的层级"""
        sorted_echelons = self.get_sorted_echelons()
        return sorted_echelons[0] if sorted_echelons else None
    
    def has_circuit_breaker(self) -> bool:
        """是否启用了熔断器"""
        return self.circuit_breaker is not None
    
    def get_all_models(self) -> List[str]:
        """获取所有层级中的模型名称（去重）"""
        models = set()
        for echelon in self.echelons.values():
            models.update(echelon.models)
        return sorted(list(models))


class RateLimitingConfig(BaseConfig):
    """限流配置"""
    enabled: bool = Field(True, description="是否启用限流")
    algorithm: RateLimitingAlgorithm = Field(RateLimitingAlgorithm.TOKEN_BUCKET, description="限流算法")
    token_bucket: Optional[Dict[str, Any]] = Field(None, description="令牌桶配置")
    sliding_window: Optional[Dict[str, Any]] = Field(None, description="滑动窗口配置")


class PollingPoolFallbackConfig(BaseConfig):
    """轮询池降级配置"""
    strategy: str = Field("instance_rotation", description="降级策略（instance_rotation, simple_retry）")
    max_instance_attempts: int = Field(2, description="最大实例尝试次数", ge=1, le=10)


class PollingPoolConfig(BaseConfig):
    """轮询池配置"""
    name: str = Field(..., description="轮询池名称")
    description: str = Field("", description="轮询池描述")
    task_groups: List[str] = Field(..., description="任务组列表")
    rotation_strategy: RotationStrategy = Field(RotationStrategy.ROUND_ROBIN, description="轮询策略")
    health_check_interval: int = Field(30, description="健康检查间隔（秒）", ge=1, le=3600)
    failure_threshold: int = Field(3, description="失败阈值", ge=1, le=100)
    recovery_time: int = Field(60, description="恢复时间（秒）", ge=1, le=3600)
    rate_limiting: Optional[RateLimitingConfig] = Field(None, description="限流配置")
    fallback_config: Optional[PollingPoolFallbackConfig] = Field(None, description="降级配置")


class ConcurrencyControlConfig(BaseConfig):
    """并发控制配置"""
    enabled: bool = Field(True, description="是否启用并发控制")
    levels: List[Dict[str, Any]] = Field(default_factory=list, description="并发控制级别列表")


class GlobalFallbackConfig(BaseConfig):
    """全局降级配置"""
    enabled: bool = Field(True, description="是否启用全局降级")
    max_attempts: int = Field(3, description="最大尝试次数", ge=1, le=10)
    retry_delay: float = Field(1.0, description="重试延迟（秒）", ge=0.1, le=60.0)
    circuit_breaker: Optional[CircuitBreakerConfig] = Field(None, description="熔断器配置")


class TaskGroupsConfig(BaseConfig):
    """任务组总配置
    
    顶级配置对象，包含所有任务组、轮询池和全局配置。
    """
    task_groups: Dict[str, TaskGroupConfig] = Field(default_factory=dict, description="任务组配置字典")
    polling_pools: Dict[str, PollingPoolConfig] = Field(default_factory=dict, description="轮询池配置字典")
    global_fallback: Optional[GlobalFallbackConfig] = Field(None, description="全局降级配置")
    concurrency_control: Optional[ConcurrencyControlConfig] = Field(None, description="并发控制配置")
    rate_limiting: Optional[RateLimitingConfig] = Field(None, description="限流配置")
    
    # === 业务方法 ===
    
    def get_task_group(self, name: str) -> Optional[TaskGroupConfig]:
        """获取任务组配置
        
        Args:
            name: 任务组名称
            
        Returns:
            TaskGroupConfig 或 None
        """
        return self.task_groups.get(name)
    
    def get_polling_pool(self, name: str) -> Optional[PollingPoolConfig]:
        """获取轮询池配置
        
        Args:
            name: 轮询池名称
            
        Returns:
            PollingPoolConfig 或 None
        """
        return self.polling_pools.get(name)
    
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[EchelonConfig]:
        """获取层级配置
        
        Args:
            group_name: 任务组名称
            echelon_name: 层级名称
            
        Returns:
            EchelonConfig 或 None
        """
        task_group = self.get_task_group(group_name)
        if task_group:
            return task_group.echelons.get(echelon_name)
        return None
    
    def get_all_task_group_names(self) -> List[str]:
        """获取所有任务组名称"""
        return list(self.task_groups.keys())
    
    def get_all_polling_pool_names(self) -> List[str]:
        """获取所有轮询池名称"""
        return list(self.polling_pools.keys())
    
    def has_task_group(self, name: str) -> bool:
        """检查任务组是否存在"""
        return name in self.task_groups
    
    def has_polling_pool(self, name: str) -> bool:
        """检查轮询池是否存在"""
        return name in self.polling_pools
    
    def validate_business_rules(self) -> List[str]:
        """验证配置的业务规则
        
        Returns:
            错误消息列表
        """
        errors = []
        
        # 验证轮询池引用的任务组是否存在
        for pool_name, pool_config in self.polling_pools.items():
            for task_group_name in pool_config.task_groups:
                if not self.has_task_group(task_group_name):
                    errors.append(
                        f"轮询池 '{pool_name}' 引用的任务组 '{task_group_name}' 不存在"
                    )
        
        # 验证任务组的降级引用
        for group_name, group_config in self.task_groups.items():
            if group_config.fallback_config:
                for fallback_group in group_config.fallback_config.fallback_groups:
                    if not self.has_task_group(fallback_group):
                        errors.append(
                            f"任务组 '{group_name}' 的降级组 '{fallback_group}' 不存在"
                        )
        
        return errors