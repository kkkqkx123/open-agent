# Agent状态定义说明

## 当前状态实现情况

### 实现状态概述

**适配器层已实现但尚未完全集成**：虽然适配器层已经完整实现，但图节点尚未实际使用适配器进行状态转换。

### 域层状态定义（推荐使用）

**位置**: `src/domain/agent/state.py`

```python
@dataclass
class AgentState:
    """域层Agent状态定义"""
    agent_id: str = ""
    agent_type: str = ""
    messages: List[AgentMessage] = field(default_factory=list)
    # ... 其他字段
```

### 图系统状态定义（当前使用）

**位置**: `src/infrastructure/graph/state.py`

```python
class AgentState(BaseGraphState, total=False):
    """图系统Agent状态定义"""
    input: str
    output: Optional[str]
    # ... 其他字段
```

### 适配器层（已实现但未集成）

**位置**: `src/infrastructure/graph/adapters/`

- `StateAdapter`: 域层AgentState ↔ 图系统AgentState转换
- `MessageAdapter`: 域层AgentMessage ↔ 图系统消息转换  
- `AdapterFactory`: 适配器管理工厂

## 当前问题分析

### 1. 状态定义冲突依然存在

虽然适配器层已经实现，但图节点仍然直接使用域层的AgentState，没有进行状态转换：

```python
# 当前实现（问题）：节点直接使用域层状态
def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
    # 直接操作域层AgentState，没有转换
    state.messages.append(compatible_message)
```

### 2. 适配器导入但未使用

所有图节点都导入了适配器，但execute方法中没有实际使用：

```python
from src.infrastructure.graph.adapters import get_state_adapter, get_message_adapter
# 但execute方法中没有调用适配器
```

### 3. 图系统状态管理不一致

图执行器使用WorkflowState类型，但节点期望AgentState类型，存在类型不匹配。

## 推荐使用方式

### 正确的状态转换流程

```python
from src.infrastructure.graph.adapters import get_state_adapter

def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    # 1. 图状态转域状态
    state_adapter = get_state_adapter()
    domain_state = state_adapter.from_graph_state(state)
    
    # 2. 在域层处理业务逻辑
    domain_state.add_message(AgentMessage(content="响应", role="assistant"))
    
    # 3. 域状态转回图状态
    return state_adapter.to_graph_state(domain_state)
```

### 适配器使用示例

```python
# 获取适配器
state_adapter = get_state_adapter()
message_adapter = get_message_adapter()

# 状态转换
graph_state = state_adapter.to_graph_state(domain_state)
domain_state = state_adapter.from_graph_state(graph_state)

# 消息转换  
graph_message = message_adapter.to_graph_message(domain_message)
domain_message = message_adapter.from_graph_message(graph_message)
```

## 迁移计划

### 阶段1：适配器集成（待完成）
- [ ] 更新分析节点使用适配器
- [ ] 更新LLM节点使用适配器  
- [ ] 更新工具节点使用适配器
- [ ] 更新条件节点使用适配器

### 阶段2：状态统一（待完成）
- [ ] 移除基础设施层的重复状态定义
- [ ] 统一使用域层状态定义
- [ ] 更新所有导入引用

## 架构原则

1. **单一来源**：状态定义统一到域层
2. **适配器模式**：通过适配器解决系统间差异
3. **类型安全**：完整的类型注解和转换
4. **向后兼容**：逐步迁移，不破坏现有功能

## 总结

当前适配器层已经实现，但尚未集成到图节点执行流程中。状态定义冲突问题依然存在，需要通过适配器集成来解决。建议按照迁移计划逐步完成适配器集成工作。