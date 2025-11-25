# Modular Agent Framework Developer Guide

This document provides essential information for AI agents working with the Modular Agent Framework codebase.

## Project Overview

The Modular Agent Framework is a Python-based multi-agent system built on LangGraph, featuring:
- **Multi-model LLM integration** (OpenAI, Gemini, Anthropic, Mock)
- **Flexible tool system** supporting native, MCP, and built-in tools
- **Configuration-driven architecture** with YAML-based configs and environment variable injection
- **LangGraph Studio integration** for visualization and debugging
- **Flattened architectural layers**: Core + Services + Adapters
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
.venv\Scripts\activate  # Windows

# Install dependencies
uv sync

```

## Development Commands
When you find environment issues, you can use uv run to execute python commands in the virtual environment, or use .venv\Scripts\activate to activate the virtual environment first.

You can use the following commands to check the code quality:

```bash
uv run mypy <relative path to the file> --follow-imports=silent
uv run flake8 <relative path to the file>
```

Usually mypy is enough. if I didn't ask you to use remaining tools, you can skip them
If I don't ask you to check whole codebase, always use --follow-imports=silent to avoid check relative files.


**test**
```bash
uv run pytest <file-path or directory-path>
```

## Codebase Architecture

### New Flattened Architecture

The framework has been redesigned from a traditional 4-layer architecture to a flattened structure that reduces complexity while maintaining functionality:

**Previous Architecture**: Domain → Application → Infrastructure → Presentation
**New Architecture**: Core + Services + Adapters

### Directory Structure
src/
├── interfaces/             # 接口层（集中化接口定义）
├── core/                   # 核心模块（Domain + 部分Infrastructure）
│   ├── config/             # 统一配置系统
│   ├── tools/              # 工具系统核心
│   ├── llm/                # LLM系统核心
│   ├── workflow/           # 工作流核心
│   ├── state/              # 状态管理核心
│   ├── sessions/           # 会话管理核心
│   ├── threads/            # 线程管理核心
│   ├── checkpoints/        # 检查点核心
│   ├── history/            # 历史管理核心
│   ├── prompts/            # 提示系统核心
│   ├── storage/            # 存储核心
│   └── common/             # 通用组件
├── services/               # 服务层（Application + 部分Infrastructure）
│   ├── workflow/           # 工作流服务
│   ├── session/            # 会话服务
│   ├── thread/             # 线程服务
│   ├── checkpoint/         # 检查点服务
│   ├── history/            # 历史服务
│   ├── llm/                # LLM服务
│   ├── tools/              # 工具服务
│   ├── state/              # 状态服务
│   ├── container/          # 依赖注入容器
│   ├── logger/             # 日志服务
│   └── monitoring/         # 监控服务
├── adapters/               # 适配器层（Presentation的部分功能）
│   ├── storage/            # 存储适配器
│   ├── api/                # API适配器
│   ├── tui/                # TUI适配器
│   └── cli/                # CLI适配器
└── bootstrap.py            # 应用程序启动入口

### Core Infrastructure Components

1. **Unified Configuration System** (`src/core/config/`)
   - 简化的配置管理器，整合加载、处理和验证
   - 支持配置继承和环境变量解析
   - 类型安全的配置模型（Pydantic）
   - 配置缓存和性能优化
   - 配置导出和模板生成

2. **Dependency Injection Container** (`src/services/container/`)
   - 管理服务生命周期（单例、瞬态、作用域）
   - 支持多环境绑定（开发、测试、生产）
   - 自动依赖解析
   - 循环依赖检测与预防
   - 性能监控与缓存

3. **LLM Module** (`src/core/llm/` + `src/services/llm/`)
   - 核心接口和实体定义
   - 支持多提供商：OpenAI, Gemini, Anthropic, Mock
   - 连接池与可配置池大小
   - 智能故障转移机制
   - 基于提供商标记器的标记计数

4. **Tool System** (`src/core/tools/` + `src/services/tools/`)
   - 核心接口和工厂模式
   - 支持原生Python工具、MCP工具和内置工具
   - 动态工具发现与注册
   - 工具执行管理与错误处理
   - 工具缓存以优化性能

5. **Workflow Engine** (`src/core/workflow/` + `src/services/workflow/`)
   - 核心工作流实体和模式
   - LangGraph集成与自定义扩展
   - 状态管理与序列化能力
   - 节点注册表用于动态工作流组合
   - 带检查点持久化的图执行

6. **Session Management** (`src/core/sessions/` + `src/services/session/`)
   - 核心会话接口和实体
   - 会话生命周期管理（创建、更新、删除）
   - 线程管理与元数据跟踪
   - 检查点持久化与恢复
   - 会话状态序列化

7. **History Management** (`src/core/history/` + `src/services/history/`)
   - 核心历史接口和存储
   - 完整对话历史存储
   - 基于SQLite后端的检查点管理
   - 历史回放与分析

8. **State Management** (`src/core/state/` + `src/services/state/`)
   - 核心状态接口和存储
   - 带历史和快照的状态管理
   - SQLite后端持久化
   - 快照存储与恢复

9. **Thread Management** (`src/core/threads/` + `src/services/thread/`)
   - 核心线程接口和实体
   - 线程存储与元数据管理
   - 分支存储用于线程分支
   - 快照存储用于线程状态保存

10. **Checkpoint Management** (`src/core/checkpoints/` + `src/services/checkpoint/`)
    - 核心检查点接口和存储
    - 检查点存储与管理
    - 内存和SQLite存储后端
    - 性能优化

11. **Logging System** (`src/services/logger/`)
    - 多输出日志（控制台、文件、JSON）
    - 结构化日志与丰富格式
    - 敏感信息日志脱敏

12. **TUI Interface** (`src/adapters/tui/`)
    - 基于blessed的富终端用户界面
    - 实时工作流可视化
    - 组件化UI架构
    - 事件驱动交互模型

13. **API Interface** (`src/adapters/api/`)
    - 基于FastAPI框架的RESTful API
    - WebSocket支持实时通信
    - 认证与授权
    - 基于DAO模式的数据访问层

14. **Performance Monitoring** (`src/services/monitoring/`)
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
├── monitoring.yaml      # 性能监控配置
├── llms/                # 模型配置
│   ├── _group.yaml      # 模型组配置
│   ├── mock.yaml        # 模拟LLM配置
│   ├── test_no_function_calling.yaml
│   ├── provider/        # 供应商特定配置
│   │   ├── anthropic/   # Anthropic模型
│   │   ├── gemini/      # Gemini模型
│   │   ├── human_relay/ # 人工中继模型
│   │   └── openai/      # OpenAI模型
│   └── tokens_counter/  # 标记计数配置
├── nodes/               # 节点配置
├── prompts/             # 提示模板和系统消息
│   ├── rules/           # 提示规则
│   ├── system/          # 系统提示
│   └── user_commands/   # 用户命令提示
├── tool-sets/           # 工具集配置
├── tools/               # 个体工具配置
└── workflows/           # 工作流配置

关键特性：
- **配置继承**：使用`inherits_from`字段进行组配置与个体覆盖
- **环境变量注入**：`${ENV_VAR:DEFAULT}`格式自动解析
- **验证**：使用Pydantic模型进行配置验证和类型安全
- **热重载**：开发环境支持文件监听
- **多环境**：测试、开发、生产环境具有特定覆盖
- **模块化结构**：分层配置便于维护
- **类型安全**：所有配置选项强类型验证
- **性能**：缓存和懒加载以实现最佳性能

## 模块依赖关系

模块依赖关系：
接口层提供所有接口定义，是系统的基础约束。
核心层包含实体、基类和核心逻辑，依赖接口层。
服务层依赖于核心层和接口层，提供具体的业务服务实现。
适配器层依赖于核心层、服务层和接口层，提供外部接口适配。
依赖注入容器为所有层级提供服务解析。
配置系统为所有层级提供配置支持。
日志与监控系统贯穿所有层级。

旧的infrastructure已经废弃，留下的监控模块等待迁移。

### 依赖关系流

```
Adapters (API/TUI/CLI)
    ↓
Services (Business Logic)
    ↓
Core (Entities & Core Logic)
    ↓
Interfaces (Abstract Contracts)
```

## 开发流程

### 1. 新功能开发
- 遵循扁平化架构约束（Interfaces → Core → Services → Adapters）
- 在核心层定义接口和实体
- 在服务层实现业务逻辑
- 在适配器层提供外部接口
- 使用适当的生命周期（单例、瞬态、作用域）在依赖容器中注册服务
- 使用配置文件进行定制，支持继承和环境变量注入
- 编写单元和集成测试，进行适当的模拟
- 确保类型注解并遵循Python 3.13+类型提示
- 对所有服务依赖使用依赖注入
- 使用自定义异常类型实现适当的错误处理

### 2. 测试策略
- **单元测试**：核心层和服务层核心业务逻辑覆盖率≥90%
- **集成测试**：模块交互和基础设施组件覆盖率≥80%
- **端到端测试**：完整工作流和用户场景覆盖率≥70%

### 3. 代码质量标准
- 使用类型注解（由mypy严格模式强制执行）
- 编写包含参数和返回类型文档的完整docstring
- 遵循所有服务实例化的依赖注入模式
- 对所有外部依赖使用配置驱动方法

### 4. 配置变更
- 使用新的配置系统API进行配置管理
- 更新相应`_group.yaml`文件中的组配置
- 创建具有继承的特定`.yaml`配置文件
- 部署前使用环境检查器验证
- 在配置指南中记录新配置选项
- 确保环境变量引用使用`${VAR:DEFAULT}`格式
- 测试配置继承和环境变量解析
- 添加新选项时更新配置验证模式

### 5. 错误处理
- 使用来自`src.core.common.exceptions`的特定异常类型
- 在各层之间实现适当的错误传播
- 使用适当的上下文和严重性记录错误
- 为用户提供有意义的错误消息
- 优雅地处理配置错误并提供备用方案


## Coding Specifications
必须遵循mypy类型规范。例如，函数必须用类型提示进行注解。

### 接口定义位置
- **所有接口定义必须放在集中的接口层** (`src/interfaces/`)
- Core 层实现接口层的接口
- Services 层依赖接口层的接口
- Adapters 层实现或依赖接口层的接口
- 不允许在各层中定义分散的接口文件

### 接口使用原则
1. **单一真实来源**：所有接口定义集中在 `src/interfaces/` 目录
2. **类型安全**：使用 `TYPE_CHECKING` 避免运行时循环依赖。对于核心外部依赖，如langchain，不需要保证类型安全。
3. **统一导出**：通过 `src/interfaces/__init__.py` 统一导出所有接口
4. **向后兼容**：各层可以重新导出接口层的接口以保持兼容性

**注意：Sessions 服务模块说明(Sessions才是服务层的顶层模块，workflow是与langgraph交互的模块)**

## Language
代码和文档中始终使用中文。但在配置文件和与LLM提示相关的代码中，优先使用英文。
