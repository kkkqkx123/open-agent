# 接口层级架构文档

本文档说明 `src/interfaces` 目录中各接口的层级关系，虽然保持原有目录结构，但按照三层架构原则进行逻辑分层。

## 接口层级架构

### 应用层接口 (Application Layer Interfaces)
应用层接口负责业务流程编排、用例逻辑和跨领域服务协调。

#### 核心应用层接口
- `ISessionService` - 会话业务服务，协调会话相关的所有业务逻辑
- `IWorkflowManager` - 工作流管理服务，负责工作流的生命周期管理
- `IToolManager` - 工具管理服务，负责工具的注册、执行和管理
- `ILLMManager` - LLM管理服务，负责LLM客户端的管理和调度
- `IHistoryManager` - 历史管理服务，负责历史记录的管理和查询

#### 应用层接口特点
- 协调多个领域服务
- 处理业务用例
- 管理事务边界
- 提供高级API

### 领域层接口 (Domain Layer Interfaces)
领域层接口定义核心业务概念、业务规则和领域服务。

#### 核心领域接口
- `ISession` / `ISessionManager` - 会话核心概念和管理
- `IWorkflow` / `IWorkflowState` - 工作流核心概念和状态
- `IThread` / `IThreadManager` - 线程核心概念和管理
- `IState` / `IStateManager` - 状态核心概念和管理
- `ITool` / `IToolRegistry` - 工具核心概念和注册
- `ILLMClient` - LLM客户端核心抽象
- `ICheckpoint` / `ICheckpointManager` - 检查点核心概念和管理

#### 领域层接口特点
- 定义业务实体
- 封装业务规则
- 提供领域服务
- 保持业务纯净性

### 基础设施层接口 (Infrastructure Layer Interfaces)
基础设施层接口提供技术实现抽象、数据持久化和外部系统集成。

#### 核心基础设施接口
- `ISessionRepository` - 会话数据持久化
- `IStateRepository` - 状态数据持久化
- `ICheckpointRepository` - 检查点数据持久化
- `IHistoryRepository` - 历史数据持久化
- `ISnapshotRepository` - 快照数据持久化
- `IUnifiedStorage` - 统一存储抽象
- `IDependencyContainer` - 依赖注入容器
- `IConfigurationManager` - 配置管理
- `ILogger` - 日志记录

#### 基础设施层接口特点
- 提供技术抽象
- 处理数据持久化
- 集成外部系统
- 支持横切关注点

## 目录结构与层级映射

虽然保持原有目录结构，但各模块按以下方式映射到层级：

### 核心接口模块层级映射
```
src/interfaces/
├── common.py           # 基础设施层 - 通用接口
├── configuration.py    # 基础设施层 - 配置管理
├── container.py        # 基础设施层 - 依赖注入
├── llm.py             # 领域层 - LLM核心抽象 + 应用层 - LLM管理
├── checkpoint.py      # 领域层 - 检查点核心抽象
├── history.py         # 应用层 - 历史管理服务
└── storage/           # 基础设施层 - 存储抽象
```

### 子模块接口层级映射

#### prompts/ 模块
```
src/interfaces/prompts/
├── models.py          # 领域层 - 提示词核心实体
├── types.py           # 领域层 - 提示词类型抽象
├── loader.py          # 基础设施层 - 提示词加载
├── injector.py        # 应用层 - 提示词注入服务
├── cache.py           # 基础设施层 - 提示词缓存
└── registry.py        # 领域层 - 提示词注册管理
```

#### repository/ 模块
```
src/interfaces/repository/
├── session.py         # 基础设施层 - 会话数据访问
├── state.py           # 基础设施层 - 状态数据访问
├── checkpoint.py      # 基础设施层 - 检查点数据访问
├── history.py         # 基础设施层 - 历史数据访问
└── snapshot.py        # 基础设施层 - 快照数据访问
```

#### sessions/ 模块
```
src/interfaces/sessions/
├── base.py            # 领域层 - 会话核心管理
├── service.py         # 应用层 - 会话业务服务
└── association.py     # 领域层 - 会话关联关系
```

#### state/ 模块
```
src/interfaces/state/
├── interfaces.py      # 领域层 - 状态核心抽象
├── entities.py        # 领域层 - 状态实体定义
├── workflow.py        # 领域层 - 工作流状态
├── manager.py         # 领域层 - 状态管理服务
├── history.py         # 领域层 - 状态历史管理
├── snapshot.py        # 领域层 - 状态快照管理
├── serializer.py      # 基础设施层 - 状态序列化
├── factory.py         # 基础设施层 - 状态工厂
├── lifecycle.py       # 领域层 - 状态生命周期
└── storage/           # 基础设施层 - 状态存储
```

#### threads/ 模块
```
src/interfaces/threads/
├── base.py            # 领域层 - 线程核心管理
├── service.py         # 应用层 - 线程业务服务
├── collaboration.py   # 应用层 - 线程协作服务
├── branch_service.py  # 应用层 - 线程分支服务
├── coordinator.py     # 应用层 - 线程协调服务
└── storage.py         # 基础设施层 - 线程数据访问
```

#### tool/ 模块
```
src/interfaces/tool/
├── base.py            # 领域层 - 工具核心抽象
├── config.py          # 领域层 - 工具配置实体
├── state_manager.py   # 基础设施层 - 工具状态管理
├── registry.py        # 领域层 - 工具注册管理
├── executor.py        # 应用层 - 工具执行服务
└── factory.py         # 基础设施层 - 工具工厂
```

#### workflow/ 模块
```
src/interfaces/workflow/
├── core.py            # 领域层 - 工作流核心抽象
├── graph.py           # 领域层 - 工作流图抽象
├── execution.py       # 应用层 - 工作流执行服务
├── services.py        # 应用层 - 工作流管理服务
├── builders.py        # 应用层 - 工作流构建服务
├── templates.py       # 领域层 - 工作流模板
├── plugins.py         # 基础设施层 - 工作流插件
└── visualization.py   # 基础设施层 - 工作流可视化
```

## 依赖关系原则

### 依赖方向
1. **应用层** → **领域层** → **基础设施层**
2. 同层内可以相互依赖
3. 禁止反向依赖（基础设施层不能依赖领域层和应用层）

### 接口设计原则
1. **应用层接口**：组合多个领域服务，提供业务用例
2. **领域层接口**：定义业务概念，保持业务纯净
3. **基础设施层接口**：提供技术抽象，支持领域需求

### 实现指导
1. **应用层实现**：协调领域服务，处理业务逻辑
2. **领域层实现**：实现业务规则，保持独立性
3. **基础设施层实现**：提供技术支持，集成外部系统

## 接口命名约定

### 层级前缀约定
虽然保持原有命名，但理解其层级含义：
- `I*Manager` - 通常是应用层或领域层管理接口
- `I*Service` - 通常是应用层业务服务接口
- `I*Repository` - 通常是基础设施层数据访问接口
- `I*` (其他) - 根据功能确定层级

### 方法命名约定
- `create_*` / `get_*` / `update_*` / `delete_*` - 标准CRUD操作
- `*_async` - 异步版本方法
- `*_stream` - 流式处理方法
- `list_*` - 列表查询方法

## 最佳实践

### 接口设计
1. **单一职责**：每个接口只负责一个明确的职责
2. **接口隔离**：客户端不应该依赖它不需要的接口
3. **依赖倒置**：高层模块不应该依赖低层模块
4. **开闭原则**：对扩展开放，对修改关闭

### 层级协作
1. **应用层**通过领域层接口调用领域服务
2. **领域层**通过基础设施层接口获取技术支持
3. **基础设施层**实现具体的技术细节

### 测试策略
1. **应用层测试**：测试业务用例和流程编排
2. **领域层测试**：测试业务规则和领域逻辑
3. **基础设施层测试**：测试技术实现和集成

通过这种逻辑分层，我们可以在保持原有目录结构的同时，实现清晰的架构分层和职责分离。