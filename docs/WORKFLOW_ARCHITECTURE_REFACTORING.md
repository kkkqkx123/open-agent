# 工作流架构重构文档

## 概述

本文档描述了 `src/core/workflow/graph` 目录的架构重构过程，包括重构的目标、方法、结果和使用指南。

## 重构目标

### 主要问题
1. **全局状态滥用**：graph 层使用全局注册表，违反依赖注入原则
2. **服务逻辑分散**：业务逻辑和执行逻辑混合，职责不清晰
3. **依赖关系混乱**：组件间通过硬编码方式获取依赖
4. **测试困难**：全局状态影响单元测试

### 重构目标
1. **移除全局状态**：使用依赖注入替代全局注册表
2. **明确层次边界**：分离业务逻辑和执行逻辑
3. **统一依赖管理**：通过依赖注入容器管理所有依赖
4. **提高可测试性**：支持依赖替换和模拟

## 架构设计

### 重构前架构
```
src/core/workflow/graph/
├── service.py          # GraphService - 使用全局注册表
├── registry/
│   └── global_registry.py  # 全局注册表
├── decorators.py        # 装饰器 - 直接注册到全局
└── ...
```

### 重构后架构
```
src/
├── interfaces/
│   └── workflow/
│       ├── registry.py      # 注册表接口
│       └── coordinator.py   # 协调器接口
├── core/
│   └── workflow/
│       ├── registry/
│       │   └── workflow_registry.py  # 注册表实现
│       ├── coordinator/
│       │   └── workflow_coordinator.py  # 协调器实现
│       └── ...
├── services/
│   └── workflow/
│       ├── workflow_service_factory.py  # 服务工厂
│       └── workflow_orchestrator.py     # 业务编排器
└── container/
    └── container.py       # 依赖注入容器
```

## 核心组件

### 1. 注册表接口和实现

#### 接口定义
```python
# src/interfaces/workflow/registry.py
class IComponentRegistry(ABC):
    def register_node(self, node_type: str, node_class: Type[INode]) -> None: ...
    def get_node_class(self, node_type: str) -> Optional[Type[INode]]: ...
    # ...

class IFunctionRegistry(ABC):
    def register_node_function(self, name: str, function: Any) -> None: ...
    def get_node_function(self, name: str) -> Optional[Any]: ...
    # ...

class IWorkflowRegistry(ABC):
    @property
    def component_registry(self) -> IComponentRegistry: ...
    @property
    def function_registry(self) -> IFunctionRegistry: ...
    # ...
```

#### 实现类
```python
# src/core/workflow/registry/workflow_registry.py
class WorkflowRegistry(IWorkflowRegistry):
    def __init__(self):
        self._component_registry = ComponentRegistry()
        self._function_registry = FunctionRegistry()
    
    # 实现所有接口方法...
```

### 2. 工作流协调器

#### 接口定义
```python
# src/interfaces/workflow/coordinator.py
class IWorkflowCoordinator(ABC):
    def create_workflow(self, config: GraphConfig) -> IWorkflow: ...
    def execute_workflow(self, workflow: IWorkflow, initial_state: IWorkflowState) -> IWorkflowState: ...
    def validate_workflow_config(self, config: GraphConfig) -> List[str]: ...
    # ...
```

#### 实现类
```python
# src/core/workflow/coordinator/workflow_coordinator.py
class WorkflowCoordinator(IWorkflowCoordinator):
    def __init__(self, builder: IWorkflowBuilder, executor: IWorkflowExecutor, 
                 validator: IWorkflowValidator, lifecycle_manager: WorkflowLifecycleManager,
                 graph_service: Optional[Any] = None):
        # 通过构造函数注入所有依赖
        self._builder = builder
        self._executor = executor
        self._validator = validator
        self._lifecycle_manager = lifecycle_manager
        self._graph_service = graph_service
    
    # 实现所有接口方法...
```

### 3. 服务工厂

```python
# src/services/workflow/workflow_service_factory.py
class WorkflowServiceFactory:
    def __init__(self, container: IDependencyContainer):
        self._container = container
    
    def create_workflow_coordinator(self) -> IWorkflowCoordinator:
        # 从容器获取所有依赖
        builder = self._container.get(IWorkflowBuilder)
        executor = self._container.get(IWorkflowExecutor)
        validator = self._container.get(IWorkflowValidator)
        lifecycle_manager = self._container.get(WorkflowLifecycleManager)
        
        # 创建协调器
        return create_workflow_coordinator(
            builder=builder,
            executor=executor,
            validator=validator,
            lifecycle_manager=lifecycle_manager
        )
    
    def register_workflow_services(self, environment: str = "default") -> None:
        # 注册所有工作流相关服务到容器
        # ...
```

### 4. 业务编排器

```python
# src/services/workflow/workflow_orchestrator.py
class WorkflowOrchestrator:
    def __init__(self, workflow_coordinator: IWorkflowCoordinator):
        self._workflow_coordinator = workflow_coordinator
    
    def orchestrate_workflow_execution(self, workflow_config: Dict[str, Any], 
                                     business_context: Dict[str, Any]) -> Dict[str, Any]:
        # 业务逻辑处理
        processed_config = self._process_business_rules(workflow_config, business_context)
        
        # 创建工作流
        config = GraphConfig.from_dict(processed_config)
        workflow = self._workflow_coordinator.create_workflow(config)
        
        # 执行工作流
        initial_state = self._create_initial_state(business_context)
        result_state = self._workflow_coordinator.execute_workflow(workflow, initial_state)
        
        # 业务结果处理
        return self._process_business_result(result_state, business_context)
```

## 层次边界

### 架构层次
```
Adapters (API/CLI/TUI) - 顶层接口
    ↓ 依赖
Services (业务服务层) - 业务协调
    ↓ 依赖
Core Workflow (底层执行层) - 执行逻辑
    ↓ 依赖
Interfaces (接口定义) - 基础约束
```

### 职责分工

#### Core Workflow 层（底层执行层）
- **职责**：专注于工作流的创建和执行
- **特点**：
  - 纯执行逻辑，不包含业务逻辑
  - 通过构造函数接受依赖
  - 提供可复用的执行组件
- **主要组件**：
  - `WorkflowCoordinator`：内部协调
  - `WorkflowRegistry`：组件注册
  - `GraphService`：图服务

#### Services 层（中间协调层）
- **职责**：业务逻辑协调和全局服务管理
- **特点**：
  - 处理业务规则和验证
  - 管理服务生命周期
  - 为上层提供统一接口
- **主要组件**：
  - `WorkflowServiceFactory`：服务工厂
  - `WorkflowOrchestrator`：业务编排器

## 使用指南

### 1. 基本使用

#### 设置服务
```python
from src.services.container import get_global_container
from src.services.workflow import create_workflow_service_factory

# 获取容器
container = get_global_container()

# 创建服务工厂
factory = create_workflow_service_factory(container)

# 注册服务
factory.register_workflow_services(environment="development")
```

#### 创建工作流
```python
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.core.workflow.config.config import GraphConfig

# 获取协调器
coordinator = container.get(IWorkflowCoordinator)

# 创建配置
config = GraphConfig.from_dict({
    "name": "my_workflow",
    "nodes": {...},
    "edges": [...],
    "entry_point": "start"
})

# 创建工作流
workflow = coordinator.create_workflow(config)
```

#### 执行工作流
```python
from src.services.workflow import create_workflow_orchestrator

# 创建编排器
orchestrator = create_workflow_orchestrator(coordinator)

# 执行工作流（包含业务逻辑）
result = orchestrator.orchestrate_workflow_execution(
    workflow_config=workflow_config,
    business_context={
        "environment": "development",
        "user_id": "user123",
        "user_role": "user"
    }
)
```

### 2. 高级配置

#### 环境特定配置
```python
# 开发环境
factory.register_workflow_services(
    environment="development",
    config={
        "enable_debug": True,
        "max_execution_time": 300
    }
)

# 生产环境
factory.register_workflow_services(
    environment="production",
    config={
        "enable_debug": False,
        "max_execution_time": 3600,
        "enable_monitoring": True
    }
)
```

#### 自定义注册
```python
from src.interfaces.workflow.registry import IComponentRegistry

# 注册自定义节点类型
registry = container.get(IWorkflowRegistry)
registry.component_registry.register_node("custom_node", CustomNodeClass)

# 注册自定义函数
registry.function_registry.register_node_function("custom_function", custom_function)
```

## 迁移指南

### 从全局注册表迁移

#### 旧代码
```python
# 旧方式：使用全局注册表
from src.core.workflow.graph.registry.global_registry import get_global_registry

registry = get_global_registry()
registry.register_node("my_node", MyNodeClass)
```

#### 新代码
```python
# 新方式：使用依赖注入
from src.services.container import get_global_container
from src.interfaces.workflow.registry import IWorkflowRegistry

container = get_global_container()
registry = container.get(IWorkflowRegistry)
registry.component_registry.register_node("my_node", MyNodeClass)
```

### 从 GraphService 迁移

#### 旧代码
```python
# 旧方式：直接创建
from src.core.workflow.graph.service import get_graph_service

service = get_graph_service()
graph = service.build_graph(config)
```

#### 新代码
```python
# 新方式：通过依赖注入
from src.services.container import get_global_container
from src.interfaces.workflow.graph import IGraphService

container = get_global_container()
service = container.get(IGraphService)
graph = service.build_graph(config)
```

## 测试指南

### 单元测试

#### 测试注册表
```python
def test_component_registry():
    registry = ComponentRegistry()
    
    # 注册节点
    registry.register_node("test_node", MockNodeClass)
    
    # 验证
    assert registry.get_node_class("test_node") == MockNodeClass
```

#### 测试协调器
```python
def test_workflow_coordinator():
    # 创建模拟依赖
    mock_builder = Mock(spec=IWorkflowBuilder)
    mock_executor = Mock(spec=IWorkflowExecutor)
    mock_validator = Mock(spec=IWorkflowValidator)
    mock_lifecycle = Mock()
    
    # 创建协调器
    coordinator = create_workflow_coordinator(
        builder=mock_builder,
        executor=mock_executor,
        validator=mock_validator,
        lifecycle_manager=mock_lifecycle
    )
    
    # 测试创建工作流
    config = GraphConfig.from_dict({...})
    workflow = coordinator.create_workflow(config)
    
    # 验证调用
    mock_validator.validate.assert_called_once()
    mock_builder.build_graph.assert_called_once()
```

### 集成测试

#### 端到端测试
```python
def test_end_to_end_workflow():
    # 设置服务
    container = get_global_container()
    factory = create_workflow_service_factory(container)
    factory.register_workflow_services()
    
    # 创建编排器
    coordinator = container.get(IWorkflowCoordinator)
    orchestrator = create_workflow_orchestrator(coordinator)
    
    # 执行工作流
    result = orchestrator.orchestrate_workflow_execution(
        workflow_config={...},
        business_context={...}
    )
    
    # 验证结果
    assert result["success"] is True
```

## 性能优化

### 依赖注入优化
1. **生命周期管理**：
   - 单例：重量级服务（如执行器、验证器）
   - 瞬态：轻量级服务（如构建器）
   - 作用域：生命周期相关的服务

2. **延迟加载**：
   - 只在需要时创建服务实例
   - 使用工厂方法延迟初始化

### 注册表优化
1. **缓存机制**：
   - 缓存常用的节点和边类型
   - 使用 LRU 缓存避免内存泄漏

2. **批量操作**：
   - 批量注册减少验证开销
   - 延迟验证到使用时

## 故障排除

### 常见问题

#### 1. 依赖注入失败
```
错误: ValueError: 服务未注册: IWorkflowBuilder
解决: 确保在使用前注册所有必需的服务
```

#### 2. 循环依赖
```
错误: 检测到循环依赖
解决: 重新设计组件依赖关系，使用接口隔离
```

#### 3. 配置验证失败
```
错误: 工作流配置验证失败
解决: 检查配置格式和必需字段
```

### 调试技巧

#### 启用调试日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看服务注册过程
logger = logging.getLogger("src.services.workflow")
logger.setLevel(logging.DEBUG)
```

#### 验证服务配置
```python
factory = create_workflow_service_factory(container)
errors = factory.validate_service_configuration()
if errors:
    print(f"配置错误: {errors}")
```

## 总结

### 重构成果
1. **移除全局状态**：完全消除全局注册表的使用
2. **明确层次边界**：业务逻辑和执行逻辑清晰分离
3. **统一依赖管理**：通过依赖注入容器管理所有依赖
4. **提高可测试性**：支持依赖替换和模拟

### 架构优势
1. **可维护性**：清晰的职责分离和依赖关系
2. **可扩展性**：通过配置和接口轻松扩展功能
3. **可测试性**：依赖注入支持完整的单元测试
4. **性能优化**：生命周期管理和缓存机制

### 后续改进
1. **监控和指标**：添加性能监控和指标收集
2. **配置管理**：完善配置验证和热重载
3. **错误处理**：改进错误处理和恢复机制
4. **文档完善**：持续更新文档和示例

通过这次重构，我们建立了一个更加清晰、可维护和可扩展的工作流架构，为未来的功能扩展和性能优化奠定了坚实的基础。