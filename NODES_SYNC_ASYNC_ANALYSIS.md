# 节点同步/异步实现分析与修改方案

## 问题发现

在分析workflow nodes的实现后，发现了**与LLMNode类似的跨域调用问题**。

### 当前各节点的实现情况

| 节点类型 | execute() | execute_async() | 问题 |
|---------|---------|---|------|
| **LLMNode** | ✗ 创建新循环运行_execute_async() | ✓ 有真实异步实现 | 跨域调用 |
| **ToolNode** | ✓ 纯同步 | ❓ 未找到实现 | 无async实现 |
| **ConditionNode** | ✓ 纯同步 | ❓ 未找到实现 | 无async实现 |
| **StartNode** | ✓ 纯同步 | ❓ 未找到实现 | 无async实现 |
| **EndNode** | ✓ 纯同步 | ❓ 未找到实现 | 无async实现 |
| **WaitNode** | ✓ 纯同步 | ❓ 未找到实现 | 无async实现 |

## 问题1：LLMNode的跨域调用问题

**代码（第45-57行）**：
```python
def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
    """执行LLM调用逻辑"""
    try:
        import asyncio
        
        # 在同步方法中运行异步逻辑
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._execute_async(state, config))
        finally:
            loop.close()
```

**问题**：
- ✗ 在execute()中创建新事件循环运行_execute_async()
- ✗ 这是跨域调用：从同步方法进入异步
- ✗ 如果execute()在异步上下文中被调用，会导致问题
- ✗ 违反了workflow execution modes的设计原则

**为什么出现这个问题**：
- LLMNode的真实逻辑是异步的（调用LLM需要I/O）
- 但被迫实现同步execute()以符合接口
- 所以只能在execute()中创建新循环

## 问题2：其他节点缺少execute_async()实现

**观察**：
- ToolNode、ConditionNode等只有execute()
- 没有找到它们的execute_async()实现
- 是否继承自BaseNode的默认实现？

让我检查BaseNode：

```python
# BaseNode (base.py 第82-92行)
@abstractmethod
async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
    """异步执行节点"""
    pass
```

**问题**：
- BaseNode的execute_async()是抽象方法，子类必须实现
- 但ToolNode、ConditionNode没有实现
- 这应该导致编译错误，除非它们是在其他文件中实现的

## 修改方案

### 方案A：节点应该分为两类（推荐）✓

```
BaseNode
├─ SyncNode（纯同步节点）
│  └─ 只实现execute()
│  └─ execute_async()从BaseNode继承（会raise）
│
└─ AsyncNode（可异步节点）
   └─ 既实现execute()也实现execute_async()
   └─ 都有真实实现（不互相调用）
```

#### 实现方式

**1. 创建SyncNode基类**
```python
# src/core/workflow/graph/nodes/sync_node.py
class SyncNode(BaseNode):
    """纯同步节点基类
    
    用于本地快速操作的节点（条件判断、状态转换等）
    不支持异步调用。
    """
    
    @abstractmethod
    def execute(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """同步执行节点"""
        pass
    
    async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点（不支持）
        
        纯同步节点不支持异步调用。
        请使用AsyncMode中的SyncMode，或改为AsyncNode。
        """
        raise RuntimeError(
            f"节点 {self.node_id} 是纯同步节点，不支持异步执行。"
            f"请使用 SyncMode 或改为 AsyncNode 实现。"
        )
```

**2. 修改LLMNode为AsyncNode**
```python
# src/core/workflow/graph/nodes/async_node.py
class AsyncNode(BaseNode):
    """异步节点基类
    
    用于I/O密集操作的节点（LLM调用、API请求等）
    同时支持同步和异步调用。
    """
    
    def execute(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """同步执行节点（仅作为兼容性提供）
        
        注意：在已有事件循环的上下文中调用会失败。
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                f"节点 {self.node_id} 不能在事件循环中以同步方式调用。"
                f"请使用 execute_async() 或在线程池中执行。"
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
            
            # 没有循环，创建新循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute_async(state, config))
            finally:
                loop.close()
    
    @abstractmethod
    async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点（真实实现）"""
        pass
```

**3. 具体节点继承对应基类**
```python
# LLM节点：异步节点
class LLMNode(AsyncNode):
    async def execute_async(self, state, config):
        # 真实异步实现
        ...

# 条件节点：同步节点  
class ConditionNode(SyncNode):
    def execute(self, state, config):
        # 快速同步条件判断
        ...

# 工具节点：同步节点（工具执行由工具系统负责异步性）
class ToolNode(SyncNode):
    def execute(self, state, config):
        # 同步协调工具执行
        ...
```

### 方案B：不分离，统一使用AsyncNode（不推荐）✗

**缺点**：
- 所有节点都支持异步，但大多数是假异步
- ConditionNode、StartNode等不需要异步
- 浪费资源和复杂度

### 方案C：保持现状，只修改LLMNode（折中）⚠️

**优点**：
- 影响最小
- 只修改LLMNode

**缺点**：
- 其他节点仍然不一致
- 没有清晰的架构规范
- 未来容易出现类似问题

## 推荐方案详细实现

### Step 1：创建基类

**文件：src/core/workflow/graph/nodes/sync_node.py**
```python
"""纯同步节点基类"""

from typing import Dict, Any
from src.interfaces.workflow.graph import INode, NodeExecutionResult
from src.interfaces.state.interfaces import IState
from .base import BaseNode


class SyncNode(BaseNode):
    """纯同步节点基类
    
    用于本地、快速、CPU密集的操作。
    示例：条件判断、数据转换、状态管理
    
    特点：
    - execute()有真实同步实现
    - execute_async()抛出RuntimeError
    - 不能在异步上下文中被直接调用
    """
    
    async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点（不支持）
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Raises:
            RuntimeError: 纯同步节点不支持异步执行
        """
        raise RuntimeError(
            f"SyncNode '{self.node_id}' does not support async execution. "
            f"This node is synchronous only. "
            f"Consider using AsyncMode with SyncMode, or refactor as AsyncNode."
        )
```

**文件：src/core/workflow/graph/nodes/async_node.py**
```python
"""异步节点基类"""

import asyncio
import logging
from typing import Dict, Any
from src.interfaces.workflow.graph import INode, NodeExecutionResult
from src.interfaces.state.interfaces import IState
from .base import BaseNode

logger = logging.getLogger(__name__)


class AsyncNode(BaseNode):
    """异步节点基类
    
    用于I/O密集操作。
    示例：LLM调用、API请求、数据库查询
    
    特点：
    - execute()创建新循环调用execute_async()
    - execute_async()有真实异步实现
    - 同步调用会有新循环创建的开销
    - 异步调用无额外开销
    """
    
    def execute(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """同步执行节点（创建新事件循环）
        
        警告：
        - 不能在已有事件循环的上下文中调用
        - 会创建新的事件循环，有性能开销
        - 优先使用 execute_async()
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
            
        Raises:
            RuntimeError: 如果在运行的事件循环中调用
        """
        try:
            # 检查是否已在事件循环中
            asyncio.get_running_loop()
            raise RuntimeError(
                f"AsyncNode '{self.node_id}' cannot be called synchronously "
                f"from within a running event loop. "
                f"Use execute_async() instead."
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
            
            # 没有循环，创建新循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                logger.warning(
                    f"AsyncNode '{self.node_id}' executing synchronously. "
                    f"This creates a new event loop, consider using execute_async()."
                )
                return loop.run_until_complete(self.execute_async(state, config))
            finally:
                loop.close()
```

### Step 2：修改现有节点

**ToolNode → SyncNode**
```python
from .sync_node import SyncNode

@node("tool_node")
class ToolNode(SyncNode):  # 改为继承SyncNode
    """工具执行节点"""
    
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        # 现有实现保持不变
        ...
    
    # 不需要实现execute_async()
```

**ConditionNode → SyncNode**
```python
from .sync_node import SyncNode

@node("condition_node")
class ConditionNode(SyncNode):  # 改为继承SyncNode
    """条件判断节点"""
    
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        # 现有实现保持不变
        ...
```

**LLMNode → AsyncNode**
```python
from .async_node import AsyncNode

@node("llm_node")
class LLMNode(AsyncNode):  # 改为继承AsyncNode
    """LLM调用节点"""
    
    # 移除execute()中创建新循环的代码
    # execute()会从AsyncNode继承（自动创建循环）
    
    async def execute_async(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        # 将现有的_execute_async()逻辑移到这里
        ...
```

**StartNode / EndNode / WaitNode → SyncNode**
```python
from .sync_node import SyncNode

@node("start_node")
class StartNode(SyncNode):
    def execute(self, state, config):
        # 现有实现
        ...

@node("end_node")
class EndNode(SyncNode):
    def execute(self, state, config):
        # 现有实现
        ...

@node("wait_node")
class WaitNode(SyncNode):
    def execute(self, state, config):
        # 现有实现
        ...
```

### Step 3：更新BaseNode

```python
class BaseNode(INode, ABC):
    """节点基类（抽象）
    
    注意：不要直接继承此类实现节点。
    应该继承 SyncNode 或 AsyncNode。
    """
    
    @abstractmethod
    def execute(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """同步执行节点（子类必须实现）"""
        pass
    
    @abstractmethod
    async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点（子类必须实现或继承默认）"""
        pass
```

## 修改清单

```
[ ] 1. 创建 src/core/workflow/graph/nodes/sync_node.py
[ ] 2. 创建 src/core/workflow/graph/nodes/async_node.py
[ ] 3. 修改 LLMNode：继承AsyncNode，移除execute()中的循环代码
[ ] 4. 修改 ToolNode：继承SyncNode
[ ] 5. 修改 ConditionNode：继承SyncNode
[ ] 6. 修改 StartNode：继承SyncNode
[ ] 7. 修改 EndNode：继承SyncNode
[ ] 8. 修改 WaitNode：继承SyncNode
[ ] 9. 更新 __init__.py 导出新的基类
[ ] 10. 更新文档和示例
[ ] 11. 运行测试验证
```

## 性能影响

### 改进前后对比

| 场景 | 改进前 | 改进后 | 改进 |
|------|--------|--------|------|
| **LLMNode异步调用** | 直接调用_execute_async() | 直接调用execute_async() | 无变化 ✓ |
| **LLMNode同步调用** | 创建新循环 | 从AsyncNode继承（创建新循环） | 无变化 ✓ |
| **ConditionNode异步调用** | 创建新循环调用execute() | 直接抛RuntimeError | 改善（避免不必要的循环） ✓ |
| **ToolNode异步调用** | 创建新循环调用execute() | 直接抛RuntimeError | 改善（避免不必要的循环） ✓ |

## 向后兼容性

⚠️ **破坏性变更**

如果外部代码以异步方式调用SyncNode：
```python
# 旧代码（现在会失败）
result = await sync_node.execute_async(state, config)

# 新代码（应该）
result = sync_node.execute(state, config)
```

**迁移指南**：
1. 同步节点只能同步调用
2. 异步节点可以两种方式调用
3. 在workflow execution modes中正确选择模式

## 测试覆盖

```python
# test_nodes.py

def test_sync_node_execute_works():
    """SyncNode同步执行应该工作"""
    
def test_sync_node_async_raises():
    """SyncNode异步执行应该抛异常"""
    
def test_async_node_execute_creates_loop():
    """AsyncNode同步执行应该创建新循环"""
    
def test_async_node_async_direct():
    """AsyncNode异步执行应该直接调用"""
```

## 总结

这个修改确立了清晰的节点架构：

1. **SyncNode** - 纯同步，本地快速操作
2. **AsyncNode** - 异步优先，I/O密集操作
3. **明确的失败** - 错误调用立即抛异常
4. **性能改善** - 避免不必要的事件循环创建
5. **架构一致** - 与workflow execution modes的设计一致
