# Graph Hook系统API参考

## 核心接口

### INodeHook

Hook的基础接口，所有Hook都必须实现此接口。

```python
class INodeHook(ABC):
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化Hook
        
        Args:
            hook_config: Hook配置字典
        """
    
    @property
    @abstractmethod
    def hook_type(self) -> str:
        """Hook类型标识"""
        pass
    
    @abstractmethod
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行前Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        pass
    
    @abstractmethod
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        pass
    
    @abstractmethod
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查Hook是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.enabled
    
    def validate_config(self) -> List[str]:
        """验证Hook配置
        
        Returns:
            List[str]: 验证错误列表
        """
        return []
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点
        
        Returns:
            List[HookPoint]: 支持的Hook执行点列表
        """
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]
```

### IHookManager

Hook管理器接口，负责Hook的注册、执行和配置管理。

```python
class IHookManager(ABC):
    @abstractmethod
    def register_hook(self, hook: INodeHook, node_types: Optional[List[str]] = None) -> None:
        """注册Hook
        
        Args:
            hook: Hook实例
            node_types: 适用的节点类型列表，None表示全局Hook
        """
        pass
    
    @abstractmethod
    def get_hooks_for_node(self, node_type: str) -> List[INodeHook]:
        """获取指定节点的Hook列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[INodeHook]: Hook列表
        """
        pass
    
    @abstractmethod
    def execute_hooks(
        self, 
        hook_point: HookPoint, 
        context: HookContext
    ) -> HookExecutionResult:
        """执行指定Hook点的所有Hook
        
        Args:
            hook_point: Hook执行点
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: 合并后的Hook执行结果
        """
        pass
    
    @abstractmethod
    def load_hooks_from_config(self, config_path: str) -> None:
        """从配置文件加载Hook
        
        Args:
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def clear_hooks(self) -> None:
        """清除所有Hook"""
        pass
```

## 数据结构

### HookContext

Hook执行上下文，包含Hook执行所需的所有信息。

```python
@dataclass
class HookContext:
    node_type: str                    # 节点类型
    state: AgentState                  # Agent状态
    config: Dict[str, Any]            # 节点配置
    hook_point: HookPoint              # Hook执行点
    error: Optional[Exception] = None  # 错误信息（仅ON_ERROR时）
    execution_result: Optional[NodeExecutionResult] = None  # 执行结果（仅AFTER_EXECUTE时）
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据
    hook_manager: Optional[IHookManager] = None  # Hook管理器引用
```

### HookExecutionResult

Hook执行结果，包含Hook的执行结果和可能的修改。

```python
class HookExecutionResult:
    def __init__(
        self,
        should_continue: bool = True,                    # 是否继续执行
        modified_state: Optional[AgentState] = None,     # 修改后的状态
        modified_result: Optional[NodeExecutionResult] = None,  # 修改后的执行结果
        force_next_node: Optional[str] = None,           # 强制指定的下一个节点
        metadata: Optional[Dict[str, Any]] = None        # Hook执行元数据
    ) -> None:
        pass
    
    def __bool__(self) -> bool:
        """布尔值转换，表示是否继续执行"""
        return self.should_continue
```

### HookPoint

Hook执行点枚举。

```python
class HookPoint(Enum):
    BEFORE_EXECUTE = "before_execute"  # 节点执行前
    AFTER_EXECUTE = "after_execute"    # 节点执行后
    ON_ERROR = "on_error"              # 节点出错时
```

## 配置模型

### HookConfig

Hook配置模型。

```python
class HookConfig(BaseModel):
    type: HookType = Field(..., description="Hook类型")
    enabled: bool = Field(True, description="是否启用")
    config: Dict[str, Any] = Field(default_factory=dict, description="Hook特定配置")
    node_types: Optional[List[str]] = Field(None, description="适用的节点类型列表")
    priority: int = Field(0, description="Hook执行优先级")
```

### NodeHookConfig

节点Hook配置模型。

```python
class NodeHookConfig(BaseModel):
    node_type: str = Field(..., description="节点类型")
    hooks: List[HookConfig] = Field(default_factory=list, description="Hook配置列表")
    inherit_global: bool = Field(True, description="是否继承全局Hook配置")
```

### GlobalHookConfig

全局Hook配置模型。

```python
class GlobalHookConfig(BaseModel):
    hooks: List[HookConfig] = Field(default_factory=list, description="全局Hook配置列表")
```

## 核心实现类

### NodeHookManager

Hook管理器的默认实现。

```python
class NodeHookManager(IHookManager):
    def __init__(self, config_loader) -> None:
        """初始化Hook管理器
        
        Args:
            config_loader: 配置加载器
        """
    
    def register_hook(self, hook: INodeHook, node_types: Optional[List[str]] = None) -> None:
        """注册Hook"""
        pass
    
    def get_hooks_for_node(self, node_type: str) -> List[INodeHook]:
        """获取指定节点的Hook列表"""
        pass
    
    def execute_hooks(
        self, 
        hook_point: HookPoint, 
        context: HookContext
    ) -> HookExecutionResult:
        """执行指定Hook点的所有Hook"""
        pass
    
    def load_hooks_from_config(self, config_path: Optional[str] = None) -> None:
        """从配置文件加载Hook"""
        pass
    
    def load_node_hooks_from_config(self, node_type: str) -> None:
        """从配置文件加载指定节点的Hook"""
        pass
    
    def clear_hooks(self) -> None:
        """清除所有Hook"""
        pass
    
    def get_execution_count(self, node_type: str) -> int:
        """获取节点执行次数"""
        pass
    
    def increment_execution_count(self, node_type: str) -> int:
        """增加节点执行计数"""
        pass
    
    def reset_execution_count(self, node_type: str) -> None:
        """重置节点执行计数"""
        pass
    
    def update_performance_stats(
        self, 
        node_type: str, 
        execution_time: float, 
        success: bool = True
    ) -> None:
        """更新性能统计"""
        pass
    
    def get_performance_stats(self, node_type: str) -> Dict[str, Any]:
        """获取性能统计"""
        pass
```

### HookAwareGraphBuilder

支持Hook的Graph构建器。

```python
class HookAwareGraphBuilder(GraphBuilder):
    def __init__(
        self,
        node_registry=None,
        template_registry=None,
        hook_manager: Optional[IHookManager] = None,
        config_loader=None
    ) -> None:
        """初始化Hook感知的Graph构建器"""
        pass
    
    def set_hook_manager(self, hook_manager: IHookManager) -> None:
        """设置Hook管理器"""
        pass
    
    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateCollaborationManager] = None):
        """构建LangGraph图（支持Hook）"""
        pass
    
    def build_from_yaml(self, yaml_path: str, state_manager: Optional[IStateCollaborationManager] = None):
        """从YAML文件构建图（支持Hook）"""
        pass
    
    def add_hook_to_node(self, node_type: str, hook, is_global: bool = False) -> None:
        """向节点添加Hook"""
        pass
    
    def remove_hooks_from_node(self, node_type: str) -> None:
        """移除节点的所有Hook"""
        pass
    
    def get_hook_statistics(self) -> Dict[str, Any]:
        """获取Hook统计信息"""
        pass
    
    def enable_hooks_for_graph(self, graph_config: GraphConfig) -> None:
        """为图启用Hook"""
        pass
    
    def disable_hooks_for_graph(self) -> None:
        """禁用图的所有Hook"""
        pass
```

## 内置Hook类

### DeadLoopDetectionHook

死循环检测Hook。

```python
class DeadLoopDetectionHook(INodeHook):
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化死循环检测Hook
        
        配置参数:
        - max_iterations: 最大迭代次数 (默认: 20)
        - fallback_node: 回退节点 (默认: "dead_loop_check")
        - log_level: 日志级别 (默认: "WARNING")
        - check_interval: 检查间隔 (默认: 1)
        - reset_on_success: 成功时重置计数 (默认: True)
        """
        pass
    
    @property
    def hook_type(self) -> str:
        return "dead_loop_detection"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行前检查死循环"""
        pass
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后更新计数"""
        pass
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误时不重置计数"""
        pass
```

### PerformanceMonitoringHook

性能监控Hook。

```python
class PerformanceMonitoringHook(INodeHook):
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化性能监控Hook
        
        配置参数:
        - timeout_threshold: 超时阈值 (默认: 10.0)
        - log_slow_executions: 记录慢执行 (默认: True)
        - metrics_collection: 收集指标 (默认: True)
        - slow_execution_threshold: 慢执行阈值 (默认: 5.0)
        - enable_profiling: 启用性能分析 (默认: False)
        """
        pass
    
    @property
    def hook_type(self) -> str:
        return "performance_monitoring"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始时间"""
        pass
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """计算执行时间并记录"""
        pass
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误执行时间"""
        pass
```

### ErrorRecoveryHook

错误恢复Hook。

```python
class ErrorRecoveryHook(INodeHook):
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化错误恢复Hook
        
        配置参数:
        - max_retries: 最大重试次数 (默认: 3)
        - fallback_node: 回退节点 (默认: "error_handler")
        - retry_delay: 重试延迟 (默认: 1.0)
        - exponential_backoff: 指数退避 (默认: True)
        - retry_on_exceptions: 重试异常类型 (默认: ["Exception"])
        """
        pass
    
    @property
    def hook_type(self) -> str:
        return "error_recovery"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """检查重试次数"""
        pass
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """成功执行后重置重试计数"""
        pass
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理和重试逻辑"""
        pass
```

### LoggingHook

日志Hook。

```python
class LoggingHook(INodeHook):
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化日志Hook
        
        配置参数:
        - log_level: 日志级别 (默认: "INFO")
        - structured_logging: 结构化日志 (默认: True)
        - log_execution_time: 记录执行时间 (默认: True)
        - log_state_changes: 记录状态变化 (默认: False)
        - log_format: 日志格式 (默认: "json")
        """
        pass
    
    @property
    def hook_type(self) -> str:
        return "logging"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行开始日志"""
        pass
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """记录节点执行完成日志"""
        pass
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """记录错误日志"""
        pass
```

### MetricsCollectionHook

指标收集Hook。

```python
class MetricsCollectionHook(INodeHook):
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化指标收集Hook
        
        配置参数:
        - enable_performance_metrics: 启用性能指标 (默认: True)
        - enable_business_metrics: 启用业务指标 (默认: True)
        - enable_system_metrics: 启用系统指标 (默认: False)
        - metrics_endpoint: 指标端点 (默认: None)
        - collection_interval: 收集间隔 (默认: 60)
        """
        pass
    
    @property
    def hook_type(self) -> str:
        return "metrics_collection"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """记录开始指标"""
        pass
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """收集执行指标"""
        pass
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """收集错误指标"""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取收集的指标"""
        pass
    
    def reset_metrics(self) -> None:
        """重置指标"""
        pass
```

## 装饰器和工具函数

### with_hooks

Hook装饰器，用于为节点执行方法添加Hook支持。

```python
def with_hooks(hook_manager: Optional[IHookManager] = None):
    """Hook装饰器工厂函数
    
    Args:
        hook_manager: Hook管理器实例，如果为None则尝试从全局获取
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(execute_method: Callable) -> Callable:
        """装饰器函数"""
        @functools.wraps(execute_method)
        def wrapper(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
            """包装的执行方法"""
            # Hook执行逻辑
            pass
        return wrapper
    return decorator
```

### make_node_hookable

将现有节点类转换为支持Hook的节点类。

```python
def make_node_hookable(node_class: type, hook_manager: Optional[IHookManager] = None) -> type:
    """将现有节点类转换为支持Hook的节点类
    
    Args:
        node_class: 原始节点类
        hook_manager: Hook管理器实例
        
    Returns:
        type: 支持Hook的节点类
    """
    pass
```

### create_hook_aware_builder

创建Hook感知的Graph构建器。

```python
def create_hook_aware_builder(
    node_registry=None,
    template_registry=None,
    hook_manager: Optional[IHookManager] = None,
    config_loader=None
) -> HookAwareGraphBuilder:
    """创建Hook感知的Graph构建器
    
    Args:
        node_registry: 节点注册表
        template_registry: 模板注册表
        hook_manager: Hook管理器
        config_loader: 配置加载器
        
    Returns:
        HookAwareGraphBuilder: Hook感知的Graph构建器
    """
    pass
```

### create_builtin_hook

创建内置Hook实例。

```python
def create_builtin_hook(hook_config: Dict[str, Any]) -> Optional[INodeHook]:
    """创建内置Hook实例
    
    Args:
        hook_config: Hook配置
        
    Returns:
        Optional[INodeHook]: Hook实例
    """
    pass
```

## 配置函数

### create_hook_config

创建Hook配置。

```python
def create_hook_config(hook_type: HookType, **kwargs) -> HookConfig:
    """创建Hook配置
    
    Args:
        hook_type: Hook类型
        **kwargs: 配置参数
        
    Returns:
        HookConfig: Hook配置实例
    """
    pass
```

### validate_hook_config

验证Hook配置。

```python
def validate_hook_config(config: Dict[str, Any]) -> List[str]:
    """验证Hook配置
    
    Args:
        config: Hook配置字典
        
    Returns:
        List[str]: 验证错误列表
    """
    pass
```

### merge_hook_configs

合并全局和节点Hook配置。

```python
def merge_hook_configs(
    global_config: GlobalHookConfig,
    node_config: NodeHookConfig
) -> List[HookConfig]:
    """合并全局和节点Hook配置
    
    Args:
        global_config: 全局Hook配置
        node_config: 节点Hook配置
        
    Returns:
        List[HookConfig]: 合并后的Hook配置列表
    """
    pass
```

## 全局函数

### set_global_hook_manager

设置全局Hook管理器。

```python
def set_global_hook_manager(hook_manager: IHookManager) -> None:
    """设置全局Hook管理器
    
    Args:
        hook_manager: Hook管理器实例
    """
    pass
```

### get_global_hook_manager

获取全局Hook管理器。

```python
def get_global_hook_manager() -> Optional[IHookManager]:
    """获取全局Hook管理器
    
    Returns:
        Optional[IHookManager]: Hook管理器实例
    """
    pass
```

### clear_global_hook_manager

清除全局Hook管理器。

```python
def clear_global_hook_manager() -> None:
    """清除全局Hook管理器"""
    pass
```

## 异常类

Hook系统可能抛出的异常：

```python
# 配置相关异常
class ConfigurationError(Exception):
    """配置错误"""
    pass

# Hook执行相关异常
class HookExecutionError(Exception):
    """Hook执行错误"""
    pass

# Hook注册相关异常
class HookRegistrationError(Exception):
    """Hook注册错误"""
    pass
```

## 类型定义

```python
# Hook类型枚举
class HookType(str, Enum):
    DEAD_LOOP_DETECTION = "dead_loop_detection"
    PERFORMANCE_MONITORING = "performance_monitoring"
    ERROR_RECOVERY = "error_recovery"
    LOGGING = "logging"
    METRICS_COLLECTION = "metrics_collection"
    CUSTOM = "custom"

# 配置值类型
ConfigValue = TypeVar("ConfigValue", Dict[str, Any], List[Any], str, Any)

# Hook工厂函数类型
HookFactory = Callable[[Dict[str, Any]], Optional[INodeHook]]