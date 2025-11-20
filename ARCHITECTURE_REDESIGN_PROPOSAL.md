# 工作流架构重新设计方案

## 设计原则

1. **严格分层依赖**: Adapters → Services → Core，禁止反向依赖
2. **接口隔离**: 所有接口定义在独立的接口模块中
3. **依赖倒置**: 高层模块不依赖低层模块，都依赖抽象
4. **单一职责**: 每个模块只负责一个明确的职责

## 新架构设计

### 1. 接口层重构

#### 1.1 创建独立接口模块

```
src/interfaces/
├── __init__.py
├── workflow/
│   ├── __init__.py
│   ├── core.py          # 核心工作流接口
│   ├── execution.py     # 执行相关接口
│   ├── state.py         # 状态相关接口
│   ├── graph.py         # 图相关接口
│   └── validation.py    # 验证相关接口
├── state/
│   ├── __init__.py
│   └── interfaces.py    # 状态管理接口
└── tools/
    ├── __init__.py
    └── interfaces.py    # 工具相关接口
```

#### 1.2 接口定义原则

- 所有接口定义在 `src/interfaces/` 下
- 接口不依赖具体实现
- 接口之间可以相互引用，但不能形成循环

### 2. Core层重构

#### 2.1 Core层职责重新定义

```
src/core/workflow/
├── __init__.py          # 简化导入
├── entities/            # 实体定义
│   ├── __init__.py
│   ├── workflow.py      # 工作流实体
│   └── execution.py     # 执行实体
├── value_objects/       # 值对象
│   ├── __init__.py
│   ├── step.py          # 步骤值对象
│   └── transition.py    # 转换值对象
├── exceptions/          # 异常定义
│   ├── __init__.py
│   └── workflow.py      # 工作流异常
├── graph/               # 图相关核心逻辑
│   ├── __init__.py
│   ├── interfaces.py    # 图接口（从src/interfaces/graph导入）
│   ├── nodes/           # 节点核心逻辑
│   │   ├── __init__.py
│   │   ├── base.py      # 节点基类
│   │   ├── llm_node.py  # LLM节点
│   │   └── tool_node.py # 工具节点
│   └── edges/           # 边核心逻辑
│       ├── __init__.py
│       └── base.py      # 边基类
├── config/              # 配置核心逻辑
│   ├── __init__.py
│   └── models.py        # 配置模型
└── workflow.py          # 工作流核心实现
```

#### 2.2 Core层依赖规则

- Core层只依赖接口层 (`src/interfaces/`)
- Core层不依赖Services层
- Core层内部模块可以相互依赖，但不能形成循环

### 3. Services层重构

#### 3.1 Services层职责重新定义

```
src/services/workflow/
├── __init__.py          # 简化导入
├── interfaces/          # 服务接口（从src/interfaces导入）
│   └── __init__.py
├── execution/           # 执行服务
│   ├── __init__.py
│   ├── executor.py      # 执行器实现
│   └── strategies.py    # 执行策略
├── building/            # 构建服务
│   ├── __init__.py
│   ├── builder.py       # 构建器实现
│   └── factory.py       # 工厂实现
├── validation/          # 验证服务
│   ├── __init__.py
│   ├── validator.py     # 验证器实现
│   └── rules.py         # 验证规则
├── configuration/       # 配置服务
│   ├── __init__.py
│   ├── loader.py        # 配置加载器
│   └── processor.py     # 配置处理器
└── registry/            # 注册表服务
    ├── __init__.py
    ├── function_registry.py  # 函数注册表
    └── node_registry.py      # 节点注册表
```

#### 3.2 Services层依赖规则

- Services层依赖Core层和接口层
- Services层内部模块可以相互依赖，但不能形成循环
- Services层不依赖Adapters层

### 4. 依赖注入重构

#### 4.1 容器配置

```
src/services/container/
├── __init__.py
├── workflow_container.py    # 工作流容器配置
└── bindings.py              # 依赖绑定配置
```

#### 4.2 依赖注入原则

- 所有依赖通过容器注入
- 避免硬编码依赖
- 支持接口和实现的绑定

## 具体重构方案

### 1. 解决接口循环依赖

#### 1.1 移动IWorkflowState接口

**当前问题**:
- `src/core/workflow/interfaces.py` 定义 `IWorkflowState`
- `src/core/workflow/states/base.py` 使用 `IWorkflowState`
- 形成循环依赖

**解决方案**:
- 将 `IWorkflowState` 移到 `src/interfaces/state/interfaces.py`
- 更新所有引用

#### 1.2 重构验证器接口

**当前问题**:
- Core层验证器依赖Services层功能

**解决方案**:
- 在 `src/interfaces/workflow/validation.py` 定义验证接口
- Core层提供基础验证逻辑
- Services层实现具体验证功能

### 2. 解决节点配置依赖

#### 2.1 定义配置接口

**当前问题**:
- Core层节点直接依赖Services层配置加载器

**解决方案**:
- 在 `src/interfaces/workflow/config.py` 定义配置接口
- Core层节点通过接口使用配置
- Services层实现配置加载器

#### 2.2 使用依赖注入

**实施方案**:
- 节点通过构造函数接收配置接口
- 容器负责注入具体实现
- 避免直接依赖

### 3. 简化模块导入

#### 3.1 清理__init__.py

**当前问题**:
- `__init__.py` 导入过多内容
- 增加循环依赖风险

**解决方案**:
- 只导入必要的公共接口
- 具体实现由用户按需导入
- 使用延迟导入

#### 3.2 导入优化

**实施方案**:
- 使用 `TYPE_CHECKING` 进行类型检查导入
- 使用函数内部导入避免循环依赖
- 提供便捷的导入函数

## 实施步骤

### 第一阶段：接口重构

1. 创建 `src/interfaces/` 目录结构
2. 移动接口定义到正确位置
3. 更新所有接口引用
4. 测试接口导入

### 第二阶段：Core层重构

1. 重构Core层目录结构
2. 移除Core层对Services层的依赖
3. 更新Core层内部依赖
4. 测试Core层功能

### 第三阶段：Services层重构

1. 重构Services层目录结构
2. 实现新的服务接口
3. 更新Services层内部依赖
4. 测试Services层功能

### 第四阶段：依赖注入重构

1. 配置依赖注入容器
2. 更新所有依赖注入
3. 测试依赖注入功能
4. 优化性能

### 第五阶段：集成测试

1. 端到端功能测试
2. 性能测试
3. 兼容性测试
4. 文档更新

## 预期效果

1. **消除循环依赖**: 所有循环依赖将被解决
2. **清晰架构**: 分层明确，职责清晰
3. **易于维护**: 模块化设计，便于维护
4. **易于测试**: 依赖注入，便于单元测试
5. **易于扩展**: 接口设计，便于功能扩展

## 风险控制

1. **向后兼容**: 保持API兼容性
2. **渐进迁移**: 分阶段实施，降低风险
3. **全面测试**: 每个阶段都进行充分测试
4. **回滚机制**: 准备回滚方案

## 成功指标

1. 所有模块可以正常导入
2. 没有循环依赖警告
3. 单元测试通过率100%
4. 集成测试通过率100%
5. 性能不低于重构前