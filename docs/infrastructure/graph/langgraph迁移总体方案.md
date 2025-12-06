# LangGraph迁移总体方案

## 概述

本文档提供了LangGraph迁移到基础设施层的完整方案，旨在彻底移除LangGraph外部依赖，建立自主可控的图工作流引擎。

## 迁移背景

### 当前依赖分析

项目主要通过以下组件使用LangGraph：

1. **LangGraphAdapter**：核心适配器，负责LangGraph图的创建和管理、工作流执行和流式处理、Checkpoint状态管理
2. **LangGraphCheckpointAdapter**：检查点适配器，作为反防腐层将领域模型转换为LangGraph格式
3. **TUI组件**：LangGraph状态面板显示

### 核心功能使用

项目中主要使用了LangGraph的以下核心功能：

1. **状态图构建（StateGraph）**：构建有状态的工作流图，支持节点和边的定义
2. **检查点管理（Checkpoint）**：工作流状态持久化和恢复
3. **工作流执行（Pregel）**：执行编译后的图工作流
4. **图常量和类型**：图定义和执行控制

## 核心发现与策略调整

### 重要发现

通过深入分析发现，项目已经在核心层实现了完善的图工作流系统：

1. **GraphService**：提供统一的图操作接口，集成节点、边、触发器、插件等所有组件
2. **ElementBuilderFactory**：统一的元素构建器创建和管理功能
3. **完整的节点和边实现**：包括各种类型的节点（LLMNode、ToolNode、ConditionNode等）和边
4. **插件和触发器系统**：支持扩展和自定义行为

### 策略调整：整合而非替换

基于以上发现，迁移策略从完全替换调整为整合：

1. **保留核心层graph系统**：不丢弃已经完善的核心层graph系统
2. **基础设施层专注于LangGraph功能替代**：只实现LangGraph特有的功能
3. **适配器层改造**：使用新的基础设施层组件替换LangGraph依赖

## 迁移架构设计

### 整体架构

迁移后的架构将包含以下层次：

1. **核心层**：保留现有的GraphService、Graph、ElementBuilderFactory等组件
2. **基础设施层**：新增StateGraphEngine、ExecutionEngine、CheckpointManager等组件
3. **适配器层**：改造LangGraphAdapter和LangGraphCheckpointAdapter使用新组件
4. **服务层**：WorkflowService、ThreadService、CheckpointService保持不变

### 组件映射关系

| LangGraph组件 | 基础设施层组件 | 功能说明 |
|---------------|---------------|----------|
| StateGraph | StateGraphEngine | 状态图构建和管理 |
| Pregel | ExecutionEngine | 图工作流执行引擎 |
| BaseCheckpointSaver | BaseCheckpointSaver | 检查点保存器基类 |
| InMemorySaver | MemoryCheckpointSaver | 内存检查点保存器 |
| SqliteSaver | SqliteCheckpointSaver | SQLite检查点保存器 |
| BaseChannel | BaseChannel | 通道基类 |
| LastValue | LastValueChannel | 最后值通道 |
| Topic | TopicChannel | 主题通道 |
| BinaryOperatorAggregate | BinaryOperatorChannel | 二元操作通道 |
| Command | Command | 命令控制 |
| Send | Send | 消息发送 |
| StateSnapshot | StateSnapshot | 状态快照 |

## 实施计划

### 第一阶段：基础设施层实现（2-3周）

1. **创建目录结构**
   - src/infrastructure/graph/engine/
   - src/infrastructure/graph/execution/
   - src/infrastructure/graph/checkpoint/
   - src/infrastructure/graph/channels/
   - src/infrastructure/graph/types/

2. **迁移可直接复用的组件**
   - 基础类型和常量
   - 错误定义
   - 通道系统

3. **实现核心组件**
   - StateGraphEngine
   - ExecutionEngine
   - CheckpointManager

### 第二阶段：适配器层改造（1-2周）

1. **重写LangGraphAdapter**为InternalGraphAdapter
2. **重写LangGraphCheckpointAdapter**为InternalCheckpointAdapter
3. **保持与核心层graph系统的协作**
4. **集成测试**

### 第三阶段：集成和优化（1-2周）

1. **确保基础设施层与核心层graph系统的良好集成**
2. **性能测试和优化**
3. **移除LangGraph依赖**
4. **文档更新**

## 预期收益

### 技术收益

1. **减少外部依赖**：移除对LangGraph的依赖，降低供应链风险
2. **保留现有投资**：不丢弃已经完善的核心层graph系统
3. **性能优化**：针对项目特定需求优化的执行引擎
4. **更好的系统集成**：减少适配层复杂度，提高代码可维护性

### 业务收益

1. **成本降低**：减少外部依赖的许可和维护成本
2. **自主可控**：完全自主可控的核心技术
3. **响应速度**：更快的问题定位和修复速度
4. **扩展性**：更好的业务扩展支持

## 风险控制

1. **功能验证**：每个阶段完成后进行全面的功能验证
2. **性能测试**：确保新实现性能不低于原LangGraph实现
3. **回滚计划**：准备快速回滚方案
4. **监控告警**：迁移过程中加强监控和告警

## 结论

通过整合而非替换的策略，我们可以在移除LangGraph依赖的同时，最大化保留现有投资。这种方案既能实现技术目标，又能降低迁移风险，预计4-6周完成迁移。
