# Agent架构重新设计

## 1. 当前架构分析

### 1.1 现状概述
当前项目中的Agent与Workflow紧密耦合，Agent配置主要作为Workflow节点的参数使用，缺乏独立的Agent层。

### 1.2 存在的问题
1. **职责不清**：Agent的智能决策逻辑与Workflow的流程控制逻辑混合
2. **紧耦合**：Agent和Workflow高度耦合，难以独立演进
3. **复用性差**：难以在不同Workflow中复用相同的Agent行为
4. **测试困难**：由于耦合，难以对Agent进行独立测试

### 1.3 当前架构关系
```
Workflow节点 ←→ Agent配置
    ↓              ↓
  直接使用      作为参数
```

## 2. 目标架构设计

### 2.1 设计原则
- **单一职责**：Agent专注于智能决策，Workflow专注于流程控制
- **松耦合**：通过接口和事件机制实现松耦合
- **高内聚**：相关功能聚集在各自的模块中
- **可扩展**：易于添加新的Agent类型和功能

### 2.2 架构层次
```
    UI/Presentation Layer
           ↓
    Application Layer (Session Management)
           ↓
    Workflow Layer (Process Control)
           ↓
    Agent Layer (Intelligence & Decision)
           ↓
    Infrastructure Layer (Tools, LLMs, etc.)
```

## 3. 详细设计

### 3.1 Agent域模型

#### 3.1.1 IAgent接口
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class IAgent(ABC):
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """执行Agent逻辑，返回更新后的状态"""
    
    @abstractmethod
    def can_handle(self, state: AgentState) -> bool:
        """判断Agent是否能处理当前状态"""
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取Agent的能力列表"""
```

#### 3.1.2 Agent基类
```python
class BaseAgent(IAgent):
    def __init__(self, config: AgentConfig, llm_client: ILLMClient, tool_executor: IToolExecutor):
        self.config = config
        self.llm_client = llm_client
        self.tool_executor = tool_executor
    
    async def execute(self, state: AgentState) -> AgentState:
        # 基础执行逻辑
        pass
    
    def can_handle(self, state: AgentState) -> bool:
        # 基础判断逻辑
        pass
```

### 3.2 Agent配置系统

#### 3.2.1 独立的Agent配置
```python
class AgentConfig(BaseConfig):
    # 基础配置
    name: str
    description: str
    agent_type: str  # 指定Agent类型，如"react", "plan_execute"等
    
    # 智能配置
    system_prompt: str
    decision_strategy: str  # 决策策略
    memory_config: MemoryConfig  # 记忆配置
    
    # 工具配置
    tools: List[str]
    tool_sets: List[str]
    
    # 行为配置
    max_iterations: int
    timeout: int
    retry_count: int
```

### 3.3 Agent管理器

#### 3.3.1 IAgentManager接口
```python
class IAgentManager(ABC):
    @abstractmethod
    def create_agent(self, config: AgentConfig) -> IAgent:
        """根据配置创建Agent"""
    
    @abstractmethod
    async def execute_agent(self, agent_id: str, input_state: AgentState) -> AgentState:
        """执行指定Agent"""
    
    @abstractmethod
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """注册Agent类型"""
```

#### 3.3.2 AgentManager实现
```python
class AgentManager(IAgentManager):
    def __init__(self, llm_registry: ILLMRegistry, tool_registry: IToolRegistry):
        self.llm_registry = llm_registry
        self.tool_registry = tool_registry
        self.agents: Dict[str, IAgent] = {}
        self.agent_types: Dict[str, Type[IAgent]] = {}
    
    def create_agent(self, config: AgentConfig) -> IAgent:
        if config.agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {config.agent_type}")
        
        llm_client = self.llm_registry.get_client(config.llm)
        tool_executor = self._create_tool_executor(config)
        
        agent_class = self.agent_types[config.agent_type]
        return agent_class(config, llm_client, tool_executor)
    
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        self.agent_types[agent_type] = agent_class
```

### 3.4 Agent状态管理

#### 3.4.1 AgentState重构
```python
@dataclass
class AgentState:
    # Agent特定状态
    agent_id: str = ""
    agent_config: Optional[AgentConfig] = None
    
    # 记忆相关
    memory: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 任务相关
    current_task: Optional[str] = None
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 工具执行结果
    tool_results: List[ToolResult] = field(default_factory=list)
    
    # 控制参数
    max_iterations: int = 10
    iteration_count: int = 0
    workflow_name: str = ""
    
    # 错误和日志
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
```

### 3.5 具体Agent实现

#### 3.5.1 ReAct Agent
```python
class ReActAgent(BaseAgent):
    """实现ReAct算法的Agent"""
    
    async def execute(self, state: AgentState) -> AgentState:
        # 实现ReAct算法：Reasoning + Acting
        # 1. 分析当前状态
        # 2. 决策下一步行动
        # 3. 执行行动（可能包括调用工具）
        # 4. 观察结果
        # 5. 更新状态
        pass
```

#### 3.5.2 Plan-Execute Agent
```python
class PlanExecuteAgent(BaseAgent):
    """实现Plan-and-Execute算法的Agent"""
    
    async def execute(self, state: AgentState) -> AgentState:
        # 1. 根据目标制定计划
        # 2. 逐步执行计划
        # 3. 监控执行结果
        # 4. 必要时调整计划
        pass
```

### 3.6 Workflow与Agent的交互

#### 3.6.1 调整Workflow节点
```python
# 修改后的Workflow节点
async def agent_execution_node(state: AgentState) -> AgentState:
    """调用独立的Agent而不是直接实现逻辑"""
    agent_manager = get_service(IAgentManager)
    
    # 根据当前状态选择合适的Agent
    agent_id = state.context.get("current_agent_id", "default_agent")
    
    # 执行Agent
    updated_state = await agent_manager.execute_agent(agent_id, state)
    
    return updated_state
```

#### 3.6.2 事件驱动的交互
```python
class AgentEvent(Enum):
    EXECUTION_STARTED = "execution_started"
    TOOL_CALL_REQUESTED = "tool_call_requested"
    DECISION_MADE = "decision_made"
    EXECUTION_COMPLETED = "execution_completed"
    ERROR_OCCURRED = "error_occurred"

class IAgentEventManager(ABC):
    @abstractmethod
    def subscribe(self, event_type: AgentEvent, handler: Callable) -> None:
        """订阅Agent事件"""
    
    @abstractmethod
    def publish(self, event: AgentEvent, data: Dict[str, Any]) -> None:
        """发布Agent事件"""
```

## 4. 实施计划

### 4.1 第一阶段：基础设施
- 创建Agent域模型和接口
- 实现基础的AgentManager
- 创建独立的Agent配置系统

### 4.2 第二阶段：核心实现
- 实现具体的Agent类型（ReAct, Plan-Execute等）
- 实现Agent状态管理
- 修改Workflow以使用独立的Agent

### 4.3 第三阶段：集成和优化
- 集成Agent事件系统
- 优化性能和错误处理
- 完善测试覆盖

## 5. 预期收益

1. **职责分离**：Agent和Workflow各司其职，代码更清晰
2. **可复用性**：Agent可在不同Workflow中复用
3. **可测试性**：独立的Agent更容易测试
4. **可扩展性**：更容易添加新的Agent类型
5. **维护性**：模块化设计，易于维护和演进

## 6. 风险和缓解

### 6.1 风险
- 迁移现有代码的工作量较大
- 可能引入新的复杂性

### 6.2 缓解措施
- 逐步迁移，保持向后兼容
- 充分的测试确保迁移质量
- 详细的文档和示例