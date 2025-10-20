# 工作流系统API参考

本文档提供工作流系统所有公共API的详细参考。

## 目录

1. [核心模块](#核心模块)
2. [配置模块](#配置模块)
3. [节点系统](#节点系统)
4. [边系统](#边系统)
5. [工作流管理](#工作流管理)
6. [会话管理](#会话管理)
7. [触发器系统](#触发器系统)
8. [性能优化](#性能优化)
9. [可视化](#可视化)

## 核心模块

### WorkflowManager

工作流管理器，负责工作流的加载、创建和执行。

```python
class WorkflowManager(IWorkflowManager):
    def __init__(
        self,
        config_loader: Optional[IConfigLoader] = None,
        node_registry: Optional[NodeRegistry] = None,
        workflow_builder: Optional[WorkflowBuilder] = None
    ) -> None
```

#### 方法

##### load_workflow(config_path: str) -> str

加载工作流配置并返回工作流ID。

**参数：**
- `config_path` (str): 配置文件路径

**返回：**
- `str`: 工作流ID

**异常：**
- `FileNotFoundError`: 配置文件不存在
- `ValueError`: 配置验证失败

**示例：**
```python
manager = WorkflowManager()
workflow_id = manager.load_workflow("configs/workflows/react.yaml")
```

##### create_workflow(workflow_id: str) -> Any

创建工作流实例。

**参数：**
- `workflow_id` (str): 工作流ID

**返回：**
- `Any`: 工作流实例

**异常：**
- `ValueError`: 工作流不存在

##### run_workflow(workflow_id: str, initial_state: Optional[AgentState] = None, **kwargs) -> AgentState

运行工作流。

**参数：**
- `workflow_id` (str): 工作流ID
- `initial_state` (Optional[AgentState]): 初始状态
- `**kwargs`: 其他参数

**返回：**
- `AgentState`: 最终状态

##### run_workflow_async(workflow_id: str, initial_state: Optional[AgentState] = None, **kwargs) -> AgentState

异步运行工作流。

**参数：**
- `workflow_id` (str): 工作流ID
- `initial_state` (Optional[AgentState]): 初始状态
- `**kwargs`: 其他参数

**返回：**
- `AgentState`: 最终状态

##### stream_workflow(workflow_id: str, initial_state: Optional[AgentState] = None, **kwargs) -> Iterator[AgentState]

流式运行工作流。

**参数：**
- `workflow_id` (str): 工作流ID
- `initial_state` (Optional[AgentState]): 初始状态
- `**kwargs`: 其他参数

**返回：**
- `Iterator[AgentState]`: 中间状态生成器

##### list_workflows() -> List[str]

列出所有已加载的工作流。

**返回：**
- `List[str]`: 工作流ID列表

##### get_workflow_config(workflow_id: str) -> Optional[WorkflowConfig]

获取工作流配置。

**参数：**
- `workflow_id` (str): 工作流ID

**返回：**
- `Optional[WorkflowConfig]`: 工作流配置

##### unload_workflow(workflow_id: str) -> bool

卸载工作流。

**参数：**
- `workflow_id` (str): 工作流ID

**返回：**
- `bool`: 是否成功卸载

### WorkflowBuilder

工作流构建器，负责根据配置构建LangGraph工作流。

```python
class WorkflowBuilder:
    def __init__(self, node_registry: Optional[NodeRegistry] = None) -> None
```

#### 方法

##### load_workflow_config(config_path: str) -> WorkflowConfig

加载工作流配置。

**参数：**
- `config_path` (str): 配置文件路径

**返回：**
- `WorkflowConfig`: 工作流配置

##### build_workflow(config: WorkflowConfig) -> Any

根据配置构建工作流。

**参数：**
- `config` (WorkflowConfig): 工作流配置

**返回：**
- `Any`: 编译后的工作流

##### list_available_nodes() -> List[str]

列出所有可用的节点类型。

**返回：**
- `List[str]`: 节点类型列表

##### get_workflow_config(name: str) -> Optional[WorkflowConfig]

获取已加载的工作流配置。

**参数：**
- `name` (str): 工作流名称

**返回：**
- `Optional[WorkflowConfig]`: 工作流配置

##### clear_cache() -> None

清除缓存的配置。

## 配置模块

### WorkflowConfig

工作流配置模型。

```python
@dataclass
class WorkflowConfig:
    name: str
    description: str
    version: str = "1.0"
    state_schema: StateSchemaConfig = field(default_factory=StateSchemaConfig)
    nodes: Dict[str, NodeConfig] = field(default_factory=dict)
    edges: List[EdgeConfig] = field(default_factory=list)
    entry_point: Optional[str] = None
    additional_config: Dict[str, Any] = field(default_factory=dict)
```

#### 类方法

##### from_dict(data: Dict[str, Any]) -> WorkflowConfig

从字典创建工作流配置。

**参数：**
- `data` (Dict[str, Any]): 配置数据

**返回：**
- `WorkflowConfig`: 工作流配置实例

#### 方法

##### to_dict() -> Dict[str, Any]

转换为字典。

**返回：**
- `Dict[str, Any]`: 配置字典

##### validate() -> List[str]

验证配置的有效性。

**返回：**
- `List[str]`: 验证错误列表，空列表表示验证通过

### NodeConfig

节点配置模型。

```python
@dataclass
class NodeConfig:
    type: str
    config: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
```

#### 类方法

##### from_dict(data: Dict[str, Any]) -> NodeConfig

从字典创建节点配置。

**参数：**
- `data` (Dict[str, Any]): 配置数据

**返回：**
- `NodeConfig`: 节点配置实例

### EdgeConfig

边配置模型。

```python
@dataclass
class EdgeConfig:
    from_node: str
    to_node: str
    type: EdgeType
    condition: Optional[str] = None
    description: Optional[str] = None
```

#### 类方法

##### from_dict(data: Dict[str, Any]) -> EdgeConfig

从字典创建边配置。

**参数：**
- `data` (Dict[str, Any]): 配置数据

**返回：**
- `EdgeConfig`: 边配置实例

#### 方法

##### to_dict() -> Dict[str, Any]

转换为字典。

**返回：**
- `Dict[str, Any]`: 配置字典

### EdgeType

边类型枚举。

```python
class EdgeType(Enum):
    SIMPLE = "simple"
    CONDITIONAL = "conditional"
```

## 节点系统

### BaseNode

节点基类。

```python
class BaseNode(ABC):
    @property
    @abstractmethod
    def node_type(self) -> str:
        """节点类型标识"""
        pass

    @abstractmethod
    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑"""
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        pass

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置"""
        pass
```

### NodeRegistry

节点注册表。

```python
class NodeRegistry:
    def __init__(self) -> None
```

#### 方法

##### register_node(node_class: Type[BaseNode]) -> None

注册节点类型。

**参数：**
- `node_class` (Type[BaseNode]): 节点类

**异常：**
- `ValueError`: 节点类型已存在

##### register_node_instance(node: BaseNode) -> None

注册节点实例。

**参数：**
- `node` (BaseNode): 节点实例

**异常：**
- `ValueError`: 节点实例已存在

##### get_node_class(node_type: str) -> Type[BaseNode]

获取节点类型。

**参数：**
- `node_type` (str): 节点类型

**返回：**
- `Type[BaseNode]`: 节点类

**异常：**
- `ValueError`: 节点类型不存在

##### get_node_instance(node_type: str) -> BaseNode

获取节点实例。

**参数：**
- `node_type` (str): 节点类型

**返回：**
- `BaseNode`: 节点实例

**异常：**
- `ValueError`: 节点类型不存在

##### list_nodes() -> List[str]

列出所有注册的节点类型。

**返回：**
- `List[str]`: 节点类型列表

##### get_node_schema(node_type: str) -> Dict[str, Any]

获取节点配置Schema。

**参数：**
- `node_type` (str): 节点类型

**返回：**
- `Dict[str, Any]`: 配置Schema

##### validate_node_config(node_type: str, config: Dict[str, Any]) -> List[str]

验证节点配置。

**参数：**
- `node_type` (str): 节点类型
- `config` (Dict[str, Any]): 节点配置

**返回：**
- `List[str]`: 验证错误列表

### 内置节点

#### AnalysisNode

分析节点，负责分析用户输入和判断是否需要调用工具。

```python
class AnalysisNode(BaseNode):
    def __init__(self, llm_client: Optional[ILLMClient] = None) -> None
```

#### ToolNode

工具执行节点，负责执行工具调用并处理结果。

```python
class ToolNode(BaseNode):
    def __init__(self, tool_manager: Optional[IToolManager] = None) -> None
```

#### LLMNode

LLM调用节点，负责调用LLM生成响应。

```python
class LLMNode(BaseNode):
    def __init__(self, llm_client: Optional[ILLMClient] = None) -> None
```

#### ConditionNode

条件判断节点，负责根据状态信息进行条件判断。

```python
class ConditionNode(BaseNode):
    def __init__(self) -> None
```

## 边系统

### SimpleEdge

简单边，表示节点之间的直接连接。

```python
@dataclass
class SimpleEdge:
    from_node: str
    to_node: str
    description: Optional[str] = None
```

#### 类方法

##### from_config(config: EdgeConfig) -> SimpleEdge

从配置创建简单边。

**参数：**
- `config` (EdgeConfig): 边配置

**返回：**
- `SimpleEdge`: 简单边实例

#### 方法

##### to_config() -> EdgeConfig

转换为配置。

**返回：**
- `EdgeConfig`: 边配置

##### validate(node_names: set) -> List[str]

验证边的有效性。

**参数：**
- `node_names` (set): 可用节点名称集合

**返回：**
- `List[str]`: 验证错误列表

### ConditionalEdge

条件边，表示基于条件判断的节点连接。

```python
@dataclass
class ConditionalEdge:
    from_node: str
    to_node: str
    condition: str
    condition_type: ConditionType
    condition_parameters: Dict[str, Any]
    description: Optional[str] = None
```

#### 类方法

##### from_config(config: EdgeConfig) -> ConditionalEdge

从配置创建条件边。

**参数：**
- `config` (EdgeConfig): 边配置

**返回：**
- `ConditionalEdge`: 条件边实例

#### 方法

##### evaluate(state: AgentState) -> bool

评估条件是否满足。

**参数：**
- `state` (AgentState): 当前Agent状态

**返回：**
- `bool`: 条件是否满足

##### validate(node_names: set) -> List[str]

验证边的有效性。

**参数：**
- `node_names` (set): 可用节点名称集合

**返回：**
- `List[str]`: 验证错误列表

### ConditionType

条件类型枚举。

```python
class ConditionType(Enum):
    HAS_TOOL_CALLS = "has_tool_calls"
    NO_TOOL_CALLS = "no_tool_calls"
    HAS_TOOL_RESULTS = "has_tool_results"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    HAS_ERRORS = "has_errors"
    NO_ERRORS = "no_errors"
    MESSAGE_CONTAINS = "message_contains"
    ITERATION_COUNT_EQUALS = "iteration_count_equals"
    ITERATION_COUNT_GREATER_THAN = "iteration_count_greater_than"
    CUSTOM = "custom"
```

## 工作流管理

### IWorkflowManager

工作流管理器接口。

```python
class IWorkflowManager(ABC):
    @abstractmethod
    def load_workflow(self, config_path: str) -> str:
        """加载工作流配置"""
        pass

    @abstractmethod
    def create_workflow(self, workflow_id: str) -> Any:
        """创建工作流实例"""
        pass

    @abstractmethod
    def run_workflow(self, workflow_id: str, initial_state: Optional[AgentState] = None, **kwargs: Any) -> AgentState:
        """运行工作流"""
        pass

    @abstractmethod
    async def run_workflow_async(self, workflow_id: str, initial_state: Optional[AgentState] = None, **kwargs: Any) -> AgentState:
        """异步运行工作流"""
        pass

    @abstractmethod
    def stream_workflow(self, workflow_id: str, initial_state: Optional[AgentState] = None, **kwargs: Any) -> Union[AsyncGenerator[AgentState, None], Any]:
        """流式运行工作流"""
        pass

    @abstractmethod
    def list_workflows(self) -> List[str]:
        """列出所有已加载的工作流"""
        pass

    @abstractmethod
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置"""
        pass

    @abstractmethod
    def unload_workflow(self, workflow_id: str) -> bool:
        """卸载工作流"""
        pass
```

## 会话管理

### ISessionManager

会话管理器接口。

```python
class ISessionManager(ABC):
    @abstractmethod
    def create_session(self, workflow_config_path: str, agent_config: Optional[Dict[str, Any]] = None, initial_state: Optional[AgentState] = None) -> str:
        """创建新会话"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        pass

    @abstractmethod
    def restore_session(self, session_id: str) -> Tuple[Any, AgentState]:
        """恢复会话"""
        pass

    @abstractmethod
    def save_session(self, session_id: str, workflow: Any, state: AgentState) -> bool:
        """保存会话"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        pass

    @abstractmethod
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        pass
```

### SessionManager

会话管理器实现。

```python
class SessionManager(ISessionManager):
    def __init__(
        self,
        workflow_manager: IWorkflowManager,
        session_store: ISessionStore,
        git_manager: Optional[IGitManager] = None,
        storage_path: Optional[Path] = None
    ) -> None
```

### ISessionStore

会话存储接口。

```python
class ISessionStore(ABC):
    @abstractmethod
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话数据"""
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        pass
```

### FileSessionStore

基于文件系统的会话存储实现。

```python
class FileSessionStore(ISessionStore):
    def __init__(self, storage_path: Path) -> None
```

### MemorySessionStore

基于内存的会话存储实现（用于测试）。

```python
class MemorySessionStore(ISessionStore):
    def __init__(self) -> None
```

## 触发器系统

### ITrigger

触发器接口。

```python
class ITrigger(ABC):
    @property
    @abstractmethod
    def trigger_id(self) -> str:
        """触发器ID"""
        pass

    @property
    @abstractmethod
    def trigger_type(self) -> TriggerType:
        """触发器类型"""
        pass

    @abstractmethod
    def evaluate(self, state: AgentState, context: Dict[str, Any]) -> bool:
        """评估触发器是否应该触发"""
        pass

    @abstractmethod
    def execute(self, state: AgentState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作"""
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """获取触发器配置"""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """检查触发器是否启用"""
        pass

    @abstractmethod
    def enable(self) -> None:
        """启用触发器"""
        pass

    @abstractmethod
    def disable(self) -> None:
        """禁用触发器"""
        pass
```

### TriggerType

触发器类型枚举。

```python
class TriggerType(Enum):
    TIME = "time"
    STATE = "state"
    EVENT = "event"
    CUSTOM = "custom"
```

### TriggerSystem

触发器系统。

```python
class TriggerSystem:
    def __init__(self, max_workers: int = 4) -> None
```

#### 方法

##### register_trigger(trigger: ITrigger) -> bool

注册触发器。

**参数：**
- `trigger` (ITrigger): 触发器实例

**返回：**
- `bool`: 是否成功注册

##### unregister_trigger(trigger_id: str) -> bool

注销触发器。

**参数：**
- `trigger_id` (str): 触发器ID

**返回：**
- `bool`: 是否成功注销

##### evaluate_triggers(state: AgentState, context: Dict[str, Any]) -> List[TriggerEvent]

评估所有触发器。

**参数：**
- `state` (AgentState): 当前Agent状态
- `context` (Dict[str, Any]): 上下文信息

**返回：**
- `List[TriggerEvent]`: 触发的事件列表

##### start() -> None

启动触发器系统。

##### stop() -> None

停止触发器系统。

##### is_running() -> bool

检查系统是否正在运行。

**返回：**
- `bool`: 是否正在运行

### 内置触发器

#### TimeTrigger

时间触发器。

```python
class TimeTrigger(BaseTrigger):
    def __init__(self, trigger_id: str, trigger_time: str, config: Optional[Dict[str, Any]] = None) -> None
```

#### StateTrigger

状态触发器。

```python
class StateTrigger(BaseTrigger):
    def __init__(self, trigger_id: str, condition: str, config: Optional[Dict[str, Any]] = None) -> None
```

#### EventTrigger

事件触发器。

```python
class EventTrigger(BaseTrigger):
    def __init__(self, trigger_id: str, event_type: str, event_pattern: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> None
```

#### CustomTrigger

自定义触发器。

```python
class CustomTrigger(BaseTrigger):
    def __init__(self, trigger_id: str, evaluate_func: Callable[[AgentState, Dict[str, Any]], bool], execute_func: Callable[[AgentState, Dict[str, Any]], Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> None
```

## 性能优化

### PerformanceMonitor

性能监控器。

```python
class PerformanceMonitor:
    def __init__(self, max_history: int = 1000) -> None
```

#### 方法

##### start_measurement(operation: str, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetrics

开始性能测量。

**参数：**
- `operation` (str): 操作名称
- `metadata` (Optional[Dict[str, Any]]): 元数据

**返回：**
- `PerformanceMetrics`: 性能指标对象

##### get_metrics(operation: Optional[str] = None) -> Dict[str, List[PerformanceMetrics]]

获取性能指标。

**参数：**
- `operation` (Optional[str]): 操作名称，如果为None则返回所有操作

**返回：**
- `Dict[str, List[PerformanceMetrics]]: 性能指标

##### get_statistics(operation: str) -> Dict[str, Any]

获取操作统计信息。

**参数：**
- `operation` (str): 操作名称

**返回：**
- `Dict[str, Any]: 统计信息

##### clear_metrics(operation: Optional[str] = None) -> None

清除性能指标。

**参数：**
- `operation` (Optional[str]): 操作名称，如果为None则清除所有

### WorkflowCache

工作流缓存。

```python
class WorkflowCache:
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600) -> None
```

#### 方法

##### get(*args, **kwargs) -> Optional[Any]

获取缓存值。

**参数：**
- `*args`: 位置参数
- `**kwargs`: 关键字参数

**返回：**
- `Optional[Any]`: 缓存值，如果不存在或已过期则返回None

##### set(value: Any, *args, **kwargs) -> None

设置缓存值。

**参数：**
- `value` (Any): 缓存值
- `*args`: 位置参数
- `**kwargs`: 关键字参数

##### clear() -> None

清除所有缓存。

##### get_stats() -> Dict[str, Any]

获取缓存统计信息。

**返回：**
- `Dict[str, Any]: 统计信息

### WorkflowOptimizer

工作流优化器。

```python
class WorkflowOptimizer:
    def __init__(self) -> None
```

#### 方法

##### optimize_config_loading(config_path: str) -> Dict[str, Any]

优化配置加载。

**参数：**
- `config_path` (str): 配置文件路径

**返回：**
- `Dict[str, Any]: 配置数据

##### optimize_node_execution(nodes: List[Callable[[], Any]], parallel: bool = False) -> List[Any]

优化节点执行。

**参数：**
- `nodes` (List[Callable[[], Any]]): 节点列表
- `parallel` (bool): 是否并行执行

**返回：**
- `List[Any]: 执行结果

##### get_performance_report() -> Dict[str, Any]

获取性能报告。

**返回：**
- `Dict[str, Any]: 性能报告

##### cleanup() -> None

清理资源。

## 可视化

### IWorkflowVisualizer

工作流可视化器接口。

```python
class IWorkflowVisualizer(ABC):
    @abstractmethod
    def visualize_workflow(self, workflow_config: WorkflowConfig) -> str:
        """可视化工作流配置"""
        pass

    @abstractmethod
    def start_studio(self, port: int = 8079) -> bool:
        """启动LangGraph Studio"""
        pass

    @abstractmethod
    def stop_studio(self) -> bool:
        """停止LangGraph Studio"""
        pass

    @abstractmethod
    def is_studio_running(self) -> bool:
        """检查Studio是否正在运行"""
        pass

    @abstractmethod
    def get_studio_url(self, port: int = 8079) -> str:
        """获取Studio URL"""
        pass
```

### LangGraphStudioVisualizer

LangGraph Studio可视化器实现。

```python
class LangGraphStudioVisualizer(IWorkflowVisualizer):
    def __init__(self, studio_port: int = 8079) -> None
```

#### 方法

##### visualize_workflow(workflow_config: WorkflowConfig) -> str

可视化工作流配置。

**参数：**
- `workflow_config` (WorkflowConfig): 工作流配置

**返回：**
- `str`: 可视化URL或标识符

##### start_studio(port: int = 8079) -> bool

启动LangGraph Studio。

**参数：**
- `port` (int): Studio端口

**返回：**
- `bool`: 是否成功启动

##### stop_studio() -> bool

停止LangGraph Studio。

**返回：**
- `bool`: 是否成功停止

##### is_studio_running() -> bool

检查Studio是否正在运行。

**返回：**
- `bool`: Studio是否正在运行

##### get_studio_url(port: int = 8079) -> str

获取Studio URL。

**参数：**
- `port` (int): Studio端口

**返回：**
- `str`: Studio URL

##### export_graph_image(workflow_config: WorkflowConfig, output_path: Path, format: str = "png") -> bool

导出工作流图图像。

**参数：**
- `workflow_config` (WorkflowConfig): 工作流配置
- `output_path` (Path): 输出路径
- `format` (str): 图像格式，支持 "png", "svg", "pdf"

**返回：**
- `bool`: 是否成功导出

### MockWorkflowVisualizer

模拟工作流可视化器（用于测试）。

```python
class MockWorkflowVisualizer(IWorkflowVisualizer):
    def __init__(self) -> None
```

### 便捷函数

##### create_visualizer(use_mock: bool = False, studio_port: int = 8079) -> IWorkflowVisualizer

创建工作流可视化器。

**参数：**
- `use_mock` (bool): 是否使用模拟可视化器
- `studio_port` (int): Studio端口

**返回：**
- `IWorkflowVisualizer`: 工作流可视化器实例

## 工具函数

### 全局函数

##### get_global_registry() -> NodeRegistry

获取全局节点注册表。

**返回：**
- `NodeRegistry`: 全局节点注册表

##### register_node(node_class: Type[BaseNode]) -> None

注册节点类型到全局注册表。

**参数：**
- `node_class` (Type[BaseNode]): 节点类

##### get_node(node_type: str) -> BaseNode

从全局注册表获取节点实例。

**参数：**
- `node_type` (str): 节点类型

**返回：**
- `BaseNode`: 节点实例

##### auto_register_nodes(package_paths: List[str] = None) -> Dict[str, Any]

自动注册节点的便捷函数。

**参数：**
- `package_paths` (List[str]): 要搜索的包路径列表，如果为None则使用默认路径

**返回：**
- `Dict[str, Any]: 注册结果

##### register_builtin_nodes() -> None

注册内置节点。

##### get_global_optimizer() -> WorkflowOptimizer

获取全局优化器。

**返回：**
- `WorkflowOptimizer`: 全局优化器实例

### 装饰器

##### performance_monitor(monitor: PerformanceMonitor, operation: str)

性能监控装饰器。

**参数：**
- `monitor` (PerformanceMonitor): 性能监控器
- `operation` (str): 操作名称

**返回：**
- 装饰器函数

##### cached(cache: WorkflowCache)

缓存装饰器。

**参数：**
- `cache` (WorkflowCache): 缓存实例

**返回：**
- 装饰器函数

##### optimize_workflow_loading(func: F) -> F

工作流加载优化装饰器。

**参数：**
- `func` (F): 要优化的函数

**返回：**
- `F`: 优化后的函数

---

*更新日期：2025-10-20*