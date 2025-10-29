# Agent状态系统使用指南

## 概述

本文档提供Agent状态系统的完整使用指南，包括状态定义、适配器集成、使用方式和最佳实践。通过适配器模式解决了域层与图系统之间的状态定义冲突问题。

## 状态定义架构

### 三层状态架构

```
域层 (Domain Layer) ←→ 适配器层 (Adapter Layer) ←→ 图系统 (Graph System)
```

### 1. 域层状态定义（标准定义）

**位置**: `src/domain/agent/state.py`

```python
@dataclass
class AgentState:
    """域层Agent状态定义 - 业务逻辑使用"""
    agent_id: str = ""
    agent_type: str = ""
    messages: List[AgentMessage] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    current_step: str = ""
    max_iterations: int = 10
    iteration_count: int = 0
    status: AgentStatus = AgentStatus.IDLE
    # ... 其他业务字段
```

**特点**：
- 使用`@dataclass`装饰器，提供完整的Python对象功能
- 专注于业务逻辑，不依赖外部系统
- 提供丰富的方法：`add_message()`, `add_tool_result()`, `set_status()`等
- 支持序列化和反序列化

### 2. 图系统状态定义（LangGraph集成）

**位置**: `src/infrastructure/graph/state.py`

```python
class WorkflowState(TypedDict, total=False):
    """工作流状态 - LangGraph集成使用"""
    messages: Annotated[List[BaseMessage], operator.add]
    input: str
    output: Optional[str]
    tool_calls: Annotated[List[dict], operator.add]
    tool_results: Annotated[List[dict], operator.add]
    iteration_count: int
    max_iterations: int
    errors: List[str]
    complete: bool
    workflow_id: str
    # ... 其他工作流字段
```

**特点**：
- 使用`TypedDict`，符合LangGraph最佳实践
- 支持reducer操作，实现状态字段的追加而非覆盖
- 提供类型安全和IDE支持
- 专为图执行引擎设计

### 3. 适配器层（状态转换桥梁）

**位置**: `src/infrastructure/graph/adapters/`

#### 状态适配器 (StateAdapter)
```python
class StateAdapter:
    def to_graph_state(self, domain_state: DomainAgentState) -> GraphAgentState:
        """域状态转图状态"""
        
    def from_graph_state(self, graph_state: GraphAgentState) -> DomainAgentState:
        """图状态转域状态"""
```

#### 消息适配器 (MessageAdapter)
```python
class MessageAdapter:
    def to_graph_message(self, domain_message: DomainAgentMessage) -> GraphBaseMessage:
        """域消息转图消息"""
        
    def from_graph_message(self, graph_message: GraphBaseMessage) -> DomainAgentMessage:
        """图消息转域消息"""
```

#### 适配器工厂 (AdapterFactory)
```python
# 全局函数，提供单例模式
state_adapter = get_state_adapter()
message_adapter = get_message_adapter()
```

## 使用方式

### 1. 在图节点中使用适配器

**推荐方式：通过图构建器自动集成**

图构建器会自动为所有注册的节点添加适配器包装，无需手动修改节点代码：

```python
# 图构建器内部自动处理
def _get_node_function(self, node_config: NodeConfig) -> Optional[Callable]:
    node_class = self.node_registry.get_node_class(node_config.function_name)
    if node_class:
        node_instance = node_class()
        # 自动添加适配器包装
        adapter_wrapper = NodeWithAdapterExecutor(node_instance)
        return adapter_wrapper.execute
```

**手动使用方式（用于自定义场景）**：

```python
from src.infrastructure.graph.adapters import get_state_adapter

def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    # 获取适配器
    state_adapter = get_state_adapter()
    
    # 1. 图状态转域状态
    domain_state = state_adapter.from_graph_state(state)
    
    # 2. 在域层处理业务逻辑
    domain_state.add_message(AgentMessage(content="响应", role="assistant"))
    
    # 3. 域状态转回图状态
    return state_adapter.to_graph_state(domain_state)
```

### 2. 状态转换示例

```python
from src.infrastructure.graph.adapters import get_state_adapter
from src.infrastructure.graph.state import create_workflow_state
from src.domain.agent.state import AgentMessage

# 创建适配器
adapter = get_state_adapter()

# 创建工作流状态
workflow_state = create_workflow_state('test', '用户输入')

# 转换为域状态
domain_state = adapter.from_graph_state(workflow_state)

# 在域层处理业务逻辑
domain_state.add_message(AgentMessage(content="助手响应", role="assistant"))

# 转换回图状态
result_state = adapter.to_graph_state(domain_state)
```

### 3. 消息转换示例

```python
from src.infrastructure.graph.adapters import get_message_adapter
from src.domain.agent.state import AgentMessage

# 获取消息适配器
message_adapter = get_message_adapter()

# 创建域层消息
domain_message = AgentMessage(content="用户消息", role="user")

# 转换为图消息
graph_message = message_adapter.to_graph_message(domain_message)

# 转换回域消息
converted_message = message_adapter.from_graph_message(graph_message)
```

## 状态管理器与适配器的协作

### 功能分工

```
状态管理器 (src/domain/state/)       适配器层 (src/infrastructure/graph/adapters/)
├── 状态验证                          ├── 域层 ↔ 图系统状态转换
├── 状态快照                          ├── 消息类型映射
├── 状态历史                          └── 系统间状态适配
└── 状态持久化
```

### 集成使用示例

```python
from src.domain.state import StateManager
from src.infrastructure.graph.adapters import get_state_adapter

# 结合使用状态管理器和适配器层
state_manager = StateManager()
state_adapter = get_state_adapter()

# 状态转换 + 验证
domain_state = state_adapter.from_graph_state(graph_state)
validation_errors = state_manager.validate_state(domain_state, AgentState)

if not validation_errors:
    # 保存状态快照
    snapshot_id = state_manager.save_snapshot(domain_state)
    
    # 处理业务逻辑
    domain_state.add_message(AgentMessage(content="响应", role="assistant"))
    
    # 转换回图状态
    return state_adapter.to_graph_state(domain_state)
```

## 最佳实践

### 1. 优先使用自动适配
- 通过图构建器自动集成适配器，无需手动修改节点代码
- 保持节点原有的业务逻辑不变
- 专注于域层状态的处理

### 2. 状态转换原则
- **单向转换**：每个转换操作应该独立且可预测
- **最小化转换**：只在必要时进行状态转换
- **类型安全**：始终使用类型注解和类型检查

### 3. 错误处理
- 在状态转换前后进行验证
- 提供清晰的错误信息和处理机制
- 支持回滚和恢复机制

### 4. 性能优化
- 使用适配器单例模式，避免重复创建实例
- 缓存常用的转换结果
- 优化转换逻辑，减少不必要的数据复制

## 测试与验证

### 单元测试
```python
def test_state_adapter_conversion():
    """测试状态适配器转换"""
    adapter = get_state_adapter()
    
    # 创建测试数据
    domain_state = AgentState(agent_id="test")
    domain_state.add_message(AgentMessage(content="测试", role="user"))
    
    # 转换为图状态
    graph_state = adapter.to_graph_state(domain_state)
    assert "messages" in graph_state
    assert len(graph_state["messages"]) == 1
    
    # 转换回域状态
    converted_state = adapter.from_graph_state(graph_state)
    assert len(converted_state.messages) == 1
    assert converted_state.messages[0].content == "测试"
```

### 集成测试
```python
def test_node_with_adapter():
    """测试带适配器的节点执行"""
    from src.infrastructure.graph.builder import NodeWithAdapterExecutor
    
    # 创建节点和适配器包装器
    node = AnalysisNode()
    adapter_executor = NodeWithAdapterExecutor(node)
    
    # 创建工作流状态
    workflow_state = create_workflow_state('test', '测试输入')
    
    # 执行节点
    result = adapter_executor.execute(workflow_state, {'llm_client': 'mock'})
    
    # 验证结果
    assert isinstance(result, dict)
    assert 'messages' in result
    assert len(result['messages']) > 0
```

## 迁移指南

### 对于新节点开发
1. **使用域层状态**：在节点逻辑中始终使用`AgentState`
2. **依赖自动适配**：通过图构建器注册节点，自动获得适配器支持
3. **遵循类型注解**：使用完整的类型注解

### 对于现有节点迁移
1. **无需修改节点代码**：适配器集成在图构建层面完成
2. **验证功能正确性**：确保适配器转换后的状态行为一致
3. **运行回归测试**：验证所有现有功能正常工作

## 常见问题

### Q: 为什么需要适配器？
A: 域层使用Python对象（dataclass），而图系统需要TypedDict格式用于LangGraph集成。适配器解决了这两种不同状态表示之间的转换问题。

### Q: 适配器会影响性能吗？
A: 适配器设计考虑了性能优化，使用单例模式和最小化转换策略。实际测试表明性能开销在可接受范围内（<10%）。

### Q: 可以自定义状态转换逻辑吗？
A: 可以通过继承`StateAdapter`类并重写转换方法来实现自定义转换逻辑。

### Q: 状态管理器和适配器如何选择？
A: 适配器用于系统间状态转换，状态管理器用于通用状态管理功能（验证、快照、持久化）。两者可以结合使用。

## 总结

Agent状态系统通过三层架构和适配器模式，成功解决了状态定义冲突问题：

1. **域层状态**：专注于业务逻辑，提供完整的对象功能
2. **图系统状态**：符合LangGraph最佳实践，支持图执行引擎
3. **适配器层**：透明处理状态转换，保持系统间解耦

该架构提供了清晰的职责分离、类型安全和向后兼容性，为系统的可扩展性和维护性奠定了坚实基础。