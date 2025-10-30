# LLM降级系统API参考

## 核心类和接口

### FallbackClientWrapper

降级客户端包装器，实现了 `ILLMClient` 接口。

```python
class FallbackClientWrapper(ILLMClient):
    def __init__(
        self, 
        primary_client: ILLMClient, 
        fallback_models: List[str],
        strategy_type: str = "sequential",
        max_attempts: int = 3,
        **config_kwargs
    ) -> None
```

**参数：**
- `primary_client`: 主LLM客户端
- `fallback_models`: 降级模型列表
- `strategy_type`: 降级策略类型
- `max_attempts`: 最大尝试次数
- `**config_kwargs`: 其他配置参数

**方法：**
```python
def generate(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> LLMResponse
async def generate_async(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> LLMResponse
def stream_generate(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Generator[str, None, None]
async def stream_generate_async(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> AsyncGenerator[str, None]
def get_fallback_stats(self) -> Dict[str, Any]
def reset_fallback_stats(self) -> None
def update_fallback_config(self, **config_kwargs) -> None
def get_fallback_sessions(self, limit: Optional[int] = None)
def is_fallback_enabled(self) -> bool
```

### FallbackConfig

降级配置类。

```python
@dataclass
class FallbackConfig:
    enabled: bool = True
    max_attempts: int = 3
    fallback_models: List[str] = field(default_factory=list)
    strategy_type: str = "sequential"
    error_mappings: Dict[str, List[str]] = field(default_factory=dict)
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    fallback_on_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    fallback_on_errors: List[str] = field(default_factory=lambda: ["timeout", "rate_limit", "service_unavailable", "overloaded_error"])
    provider_config: Dict[str, Any] = field(default_factory=dict)
```

**方法：**
```python
def is_enabled(self) -> bool
def get_max_attempts(self) -> int
def get_fallback_models(self) -> List[str]
def should_fallback_on_error(self, error: Exception) -> bool
def calculate_delay(self, attempt: int) -> float
@classmethod
def from_dict(cls, config_dict: Dict[str, Any]) -> "FallbackConfig"
def to_dict(self) -> Dict[str, Any]
```

### FallbackManager

降级管理器，负责协调降级逻辑。

```python
class FallbackManager:
    def __init__(self, config: FallbackConfig, client_factory: IClientFactory, logger: Optional[IFallbackLogger] = None)
```

**方法：**
```python
async def generate_with_fallback(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, primary_model: Optional[str] = None, **kwargs: Any) -> LLMResponse
def generate_with_fallback_sync(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, primary_model: Optional[str] = None, **kwargs: Any) -> LLMResponse
async def generate_with_fallback_async(self, messages: Sequence[BaseMessage], parameters: Optional[Dict[str, Any]] = None, primary_model: Optional[str] = None, **kwargs: Any) -> LLMResponse
def get_stats(self) -> Dict[str, Any]
def get_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]
def clear_sessions(self) -> None
def is_enabled(self) -> bool
def get_available_models(self) -> List[str]
def update_config(self, config: FallbackConfig) -> None
```

## 降级策略接口

### IFallbackStrategy

降级策略接口。

```python
class IFallbackStrategy(ABC):
    @abstractmethod
    def should_fallback(self, error: Exception, attempt: int) -> bool
    
    @abstractmethod
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]
    
    @abstractmethod
    def get_fallback_delay(self, error: Exception, attempt: int) -> float
```

### SequentialFallbackStrategy

顺序降级策略。

```python
class SequentialFallbackStrategy(IFallbackStrategy):
    def __init__(self, config: FallbackConfig)
```

### PriorityFallbackStrategy

优先级降级策略。

```python
class PriorityFallbackStrategy(IFallbackStrategy):
    def __init__(self, config: FallbackConfig, priority_map: Optional[dict] = None)
```

### RandomFallbackStrategy

随机降级策略。

```python
class RandomFallbackStrategy(IFallbackStrategy):
    def __init__(self, config: FallbackConfig)
```

### ErrorTypeBasedStrategy

基于错误类型的降级策略。

```python
class ErrorTypeBasedStrategy(IFallbackStrategy):
    def __init__(self, config: FallbackConfig, error_model_mapping: Optional[dict] = None)
```

### ParallelFallbackStrategy

并行降级策略。

```python
class ParallelFallbackStrategy(IFallbackStrategy):
    def __init__(self, config: FallbackConfig, timeout: float = 30.0)
    
    async def execute_parallel_fallback(self, client_factory, messages, parameters, primary_model, **kwargs)
```

### ConditionalFallbackStrategy

条件降级策略。

```python
class ConditionalFallbackStrategy(IFallbackStrategy):
    def __init__(self, config: FallbackConfig, conditions: Optional[List[Callable[[Exception], bool]]] = None)
```

## 工厂函数

### create_fallback_manager

创建降级管理器。

```python
def create_fallback_manager(config: FallbackConfig, owner_client: Optional[Any] = None) -> FallbackManager
```

### create_fallback_strategy

创建降级策略。

```python
def create_fallback_strategy(config: FallbackConfig, **kwargs) -> IFallbackStrategy
```

**支持的策略类型：**
- `"sequential"` → `SequentialFallbackStrategy`
- `"priority"` → `PriorityFallbackStrategy`
- `"random"` → `RandomFallbackStrategy`
- `"error_type"` → `ErrorTypeBasedStrategy`
- `"parallel"` → `ParallelFallbackStrategy`
- `"conditional"` → `ConditionalFallbackStrategy`

## 条件降级工具类

### ConditionalFallback

条件降级工具类，提供常用的条件判断函数。

```python
class ConditionalFallback:
    @staticmethod
    def on_timeout(error: Exception) -> bool
    
    @staticmethod
    def on_rate_limit(error: Exception) -> bool
    
    @staticmethod
    def on_service_unavailable(error: Exception) -> bool
    
    @staticmethod
    def on_authentication_error(error: Exception) -> bool
    
    @staticmethod
    def on_model_not_found(error: Exception) -> bool
    
    @staticmethod
    def on_token_limit(error: Exception) -> bool
    
    @staticmethod
    def on_content_filter(error: Exception) -> bool
    
    @staticmethod
    def on_invalid_request(error: Exception) -> bool
    
    @staticmethod
    def on_any_error(error: Exception) -> bool
    
    @staticmethod
    def on_retryable_error(error: Exception) -> bool
```

## 会话和尝试记录

### FallbackSession

降级会话记录。

```python
@dataclass
class FallbackSession:
    primary_model: str
    start_time: float
    end_time: Optional[float] = None
    attempts: List[FallbackAttempt] = field(default_factory=list)
    success: bool = False
    final_response: Optional[Any] = None
    final_error: Optional[Exception] = None
```

**方法：**
```python
def add_attempt(self, attempt: FallbackAttempt) -> None
def mark_success(self, response: Any) -> None
def mark_failure(self, error: Exception) -> None
def get_total_duration(self) -> Optional[float]
def get_total_attempts(self) -> int
def get_successful_attempt(self) -> Optional[FallbackAttempt]
def to_dict(self) -> Dict[str, Any]
```

### FallbackAttempt

降级尝试记录。

```python
@dataclass
class FallbackAttempt:
    primary_model: str
    fallback_model: Optional[str]
    error: Optional[Exception]
    attempt_number: int
    timestamp: float
    success: bool
    response: Optional[Any] = None
    delay: float = 0.0
```

**方法：**
```python
def get_duration(self) -> Optional[float]
def to_dict(self) -> Dict[str, Any]
```

## 客户端工厂接口

### IClientFactory

客户端工厂接口。

```python
class IClientFactory(ABC):
    @abstractmethod
    def create_client(self, model_name: str) -> Any
    
    @abstractmethod
    def get_available_models(self) -> List[str]
```

### SelfManagingFallbackFactory

自管理降级工厂，用于单个客户端的自我降级。

```python
class SelfManagingFallbackFactory(IClientFactory):
    def __init__(self, owner_client: Any)
    
    def create_client(self, model_name: str) -> Any
    def get_available_models(self) -> List[str]
```

## 日志记录器接口

### IFallbackLogger

降级日志记录器接口。

```python
class IFallbackLogger(ABC):
    @abstractmethod
    def log_fallback_attempt(self, primary_model: str, fallback_model: str, error: Exception, attempt: int) -> None
    
    @abstractmethod
    def log_fallback_success(self, primary_model: str, fallback_model: str, response: LLMResponse, attempt: int) -> None
    
    @abstractmethod
    def log_fallback_failure(self, primary_model: str, error: Exception, total_attempts: int) -> None
```

### DefaultFallbackLogger

默认降级日志记录器实现。

```python
class DefaultFallbackLogger(IFallbackLogger):
    def __init__(self, enabled: bool = True)
    
    def log_fallback_attempt(self, primary_model: str, fallback_model: str, error: Exception, attempt: int) -> None
    def log_fallback_success(self, primary_model: str, fallback_model: str, response: LLMResponse, attempt: int) -> None
    def log_fallback_failure(self, primary_model: str, error: Exception, total_attempts: int) -> None
    def add_session(self, session: FallbackSession) -> None
    def get_sessions(self) -> List[FallbackSession]
    def clear_sessions(self) -> None
```

## 异常类

### LLMFallbackError

降级失败异常。

```python
class LLMFallbackError(Exception):
    def __init__(self, message: str, original_error: Optional[Exception] = None)
```

## 统计信息格式

```python
{
    "total_sessions": int,           # 总会话数
    "successful_sessions": int,      # 成功会话数
    "failed_sessions": int,          # 失败会话数
    "success_rate": float,           # 成功率 (0.0-1.0)
    "total_attempts": int,           # 总尝试次数
    "average_attempts": float,       # 平均尝试次数
    "fallback_usage": int,           # 使用降级的会话数
    "fallback_rate": float,          # 降级使用率 (0.0-1.0)
    "config": Dict[str, Any]         # 配置信息
}
```

## 配置字典格式

```python
{
    "enabled": bool,
    "max_attempts": int,
    "fallback_models": List[str],
    "strategy_type": str,
    "error_mappings": Dict[str, List[str]],
    "base_delay": float,
    "max_delay": float,
    "exponential_base": float,
    "jitter": bool,
    "fallback_on_status_codes": List[int],
    "fallback_on_errors": List[str],
    "provider_config": Dict[str, Any]
}
```

## 使用示例

### 基础使用

```python
from src.infrastructure.llm.fallback_client import FallbackClientWrapper
from src.infrastructure.llm.fallback_system import FallbackConfig

# 创建配置
config = FallbackConfig(
    enabled=True,
    fallback_models=["gpt-3.5-turbo", "claude-instant"],
    strategy_type="sequential",
    max_attempts=3
)

# 创建降级包装器
fallback_wrapper = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=config.fallback_models,
    strategy_type=config.strategy_type,
    max_attempts=config.max_attempts
)

# 使用
response = fallback_wrapper.generate(messages)
```

### 高级使用

```python
from src.infrastructure.llm.fallback_system import (
    FallbackConfig, 
    create_fallback_manager,
    PriorityFallbackStrategy,
    ConditionalFallback
)

# 创建配置
config = FallbackConfig(
    enabled=True,
    fallback_models=["gpt-3.5-turbo", "claude-instant", "gemini-pro"],
    strategy_type="priority",
    max_attempts=5
)

# 创建优先级映射
priority_map = {
    "RateLimitError": ["claude-instant", "gemini-pro"],
    "TimeoutError": ["gpt-3.5-turbo"]
}

# 创建降级管理器
fallback_manager = create_fallback_manager(config)
fallback_manager._strategy = PriorityFallbackStrategy(config, priority_map)

# 使用
response = await fallback_manager.generate_with_fallback_async(
    messages, 
    parameters={}, 
    primary_model="gpt-4"
)