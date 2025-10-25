# LangGraph编程Agent分层架构设计方案

在LangGraph中实现类似Claude Code的编程Agent系统，关键在于合理的分层设计和配置化管理。基于LangGraph的特性和最佳实践，建议采用以下分层架构。

## 推荐的层级划分

针对您的需求，建议采用**五层架构**：**LLM层 → Tool层 → Agent层 → Workflow层 → Session层**。这种划分既保证了模块化和可复用性，又与LangGraph的图结构自然契合。

### 1. LLM层（基础模型层）

**职责**：管理大语言模型的配置和实例化

**设计要点**：
- 通过配置文件管理不同模型的参数（model name、temperature、max_tokens等）
- 支持多模型配置，便于不同Agent使用不同的LLM
- 提供统一的模型调用接口

**配置示例**：
```yaml
llm:
  code_model:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.2
  planning_model:
    provider: "openai"
    model: "gpt-4o"
    temperature: 0.7
```

**实现方式**：
```python
def model_builder(config):
    return ChatOpenAI(
        model=config['model'],
        temperature=config['temperature']
    )
```

### 2. Tool层（工具层）

**职责**：封装所有外部工具和能力接口

**设计要点**：
- 每个工具独立定义，包含name、description和执行函数
- 工具描述应清晰明确，便于LLM理解和选择
- 支持工具的动态注册和组合

**配置示例**：
```yaml
tools:
  code_execution:
    name: "python_repl"
    description: "执行Python代码并返回结果"
    module: "tools.code_executor"
  file_operations:
    - name: "read_file"
      description: "读取文件内容"
    - name: "write_file"
      description: "写入文件"
```

**与图的关系**：工具通过ToolNode或ToolExecutor集成到图中，作为独立节点执行

### 3. Agent层（智能体层）

**职责**：定义单个Agent的行为逻辑和提示词

**设计要点**：
- **主Agent**：负责任务分解和总体协调
- **Sub-Agent**：专注特定领域（如代码生成、代码审查、测试等）
- 每个Agent包含独立的提示词模板和工具集

**配置示例**：
```yaml
agents:
  code_generator:
    prompt_template: "prompts/code_generator.txt"
    system_instruction: "你是一个专业的代码生成助手"
    tools: ["python_repl", "file_operations"]
    llm: "code_model"
  code_reviewer:
    prompt_template: "prompts/code_reviewer.txt"
    system_instruction: "你是代码审查专家"
    tools: ["read_file"]
    llm: "planning_model"
```

**实现方式**：
- 使用`create_react_agent`快速创建Agent
- 支持自定义提示词模板，通过`ChatPromptTemplate`管理
- Agent可以是简单的函数节点或完整的子图

**与图的关系**：每个Agent作为图中的一个节点，可以是函数节点或子图节点

### 4. Workflow层（工作流层）

**职责**：定义Agent之间的协作关系和执行流程

**设计要点**：

**a) 图结构配置**：
- 定义节点（Agents）和边（执行顺序）
- 支持条件边实现动态路由
- 支持循环结构实现迭代优化

**b) 多Agent架构模式**：
- **监督者模式（Supervisor）**：适合有明确主从关系的场景，主Agent协调多个Sub-Agent
- **分层架构（Hierarchical）**：适合复杂任务，支持多层级的Agent组织
- **自定义工作流**：预先定义Agent调用顺序

**配置示例**：
```yaml
workflow:
  architecture: "supervisor"  # 或 "hierarchical"
  nodes:
    - name: "supervisor"
      type: "agent"
      agent: "main_supervisor"
    - name: "code_generator"
      type: "agent"
      agent: "code_generator"
    - name: "code_reviewer"
      type: "agent"  
      agent: "code_reviewer"
  edges:
    - from: "START"
      to: "supervisor"
    - from: "code_generator"
      to: "supervisor"
    - from: "code_reviewer"
      to: "supervisor"
  conditional_edges:
    - from: "supervisor"
      condition: "route_decision"
      targets:
        code_generator: "code_generator"
        code_reviewer: "code_reviewer"
        FINISH: "END"
```

**状态管理**：
```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_code: str
    next: str  # 路由决策
```

**与图的关系**：Workflow层负责构建和编译StateGraph，是图结构的直接体现

### 5. Session层（会话层）

**职责**：管理用户会话、状态持久化和上下文

**设计要点**：
- 使用Checkpointer实现状态持久化
- 通过thread_id管理多个独立会话
- 支持会话恢复和历史查询

**配置示例**：
```yaml
session:
  checkpointer: "memory"  # 或 "sqlite", "postgres"
  memory_config:
    max_tokens: 100000
    strategy: "last"
```

**实现方式**：
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# 执行时指定thread_id
config = {"configurable": {"thread_id": "user_session_123"}}
result = graph.invoke(input_data, config=config)
```

**与图的关系**：Session层在图编译时注入checkpointer，不影响图结构本身

## 层级之间的关系图

```
Session层 (会话管理、状态持久化)
    ↓
Workflow层 (StateGraph、节点路由)
    ↓
Agent层 (提示词 + 工具绑定)
    ↓         ↓
Tool层    LLM层
```

## 配置文件组装实践

### 主配置文件结构

```yaml
# config.yaml
version: "1.0"

# LLM配置
llm:
  code_model: {...}
  planning_model: {...}

# 工具配置
tools:
  python_repl: {...}
  file_operations: {...}

# Agent配置
agents:
  main_supervisor:
    type: "supervisor"
    prompt_file: "prompts/supervisor.txt"
    llm: "planning_model"
    sub_agents: ["code_generator", "code_reviewer"]
  code_generator:
    prompt_file: "prompts/code_generator.txt"
    tools: ["python_repl", "file_operations"]
    llm: "code_model"

# Workflow配置
workflow:
  architecture: "supervisor"
  nodes: [...]
  edges: [...]

# Session配置
session:
  checkpointer: "memory"
```

### 提示词分离策略

**方式一：外部文件管理**
```python
# prompts/code_generator.txt
你是一个专业的Python代码生成助手。
根据用户需求生成高质量、可执行的代码。
```

**方式二：模板变量注入**
```yaml
agents:
  code_generator:
    system_instruction: "你是{role}，擅长{skill}"
    variables:
      role: "代码生成专家"
      skill: "Python编程"
```

## Sub-Agent实现方案

### 方案一：作为工具的Sub-Agent

适合简单的Sub-Agent，将其封装为工具供主Agent调用：

```python
@tool
def code_generator_agent(task: str, state: Annotated[dict, InjectedState]):
    # Sub-Agent逻辑
    result = sub_agent.invoke(task)
    return result

tools = [code_generator_agent, code_reviewer_agent]
main_supervisor = create_react_agent(llm, tools)
```

### 方案二：作为子图的Sub-Agent

适合复杂的Sub-Agent，定义为独立的子图：

```python
# 定义Sub-Agent子图
sub_agent_graph = StateGraph(SubAgentState)
sub_agent_graph.add_node("generator", generator_node)
sub_agent_graph.compile()

# 集成到主图
main_graph = StateGraph(MainState)
main_graph.add_node("sub_agent_team", 
    get_last_message | sub_agent_graph | join_result)
```

**状态转换**：子图与父图可能有不同的状态模式，需要添加输入/输出转换函数：
```python
def enter_subgraph(state):
    return {"messages": state["messages"]}

def exit_subgraph(response):
    return {"messages": [response["messages"][-1]]}
```

## 关键设计原则

1. **分离关注点**：提示词、工具、流程各自独立配置，便于维护和复用

2. **状态驱动**：通过State结构体管理Agent间通信，支持消息共享和私有状态

3. **条件路由**：使用条件边实现动态决策，根据Agent输出决定下一步执行路径

4. **可观测性**：配合LangSmith进行调试和监控，追踪多Agent执行流程

5. **渐进式复杂度**：从简单的单Agent开始，逐步演化为多Agent分层系统

通过这种分层设计，您可以灵活地通过配置文件组装不同的Agent系统，实现类似Claude Code的编程助手功能，同时保持良好的可维护性和扩展性。