# 第三阶段：LangGraph集成与YAML配置化工作流实施方案

## 项目概述

**阶段名称**：LangGraph集成与YAML配置化工作流  
**时间周期**：12天（2025-11-04 至 2025-11-15）  
**目标**：基于LangGraph重构Agent核心能力，支持YAML配置化工作流定义，集成状态追踪和可视化调试  
**技术栈**：LangGraph、LangGraph Studio、Pydantic、JSON Lines、YAML配置

## 1. 当前状态分析

### 1.1 项目现状
- ✅ 已有基础的LangGraph集成代码（`src/prompts/langgraph_integration.py`）
- ✅ 已有AgentState定义（`src/prompts/agent_state.py`）
- ✅ 已有提示词管理模块基础架构
- ✅ 已有模型集成、工具系统、提示词管理模块

### 1.2 需要改进的方向
- **工作流定义**：从硬编码转向YAML配置化
- **节点注册**：支持动态注册和发现工作流节点
- **边和触发器**：支持条件路由和动态边定义
- **配置驱动**：通过YAML文件定义完整工作流

## 2. 模块实施方案

### 2.1 YAML配置化工作流系统（6天）

#### 2.1.1 工作流配置架构（2天）
```python
# src/workflow/
├── __init__.py
├── manager.py              # IWorkflowManager实现
├── config.py               # 工作流配置模型
├── registry.py             # 节点注册表
├── builder.py              # 工作流构建器
├── nodes/                  # 预定义节点
│   ├── __init__.py
│   ├── analysis_node.py    # 分析节点
│   ├── tool_node.py        # 工具执行节点
│   ├── llm_node.py         # LLM调用节点
│   └── condition_node.py   # 条件判断节点
└── edges/                  # 边定义
    ├── __init__.py
    ├── simple_edge.py      # 简单边
    └── conditional_edge.py # 条件边
```

**YAML配置示例**：
```yaml
# configs/workflows/react.yaml
name: react_workflow
description: ReAct工作流模式
version: 1.0

state_schema:
  messages: List[BaseMessage]
  tool_calls: List[ToolCall]
  tool_results: List[ToolResult]
  iteration_count: int
  max_iterations: int

nodes:
  analyze:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      max_tokens: 2000
      
  execute_tool:
    type: tool_node
    config:
      tool_manager: default
      timeout: 30
      
  final_answer:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: final_answer

edges:
  - from: start
    to: analyze
    type: simple
    
  - from: analyze
    to: execute_tool
    condition: has_tool_call
    type: conditional
    
  - from: analyze
    to: final_answer
    condition: no_tool_call
    type: conditional
    
  - from: execute_tool
    to: analyze
    type: simple
```

#### 2.1.2 节点注册系统（2天）
```python
class NodeRegistry:
    """节点注册表"""
    
    def __init__(self):
        self._nodes: Dict[str, Type[BaseNode]] = {}
        
    def register_node(self, name: str, node_class: Type[BaseNode]) -> None:
        """注册节点类型"""
        self._nodes[name] = node_class
        
    def get_node(self, name: str) -> Type[BaseNode]:
        """获取节点类型"""
        if name not in self._nodes:
            raise ValueError(f"未知的节点类型: {name}")
        return self._nodes[name]
        
    def list_nodes(self) -> List[str]:
        """列出所有注册的节点类型"""
        return list(self._nodes.keys())

class BaseNode(ABC):
    """节点基类"""
    
    @abstractmethod
    def execute(self, state: AgentState, config: Dict) -> AgentState:
        """执行节点逻辑"""
        pass
        
    @abstractmethod
    def get_config_schema(self) -> Dict:
        """获取节点配置Schema"""
        pass

@dataclass
class AnalysisNode(BaseNode):
    """分析节点"""
    
    def execute(self, state: AgentState, config: Dict) -> AgentState:
        """执行分析逻辑"""
        llm_client = get_llm_client(config["llm_client"])
        response = llm_client.generate(state.messages)
        state.add_message(response)
        return state
        
    def get_config_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "llm_client": {"type": "string"},
                "max_tokens": {"type": "integer"}
            },
            "required": ["llm_client"]
        }
```

#### 2.1.3 工作流构建器（2天）
```python
class WorkflowBuilder:
    """工作流构建器"""
    
    def __init__(self, node_registry: NodeRegistry):
        self.node_registry = node_registry
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        
    def load_workflow_config(self, config_path: Path) -> WorkflowConfig:
        """加载工作流配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            
        return WorkflowConfig(**config_data)
        
    def build_workflow(self, config: WorkflowConfig) -> StateGraph:
        """根据配置构建工作流"""
        workflow = StateGraph(AgentState)
        
        # 注册节点
        for node_name, node_config in config.nodes.items():
            node_class = self.node_registry.get_node(node_config.type)
            node_instance = node_class()
            workflow.add_node(node_name, node_instance.execute)
            
        # 添加边
        for edge_config in config.edges:
            if edge_config.type == "simple":
                workflow.add_edge(edge_config.from_node, edge_config.to_node)
            elif edge_config.type == "conditional":
                condition_func = self._create_condition_function(edge_config.condition)
                workflow.add_conditional_edges(
                    edge_config.from_node,
                    condition_func,
                    {edge_config.to_node: edge_config.to_node}
                )
                
        workflow.set_entry_point(config.entry_point or "start")
        return workflow.compile()
        
    def _create_condition_function(self, condition: str) -> Callable:
        """创建条件函数"""
        if condition == "has_tool_call":
            return lambda state: "execute_tool" if state.tool_calls else "final_answer"
        elif condition == "no_tool_call":
            return lambda state: "final_answer" if not state.tool_calls else "execute_tool"
        else:
            # 支持自定义条件表达式
            return eval(f"lambda state: {condition}")
```

### 2.2 动态节点和边注册（3天）

#### 2.2.1 插件式节点系统（2天）
```python
# 配置驱动的节点注册
def register_nodes_from_config(config: Dict) -> None:
    """从配置注册节点"""
    for node_name, node_config in config.get("nodes", {}).items():
        if "class_path" in node_config:
            module_path, class_name = node_config["class_path"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            node_class = getattr(module, class_name)
            node_registry.register_node(node_name, node_class)
```

#### 2.2.2 条件边和触发器（1天）
```python
class ConditionalEdge:
    """条件边"""
    
    def __init__(self, condition: str, targets: Dict[str, str]):
        self.condition = condition
        self.targets = targets
        
    def evaluate(self, state: AgentState) -> str:
        """评估条件并返回目标节点"""
        if self.condition == "iteration_limit":
            return "end" if state.iteration_count >= state.max_iterations else "continue"
        elif self.condition == "has_final_answer":
            return "end" if self._has_final_answer(state) else "continue"
        else:
            # 支持自定义条件
            return self._evaluate_custom_condition(state)
            
class TriggerSystem:
    """触发器系统"""
    
    def __init__(self):
        self._triggers: Dict[str, List[Callable]] = {}
        
    def register_trigger(self, event: str, callback: Callable) -> None:
        """注册触发器"""
        if event not in self._triggers:
            self._triggers[event] = []
        self._triggers[event].append(callback)
        
    def fire(self, event: str, state: AgentState) -> None:
        """触发事件"""
        for callback in self._triggers.get(event, []):
            callback(state)
```

### 2.3 过程记录迁移（3天）

#### 2.3.1 增强的会话管理（2天）
```python
class EnhancedSessionManager(ISessionManager):
    """增强的会话管理器"""
    
    def __init__(self, storage_path: Path, workflow_builder: WorkflowBuilder):
        self.storage_path = storage_path
        self.workflow_builder = workflow_builder
        self.git_manager = GitManager(storage_path)
        
    def create_session(self, workflow_config: str, agent_config: str) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session_dir = self.storage_path / session_id
        
        # 创建工作流
        workflow_config = self.workflow_builder.load_workflow_config(workflow_config)
        workflow = self.workflow_builder.build_workflow(workflow_config)
        
        # 初始化Git仓库
        self.git_manager.init_repo(session_dir)
        
        # 保存会话配置
        self._save_session_config(session_id, workflow_config, agent_config)
        
        return session_id
        
    def restore_session(self, session_id: str) -> Tuple[StateGraph, AgentState]:
        """恢复会话"""
        session_dir = self.storage_path / session_id
        config = self._load_session_config(session_id)
        
        # 重建工作流
        workflow = self.workflow_builder.build_workflow(config.workflow_config)
        
        # 加载状态
        state = self._load_session_state(session_id)
        
        return workflow, state
```

#### 2.3.2 LangGraph Studio集成（1天）
```python
class EnhancedWorkflowVisualizer(IWorkflowVisualizer):
    """增强的工作流可视化器"""
    
    def __init__(self, studio_port: int = 8079, session_manager: ISessionManager = None):
        self.studio_port = studio_port
        self.session_manager = session_manager
        self.studio_process = None
        
    def visualize_workflow(self, workflow_config: WorkflowConfig) -> str:
        """可视化工作流配置"""
        # 生成工作流图
        graph_data = self._generate_graph_data(workflow_config)
        
        # 启动Studio（如果未运行）
        if not self.studio_process:
            self.start_studio()
            
        # 上传工作流配置到Studio
        studio_url = self._upload_to_studio(graph_data)
        return studio_url
        
    def _generate_graph_data(self, config: WorkflowConfig) -> Dict:
        """生成图数据"""
        nodes = []
        edges = []
        
        for node_name, node_config in config.nodes.items():
            nodes.append({
                "id": node_name,
                "type": node_config.type,
                "config": node_config.config
            })
            
        for edge_config in config.edges:
            edges.append({
                "source": edge_config.from_node,
                "target": edge_config.to_node,
                "type": edge_config.type,
                "condition": getattr(edge_config, 'condition', None)
            })
            
        return {"nodes": nodes, "edges": edges}
```

## 3. 目录结构规划

### 3.1 新的目录结构
```
src/
├── workflow/                   # 工作流模块（新增）
│   ├── __init__.py
│   ├── manager.py              # 工作流管理器
│   ├── config.py               # 配置模型
│   ├── registry.py             # 节点注册表
│   ├── builder.py              # 工作流构建器
│   ├── nodes/                  # 预定义节点
│   │   ├── __init__.py
│   │   ├── base.py             # 节点基类
│   │   ├── analysis_node.py    # 分析节点
│   │   ├── tool_node.py        # 工具执行节点
│   │   ├── llm_node.py         # LLM调用节点
│   │   └── condition_node.py   # 条件判断节点
│   ├── edges/                  # 边定义
│   │   ├── __init__.py
│   │   ├── base.py             # 边基类
│   │   ├── simple_edge.py      # 简单边
│   │   └── conditional_edge.py # 条件边
│   └── triggers/               # 触发器系统
│       ├── __init__.py
│       └── base.py             # 触发器基类
├── session/                    # 会话管理模块（增强）
│   ├── __init__.py
│   ├── manager.py              # 会话管理器
│   ├── store.py                # 存储后端
│   ├── event_collector.py      # 事件收集器
│   ├── player.py               # 回放器
│   └── git_manager.py          # Git版本管理
└── agent/                      # Agent核心模块（重构）
    ├── __init__.py
    ├── core.py                 # Agent核心
    └── config.py               # Agent配置

configs/
├── workflows/                  # 工作流配置目录（新增）
│   ├── react.yaml             # ReAct工作流
│   ├── plan_execute.yaml      # Plan-and-Execute工作流
│   ├── human_review.yaml      # 人工审核工作流
│   └── custom/                # 自定义工作流
│       └── example.yaml
└── agents/                    # Agent配置
    ├── data_analyst.yaml
    └── code_reviewer.yaml
```

### 3.2 配置示例
```yaml
# configs/workflows/custom/example.yaml
name: custom_workflow
description: 自定义工作流示例
version: 1.0

entry_point: start

nodes:
  start:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: assistant
      
  tool_selection:
    type: analysis_node  
    config:
      llm_client: openai-gpt4
      max_tokens: 1000
      
  tool_execution:
    type: tool_node
    config:
      tool_manager: default
      timeout: 30
      
  human_review:
    type: condition_node
    config:
      condition: "state.requires_human_review"
      
  final_output:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: final_answer

edges:
  - from: start
    to: tool_selection
    type: simple
    
  - from: tool_selection
    to: tool_execution
    condition: "len(state.tool_calls) > 0"
    type: conditional
    
  - from: tool_selection
    to: human_review
    condition: "state.requires_human_review"
    type: conditional
    
  - from: tool_selection
    to: final_output
    condition: "len(state.tool_calls) == 0 and not state.requires_human_review"
    type: conditional
    
  - from: tool_execution
    to: start
    type: simple
    
  - from: human_review
    to: final_output
    type: simple
```

## 4. 实施时间表

### 第1周：YAML配置化工作流（6天）

#### 第1-2天：工作流配置架构
- 工作流配置模型定义
- YAML配置解析器
- 配置验证系统

#### 第3-4天：节点注册系统
- 节点基类和接口定义
- 节点注册表实现
- 预定义节点开发

#### 第5-6天：工作流构建器
- 动态工作流构建
- 条件边和触发器
- 配置到代码转换

### 第2周：增强功能和集成（6天）

#### 第7-8天：动态节点和边
- 插件式节点系统
- 条件边评估器
- 触发器系统

#### 第9-10天：会话管理增强
- 增强的会话管理器
- Git版本管理集成
- 状态持久化优化

#### 第11-12天：Studio集成和测试
- LangGraph Studio可视化
- 完整集成测试
- 性能优化和文档

## 5. 关键特性

### 5.1 YAML配置化优势
- **灵活性**：通过配置文件定义复杂工作流
- **可维护性**：配置与代码分离，易于修改
- **可扩展性**：支持自定义节点和边
- **可视化**：配置可直观展示工作流结构

### 5.2 向后兼容性
- 保持现有`src/prompts/langgraph_integration.py`接口
- 提供配置迁移工具
- 支持渐进式迁移

## 6. 测试策略

### 6.1 配置验证测试
- YAML配置语法验证
- 节点配置Schema验证
- 工作流完整性检查

### 6.2 集成测试
- 工作流构建和执行测试
- 节点注册和发现测试
- 条件边和触发器测试

### 6.3 性能测试
- 工作流构建性能
- 大规模配置加载性能
- 会话恢复性能

---
*文档版本：V2.0 - YAML配置化版本*
*更新日期：2025-10-20*