# 节点间上下文传递机制

## 概述

本项目采用LangGraph框架构建多智能体系统，通过状态管理和消息适配器机制来实现节点间的上下文传递。整个系统遵循领域驱动设计（DDD）原则，通过状态适配器在图系统状态和域层状态之间进行转换。

## 核心组件

### 1. 状态定义 (BaseGraphState)

- **BaseGraphState**: 使用 `Dict[str, Any]` 定义基础图状态
- **消息管理**: 使用 `operator.add` 作为reducer，确保消息列表追加而不是覆盖
- **关键字段**:
  - `messages`: LangChain消息列表（追加模式）
  - `metadata`: 元数据字典
  - `execution_context`: 执行上下文
  - `current_step`: 当前步骤标识

### 2. 状态适配器 (StateAdapter)

状态适配器负责在图系统状态和域层状态之间进行双向转换：

- **from_graph_state()**: 将图状态转换为域状态 (GraphAgentState)
- **to_graph_state()**: 将域状态转换为图状态
- **消息转换**: 处理LangChain消息与内部消息格式间的转换

### 3. 消息适配器 (MessageAdapter)

- **to_langchain_message()**: 将任意格式消息转换为LangChain格式
- **from_langchain_message()**: 将LangChain消息转换为字典格式
- **convert_message_list()**: 批量转换消息列表

### 4. 图构建器 (GraphBuilder)

- **NodeWithAdapterExecutor**: 节点执行器，整合状态转换功能
- **EnhancedNodeWithAdapterExecutor**: 增强执行器，集成状态管理功能
- **构建流程**: 验证配置 → 添加节点 → 添加边 → 设置检查点 → 编译图

## 上下文传递机制

### 1. 状态转换流程

```
图状态(WorkflowState) → 状态适配器 → 域状态(GraphAgentState) → 节点处理 → 状态适配器 → 图状态(WorkflowState)
```

### 2. 消息处理流程

每个节点执行时遵循以下流程：

1. **状态获取**: 从图状态获取当前上下文
2. **格式转换**: 使用状态适配器转换为域状态
3. **节点执行**: 节点处理业务逻辑
4. **状态更新**: 更新域状态（包括消息、元数据等）
5. **结果转换**: 将域状态转换回图状态
6. **传递到下一节点**: 图状态自动传递给下一节点

### 3. 消息追加机制

- 使用LangChain的消息格式 (`HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage`)
- 通过 `operator.add` reducer确保消息追加而非覆盖
- 每个节点可向消息列表添加新消息，保持上下文连续性

### 4. 协作状态管理

- **CollaborationStateAdapter**: 提供额外的状态协作功能
- **快照机制**: 执行前创建状态快照
- **变更记录**: 记录状态变化和错误信息
- **元数据附加**: 为状态添加协作相关元数据

## 具体实现示例

### LLM节点上下文传递

LLM节点是典型的上下文使用示例：

1. **获取历史消息**: 从状态中获取消息列表
2. **构建提示词**: 结合系统提示词、工具结果构建完整提示
3. **限制上下文**: 根据配置截断过长的消息历史
4. **生成响应**: 调用LLM生成响应
5. **更新状态**: 将AI响应追加到消息列表
6. **传递状态**: 返回更新后的状态供后续节点使用

### 节点执行生命周期

```python
def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
    # 1. 获取当前状态
    # 2. 使用状态适配器转换为域状态
    domain_state = state_adapter.from_graph_state(state)
    
    # 3. 执行节点业务逻辑
    result = self.node.execute(domain_state, config)
    
    # 4. 将结果转换回图状态
    return state_adapter.to_graph_state(result.state)
```

## 配置与扩展

### 节点注册机制

- **装饰器注册**: 使用 `@node("node_name")` 装饰器自动注册
- **类型检查**: 验证节点配置和类型兼容性
- **实例管理**: 支持单例和工厂模式创建节点实例

### 插件系统

- **Hook插件**: 在节点执行前后插入逻辑（如日志、监控）
- **状态管理**: 通过插件扩展状态处理能力
- **错误处理**: 统一的错误记录和恢复机制

## 最佳实践

1. **状态不可变性**: 尽量避免直接修改原始状态，创建新的状态对象
2. **消息追加**: 使用追加模式保持对话历史完整
3. **上下文管理**: 合理控制上下文大小，避免过度累积
4. **错误处理**: 在状态中记录错误信息，便于调试和恢复
5. **类型安全**: 使用类型注解确保状态字段的正确使用

## 总结

本项目通过状态适配器模式实现了图系统与域层之间的清晰分层，通过消息追加机制保证了上下文的连续性，通过协作状态管理提供了高级状态功能。这种设计既保持了LangGraph的原生能力，又提供了领域驱动的扩展性。