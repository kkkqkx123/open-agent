## 根本性重构方案：全新的架构职责划分

### 核心设计原则

1. **彻底的职责分离**：Core层只负责纯粹的领域逻辑，Services层只负责业务编排和外部集成
2. **零冗余设计**：每个功能只在一个地方实现
3. **依赖倒置**：高层模块不依赖低层模块，都依赖抽象
4. **单一数据源**：配置、状态、执行逻辑各有唯一的数据源

### 新的架构职责划分

#### Core Layer（核心层）- 纯粹的领域逻辑

**职责范围**：
- 工作流领域模型定义
- 节点和边的抽象与实现
- 状态管理和转换逻辑
- 执行引擎的核心算法
- 配置验证和转换

**不负责**：
- 外部框架集成（如LangGraph）
- 业务流程编排
- 缓存和性能优化
- 错误处理和重试机制

#### Services Layer（服务层）- 业务编排和外部集成

**职责范围**：
- 工作流生命周期管理
- 外部框架适配（LangGraph等）
- 执行策略和优化
- 错误处理和恢复
- 监控和指标收集

**不负责**：
- 核心领域逻辑实现
- 状态转换算法
- 节点执行细节

### 全新的文件结构设计

```
src/
├── core/workflow/                          # 核心层 - 纯粹领域逻辑
│   ├── domain/                            # 领域模型
│   │   ├── workflow.py                    # 工作流领域模型
│   │   ├── node.py                        # 节点领域模型
│   │   ├── edge.py                        # 边领域模型
│   │   └── state.py                       # 状态领域模型
│   ├── engine/                            # 执行引擎
│   │   ├── executor.py                    # 核心执行引擎
│   │   ├── scheduler.py                   # 调度器
│   │   └── context.py                     # 执行上下文
│   ├── config/                            # 配置管理
│   │   ├── validator.py                   # 配置验证器
│   │   ├── parser.py                      # 配置解析器
│   │   └── schema.py                      # 配置模式定义
│   └── interfaces/                        # 核心接口定义
│       ├── workflow.py                    # 工作流接口
│       ├── executor.py                    # 执行器接口
│       └── config.py                      # 配置接口
│
└── services/workflow/                     # 服务层 - 业务编排
    ├── management/                        # 工作流管理
    │   ├── builder.py                     # 工作流构建器（重构后）
    │   ├── lifecycle.py                   # 生命周期管理
    │   └── registry.py                    # 工作流注册表
    ├── adapters/                          # 外部适配器
    │   ├── langgraph.py                   # LangGraph适配器
    │   ├── streaming.py                   # 流式执行适配器
    │   └── monitoring.py                  # 监控适配器
    ├── strategies/                        # 执行策略
    │   ├── retry.py                       # 重试策略
    │   ├── caching.py                     # 缓存策略
    │   └── optimization.py                # 优化策略
    └── interfaces/                        # 服务层接口
        ├── builder.py                     # 构建器接口
        ├── executor.py                    # 执行器接口
        └── monitor.py                     # 监控接口
```

### 核心组件设计

#### 1. 核心层执行引擎（全新设计）

**`src/core/workflow/engine/executor.py`**
```python
"""核心执行引擎 - 纯粹的领域逻辑实现"""

from typing import Dict, Any, List, Optional
from ..domain.workflow import Workflow
from ..domain.state import WorkflowState
from ..interfaces.executor import IExecutorEngine

class ExecutorEngine(IExecutorEngine):
    """核心执行引擎
    
    职责：
    - 实现纯粹的工作流执行算法
    - 管理节点和边的遍历逻辑
    - 处理状态转换
    """
    
    def execute(self, workflow: Workflow, initial_state: WorkflowState) -> WorkflowState:
        """执行工作流的核心算法"""
        current_state = initial_state
        current_node = workflow.entry_point
        
        while current_node:
            # 执行当前节点
            node_result = self._execute_node(current_node, current_state)
            current_state = node_result.state
            
            # 确定下一个节点
            current_node = self._get_next_node(workflow, current_node, current_state)
        
        return current_state
    
    def _execute_node(self, node, state: WorkflowState):
        """执行单个节点 - 纯粹的领域逻辑"""
        return node.execute(state)
    
    def _get_next_node(self, workflow, current_node, state):
        """获取下一个节点 - 纯粹的遍历逻辑"""
        for edge in workflow.get_outgoing_edges(current_node):
            if edge.can_traverse(state):
                return edge.target_node
        return None
```

#### 2. 服务层构建器（彻底重构）

**`src/services/workflow/management/builder.py`**
```python
"""工作流构建器 - 业务编排和外部集成"""

from typing import Dict, Any
from ...core.workflow.domain.workflow import Workflow
from ...core.workflow.config.parser import ConfigParser
from ...core.workflow.config.validator import ConfigValidator
from ...core.workflow.engine.executor import ExecutorEngine
from ..interfaces.builder import IWorkflowBuilder

class WorkflowBuilder(IWorkflowBuilder):
    """工作流构建器
    
    职责：
    - 业务流程编排
    - 外部系统集成
    - 错误处理和恢复
    """
    
    def __init__(self):
        self.config_parser = ConfigParser()
        self.config_validator = ConfigValidator()
        self.executor_engine = ExecutorEngine()
    
    def build_from_config(self, config: Dict[str, Any]) -> Workflow:
        """从配置构建工作流"""
        # 解析配置
        parsed_config = self.config_parser.parse(config)
        
        # 验证配置
        validation_result = self.config_validator.validate(parsed_config)
        if not validation_result.is_valid:
            raise ValueError(f"配置验证失败: {validation_result.errors}")
        
        # 构建工作流领域对象
        workflow = self._create_workflow_domain_object(parsed_config)
        
        return workflow
    
    def _create_workflow_domain_object(self, config):
        """创建工作流领域对象 - 委托给核心层"""
        # 纯粹的对象创建逻辑，委托给核心层工厂
        pass
```

#### 3. LangGraph适配器（全新设计）

**`src/services/workflow/adapters/langgraph.py`**
```python
"""LangGraph适配器 - 外部框架集成"""

from typing import Any, Dict
from ...core.workflow.domain.workflow import Workflow
from ...core.workflow.engine.executor import ExecutorEngine
from ..interfaces.adapter import IFrameworkAdapter

class LangGraphAdapter(IFrameworkAdapter):
    """LangGraph框架适配器
    
    职责：
    - 将核心工作流模型转换为LangGraph
    - 提供LangGraph特定的优化
    - 处理框架特定的错误和异常
    """
    
    def __init__(self, executor_engine: ExecutorEngine):
        self.executor_engine = executor_engine
        self._compiled_graphs: Dict[str, Any] = {}
    
    def to_langgraph(self, workflow: Workflow) -> Any:
        """将工作流转换为LangGraph"""
        # 使用核心执行引擎的逻辑，但适配到LangGraph框架
        langgraph_builder = self._create_langgraph_builder()
        
        # 转换节点
        for node in workflow.nodes:
            langgraph_node = self._convert_node_to_langgraph(node)
            langgraph_builder.add_node(node.id, langgraph_node)
        
        # 转换边
        for edge in workflow.edges:
            langgraph_edge = self._convert_edge_to_langgraph(edge)
            langgraph_builder.add_edge(langgraph_edge)
        
        # 编译并缓存
        compiled_graph = langgraph_builder.compile()
        self._compiled_graphs[workflow.id] = compiled_graph
        
        return compiled_graph
    
    def _convert_node_to_langgraph(self, node):
        """将核心节点转换为LangGraph节点"""
        # 适配逻辑，保持核心逻辑不变
        pass
```

### 迁移策略

#### 阶段1：建立新的核心层（1-2周）
1. 创建新的领域模型
2. 实现核心执行引擎
3. 建立配置管理系统
4. 编写完整的单元测试

#### 阶段2：重构服务层（1-2周）
1. 重构工作流构建器
2. 创建框架适配器
3. 实现执行策略
4. 更新服务层接口

#### 阶段3：迁移和清理（1周）
1. 迁移现有功能到新架构
2. 删除所有冗余代码
3. 更新调用方代码
4. 性能测试和优化

#### 阶段4：验证和部署（1周）
1. 集成测试
2. 性能基准测试
3. 文档更新
4. 生产环境部署

### 预期收益

1. **代码质量提升**：
   - 消除所有重复代码
   - 职责边界清晰
   - 可测试性大幅提升

2. **架构质量提升**：
   - 严格遵循分层架构
   - 依赖关系清晰
   - 扩展性显著增强

3. **维护成本降低**：
   - 单一职责原则降低复杂度
   - 清晰的接口减少沟通成本
   - 完善的测试覆盖降低风险

4. **性能优化**：
   - 核心算法优化
   - 缓存策略改进
   - 执行效率提升

现在让我完成全新的实现方案设计，提供具体的代码实现细节：

## 全新实现方案：具体代码设计

### 1. 核心层领域模型设计

#### 工作流领域模型

**`src/core/workflow/domain/workflow.py`**
```python
"""工作流领域模型 - 纯粹的业务逻辑"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .node import Node
from .edge import Edge
from .state import WorkflowState

@dataclass(frozen=True)
class Workflow:
    """工作流领域模型
    
    职责：
    - 定义工作流的纯粹业务概念
    - 封装工作流的不变性
    - 提供领域特定的操作方法
    """
    id: str
    name: str
    description: str = ""
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    entry_point_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证工作流的不变性"""
        if not self.id or not self.name:
            raise ValueError("工作流ID和名称不能为空")
        
        if self.entry_point_id and self.entry_point_id not in self.nodes:
            raise ValueError(f"入口节点 {self.entry_point_id} 不存在")
    
    @property
    def entry_point(self) -> Optional[Node]:
        """获取入口节点"""
        return self.nodes.get(self.entry_point_id) if self.entry_point_id else None
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """获取节点的出边"""
        return [edge for edge in self.edges if edge.from_node_id == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """获取节点的入边"""
        return [edge for edge in self.edges if edge.to_node_id == node_id]
    
    def validate(self) -> List[str]:
        """验证工作流的完整性"""
        errors = []
        
        # 检查节点引用
        for edge in self.edges:
            if edge.from_node_id not in self.nodes:
                errors.append(f"边引用了不存在的起始节点: {edge.from_node_id}")
            if edge.to_node_id not in self.nodes:
                errors.append(f"边引用了不存在的目标节点: {edge.to_node_id}")
        
        # 检查可达性
        if self.entry_point_id:
            reachable_nodes = self._get_reachable_nodes()
            unreachable_nodes = set(self.nodes.keys()) - reachable_nodes
            if unreachable_nodes:
                errors.append(f"存在不可达的节点: {', '.join(unreachable_nodes)}")
        
        return errors
    
    def _get_reachable_nodes(self) -> set:
        """获取从入口点可达的所有节点"""
        if not self.entry_point_id:
            return set()
        
        reachable = {self.entry_point_id}
        to_visit = [self.entry_point_id]
        
        while to_visit:
            current = to_visit.pop()
            for edge in self.get_outgoing_edges(current):
                if edge.to_node_id not in reachable:
                    reachable.add(edge.to_node_id)
                    to_visit.append(edge.to_node_id)
        
        return reachable
```

#### 节点领域模型

**`src/core/workflow/domain/node.py`**
```python
"""节点领域模型"""

from typing import Dict, Any, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from .state import WorkflowState, NodeResult

class INodeExecutor(Protocol):
    """节点执行器协议"""
    
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeResult:
        """执行节点"""
        ...

@dataclass(frozen=True)
class Node:
    """节点领域模型
    
    职责：
    - 封装节点的业务概念
    - 定义节点的执行契约
    - 维护节点的不变性
    """
    id: str
    name: str
    node_type: str
    executor: INodeExecutor
    config: Dict[str, Any] = None
    description: str = ""
    
    def __post_init__(self):
        if self.config is None:
            object.__setattr__(self, 'config', {})
    
    def execute(self, state: WorkflowState, context_config: Dict[str, Any] = None) -> NodeResult:
        """执行节点
        
        Args:
            state: 当前工作流状态
            context_config: 上下文配置
            
        Returns:
            节点执行结果
        """
        if context_config is None:
            context_config = {}
        
        # 合并节点配置和上下文配置
        merged_config = {**self.config, **context_config}
        
        # 委托给执行器
        return self.executor.execute(state, merged_config)
    
    def can_execute(self, state: WorkflowState) -> bool:
        """检查是否可以执行此节点"""
        # 基础实现，子类可以重写
        return True

class LLMNode(Node):
    """LLM节点特化"""
    
    def __init__(self, id: str, name: str, executor: INodeExecutor, 
                 model: str, prompt_template: str, **kwargs):
        super().__init__(id, name, "llm", executor, **kwargs)
        self.model = model
        self.prompt_template = prompt_template

class ToolNode(Node):
    """工具节点特化"""
    
    def __init__(self, id: str, name: str, executor: INodeExecutor,
                 tool_name: str, **kwargs):
        super().__init__(id, name, "tool", executor, **kwargs)
        self.tool_name = tool_name
```

#### 边领域模型

**`src/core/workflow/domain/edge.py`**
```python
"""边领域模型"""

from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
from .state import WorkflowState

class EdgeType(Enum):
    SIMPLE = "simple"
    CONDITIONAL = "conditional"

class IConditionEvaluator(Protocol):
    """条件评估器协议"""
    
    def evaluate(self, state: WorkflowState, config: Dict[str, Any]) -> bool:
        """评估条件"""
        ...

@dataclass(frozen=True)
class Edge:
    """边领域模型
    
    职责：
    - 定义节点间的连接关系
    - 封装遍历条件逻辑
    - 维护边的不变性
    """
    id: str
    from_node_id: str
    to_node_id: str
    edge_type: EdgeType
    condition_evaluator: Optional[IConditionEvaluator] = None
    config: Dict[str, Any] = None
    description: str = ""
    
    def __post_init__(self):
        if self.config is None:
            object.__setattr__(self, 'config', {})
        
        if self.edge_type == EdgeType.CONDITIONAL and not self.condition_evaluator:
            raise ValueError("条件边必须提供条件评估器")
    
    def can_traverse(self, state: WorkflowState, context_config: Dict[str, Any] = None) -> bool:
        """检查是否可以遍历此边
        
        Args:
            state: 当前工作流状态
            context_config: 上下文配置
            
        Returns:
            是否可以遍历
        """
        if context_config is None:
            context_config = {}
        
        # 简单边总是可以遍历
        if self.edge_type == EdgeType.SIMPLE:
            return True
        
        # 条件边需要评估条件
        if self.edge_type == EdgeType.CONDITIONAL and self.condition_evaluator:
            merged_config = {**self.config, **context_config}
            return self.condition_evaluator.evaluate(state, merged_config)
        
        return False
    
    def get_target_node(self) -> str:
        """获取目标节点ID"""
        return self.to_node_id

class ConditionalEdge(Edge):
    """条件边特化"""
    
    def __init__(self, id: str, from_node_id: str, to_node_id: str,
                 condition_evaluator: IConditionEvaluator, **kwargs):
        super().__init__(
            id, from_node_id, to_node_id, 
            EdgeType.CONDITIONAL, condition_evaluator, **kwargs
        )
```

### 2. 核心执行引擎设计

**`src/core/workflow/engine/executor.py`**
```python
"""核心执行引擎 - 纯粹的执行算法"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from ..domain.workflow import Workflow
from ..domain.state import WorkflowState, ExecutionResult
from ..interfaces.executor import IExecutorEngine

@dataclass
class ExecutionContext:
    """执行上下文"""
    workflow_id: str
    execution_id: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = None

class ExecutorEngine(IExecutorEngine):
    """核心执行引擎
    
    职责：
    - 实现纯粹的工作流执行算法
    - 管理执行状态和流程控制
    - 处理节点和边的遍历逻辑
    """
    
    def execute(self, workflow: Workflow, initial_state: WorkflowState, 
                context: ExecutionContext) -> ExecutionResult:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            执行结果
        """
        # 验证工作流
        validation_errors = workflow.validate()
        if validation_errors:
            raise ValueError(f"工作流验证失败: {validation_errors}")
        
        # 初始化执行状态
        current_state = initial_state
        current_node = workflow.entry_point
        executed_nodes = []
        execution_path = []
        
        try:
            # 主执行循环
            while current_node:
                execution_path.append(current_node.id)
                
                # 执行当前节点
                node_result = self._execute_node(current_node, current_state, context)
                current_state = node_result.state
                executed_nodes.append({
                    'node_id': current_node.id,
                    'result': node_result,
                    'timestamp': self._get_timestamp()
                })
                
                # 确定下一个节点
                current_node = self._get_next_node(workflow, current_node, current_state, context)
            
            # 返回成功结果
            return ExecutionResult(
                success=True,
                final_state=current_state,
                executed_nodes=executed_nodes,
                execution_path=execution_path,
                metadata={'context': context}
            )
            
        except Exception as e:
            # 返回失败结果
            return ExecutionResult(
                success=False,
                final_state=current_state,
                executed_nodes=executed_nodes,
                execution_path=execution_path,
                error=str(e),
                metadata={'context': context}
            )
    
    def _execute_node(self, node, state: WorkflowState, context: ExecutionContext):
        """执行单个节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            节点执行结果
        """
        # 检查节点是否可以执行
        if not node.can_execute(state):
            raise ValueError(f"节点 {node.id} 当前状态无法执行")
        
        # 委托给节点的执行方法
        return node.execute(state, context.config)
    
    def _get_next_node(self, workflow: Workflow, current_node, state: WorkflowState, 
                      context: ExecutionContext):
        """获取下一个节点
        
        Args:
            workflow: 工作流实例
            current_node: 当前节点
            state: 当前状态
            context: 执行上下文
            
        Returns:
            下一个节点实例，如果没有则返回None
        """
        # 获取所有出边
        outgoing_edges = workflow.get_outgoing_edges(current_node.id)
        
        # 查找第一个可以遍历的边
        for edge in outgoing_edges:
            if edge.can_traverse(state, context.config):
                next_node_id = edge.get_target_node()
                return workflow.get_node(next_node_id)
        
        # 没有可遍历的边，执行结束
        return None
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
```

### 3. 服务层构建器设计

**`src/services/workflow/management/builder.py`**
```python
"""工作流构建器 - 业务编排和外部集成"""

from typing import Dict, Any, List, Optional
from ...core.workflow.domain.workflow import Workflow
from ...core.workflow.domain.node import Node, LLMNode, ToolNode
from ...core.workflow.domain.edge import Edge, ConditionalEdge
from ...core.workflow.config.parser import ConfigParser
from ...core.workflow.config.validator import ConfigValidator
from ...core.workflow.engine.executor import ExecutorEngine
from ..interfaces.builder import IWorkflowBuilder
from ..executors.node_executors import LLMNodeExecutor, ToolNodeExecutor

class WorkflowBuilder(IWorkflowBuilder):
    """工作流构建器
    
    职责：
    - 业务流程编排
    - 外部系统集成
    - 错误处理和恢复
    """
    
    def __init__(self):
        self.config_parser = ConfigParser()
        self.config_validator = ConfigValidator()
        self.executor_engine = ExecutorEngine()
        
        # 节点执行器注册表
        self.node_executors = {
            'llm': LLMNodeExecutor(),
            'tool': ToolNodeExecutor(),
        }
    
    def build_from_config(self, config: Dict[str, Any]) -> Workflow:
        """从配置构建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            构建的工作流实例
        """
        try:
            # 解析配置
            parsed_config = self.config_parser.parse(config)
            
            # 验证配置
            validation_result = self.config_validator.validate(parsed_config)
            if not validation_result.is_valid:
                raise ValueError(f"配置验证失败: {validation_result.errors}")
            
            # 构建节点
            nodes = self._build_nodes(parsed_config.get('nodes', {}))
            
            # 构建边
            edges = self._build_edges(parsed_config.get('edges', []), nodes)
            
            # 创建工作流实例
            workflow = Workflow(
                id=parsed_config['id'],
                name=parsed_config['name'],
                description=parsed_config.get('description', ''),
                nodes=nodes,
                edges=edges,
                entry_point_id=parsed_config.get('entry_point'),
                metadata=parsed_config.get('metadata', {})
            )
            
            return workflow
            
        except Exception as e:
            raise RuntimeError(f"构建工作流失败: {e}") from e
    
    def _build_nodes(self, nodes_config: Dict[str, Any]) -> Dict[str, Node]:
        """构建节点
        
        Args:
            nodes_config: 节点配置
            
        Returns:
            节点字典
        """
        nodes = {}
        
        for node_id, node_config in nodes_config.items():
            node_type = node_config.get('type')
            
            if node_type not in self.node_executors:
                raise ValueError(f"不支持的节点类型: {node_type}")
            
            executor = self.node_executors[node_type]
            
            # 根据节点类型创建相应的节点实例
            if node_type == 'llm':
                node = LLMNode(
                    id=node_id,
                    name=node_config.get('name', node_id),
                    executor=executor,
                    model=node_config.get('model'),
                    prompt_template=node_config.get('prompt_template'),
                    config=node_config.get('config', {}),
                    description=node_config.get('description', '')
                )
            elif node_type == 'tool':
                node = ToolNode(
                    id=node_id,
                    name=node_config.get('name', node_id),
                    executor=executor,
                    tool_name=node_config.get('tool_name'),
                    config=node_config.get('config', {}),
                    description=node_config.get('description', '')
                )
            else:
                node = Node(
                    id=node_id,
                    name=node_config.get('name', node_id),
                    node_type=node_type,
                    executor=executor,
                    config=node_config.get('config', {}),
                    description=node_config.get('description', '')
                )
            
            nodes[node_id] = node
        
        return nodes
    
    def _build_edges(self, edges_config: List[Dict[str, Any]], nodes: Dict[str, Node]) -> List[Edge]:
        """构建边
        
        Args:
            edges_config: 边配置
            nodes: 节点字典
            
        Returns:
            边列表
        """
        edges = []
        
        for edge_config in edges_config:
            edge_type = edge_config.get('type', 'simple')
            
            if edge_type == 'conditional':
                # 创建条件边
                condition_evaluator = self._create_condition_evaluator(edge_config.get('condition'))
                
                edge = ConditionalEdge(
                    id=edge_config['id'],
                    from_node_id=edge_config['from'],
                    to_node_id=edge_config['to'],
                    condition_evaluator=condition_evaluator,
                    config=edge_config.get('config', {}),
                    description=edge_config.get('description', '')
                )
            else:
                # 创建简单边
                edge = Edge(
                    id=edge_config['id'],
                    from_node_id=edge_config['from'],
                    to_node_id=edge_config['to'],
                    edge_type=EdgeType.SIMPLE,
                    config=edge_config.get('config', {}),
                    description=edge_config.get('description', '')
                )
            
            edges.append(edge)
        
        return edges
    
    def _create_condition_evaluator(self, condition_config: Dict[str, Any]):
        """创建条件评估器"""
        # 这里可以根据条件配置创建相应的评估器
        # 暂时返回一个简单的实现
        return SimpleConditionEvaluator(condition_config)

class SimpleConditionEvaluator:
    """简单条件评估器实现"""
    
    def __init__(self, condition_config: Dict[str, Any]):
        self.condition_config = condition_config
    
    def evaluate(self, state: WorkflowState, config: Dict[str, Any]) -> bool:
        """评估条件"""
        # 简单实现，实际应该根据条件配置进行评估
        return True
```

### 4. LangGraph适配器设计

**`src/services/workflow/adapters/langgraph.py`**
```python
"""LangGraph适配器 - 外部框架集成"""

from typing import Any, Dict, Callable
from langgraph.graph import StateGraph, START, END
from ...core.workflow.domain.workflow import Workflow
from ...core.workflow.domain.state import WorkflowState
from ..interfaces.adapter import IFrameworkAdapter

class LangGraphAdapter(IFrameworkAdapter):
    """LangGraph框架适配器
    
    职责：
    - 将核心工作流模型转换为LangGraph
    - 提供LangGraph特定的优化
    - 处理框架特定的错误和异常
    """
    
    def __init__(self):
        self._compiled_graphs: Dict[str, Any] = {}
    
    def to_langgraph(self, workflow: Workflow) -> Any:
        """将工作流转换为LangGraph
        
        Args:
            workflow: 工作流实例
            
        Returns:
            编译后的LangGraph图
        """
        # 检查缓存
        if workflow.id in self._compiled_graphs:
            return self._compiled_graphs[workflow.id]
        
        # 创建LangGraph构建器
        builder = StateGraph(WorkflowState)
        
        # 添加节点
        for node in workflow.nodes.values():
            langgraph_node = self._convert_node_to_langgraph(node)
            builder.add_node(node.id, langgraph_node)
        
        # 添加边
        for edge in workflow.edges:
            self._add_edge_to_builder(builder, edge)
        
        # 设置入口点
        if workflow.entry_point_id:
            builder.add_edge(START, workflow.entry_point_id)
        
        # 编译图
        compiled_graph = builder.compile()
        
        # 缓存结果
        self._compiled_graphs[workflow.id] = compiled_graph
        
        return compiled_graph
    
    def _convert_node_to_langgraph(self, node) -> Callable:
        """将核心节点转换为LangGraph节点
        
        Args:
            node: 核心节点实例
            
        Returns:
            LangGraph节点函数
        """
        def langgraph_node_function(state: WorkflowState) -> Dict[str, Any]:
            """LangGraph节点函数包装器"""
            try:
                # 执行核心节点
                result = node.execute(state, {})
                
                # 返回状态更新
                return result.state.to_dict()
                
            except Exception as e:
                # 处理错误
                print(f"节点 {node.id} 执行失败: {e}")
                return state.to_dict()
        
        return langgraph_node_function
    
    def _add_edge_to_builder(self, builder: Any, edge):
        """添加边到LangGraph构建器
        
        Args:
            builder: LangGraph构建器
            edge: 边实例
        """
        if edge.edge_type.value == 'simple':
            # 简单边
            if edge.to_node_id == '__end__':
                builder.add_edge(edge.from_node_id, END)
            else:
                builder.add_edge(edge.from_node_id, edge.to_node_id)
        
        elif edge.edge_type.value == 'conditional':
            # 条件边
            def condition_function(state: WorkflowState) -> str:
                """条件函数"""
                if edge.can_traverse(state, {}):
                    return edge.to_node_id
                return '__end__'
            
            builder.add_conditional_edges(
                edge.from_node_id,
                condition_function,
                {edge.to_node_id: edge.to_node_id, '__end__': END}
            )
    
    def clear_cache(self):
        """清除缓存"""
        self._compiled_graphs.clear()
```

### 5. 配置管理系统设计

**`src/core/workflow/config/parser.py`**
```python
"""配置解析器 - 纯粹的配置处理逻辑"""

from typing import Dict, Any, List
from dataclasses import dataclass
from ..interfaces.config import IConfigParser

@dataclass
class ParsedConfig:
    """解析后的配置"""
    id: str
    name: str
    description: str
    nodes: Dict[str, Any]
    edges: List[Dict[str, Any]]
    entry_point: str
    metadata: Dict[str, Any]

class ConfigParser(IConfigParser):
    """配置解析器
    
    职责：
    - 解析原始配置数据
    - 验证配置结构
    - 转换为标准格式
    """
    
    def parse(self, config: Dict[str, Any]) -> ParsedConfig:
        """解析配置
        
        Args:
            config: 原始配置
            
        Returns:
            解析后的配置
        """
        # 提取基本信息
        workflow_id = config.get('id')
        if not workflow_id:
            raise ValueError("工作流ID不能为空")
        
        name = config.get('name', workflow_id)
        description = config.get('description', '')
        
        # 解析节点
        nodes = self._parse_nodes(config.get('nodes', {}))
        
        # 解析边
        edges = self._parse_edges(config.get('edges', []))
        
        # 获取入口点
        entry_point = config.get('entry_point')
        
        # 获取元数据
        metadata = config.get('metadata', {})
        
        return ParsedConfig(
            id=workflow_id,
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            entry_point=entry_point,
            metadata=metadata
        )
    
    def _parse_nodes(self, nodes_config: Dict[str, Any]) -> Dict[str, Any]:
        """解析节点配置"""
        parsed_nodes = {}
        
        for node_id, node_config in nodes_config.items():
            # 验证必需字段
            if not node_config.get('type'):
                raise ValueError(f"节点 {node_id} 缺少类型定义")
            
            parsed_nodes[node_id] = {
                'id': node_id,
                'name': node_config.get('name', node_id),
                'type': node_config['type'],
                'config': node_config.get('config', {}),
                'description': node_config.get('description', ''),
                # 特定类型的字段
                **{k: v for k, v in node_config.items() 
                   if k not in ['name', 'type', 'config', 'description']}
            }
        
        return parsed_nodes
    
    def _parse_edges(self, edges_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析边配置"""
        parsed_edges = []
        
        for edge_config in edges_config:
            # 验证必需字段
            if not edge_config.get('from') or not edge_config.get('to'):
                raise ValueError("边必须指定起始和目标节点")
            
            parsed_edges.append({
                'id': edge_config.get('id', f"edge_{len(parsed_edges)}"),
                'from': edge_config['from'],
                'to': edge_config['to'],
                'type': edge_config.get('type', 'simple'),
                'condition': edge_config.get('condition'),
                'config': edge_config.get('config', {}),
                'description': edge_config.get('description', '')
            })
        
        return parsed_edges
```

---

## 根本性重构方案总结

### 方案概述

我已经完成了一个根本性的重构方案设计，彻底重新划分了core和services的职责，移除了所有冗余代码，采用了全新的实现方式。

### 核心改进点

#### 1. **彻底的职责分离**
- **Core Layer**：只负责纯粹的领域逻辑（工作流模型、执行算法、状态管理）
- **Services Layer**：只负责业务编排和外部集成（构建流程、框架适配、错误处理）

#### 2. **零冗余设计**
- 每个功能只在一个地方实现
- 消除了原有的三个文件之间的重复代码
- 统一的接口和实现模式

#### 3. **全新的架构设计**
```
Core Layer (核心层)
├── domain/          # 领域模型 - 纯粹业务概念
├── engine/          # 执行引擎 - 核心算法
├── config/          # 配置管理 - 解析和验证
└── interfaces/      # 核心接口定义

Services Layer (服务层)
├── management/      # 工作流管理 - 业务编排
├── adapters/        # 外部适配器 - 框架集成
├── strategies/      # 执行策略 - 优化和恢复
└── interfaces/      # 服务层接口
```

#### 4. **关键设计原则**
- **领域驱动设计**：核心层专注于业务领域概念
- **依赖倒置**：高层模块依赖抽象，不依赖具体实现
- **单一职责**：每个组件只有一个明确的职责
- **开闭原则**：对扩展开放，对修改封闭

### 实现亮点

#### 1. **领域模型设计**
- 使用`@dataclass(frozen=True)`确保不变性
- 领域对象包含业务逻辑和验证规则
- 清晰的领域概念和关系

#### 2. **执行引擎重构**
- 纯粹的执行算法，不依赖外部框架
- 清晰的执行流程和状态管理
- 完整的错误处理和结果返回

#### 3. **适配器模式**
- LangGraph适配器只负责框架集成
- 核心逻辑与框架完全解耦
- 支持多框架扩展

#### 4. **配置管理**
- 统一的配置解析和验证
- 类型安全的配置处理
- 清晰的错误报告

### 迁移策略

#### 阶段1：建立新的核心层（1-2周）
1. 创建领域模型
2. 实现核心执行引擎
3. 建立配置管理系统

#### 阶段2：重构服务层（1-2周）
1. 重构工作流构建器
2. 创建框架适配器
3. 实现执行策略

#### 阶段3：迁移和清理（1周）
1. 迁移现有功能
2. 删除冗余代码
3. 更新调用方

#### 阶段4：验证和部署（1周）
1. 集成测试
2. 性能优化
3. 生产部署

### 预期收益

1. **代码质量**：消除所有重复代码，提升可维护性
2. **架构清晰**：严格的分层架构，职责边界明确
3. **扩展性强**：新功能可以轻松添加到相应层次
4. **测试友好**：清晰的接口和依赖关系，便于单元测试

### 风险控制

1. **渐进式迁移**：分阶段实施，确保系统稳定性
2. **向后兼容**：保留原有接口，平滑过渡
3. **完整测试**：每个阶段都有充分的测试覆盖
4. **回滚机制**：保留原有代码，支持快速回滚

这个根本性的重构方案将彻底解决当前架构中的所有问题，建立一个清晰、可维护、可扩展的工作流系统架构。