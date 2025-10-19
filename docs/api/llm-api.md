# LLM模块API文档

本文档提供了LLM模块的完整API参考，包括所有类、方法和函数的详细说明。

## 目录

1. [核心接口](#核心接口)
2. [客户端实现](#客户端实现)
3. [工厂模式](#工厂模式)
4. [配置模型](#配置模型)
5. [数据模型](#数据模型)
6. [钩子机制](#钩子机制)
7. [降级策略](#降级策略)
8. [异常类](#异常类)
9. [工具函数](#工具函数)

## 核心接口

### ILLMClient

LLM客户端的核心接口，定义了所有LLM客户端必须实现的方法。

```python
class ILLMClient(ABC):
    def generate(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本响应"""
        
    async def generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """异步生成文本响应"""
        
    async def stream_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式生成文本响应"""
        
    def get_token_count(self, text: str) -> int:
        """计算文本的token数量"""
        
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表的token数量"""
        
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
```

### ILLMCallHook

LLM调用钩子接口，用于在调用前后执行自定义逻辑。

```python
class ILLMCallHook(ABC):
    def before_call(
        self,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """调用前的钩子"""
        
    def after_call(
        self,
        response: LLMResponse,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """调用后的钩子"""
        
    def on_error(
        self,
        error: Exception,
        messages: List[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """错误处理钩子"""
```

## 客户端实现

### BaseLLMClient

所有LLM客户端的基类，提供了通用的实现逻辑。

```python
class BaseLLMClient(ILLMClient):
    def __init__(self, config: LLMClientConfig) -> None:
        """初始化客户端"""
        
    def add_hook(self, hook: ILLMCallHook) -> None:
        """添加调用钩子"""
        
    def remove_hook(self, hook: ILLMCallHook) -> None:
        """移除调用钩子"""
        
    def clear_hooks(self) -> None:
        """清除所有钩子"""
```

### OpenAIClient

OpenAI API的客户端实现。

```python
class OpenAIClient(BaseLLMClient):
    def __init__(self, config: OpenAIConfig) -> None:
        """初始化OpenAI客户端"""
        
    def get_token_count(self, text: str) -> int:
        """使用tiktoken计算token数量"""
        
    def supports_function_calling(self) -> bool:
        """OpenAI支持函数调用"""
```

### GeminiClient

Google Gemini API的客户端实现。

```python
class GeminiClient(BaseLLMClient):
    def __init__(self, config: GeminiConfig) -> None:
        """初始化Gemini客户端"""
        
    def _convert_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """转换消息格式以适应Gemini API"""
        
    def supports_function_calling(self) -> bool:
        """Gemini支持函数调用"""
```

### AnthropicClient

Anthropic Claude API的客户端实现。

```python
class AnthropicClient(BaseLLMClient):
    def __init__(self, config: AnthropicConfig) -> None:
        """初始化Anthropic客户端"""
        
    def _convert_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """转换消息格式以适应Anthropic API"""
        
    def supports_function_calling(self) -> bool:
        """Anthropic支持函数调用"""
```

### MockLLMClient

用于测试的模拟客户端。

```python
class MockLLMClient(BaseLLMClient):
    def __init__(self, config: MockConfig) -> None:
        """初始化Mock客户端"""
        
    def set_response_template(self, key: str, template: str) -> None:
        """设置响应模板"""
        
    def set_error_rate(self, error_rate: float) -> None:
        """设置错误率"""
        
    def set_response_delay(self, delay: float) -> None:
        """设置响应延迟"""
```

## 工厂模式

### LLMFactory

LLM客户端工厂，负责创建和管理客户端实例。

```python
class LLMFactory(ILLMClientFactory):
    def __init__(self, config: Optional[LLMModuleConfig] = None) -> None:
        """初始化工厂"""
        
    def create_client(self, config: Dict[str, Any]) -> ILLMClient:
        """创建LLM客户端实例"""
        
    def create_client_from_config(self, client_config: LLMClientConfig) -> ILLMClient:
        """从LLMClientConfig创建客户端实例"""
        
    def get_cached_client(self, model_name: str) -> Optional[ILLMClient]:
        """获取缓存的客户端实例"""
        
    def cache_client(self, model_name: str, client: ILLMClient) -> None:
        """缓存客户端实例"""
        
    def get_or_create_client(self, model_name: str, config: Dict[str, Any]) -> ILLMClient:
        """获取或创建客户端实例"""
        
    def clear_cache(self) -> None:
        """清除所有缓存的客户端实例"""
        
    def list_supported_types(self) -> List[str]:
        """列出支持的模型类型"""
        
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
```

### 全局工厂函数

```python
def get_global_factory() -> LLMFactory:
    """获取全局工厂实例"""
    
def set_global_factory(factory: LLMFactory) -> None:
    """设置全局工厂实例"""
    
def create_client(config: Dict[str, Any]) -> ILLMClient:
    """使用全局工厂创建客户端"""
    
def get_cached_client(model_name: str) -> Optional[ILLMClient]:
    """使用全局工厂获取缓存的客户端"""
```

## 配置模型

### LLMClientConfig

LLM客户端的基础配置。

```python
@dataclass
class LLMClientConfig:
    model_type: str
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None
    fallback_enabled: bool = True
    fallback_models: List[str] = field(default_factory=list)
    max_fallback_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 特定模型配置

```python
@dataclass
class OpenAIConfig(LLMClientConfig):
    organization: Optional[str] = None
    
@dataclass
class GeminiConfig(LLMClientConfig):
    pass
    
@dataclass
class AnthropicConfig(LLMClientConfig):
    pass
    
@dataclass
class MockConfig(LLMClientConfig):
    response_delay: float = 0.1
    error_rate: float = 0.0
    error_types: List[str] = field(default_factory=lambda: ["timeout", "rate_limit"])
```

### LLMModuleConfig

LLM模块的配置。

```python
@dataclass
class LLMModuleConfig:
    default_model: str = "openai-gpt4"
    default_timeout: int = 30
    default_max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 100
    hooks_enabled: bool = True
    log_requests: bool = True
    log_responses: bool = True
    log_errors: bool = True
    fallback_enabled: bool = True
    global_fallback_models: List[str] = field(default_factory=list)
    max_concurrent_requests: int = 10
    request_queue_size: int = 100
    metrics_enabled: bool = True
    performance_tracking: bool = True
```

## 数据模型

### LLMResponse

LLM响应模型。

```python
@dataclass
class LLMResponse:
    content: str
    message: BaseMessage
    token_usage: TokenUsage
    model: str
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

### TokenUsage

Token使用情况模型。

```python
@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        """合并Token使用情况"""
```

### ModelInfo

模型信息模型。

```python
@dataclass
class ModelInfo:
    name: str
    type: str
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None
    supports_function_calling: bool = False
    supports_streaming: bool = True
    pricing: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## 钩子机制

### LoggingHook

日志记录钩子。

```python
class LoggingHook(ILLMCallHook):
    def __init__(
        self,
        log_requests: bool = True,
        log_responses: bool = True,
        log_errors: bool = True
    ) -> None:
        """初始化日志钩子"""
```

### MetricsHook

指标收集钩子。

```python
class MetricsHook(ILLMCallHook):
    def __init__(self) -> None:
        """初始化指标钩子"""
        
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        
    def reset_metrics(self) -> None:
        """重置指标"""
```

### FallbackHook

降级处理钩子。

```python
class FallbackHook(ILLMCallHook):
    def __init__(
        self,
        fallback_models: List[str],
        max_attempts: int = 3
    ) -> None:
        """初始化降级钩子"""
```

### RetryHook

重试钩子。

```python
class RetryHook(ILLMCallHook):
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> None:
        """初始化重试钩子"""
```

### CompositeHook

组合钩子。

```python
class CompositeHook(ILLMCallHook):
    def __init__(self, hooks: List[ILLMCallHook]) -> None:
        """初始化组合钩子"""
        
    def add_hook(self, hook: ILLMCallHook) -> None:
        """添加钩子"""
        
    def remove_hook(self, hook: ILLMCallHook) -> None:
        """移除钩子"""
```

## 降级策略

### FallbackManager

降级管理器。

```python
class FallbackManager:
    def __init__(
        self,
        fallback_models: List[FallbackModel],
        strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
        max_attempts: int = 3,
        timeout: float = 30.0
    ) -> None:
        """初始化降级管理器"""
        
    def execute_fallback(
        self,
        primary_client: ILLMClient,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """执行降级策略"""
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        
    def reset_stats(self) -> None:
        """重置统计信息"""
```

### FallbackModel

降级模型配置。

```python
@dataclass
class FallbackModel:
    name: str
    priority: int = 0
    weight: float = 1.0
    enabled: bool = True
    conditions: Optional[List[Callable[[Exception], bool]]] = None
```

### FallbackStrategy

降级策略枚举。

```python
class FallbackStrategy(Enum):
    SEQUENTIAL = "sequential"  # 顺序降级
    PARALLEL = "parallel"    # 并行降级
    RANDOM = "random"        # 随机降级
    PRIORITY = "priority"    # 优先级降级
```

### ConditionalFallback

条件降级工具类。

```python
class ConditionalFallback:
    @staticmethod
    def on_timeout(error: Exception) -> bool:
        """超时条件"""
        
    @staticmethod
    def on_rate_limit(error: Exception) -> bool:
        """频率限制条件"""
        
    @staticmethod
    def on_service_unavailable(error: Exception) -> bool:
        """服务不可用条件"""
        
    @staticmethod
    def on_retryable_error(error: Exception) -> bool:
        """可重试错误条件"""
```

## 异常类

### 基础异常

```python
class LLMError(Exception):
    """LLM模块基础异常"""
    
class LLMClientCreationError(LLMError):
    """LLM客户端创建错误"""
    
class UnsupportedModelTypeError(LLMError):
    """不支持的模型类型错误"""
```

### 调用异常

```python
class LLMCallError(LLMError):
    """LLM调用错误"""
    
class LLMTimeoutError(LLMCallError):
    """LLM调用超时错误"""
    
class LLMRateLimitError(LLMCallError):
    """LLM调用频率限制错误"""
    
class LLMAuthenticationError(LLMCallError):
    """LLM认证错误"""
    
class LLMModelNotFoundError(LLMCallError):
    """LLM模型未找到错误"""
    
class LLMTokenLimitError(LLMCallError):
    """LLM Token限制错误"""
    
class LLMContentFilterError(LLMCallError):
    """LLM内容过滤错误"""
    
class LLMServiceUnavailableError(LLMCallError):
    """LLM服务不可用错误"""
    
class LLMInvalidRequestError(LLMCallError):
    """LLM无效请求错误"""
```

### 配置异常

```python
class LLMConfigurationError(LLMError):
    """LLM配置错误"""
    
class LLMFallbackError(LLMError):
    """LLM降级错误"""
```

## 工具函数

### 配置转换

```python
def from_dict(config_dict: Dict[str, Any]) -> LLMClientConfig:
    """从字典创建配置"""
```

### Token计算

```python
def estimate_tokens(text: str) -> int:
    """估算文本的token数量"""
```

### 错误处理

```python
def is_retryable_error(error: Exception) -> bool:
    """判断错误是否可重试"""
    
def get_error_type(error: Exception) -> str:
    """获取错误类型"""
```

---

更多详细信息请参考源代码注释和使用示例。