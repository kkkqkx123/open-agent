# 文档2：Agent核心与工作流需求文档（LangGraph集成版）

## 1. 文档标识
- 模块名称：Agent核心与工作流
- 版本：V2.0（LangGraph集成版）
- 依赖模块：基础架构与环境配置、模型集成、工具系统、配置系统
- 重大变更：引入LangGraph替换自定义工作流引擎

## 2. 模块目标
基于LangGraph实现Agent的核心推理能力与工作流编排，支持ReAct等工作流模式，利用LangGraph Studio提供可视化调试能力，确保Agent行为可配置、可观测。

## 3. 技术栈
- **核心库**：langgraph（工作流编排）、langgraph-studio（可视化）
- **数据验证**：pydantic（状态模型定义）
- **表达式引擎**：Jinja2（条件路由，可选）

## 4. 功能性需求

### 4.1 Agent核心能力

#### 4.1.1 对话上下文管理
- 定义`AgentState`（Pydantic模型），继承自LangGraph的`StateGraph`状态管理
- 包含字段：`messages`（对话历史）、`tool_calls`（工具调用记录）、`iteration_count`（迭代次数）
- 支持上下文窗口大小配置（通过`max_context_tokens`控制），自动截断超量历史消息
- 会话恢复时，能从`AgentState`重建完整对话上下文

#### 4.1.2 LangGraph节点定义
- **analysis_node**：调用LLM分析用户意图，判断是否需要调用工具
- **tool_selection_node**：根据意图从`ToolManager`获取可用工具，生成工具调用参数
- **tool_execution_node**：执行工具调用并处理结果
- **should_continue_edge**：根据迭代次数、工具调用结果判断是否终止工作流

#### 4.1.3 输出支持
- 同时支持非流式输出（完整结果返回）与流式输出（逐段返回）
- 流式输出时，支持"思考过程"与"最终结果"分离显示

#### 4.1.4 异常检测
- 利用LangGraph内置异常处理机制
- 检测工具调用连续失败，触发状态转换
- 检测工作流死循环，自动终止并返回异常信息

### 4.2 LangGraph工作流管理

#### 4.2.1 工作流定义（Python API）
- 使用LangGraph的`StateGraph` API定义工作流
- 支持多种工作流模式：
  ```python
  # ReAct模式示例
  graph = StateGraph(AgentState)
  
  graph.add_node("analyze", analysis_node)
  graph.add_node("execute_tool", tool_execution_node)
  
  graph.add_edge("start", "analyze")
  graph.add_conditional_edges(
      "analyze",
      should_continue,
      {"continue": "execute_tool", "end": END}
  )
  graph.add_edge("execute_tool", "analyze")
  ```

#### 4.2.2 预定义工作流模式
1. **ReAct模式**：推理→工具调用→结果处理循环
2. **Plan-and-Execute模式**：先生成计划→分步执行计划
3. **人工审核模式**：关键节点插入人工审核步骤

#### 4.2.3 工作流配置化支持
- 支持通过YAML配置生成LangGraph工作流（可选）
- 配置到代码的转换器，保持灵活性

### 4.3 LangGraph Studio集成

#### 4.3.1 实时可视化
- 集成LangGraph Studio提供工作流实时可视化
- 显示当前执行节点、状态变化、工具调用结果
- 支持工作流调试和性能分析

#### 4.3.2 会话回放
- 利用LangGraph内置状态追踪功能
- 支持会话历史回放和调试

## 5. 非功能性需求
- **可扩展性**：新增工作流模式时，只需定义新节点和边
- **性能**：LangGraph原生优化，节点执行高效
- **可观测性**：LangGraph Studio提供专业级监控

## 6. 依赖接口
- `IConfigLoader`（基础架构模块）：加载工作流配置
- `ILLMClient`（模型集成模块）：调用LLM完成推理
- `IToolManager`（工具系统模块）：获取可用工具列表
- `IConfigSystem`（配置系统模块）：获取Agent配置参数

## 7. 提供接口
- `IAgentCore`：Agent核心接口（`run(message: str, session_id: str) -> Union[Stream, str]`）
- `ILangGraphManager`：LangGraph管理接口（`create_workflow(config: dict) -> StateGraph`）
- `IWorkflowVisualizer`：可视化接口（`get_studio_url(session_id: str) -> str`）

## 8. 测试要点
- LangGraph工作流测试：验证节点执行和状态转换
- 集成测试：Agent与LangGraph的协同工作
- 可视化测试：LangGraph Studio功能验证

## 9. 与原始设计的差异

### 简化内容
- **移除**：自定义YAML工作流解析器
- **移除**：自定义状态管理器（StateManager）
- **移除**：自定义工作流监控器（WorkflowMonitor）
- **简化**：事件记录系统（利用LangGraph内置追踪）

### 新增优势
- **专业化**：使用业界标准的工作流框架
- **可视化**：集成LangGraph Studio专业调试工具
- **维护性**：减少自定义代码，依赖成熟框架
- **扩展性**：原生支持复杂工作流模式

## 10. 迁移策略
1. 阶段1：实现LangGraph基础集成，保持向后兼容
2. 阶段2：逐步迁移现有工作流到LangGraph
3. 阶段3：完全切换到LangGraph，移除旧有实现

---
*文档版本：V2.0 - LangGraph集成版*
*更新日期：2025-10-17*