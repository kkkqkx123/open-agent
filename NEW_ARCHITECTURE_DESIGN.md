# Modular Agent V2 - 全新架构设计

## 概述

本文档描述了Modular Agent项目的全新架构设计。基于对当前四层架构问题的深入分析，我们设计了一个更加简单、实用、可扩展的模块化架构。

## 当前架构问题分析

### 主要问题

1. **过度工程化**：每个功能都需要定义接口→实现→协调→展示，导致大量样板代码
2. **依赖注入复杂**：需要按顺序配置四层的DI，维护60多个服务类型
3. **调试困难**：调用链过长，一个简单功能需要穿越多个层次
4. **配置复杂**：多层配置文件，理解和维护困难
5. **演进困难**：如WorkflowManager类430行代码，包含大量向后兼容逻辑

### 具体实例

- `TUIApp`类1094行代码，违反单一职责原则
- `InfrastructureModule`需要注册60多个服务类型
- 配置文件层次过多：global.yaml、application.yaml加上各子目录配置

## 新架构设计原则

### 核心原则

1. **简单优先**：避免过度抽象，用最简单的方式解决问题
2. **模块化设计**：按功能域划分模块，而不是按层次划分
3. **插件化架构**：核心功能保持稳定，扩展功能通过插件实现
4. **配置驱动**：通过配置文件控制行为，减少硬编码
5. **渐进式复杂度**：简单功能简单实现，复杂功能按需增加复杂度
6. **开发者友好**：减少样板代码，提高开发效率和调试体验

## 新架构模块结构

### 目录结构

```
modular-agent/
├── src/
│   ├── core/           # 核心模块
│   │   ├── engine/     # 工作流引擎
│   │   ├── config/     # 配置管理
│   │   └── logging/    # 日志系统
│   ├── features/       # 功能模块
│   │   ├── llm/        # LLM客户端
│   │   ├── tools/      # 工具系统
│   │   ├── agents/     # 智能体
│   │   └── workflows/  # 工作流
│   ├── interfaces/     # 接口模块
│   │   ├── cli/        # 命令行
│   │   ├── tui/        # 终端界面
│   │   └── api/        # REST API
│   └── plugins/        # 插件系统
│       ├── storage/    # 存储插件
│       └── monitoring/ # 监控插件
├── configs             # 配置文件目录
├── plugins/            # 外部插件目录
└── examples/           # 示例和模板
```

### 模块分类

#### 1. 核心模块（Core）
- **engine**：工作流引擎核心，包含状态管理和执行逻辑
- **config**：统一配置管理，支持环境变量和配置文件
- **logging**：简化的日志系统

#### 2. 功能模块（Features）
- **llm**：LLM客户端管理，支持多提供商
- **tools**：工具系统，支持原生和MCP工具
- **agents**：智能体实现
- **workflows**：工作流模板和执行

#### 3. 接口模块（Interfaces）
- **cli**：命令行接口
- **tui**：终端用户界面
- **api**：REST API接口
- **sdk**：Python SDK

#### 4. 插件模块（Plugins）
- **storage**：存储插件（文件、数据库等）
- **monitoring**：监控插件
- **auth**：认证插件

## 依赖关系设计

### 依赖原则

1. **单向依赖原则**：Interfaces → Features → Core，Plugins可以依赖Core但不被Core依赖
2. **最小依赖**：每个模块只依赖真正需要的功能，避免传递依赖
3. **接口隔离**：模块间通过明确的接口通信，不直接依赖内部实现
4. **插件解耦**：插件通过标准接口与核心系统交互，可以独立开发和部署

### 具体依赖关系

```
Interfaces
    ↓
Features
    ↓
Core ← Plugins
```

- 所有模块都可以使用Core的config和logging
- Features模块之间可以相互依赖（如agents依赖workflows）
- Interfaces模块依赖需要的Features模块
- Plugins模块依赖Core接口，可以扩展Features功能

## 核心模块详细设计

### core/engine

```python
# 工作流引擎核心
class WorkflowEngine:
    def execute(self, workflow: Workflow, state: State) -> State
    def stream_execute(self, workflow: Workflow, state: State) -> Iterator[State]

# 状态管理
class StateManager:
    def save_state(self, state: State, checkpoint_id: str) -> bool
    def load_state(self, checkpoint_id: str) -> Optional[State]
    def list_checkpoints(self) -> List[str]

# 任务调度
class TaskScheduler:
    def schedule(self, task: Task) -> str
    def cancel(self, task_id: str) -> bool
    def get_status(self, task_id: str) -> TaskStatus
```

### core/config

```python
# 单一配置类
class Config:
    def get(self, key: str, default=None) -> Any
    def set(self, key: str, value: Any) -> None
    def reload(self) -> None

# 配置验证
class Schema:
    def validate(self, config: Dict[str, Any]) -> List[str]
    def get_defaults(self) -> Dict[str, Any]

# 配置加载
class Loader:
    def load_file(self, path: str) -> Dict[str, Any]
    def watch_file(self, path: str, callback: Callable) -> None
```

### core/logging

```python
# 简化的日志接口
class Logger:
    def debug(self, message: str, **kwargs) -> None
    def info(self, message: str, **kwargs) -> None
    def warning(self, message: str, **kwargs) -> None
    def error(self, message: str, **kwargs) -> None

# 多种输出格式
class Formatters:
    def text(self, record: LogRecord) -> str
    def json(self, record: LogRecord) -> str
    def structured(self, record: LogRecord) -> Dict[str, Any]

# 多种输出处理器
class Handlers:
    def console(self, formatter: Formatter) -> Handler
    def file(self, path: str, formatter: Formatter) -> Handler
    def remote(self, url: str, formatter: Formatter) -> Handler
```

## 配置系统设计

### 单一配置文件

```yaml
# config.yaml
application:
  name: "ModularAgent"
  version: "2.0.0"
  environment: "${ENV:development}"

core:
  engine:
    max_concurrent_workflows: 10
    checkpoint_interval: 30
  config:
    auto_reload: true
    watch_interval: 5
  logging:
    level: "INFO"
    outputs:
      - type: "console"
        format: "text"
      - type: "file"
        path: "logs/agent.log"
        format: "json"

features:
  llm:
    default_provider: "openai"
    timeout: 30
    max_retries: 3
  tools:
    auto_discovery: true
    plugin_paths: ["plugins/tools"]
  agents:
    default_type: "react"
    max_steps: 100
  workflows:
    template_path: "templates"
    auto_save: true

interfaces:
  cli:
    enabled: true
  tui:
    enabled: true
    refresh_rate: 0.1
  api:
    enabled: false
    host: "localhost"
    port: 8000

plugins:
  storage:
    type: "file"
    path: "data"
  monitoring:
    enabled: false
    metrics_port: 9090
```

### 环境变量支持

- `${ENV:development}`：环境变量替换，支持默认值
- `${VAR:default}`：通用环境变量语法
- 配置验证：启动时自动验证配置完整性

## 启动流程设计

### 简单启动流程

```python
# 主启动文件
class Application:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config.load(config_path)
        self.modules = {}
    
    def start(self):
        self._initialize_core()
        self._load_features()
        self._load_plugins()
        self._start_interfaces()
    
    def _initialize_core(self):
        # 初始化核心模块
        pass
    
    def _load_features(self):
        # 自动发现和加载功能模块
        pass
    
    def _load_plugins(self):
        # 加载插件
        pass
    
    def _start_interfaces(self):
        # 启动接口
        pass

# 使用方式
app = Application()
app.start()
```

### 模块自动发现

- 扫描模块目录，自动注册模块
- 延迟初始化：只初始化需要的模块
- 错误处理：清晰的错误信息和恢复建议

## 插件系统设计

### 插件接口

```python
# 基础插件接口
class Plugin:
    def initialize(self, config: Dict[str, Any]) -> None
    def start(self) -> None
    def stop(self) -> None
    def get_info(self) -> PluginInfo

# 存储插件接口
class StoragePlugin(Plugin):
    def save(self, key: str, data: Any) -> bool
    def load(self, key: str) -> Optional[Any]
    def delete(self, key: str) -> bool
    def list_keys(self) -> List[str]

# 监控插件接口
class MonitoringPlugin(Plugin):
    def record_metric(self, name: str, value: float, tags: Dict[str, str]) -> None
    def create_dashboard(self, config: Dict[str, Any]) -> str
    def get_metrics(self, query: str) -> List[Metric]
```

### 插件管理

```python
# 插件管理器
class PluginManager:
    def load_plugin(self, path: str) -> Plugin
    def unload_plugin(self, name: str) -> bool
    def list_plugins(self) -> List[PluginInfo]
    def get_plugin(self, name: str) -> Optional[Plugin]

# 插件注册表
class Registry:
    def register(self, plugin_class: Type[Plugin]) -> None
    def get(self, name: str) -> Optional[Type[Plugin]]
    def list_available(self) -> List[str]

# 动态插件加载
class Loader:
    def load_from_file(self, path: str) -> Plugin
    def load_from_module(self, module_name: str) -> Plugin
    def watch_directory(self, path: str, callback: Callable) -> None
```

### 插件特点

1. **热插拔**：运行时加载和卸载插件
2. **隔离性**：插件在独立环境中运行
3. **配置独立**：每个插件有自己的配置
4. **版本管理**：支持插件版本控制和依赖

## 迁移策略

### 全新开始

由于可以彻底放弃当前项目，迁移策略可以更加激进：

1. **创建新项目**：创建新的项目结构，不继承现有代码
2. **功能保留**：保留当前项目的核心功能需求，但重新实现
3. **渐进开发**：先实现核心功能，再逐步添加其他功能
4. **数据迁移**：提供工具将现有的配置、会话数据迁移到新格式
5. **并行开发**：在新架构稳定前，可以并行维护旧项目

### 关键迁移点

- **工作流定义格式转换**：将当前的工作流配置转换为新格式
- **配置文件格式统一**：将多层配置合并为单一配置文件
- **会话数据格式迁移**：提供数据迁移工具
- **API接口兼容性保证**：确保外部集成不受影响

### 迁移工具

```python
# 配置迁移工具
class ConfigMigrator:
    def migrate_old_config(self, old_config_path: str) -> Dict[str, Any]
    def validate_new_config(self, config: Dict[str, Any]) -> List[str]

# 数据迁移工具
class DataMigrator:
    def migrate_sessions(self, old_path: str, new_path: str) -> bool
    def migrate_workflows(self, old_path: str, new_path: str) -> bool
    def migrate_checkpoints(self, old_path: str, new_path: str) -> bool
```

## 新架构优势

### 与旧架构对比

| 方面 | 旧架构 | 新架构 |
|------|--------|--------|
| 架构模式 | 4层架构 | 功能模块化 |
| 依赖管理 | 复杂DI容器 | 简单工厂模式 |
| 配置管理 | 多层配置文件 | 单一配置文件 |
| 抽象程度 | 过度抽象 | 实用主义 |
| 开发效率 | 大量样板代码 | 简单直接 |
| 调试体验 | 调用链过长 | 清晰简单 |
| 扩展性 | 修改困难 | 插件化扩展 |

### 核心优势

1. **简单性**：消除了过度工程化的四层架构，采用直观的模块化设计
2. **可维护性**：清晰的模块边界和依赖关系，易于理解和修改
3. **可扩展性**：插件系统支持功能扩展，核心保持稳定
4. **开发效率**：减少样板代码，简化配置和启动流程
5. **调试友好**：简单的调用链，清晰的错误信息

## 实施计划

### 第一阶段：核心模块（2-3周）
- 实现core/engine、core/config、core/logging
- 基础的工作流执行能力
- 简单的配置和日志系统

### 第二阶段：功能模块（3-4周）
- 实现features/llm、features/tools
- 基础的智能体和工作流功能
- 简单的CLI接口

### 第三阶段：接口和插件（2-3周）
- 实现interfaces/tui、interfaces/api
- 插件系统基础框架
- 存储和监控插件

### 第四阶段：完善和优化（2-3周）
- 性能优化
- 文档完善
- 迁移工具开发

## 总结

新架构专注于解决实际问题，提供更好的开发体验和用户体验。通过简化设计、模块化组织和插件化扩展，新架构能够在保持功能完整性的同时，显著提高开发效率和可维护性。

这个设计彻底摆脱了当前四层架构的复杂性束缚，采用更加实用主义的方法，为项目的长期发展奠定了坚实的基础。