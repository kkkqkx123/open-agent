# 统一依赖注入容器设计方案

## 1. 现状分析

### 1.1 当前架构层级
```
src/
├── presentation/     # 表现层 (UI和API接口)
├── application/       # 应用层 (用例协调和会话管理)
├── domain/           # 领域层 (核心业务逻辑和实体)
└── infrastructure/   # 基础设施层 (技术实现和外部依赖)
```

### 1.2 现有DI容器实现

#### 基础设施层容器
- **文件**: `src/infrastructure/container.py`
- **功能**: 基础依赖注入容器，提供服务注册、解析、生命周期管理
- **特点**: 支持单例、瞬态、作用域生命周期，具备循环依赖检测

#### 基础设施层配置
- **文件**: `src/infrastructure/di_config.py`
- **功能**: DIConfig类统一管理所有服务注册
- **问题**: 职责过多，包含应用层组件创建，违反分层原则

#### 应用层配置
- **文件**: `src/application/workflow/di_config.py`
- **功能**: WorkflowModule类注册工作流相关服务
- **特点**: 按模块划分，职责相对清晰

#### 其他模块配置
- **监控模块**: `src/infrastructure/monitoring/di_config.py`
- **工具验证**: `src/infrastructure/tools/validation/di_config.py`

### 1.3 核心功能模块

#### 会话管理 (Session)
- **位置**: `src/application/sessions/`
- **职责**: 用户会话生命周期管理、多线程协调
- **依赖**: ThreadManager、GitManager、配置系统

#### 线程管理 (Thread)
- **位置**: `src/domain/threads/`
- **职责**: 工作流执行实例管理、状态版本控制
- **依赖**: LangGraphAdapter、Checkpoint机制

#### 工作流管理 (Workflow)
- **位置**: `src/application/workflow/`
- **职责**: 工作流配置加载、创建、执行管理
- **依赖**: 配置系统、节点注册表、图构建器

#### 状态管理 (State)
- **位置**: `src/domain/state/`、`src/infrastructure/state/`
- **职责**: 统一状态模型、状态协作管理
- **依赖**: 状态工厂、序列化器、快照存储

#### 工具系统 (Tools)
- **位置**: `src/domain/tools/`、`src/infrastructure/tools/`
- **职责**: 工具定义、注册、执行、验证
- **依赖**: 工具注册表、MCP客户端、验证管理器

#### LLM集成
- **位置**: `src/infrastructure/llm/`
- **职责**: 多模型LLM客户端、配置管理
- **依赖**: 配置系统、异步工具支持

#### 检查点与历史
- **检查点**: `src/application/checkpoint/`、`src/domain/checkpoint/`
- **历史**: `src/application/history/`、`src/domain/history/`
- **职责**: 状态持久化、交互历史记录、回放支持

## 2. 问题识别

### 2.1 依赖倒置问题
- **基础设施层向上依赖应用层**: `thread_session_di_config.py`中基础设施层创建应用层组件
- **违反分层原则**: 高层模块不应该依赖低层模块的具体实现

### 2.2 职责混乱问题
- **单一配置类职责过多**: DIConfig类承担多种创建职责
- **工厂类与DI配置混合**: 创建逻辑与依赖注入配置耦合
- **全局状态管理耦合**: 组件创建与全局状态管理混合

### 2.3 配置分散问题
- **DI配置分散在各层**: 缺乏统一的配置策略
- **服务注册不一致**: 不同模块使用不同的注册模式
- **环境管理不统一**: 各模块独立处理环境差异

## 3. 统一DI容器设计方案

### 3.1 设计原则

#### 分层配置原则
- **基础设施层**: 只配置技术实现相关的服务
- **领域层**: 只配置核心业务逻辑服务
- **应用层**: 只配置用例协调和会话管理服务
- **表现层**: 只配置UI和API相关的服务

#### 依赖方向原则
- **单向依赖**: 高层可以依赖低层，低层不能依赖高层
- **接口隔离**: 各层通过接口进行交互
- **依赖倒置**: 依赖于抽象，不依赖于具体实现

#### 统一入口原则
- **单一配置入口**: 提供统一的配置入口点
- **模块化配置**: 各层配置独立，可组合使用
- **环境感知**: 支持不同环境的配置差异

### 3.2 分层配置架构

#### 基础设施层配置 (`src/infrastructure/di/infrastructure_config.py`)
```python
class InfrastructureModule:
    """基础设施层服务配置模块"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        # 配置系统
        container.register(IConfigLoader, FileConfigLoader)
        container.register(IConfigValidator, EnhancedConfigValidator)
        
        # 日志系统
        container.register(ILogger, StructuredFileLogger)
        container.register(ILogCleanupService, LogCleanupService)
        
        # 存储系统
        container.register(ICheckpointStore, SQLiteCheckpointStore)
        container.register(ISessionStore, FileSessionStore)
        container.register(IThreadMetadataStore, ThreadMetadataStore)
        
        # LLM客户端
        container.register(ILLMClient, OpenAIClient, "openai")
        container.register(ILLMClient, AnthropicClient, "anthropic")
        
        # 工具系统
        container.register(IToolRegistry, ToolRegistry)
        container.register(IMCPClient, MCPClient)
        
        # 监控和验证
        container.register(IPerformanceMonitor, PerformanceMonitor)
        container.register(IToolValidator, ToolValidationManager)
```

#### 领域层配置 (`src/domain/di/domain_config.py`)
```python
class DomainModule:
    """领域层服务配置模块"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        # 状态管理
        container.register(IStateManager, CompositeStateManager)
        container.register(IStateCollaborationManager, StateCollaborationManager)
        
        # 工作流核心
        container.register(IWorkflowConfigManager, WorkflowConfigManager)
        container.register(IWorkflowVisualizer, WorkflowVisualizer)
        container.register(IWorkflowRegistry, WorkflowRegistry)
        
        # 线程核心
        container.register(IThreadManager, ThreadManager)
        container.register(IThreadRepository, ThreadRepository)
        
        # 工具核心
        container.register(IToolManager, ToolManager)
        container.register(IToolExecutor, ToolExecutor)
        
        # 提示词管理
        container.register(IPromptTemplateManager, PromptTemplateManager)
        container.register(IPromptInjector, PromptInjector)
```

#### 应用层配置 (`src/application/di/application_config.py`)
```python
class ApplicationModule:
    """应用层服务配置模块"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        # 会话管理
        container.register(ISessionManager, SessionManager)
        container.register(IGitManager, GitManager)
        
        # 工作流管理
        container.register(IWorkflowManager, WorkflowManager)
        container.register(IWorkflowFactory, WorkflowFactory)
        
        # 回放管理
        container.register(IReplayManager, ReplayManager)
        
        # 检查点管理
        container.register(ICheckpointManager, CheckpointManager)
        
        # 历史管理
        container.register(IHistoryManager, HistoryManager)
```

#### 表现层配置 (`src/presentation/di/presentation_config.py`)
```python
class PresentationModule:
    """表现层服务配置模块"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        # API服务
        container.register(IAPIRouter, SessionRouter, "sessions")
        container.register(IAPIRouter, ThreadRouter, "threads")
        container.register(IAPIRouter, WorkflowRouter, "workflows")
        
        # TUI组件
        container.register(ITUIComponent, SessionComponent)
        container.register(ITUIComponent, ThreadComponent)
        container.register(ITUIComponent, WorkflowComponent)
        
        # CLI命令
        container.register(ICLICommand, RunCommand)
        container.register(ICLICommand, ConfigCommand)
```

### 3.3 统一配置入口

#### 主配置入口 (`src/app_config.py`)
```python
class ApplicationConfig:
    """应用程序统一配置入口"""
    
    def __init__(self, environment: str = "default"):
        self.environment = environment
        self.container = DependencyContainer()
        
    def configure(self, 
                 config_path: str = "configs",
                 enable_monitoring: bool = True,
                 enable_validation: bool = True) -> IDependencyContainer:
        """配置应用程序的所有服务"""
        
        # 1. 配置基础设施层（最底层）
        InfrastructureModule.register_services(self.container)
        InfrastructureModule.register_environment_services(
            self.container, self.environment
        )
        
        # 2. 配置领域层（依赖基础设施层）
        DomainModule.register_services(self.container)
        DomainModule.register_environment_services(
            self.container, self.environment
        )
        
        # 3. 配置应用层（依赖领域层）
        ApplicationModule.register_services(self.container)
        ApplicationModule.register_environment_services(
            self.container, self.environment
        )
        
        # 4. 配置表现层（依赖应用层）
        PresentationModule.register_services(self.container)
        PresentationModule.register_environment_services(
            self.container, self.environment
        )
        
        # 5. 配置横切关注点
        if enable_monitoring:
            MonitoringModule.register_services(self.container)
        
        if enable_validation:
            ValidationModule.register_services(self.container)
        
        # 6. 验证配置
        self._validate_configuration()
        
        return self.container
    
    def _validate_configuration(self) -> None:
        """验证配置的正确性"""
        # 检查循环依赖
        # 检查必需服务
        # 检查配置完整性
        pass
```

### 3.4 容器增强功能

#### 环境感知配置
```python
class EnvironmentAwareContainer:
    """环境感知的依赖注入容器"""
    
    def __init__(self):
        self.container = DependencyContainer()
        self.environment = "default"
        
    def set_environment(self, environment: str) -> None:
        """设置当前环境"""
        self.environment = environment
        self.container.set_environment(environment)
        
    def register_environment_service(self, 
                                 interface: Type[T],
                                 implementation: Type[T],
                                 environment: str = None) -> None:
        """注册环境特定的服务"""
        env = environment or self.environment
        self.container.register(interface, implementation, environment=env)
```

#### 模块化配置加载
```python
class ModuleLoader:
    """模块化配置加载器"""
    
    def __init__(self):
        self.modules: Dict[str, ModuleConfig] = {}
        
    def register_module(self, name: str, module: ModuleConfig) -> None:
        """注册配置模块"""
        self.modules[name] = module
        
    def load_module(self, name: str, container: IDependencyContainer) -> None:
        """加载指定模块的配置"""
        if name in self.modules:
            self.modules[name].register_services(container)
        
    def load_modules(self, names: List[str], container: IDependencyContainer) -> None:
        """加载多个模块的配置"""
        for name in names:
            self.load_module(name, container)
```

## 4. 实施步骤

### 4.1 第一阶段：基础设施层重构
1. **创建基础设施层配置模块** (`src/infrastructure/di/infrastructure_config.py`)
2. **迁移现有基础设施服务注册** 从 `di_config.py`
3. **测试基础设施层配置** 的独立运行

### 4.2 第二阶段：领域层重构
1. **创建领域层配置模块** (`src/domain/di/domain_config.py`)
2. **迁移领域服务注册** 从现有分散的配置
3. **确保领域层只依赖基础设施层接口**

### 4.3 第三阶段：应用层重构
1. **创建应用层配置模块** (`src/application/di/application_config.py`)
2. **迁移应用服务注册** 从 `thread_session_di_config.py`
3. **移除应用层对基础设施层的直接依赖**

### 4.4 第四阶段：统一入口创建
1. **创建统一配置入口** (`src/app_config.py`)
2. **整合各层配置模块**
3. **实现环境感知和验证机制**

### 4.5 第五阶段：迁移和测试
1. **逐步迁移现有代码** 使用新的DI容器
2. **更新所有入口点** (TUI、API、CLI)
3. **全面测试** 各层功能正常
4. **移除旧的DI配置** (`thread_session_di_config.py`)

## 5. 重构后优势

### 5.1 架构优势
- **依赖关系正确**: 严格遵循分层架构原则
- **职责单一**: 每个配置模块只负责一层的服务
- **可测试性**: 各层可以独立测试和验证

### 5.2 维护优势
- **配置集中**: 统一入口管理所有服务配置
- **模块化**: 可以按需加载特定层的配置
- **环境支持**: 灵活支持多环境配置差异

### 5.3 扩展优势
- **易于扩展**: 新增服务只需在对应层配置
- **插件化**: 支持动态加载配置模块
- **可配置**: 通过配置控制服务注册行为

### 5.4 开发优势
- **清晰的依赖关系**: 开发者容易理解服务依赖
- **一致的配置模式**: 所有服务使用统一的注册方式
- **错误检测**: 配置验证机制提前发现问题

## 6. 注意事项

### 6.1 迁移风险
- **逐步迁移**: 不要一次性替换所有DI配置
- **保持兼容**: 确保现有功能在迁移过程中正常工作
- **充分测试**: 每个阶段都要进行充分的测试验证

### 6.2 性能考虑
- **延迟加载**: 支持服务的延迟初始化
- **缓存机制**: 利用容器的缓存机制提高性能
- **生命周期**: 合理设置服务的生命周期

### 6.3 未来扩展
- **动态配置**: 支持运行时动态调整配置
- **配置中心**: 可以集成外部配置中心
- **服务发现**: 支持服务自动发现和注册

## 7. 总结

这个统一DI容器设计方案解决了当前架构中的依赖倒置和职责混乱问题，通过分层配置和统一入口，提供了一个清晰、可维护、可扩展的依赖注入框架。重构后的系统将具有更好的架构质量、更低的维护成本和更高的开发效率。