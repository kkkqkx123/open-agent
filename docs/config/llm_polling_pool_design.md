# LLM轮询池机制设计

## 轮询池概述

轮询池是LLM分组配置系统中的核心组件，负责管理多个LLM实例的负载均衡、健康检查和故障恢复。轮询池通过智能的调度算法，确保请求能够高效、可靠地分配到可用的LLM实例上。

## 轮询池架构

### 核心组件

```
轮询池架构:
┌─────────────────────────────────────────────────────────────┐
│                    轮询池管理器                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  调度器     │  │  健康检查器  │  │  故障恢复器  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  负载均衡器  │  │  限流器     │  │  监控器     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    LLM实例池                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  实例1      │  │  实例2      │  │  实例N      │         │
│  │ (状态:健康) │  │ (状态:故障) │  │ (状态:恢复) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 实例状态管理

每个LLM实例在轮询池中都有明确的状态：

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

class InstanceStatus(Enum):
    """实例状态枚举"""
    HEALTHY = "healthy"           # 健康，可以接受请求
    DEGRADED = "degraded"         # 降级，性能下降但仍可用
    UNHEALTHY = "unhealthy"       # 不健康，暂时不可用
    FAILED = "failed"            # 失败，需要故障恢复
    RECOVERING = "recovering"     # 恢复中，正在尝试恢复
    MAINTENANCE = "maintenance"   # 维护中，暂时不可用

@dataclass
class LLMInstance:
    """LLM实例信息"""
    instance_id: str
    model_name: str
    group_name: str
    echelon: str
    endpoint: str
    status: InstanceStatus
    last_health_check: datetime
    failure_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    current_load: int = 0
    max_concurrency: int = 10
    metadata: Dict[str, Any] = None
    
    def is_available(self) -> bool:
        """检查实例是否可用"""
        return self.status in [InstanceStatus.HEALTHY, InstanceStatus.DEGRADED]
    
    def can_accept_request(self) -> bool:
        """检查实例是否能接受新请求"""
        return (self.is_available() and 
                self.current_load < self.max_concurrency)
```

## 调度策略

### 1. 轮询调度 (Round Robin)

```python
class RoundRobinScheduler:
    """轮询调度器"""
    
    def __init__(self):
        self.current_index = 0
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """选择下一个实例"""
        available_instances = [inst for inst in instances if inst.can_accept_request()]
        
        if not available_instances:
            return None
        
        # 轮询选择
        selected = available_instances[self.current_index % len(available_instances)]
        self.current_index += 1
        
        return selected
```

### 2. 最少使用调度 (Least Recently Used)

```python
class LRUScheduler:
    """最少使用调度器"""
    
    def __init__(self):
        self.last_used: Dict[str, datetime] = {}
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """选择最少使用的实例"""
        available_instances = [inst for inst in instances if inst.can_accept_request()]
        
        if not available_instances:
            return None
        
        # 找到最少使用的实例
        selected = min(available_instances, 
                      key=lambda inst: self.last_used.get(inst.instance_id, datetime.min))
        
        # 更新使用时间
        self.last_used[selected.instance_id] = datetime.now()
        
        return selected
```

### 3. 加权调度 (Weighted)

```python
class WeightedScheduler:
    """加权调度器"""
    
    def __init__(self):
        self.weights: Dict[str, float] = {}
    
    def calculate_weight(self, instance: LLMInstance) -> float:
        """计算实例权重"""
        base_weight = 1.0
        
        # 根据性能调整权重
        if instance.avg_response_time > 0:
            performance_weight = 1.0 / instance.avg_response_time
        else:
            performance_weight = 1.0
        
        # 根据成功率调整权重
        total_requests = instance.success_count + instance.failure_count
        if total_requests > 0:
            success_rate = instance.success_count / total_requests
            reliability_weight = success_rate
        else:
            reliability_weight = 1.0
        
        # 根据当前负载调整权重
        load_weight = 1.0 - (instance.current_load / instance.max_concurrency)
        
        # 综合权重
        final_weight = base_weight * performance_weight * reliability_weight * load_weight
        
        return max(final_weight, 0.1)  # 最小权重
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """根据权重选择实例"""
        available_instances = [inst for inst in instances if inst.can_accept_request()]
        
        if not available_instances:
            return None
        
        # 计算权重并选择
        weights = [self.calculate_weight(inst) for inst in available_instances]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return available_instances[0]
        
        # 加权随机选择
        import random
        rand_value = random.uniform(0, total_weight)
        current_weight = 0
        
        for i, weight in enumerate(weights):
            current_weight += weight
            if rand_value <= current_weight:
                return available_instances[i]
        
        return available_instances[-1]
```

## 健康检查机制

### 健康检查器

```python
import asyncio
from typing import List, Callable

class HealthChecker:
    """健康检查器"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_check_callbacks: List[Callable] = []
        self.running = False
    
    async def start(self, instances: List[LLMInstance]):
        """启动健康检查"""
        self.running = True
        
        while self.running:
            await self._check_instances(instances)
            await asyncio.sleep(self.check_interval)
    
    async def _check_instances(self, instances: List[LLMInstance]):
        """检查所有实例"""
        tasks = [self._check_instance(instance) for instance in instances]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_instance(self, instance: LLMInstance):
        """检查单个实例"""
        try:
            # 执行健康检查
            is_healthy = await self._perform_health_check(instance)
            
            if is_healthy:
                if instance.status == InstanceStatus.FAILED:
                    instance.status = InstanceStatus.RECOVERING
                elif instance.status == InstanceStatus.RECOVERING:
                    instance.status = InstanceStatus.HEALTHY
                
                instance.failure_count = 0
            else:
                instance.failure_count += 1
                
                if instance.failure_count >= 3:
                    instance.status = InstanceStatus.FAILED
                elif instance.status == InstanceStatus.HEALTHY:
                    instance.status = InstanceStatus.DEGRADED
            
            instance.last_health_check = datetime.now()
            
        except Exception as e:
            logger.error(f"健康检查失败 {instance.instance_id}: {e}")
            instance.failure_count += 1
            if instance.failure_count >= 3:
                instance.status = InstanceStatus.FAILED
    
    async def _perform_health_check(self, instance: LLMInstance) -> bool:
        """执行具体的健康检查"""
        # 这里可以实现具体的健康检查逻辑
        # 例如发送简单的ping请求
        try:
            # 模拟健康检查
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return True
        except:
            return False
    
    def add_health_check_callback(self, callback: Callable):
        """添加健康检查回调"""
        self.health_check_callbacks.append(callback)
```

## 故障恢复机制

### 熔断器模式

```python
class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_time
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

## 限流机制

### 令牌桶限流器

```python
import time
from threading import Lock

class TokenBucketRateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, bucket_size: int, refill_rate: float):
        self.bucket_size = bucket_size
        self.refill_rate = refill_rate  # 每秒填充的令牌数
        self.tokens = bucket_size
        self.last_refill = time.time()
        self.lock = Lock()
    
    def acquire(self, tokens: int = 1) -> bool:
        """获取令牌"""
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """填充令牌桶"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
        self.last_refill = now
```

## 轮询池管理器

### 核心管理器

```python
class LLMPollingPool:
    """LLM轮询池管理器"""
    
    def __init__(self, config: PollingPoolConfig):
        self.config = config
        self.instances: List[LLMInstance] = []
        self.scheduler = self._create_scheduler()
        self.health_checker = HealthChecker(config.health_check_interval)
        self.rate_limiters: Dict[str, TokenBucketRateLimiter] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 初始化限流器
        if config.rate_limiting.enabled:
            self._init_rate_limiters()
    
    def _create_scheduler(self) -> Scheduler:
        """创建调度器"""
        strategy = self.config.rotation_strategy
        
        if strategy == "round_robin":
            return RoundRobinScheduler()
        elif strategy == "least_recently_used":
            return LRUScheduler()
        elif strategy == "weighted":
            return WeightedScheduler()
        else:
            raise ValueError(f"不支持的调度策略: {strategy}")
    
    def _init_rate_limiters(self):
        """初始化限流器"""
        for group_name in self.config.task_groups:
            rate_config = self.config.rate_limiting
            
            if rate_config.algorithm == "token_bucket":
                limiter = TokenBucketRateLimiter(
                    bucket_size=rate_config.token_bucket.bucket_size,
                    refill_rate=rate_config.token_bucket.refill_rate
                )
            else:
                # 滑动窗口限流器
                limiter = SlidingWindowRateLimiter(
                    window_size=rate_config.sliding_window.window_size,
                    max_requests=rate_config.sliding_window.max_requests
                )
            
            self.rate_limiters[group_name] = limiter
    
    async def get_instance(self, group_name: str) -> Optional[LLMInstance]:
        """获取可用的LLM实例"""
        # 检查限流
        if not self._check_rate_limit(group_name):
            return None
        
        # 获取组内实例
        group_instances = [inst for inst in self.instances 
                          if inst.group_name == group_name]
        
        if not group_instances:
            return None
        
        # 调度选择实例
        selected_instance = self.scheduler.select_instance(group_instances)
        
        if selected_instance:
            selected_instance.current_load += 1
        
        return selected_instance
    
    def release_instance(self, instance: LLMInstance):
        """释放实例"""
        if instance.current_load > 0:
            instance.current_load -= 1
    
    def _check_rate_limit(self, group_name: str) -> bool:
        """检查速率限制"""
        if group_name not in self.rate_limiters:
            return True
        
        return self.rate_limiters[group_name].acquire()
    
    async def call_llm(self, group_name: str, prompt: str, **kwargs) -> Any:
        """调用LLM"""
        instance = await self.get_instance(group_name)
        
        if not instance:
            raise Exception("没有可用的LLM实例")
        
        try:
            # 检查熔断器
            circuit_breaker = self.circuit_breakers.get(instance.instance_id)
            if circuit_breaker and circuit_breaker.state == "OPEN":
                raise Exception(f"实例 {instance.instance_id} 熔断器已开启")
            
            # 调用LLM
            start_time = time.time()
            result = await self._call_instance(instance, prompt, **kwargs)
            end_time = time.time()
            
            # 更新统计信息
            instance.success_count += 1
            response_time = end_time - start_time
            instance.avg_response_time = (
                (instance.avg_response_time * (instance.success_count - 1) + response_time) / 
                instance.success_count
            )
            
            return result
            
        except Exception as e:
            instance.failure_count += 1
            
            # 更新熔断器状态
            circuit_breaker = self.circuit_breakers.get(instance.instance_id)
            if circuit_breaker:
                circuit_breaker._on_failure()
            
            raise e
        finally:
            self.release_instance(instance)
    
    async def _call_instance(self, instance: LLMInstance, prompt: str, **kwargs) -> Any:
        """调用具体实例"""
        # 这里实现实际的LLM调用逻辑
        pass
    
    async def start(self):
        """启动轮询池"""
        # 启动健康检查
        asyncio.create_task(self.health_checker.start(self.instances))
    
    async def stop(self):
        """停止轮询池"""
        self.health_checker.running = False
```

## 配置集成

### 轮询池配置模型

```python
@dataclass
class PollingPoolConfig:
    """轮询池配置"""
    name: str
    description: str
    task_groups: List[str]
    rotation_strategy: str = "round_robin"
    health_check_interval: int = 30
    failure_threshold: int = 3
    recovery_time: int = 60
    rate_limiting: RateLimitingConfig = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PollingPoolConfig":
        """从字典创建配置"""
        return cls(
            name=config_dict["name"],
            description=config_dict.get("description", ""),
            task_groups=config_dict["task_groups"],
            rotation_strategy=config_dict.get("rotation_strategy", "round_robin"),
            health_check_interval=config_dict.get("health_check_interval", 30),
            failure_threshold=config_dict.get("failure_threshold", 3),
            recovery_time=config_dict.get("recovery_time", 60),
            rate_limiting=RateLimitingConfig.from_dict(
                config_dict.get("rate_limiting", {})
            )
        )
```

## 使用示例

### 创建和使用轮询池

```python
# 创建轮询池配置
pool_config = PollingPoolConfig.from_dict({
    "name": "single_turn_pool",
    "description": "单轮对话轮询池",
    "task_groups": ["fast_group", "fast_small_group"],
    "rotation_strategy": "round_robin",
    "health_check_interval": 30,
    "failure_threshold": 3,
    "recovery_time": 60,
    "rate_limiting": {
        "enabled": True,
        "algorithm": "token_bucket",
        "bucket_size": 1000,
        "refill_rate": 16.67
    }
})

# 创建轮询池
polling_pool = LLMPollingPool(pool_config)

# 添加实例
polling_pool.instances.extend([
    LLMInstance(
        instance_id="gpt4-1",
        model_name="gpt-4",
        group_name="fast_group",
        echelon="echelon1",
        endpoint="https://api.openai.com/v1",
        status=InstanceStatus.HEALTHY,
        last_health_check=datetime.now(),
        max_concurrency=10
    ),
    # 更多实例...
])

# 启动轮询池
await polling_pool.start()

# 使用轮询池调用LLM
try:
    result = await polling_pool.call_llm("fast_group", "Hello, how are you?")
    print(f"LLM响应: {result}")
except Exception as e:
    print(f"调用失败: {e}")

# 停止轮询池
await polling_pool.stop()
```

## 监控和指标

### 性能监控

```python
class PollingPoolMetrics:
    """轮询池指标收集器"""
    
    def __init__(self, polling_pool: LLMPollingPool):
        self.polling_pool = polling_pool
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "instance_utilization": {},
            "rate_limit_hits": 0,
            "circuit_breaker_trips": 0
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        # 计算实例利用率
        for instance in self.polling_pool.instances:
            utilization = instance.current_load / instance.max_concurrency
            self.metrics["instance_utilization"][instance.instance_id] = utilization
        
        return self.metrics
    
    def record_request(self, success: bool, response_time: float):
        """记录请求"""
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # 更新平均响应时间
        total = self.metrics["total_requests"]
        current_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
```

这个轮询池设计提供了完整的负载均衡、健康检查、故障恢复和限流机制，能够确保LLM服务的高可用性和性能。