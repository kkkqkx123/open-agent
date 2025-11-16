文档、注释、回答问题时始终使用中文，代码及配置文件中需要作为上下文供llm使用的则统一使用英文

# Modular Agent Framework Developer Guide

This document provides essential information for AI agents working with the Modular Agent Framework codebase.

## Project Overview

The Modular Agent Framework is a Python-based multi-agent system built on LangGraph, featuring:
- **Multi-model LLM integration** (OpenAI, Gemini, Anthropic, Mock)
- **Flexible tool system** supporting native, MCP, and built-in tools
- **Configuration-driven architecture** with YAML-based configs and environment variable injection
- **LangGraph Studio integration** for visualization and debugging
- **Clean architectural layers**: Domain → Application → Infrastructure → Presentation
- **Complete dependency injection** with multi-environment support
- **Real-time TUI interface** with rich components
- **RESTful API** for external integration
- **Session and thread management** with checkpoint persistence
- **Workflow engine** with ReAct and other patterns

## Development Environment Setup

### Prerequisites
- Python 3.13+
- uv (Python package manager) - install single package via `uv add`

### Environment Setup with uv
(already complete)
```bash
# Create virtual environment
uv venv

# Activate virtual environment
#(In VSCode, you can skip this step. IDE can automatically activate virtual environment)
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv sync

```

## Development Commands

### Code Quality Tools
(usually mypy is enough. if I didn't ask you to use remaining tools, you can skip them)
If I don't ask you to check whole codebase, always use --follow-imports=silent to avoid check relative files.

### Testing

### Environment Checking

### Application Execution

### Development Utilities

## Codebase Architecture

### Architectural Layers
Presentation Layer (TUI/API) → Application Layer → Domain Layer → Infrastructure Layer

### Directory Structure
src/
├── domain/              # Business logic and entities (no dependencies on other layers)
│   ├── checkpoint/     # Checkpoint interfaces and configuration
│   ├── history/        # History management interfaces and models
│   ├── prompts/        # Prompt templates and injection system
│   ├── sessions/       # Session management interfaces
│   ├── state/          # State management interfaces and collaboration
│   ├── threads/        # Thread management interfaces and models
│   ├── tools/          # Tool interfaces and types
│   └── workflow/       # Workflow entities and value objects
├── infrastructure/      # Technical implementations (depends only on domain)
│   ├── checkpoint/     # Checkpoint storage and management
│   ├── config/         # Configuration system with inheritance and validation
│   ├── container/      # Dependency injection container with lifecycle management
│   ├── graph/          # LangGraph integration with workflow execution
│   ├── history/        # History storage and service integration
│   ├── llm/            # LLM client implementations with fallback mechanisms
│   ├── logger/         # Logging system with multiple outputs and formatting
│   ├── state/          # State management with history and snapshots
│   ├── threads/        # Thread storage and metadata management
│   └── tools/          # Tool system with validation and execution
├── application/         # Use cases and workflows (depends on domain and infrastructure)
│   ├── checkpoint/     # Checkpoint management and serialization
│   ├── history/        # History management with adapters and token tracking
│   ├── sessions/       # Session lifecycle management and event collection
│   ├── threads/        # Thread coordination with branching and collaboration
│   └── workflow/       # Workflow orchestration with templates and visualization
└── presentation/       # UI and API interfaces (depends on all other layers)
    ├── api/            # RESTful API with routers, services, and data access
    ├── cli/            # Command line interface with error handling
    └── tui/            # Terminal user interface with components and subviews

### Core Infrastructure Components

1. **Dependency Injection Container** (`src/infrastructure/container/`)
   - 管理服务生命周期（单例、瞬态、作用域）
   - 支持多环境绑定（开发、测试、生产）
   - 自动依赖解析
   - 循环依赖检测与预防
   - 性能监控与缓存

2. **Configuration System** (`src/infrastructure/config/`)
   - 加载支持继承的YAML配置文件
   - 环境变量注入（`${VAR}` 和 `${VAR:default}`语法）
   - 配置热重载与文件监听
   - 配置验证与类型安全
   - 多环境配置支持

3. **Environment Checker** (`src/infrastructure/environment.py`)
   - 验证Python版本兼容性（≥3.13）
   - 检查所需包依赖
   - 验证系统资源（内存、磁盘空间）

4. **LLM Module** (`src/infrastructure/llm/`)
   - 支持多提供商：OpenAI, Gemini, Anthropic, Mock
   - 连接池与可配置池大小
   - 智能故障转移机制
   - 基于提供商标记器的标记计数

5. **Tool System** (`src/infrastructure/tools/`)
   - 支持原生Python工具、MCP工具和内置工具
   - 动态工具发现与注册
   - 工具执行管理与错误处理
   - 工具缓存以优化性能

6. **Workflow Engine** (`src/infrastructure/graph/`)
   - LangGraph集成与自定义扩展
   - 状态管理与序列化能力
   - 节点注册表用于动态工作流组合
   - 带检查点持久化的图执行

7. **Session Management** (`src/application/sessions/`)
   - 会话生命周期管理（创建、更新、删除）
   - 线程管理与元数据跟踪
   - 检查点持久化与恢复
   - 会话状态序列化

8. **History Management** (`src/infrastructure/history/`)
   - 完整对话历史存储
   - 基于SQLite后端的检查点管理
   - 历史回放与分析

9. **State Management** (`src/infrastructure/state/`)
   - 带历史和快照的状态管理
   - SQLite后端持久化
   - 快照存储与恢复

10. **Thread Management** (`src/infrastructure/threads/`)
    - 线程存储与元数据管理
    - 分支存储用于线程分支
    - 快照存储用于线程状态保存

11. **Checkpoint Management** (`src/infrastructure/checkpoint/`)
    - 检查点存储与管理
    - 内存和SQLite存储后端
    - 性能优化

12. **Logging System** (`src/infrastructure/logger/`)
    - 多输出日志（控制台、文件、JSON）
    - 结构化日志与丰富格式
    - 敏感信息日志脱敏

13. **TUI Interface** (`src/presentation/tui/`)
    - 基于blessed的富终端用户界面
    - 实时工作流可视化
    - 组件化UI架构
    - 事件驱动交互模型

14. **API Interface** (`src/presentation/api/`)
    - 基于FastAPI框架的RESTful API
    - WebSocket支持实时通信
    - 认证与授权
    - 基于DAO模式的数据访问层

15. **Performance Monitoring** (`src/infrastructure/monitoring/`)
    - 统一性能监控系统
    - 配置驱动的YAML配置
    - 性能指标收集与报告

### Configuration System

配置结构：
configs/
├── global.yaml          # 全局设置（日志、密钥、环境）
├── application.yaml     # 应用特定设置
├── history.yaml         # 历史和检查点配置
├── prompts.yaml         # 提示模板和系统消息
├── threads.yaml         # 线程管理配置
├── checkpoints/         # 检查点配置
│   └── _group.yaml      # 检查点组配置
├── graphs/              # 图和工作流示例配置
│   ├── react_example.yaml
│   └── react_with_hooks_example.yaml
├── hooks/               # 钩子配置
│   ├── _group.yaml      # 钩子组配置
│   ├── agent_execution_node_hooks.yaml
│   ├── global_hooks.yaml
│   ├── llm_node_hooks.yaml
│   └── tool_node_hooks.yaml
├── monitoring.yaml      # 性能监控配置
├── llms/                # 模型配置
│   ├── _group.yaml      # 模型组配置
│   ├── mock.yaml        # 模拟LLM配置
│   ├── test_no_function_calling.yaml
│   ├── provider/        # 供应商特定配置
│   │   ├── anthropic/   # Anthropic模型（Claude）
│   │   ├── gemini/      # Gemini模型（Gemini Pro）
│   │   ├── human_relay/ # 人工中继模型
│   │   └── openai/      # OpenAI模型（GPT-4，GPT-3.5）
│   └── tokens_counter/  # 标记计数配置
├── nodes/               # 节点配置
│   └── _group.yaml
├── prompts/             # 提示模板和系统消息
│   ├── rules/           # 提示规则
│   ├── system/          # 系统提示
│   └── user_commands/   # 用户命令提示
├── tool-sets/           # 工具集配置
│   └── _group.yaml      # 工具集组配置
├── tools/               # 个体工具配置
│   ├── calculator.yaml  # 计算器工具
│   ├── database.yaml    # 数据库工具
│   ├── fetch.yaml       # 获取工具
│   ├── hash_convert.yaml # 哈希转换工具
│   ├── sequentialthinking.yaml # 顺序思考工具
│   └── weather.yaml     # 天气工具
└── workflows/           # 工作流配置
    ├── base_workflow.yaml        # 基础工作流模板
    ├── react_workflow.yaml       # ReAct工作流
    ├── react_agent_workflow.yaml  # ReAct代理工作流
    ├── plan_execute.yaml        # 计划执行工作流
    ├── plan_execute_agent_workflow.yaml # 计划执行代理工作流
    ├── collaborative.yaml       # 协作工作流
    ├── human_review.yaml        # 人工审核工作流
    ├── bad_example_workflow.yaml # 错误示例工作流
    ├── connectivity_test_workflow.yaml # 连通性测试工作流
    └── react.yaml              # React配置

关键特性：
- **配置继承**：使用`inherits_from`字段进行组配置与个体覆盖
- **环境变量注入**：`${ENV_VAR:DEFAULT}`格式自动解析
- **验证**：使用Pydantic模型进行配置验证和类型安全
- **热重载**：开发环境支持文件监听
- **多环境**：测试、开发、生产环境具有特定覆盖
- **模块化结构**：分层配置便于维护
- **类型安全**：所有配置选项强类型验证
- **性能**：缓存和懒加载以实现最佳性能

## Module Dependencies and Relationships

模块依赖关系：
基础设施层包含配置系统、日志与指标、依赖注入。
配置系统和依赖注入共同为LLM集成、工具系统、工作流引擎提供支持。
LLM集成、工具系统、工作流引擎共同构成应用层的基础。
应用层包括会话管理、线程管理、历史管理。
会话管理、线程管理、历史管理又共同支撑表现层。
表现层包含TUI接口、API接口、CLI接口。
日志与指标系统贯穿整个架构，为所有层级提供支持。

## Development Workflow

### 1. 新功能开发
- 遵循架构层约束（领域→应用→基础设施→表现）
- 使用适当的生命周期（单例、瞬态、作用域）在依赖容器中注册服务
- 使用配置文件进行定制，支持继承和环境变量注入
- 编写单元和集成测试，进行适当的模拟
- 确保类型注解并遵循Python 3.13+类型提示
- 对所有服务依赖使用依赖注入
- 使用自定义异常类型实现适当的错误处理

### 2. 测试策略
- **单元测试**：领域和应用层核心业务逻辑覆盖率≥90%
- **集成测试**：模块交互和基础设施组件覆盖率≥80%
- **端到端测试**：完整工作流和用户场景覆盖率≥70%

### 3. 代码质量标准
- 使用类型注解（由mypy严格模式强制执行）
- 遵循black格式化（行长度：88，目标Python 3.13+）
- 使用isort组织导入（black配置文件）
- 通过flake8全面规则进行linting
- 编写包含参数和返回类型文档的完整docstring
- 遵循所有服务实例化的依赖注入模式
- 对所有外部依赖使用配置驱动方法

### 4. 配置变更
- 更新相应`_group.yaml`文件中的组配置
- 创建具有继承的特定`.yaml`配置文件
- 部署前使用环境检查器验证
- 在配置指南中记录新配置选项
- 确保环境变量引用使用`${VAR:DEFAULT}`格式
- 测试配置继承和环境变量解析
- 添加新选项时更新配置验证模式

### 5. 服务注册
- 在适当的依赖注入模块中注册服务
- 使用适当的服务生命周期（共享资源使用单例，请求范围使用瞬态）
- 为所有外部依赖实现服务接口
- 为所有服务提供测试实现
- 使用依赖注入容器进行所有服务解析

### 6. 错误处理
- 使用来自`src.infrastructure.exceptions`的特定异常类型
- 在各层之间实现适当的错误传播
- 使用适当的上下文和严重性记录错误
- 为用户提供有意义的错误消息
- 优雅地处理配置错误并提供备用方案

## Error Handling Patterns

使用来自`src.infrastructure.exceptions`的特定异常类型：
- `InfrastructureError` - 基础异常
- `ServiceNotRegisteredError` - DI容器问题
- `ServiceCreationError` - 服务实例化问题
- `CircularDependencyError` - 依赖循环检测
- `ConfigurationError` - 配置加载问题
- `EnvironmentCheckError` - 环境验证失败
- `ArchitectureViolationError` - 层级依赖违规

## Testing Utilities

框架提供了`TestContainer`用于集成测试：
`TestContainer`提供了一个隔离的测试环境，可以设置基本配置并获取服务进行测试。测试完成后会自动清理。

## Module Dependencies and Architecture

### Detailed Module Relationships

详细模块关系：
表现层（TUI接口、API接口、CLI接口）依赖于应用层的会话管理。
应用层（会话管理、工作流编排、线程协调、历史管理、检查点管理）依赖于领域层的接口。
领域层（检查点接口、历史接口、线程接口、工具接口、会话接口、状态接口、工作流实体、提示系统）依赖于基础设施层的实现。
基础设施层（依赖注入、配置系统、LLM集成、工具系统、工作流引擎、历史存储、日志与指标、状态管理、线程存储、检查点存储）是技术实现的基础。
配置系统为LLM集成、工具系统、工作流引擎提供配置支持。
依赖注入为所有基础设施组件提供服务解析。
LLM集成、工具系统、工作流引擎共同支持应用层的工作流编排。
历史存储支持应用层的历史管理。
日志与指标系统为所有层级提供支持。
状态管理、线程存储、检查点存储分别支持领域层的状态、线程、检查点接口。

### Service Registration Patterns

服务注册模式：
使用模块的di_config注册服务，如WorkflowModule.register_services_with_dependencies。
根据环境（测试、开发、生产）注册相应的服务。

### Configuration Inheritance Example

配置继承示例：
基础配置定义通用设置，特定配置通过inherits_from字段继承并覆盖或添加参数。

### Error Handling Patterns

错误处理模式：
捕获特定异常类型并进行相应处理，如服务未注册、服务创建错误、循环依赖、配置错误等。

## Language
代码和文档中始终使用中文。但在配置文件和与LLM提示相关的代码中，优先使用英文。

## Coding Specifications
必须遵循mypy类型规范。例如，函数必须用类型提示进行注解。