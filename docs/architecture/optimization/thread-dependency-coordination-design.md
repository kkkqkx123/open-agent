# SessionManager线程依赖协调增强方案

## 问题分析

当前SessionManager虽然支持多线程会话管理，但线程间的依赖协调功能相对简单。在多工作流协作场景中，需要更强大的依赖管理和协调机制。

## 设计目标

1. **依赖关系建模** - 支持复杂的线程依赖关系
2. **执行顺序控制** - 自动管理线程执行顺序
3. **数据流协调** - 协调线程间的数据传递
4. **错误处理** - 提供依赖链路的错误处理机制

## 详细设计方案

### 1. 增强的依赖关系模型

```python
class DependencyType(Enum):
    """依赖类型枚举"""
    SEQUENTIAL = "sequential"        # 顺序依赖：B必须在A完成后执行
    PARALLEL = "parallel"           # 并行依赖：A和B可以并行执行
    DATA_FLOW = "data_flow"         # 数据流依赖：B需要A的输出数据
    CONDITIONAL = "conditional"     # 条件依赖：根据条件决定是否执行

class ThreadDependency:
    """线程依赖关系定义"""
    
    def __init__(self, 
                 source_thread: str,
                 target_thread: str,
                 dependency_type: DependencyType,
                 condition: Optional[Callable] = None,
                 data_mapping: Optional[Dict[str, str]] = None):
        self.source_thread = source_thread
        self.target_thread = target_thread
        self.dependency_type = dependency_type
        self.condition = condition
        self.data_mapping = data_mapping  # 源字段 -> 目标字段映射
        self.enabled: bool = True

class DependencyGraph:
    """依赖关系图"""
    
    def __init__(self):
        self.dependencies: List[ThreadDependency] = []
        self._graph: Dict[str, List[str]] = {}  # 邻接表表示
    
    def add_dependency(self, dependency: ThreadDependency) -> None:
        """添加依赖关系"""
        self.dependencies.append(dependency)
        self._rebuild_graph()
    
    def get_execution_order(self) -> List[List[str]]:
        """获取执行顺序（拓扑排序）"""
        # 实现拓扑排序算法
        in_degree = self._calculate_in_degree()
        queue = deque([thread for thread, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            level = []
            for _ in range(len(queue)):
                thread = queue.popleft()
                level.append(thread)
                for neighbor in self._graph.get(thread, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            result.append(level)
        
        return result
    
    def validate_dependencies(self) -> List[str]:
        """验证依赖关系有效性"""
        errors = []
        # 检查循环依赖
        if self._has_cycle():
            errors.append("检测到循环依赖")
        # 检查线程存在性
        # ... 其他验证逻辑
        return errors
```

### 2. 增强的SessionManager接口

```python
class IEnhancedSessionManager(ISessionManager):
    """增强的会话管理器接口"""
    
    @abstractmethod
    async def create_session_with_advanced_dependencies(
        self,
        workflow_configs: Dict[str, str],
        dependencies: List[ThreadDependency],
        coordination_policy: CoordinationPolicy = CoordinationPolicy.STRICT
    ) -> str:
        """创建带高级依赖关系的会话"""
        pass
    
    @abstractmethod
    async def coordinate_thread_execution(self, session_id: str) -> Dict[str, Any]:
        """协调线程执行"""
        pass
    
    @abstractmethod
    async def get_dependency_status(self, session_id: str) -> Dict[str, Any]:
        """获取依赖状态"""
        pass
    
    @abstractmethod
    async def handle_dependency_failure(self, session_id: str, failed_thread: str) -> bool:
        """处理依赖失败"""
        pass
```

### 3. 协调策略设计

```python
class CoordinationPolicy(Enum):
    """协调策略"""
    STRICT = "strict"           # 严格模式：所有依赖必须满足
    BEST_EFFORT = "best_effort" # 尽力而为：尝试继续执行
    ADAPTIVE = "adaptive"       # 自适应：根据情况调整策略

class ThreadCoordinator:
    """线程协调器"""
    
    def __init__(self, policy: CoordinationPolicy = CoordinationPolicy.STRICT):
        self.policy = policy
        self.dependency_graph = DependencyGraph()
        self.thread_states: Dict[str, ThreadState] = {}
        self.data_bus: Dict[str, Any] = {}  # 线程间数据总线
    
    async def coordinate_execution(self, session_id: str) -> Dict[str, Any]:
        """协调线程执行"""
        execution_plan = self.dependency_graph.get_execution_order()
        results = {}
        
        for level in execution_plan:
            # 并行执行同一级别的线程
            tasks = []
            for thread_name in level:
                if self._can_execute(thread_name):
                    task = asyncio.create_task(self._execute_thread(thread_name))
                    tasks.append((thread_name, task))
            
            # 等待当前级别完成
            for thread_name, task in tasks:
                try:
                    result = await task
                    results[thread_name] = result
                    self._update_thread_state(thread_name, ThreadState.COMPLETED)
                    self._propagate_data(thread_name, result)
                except Exception as e:
                    self._handle_execution_failure(thread_name, e)
                    if self.policy == CoordinationPolicy.STRICT:
                        raise
        
        return results
    
    def _can_execute(self, thread_name: str) -> bool:
        """检查线程是否可以执行"""
        dependencies = self.dependency_graph.get_dependencies_for_thread(thread_name)
        for dep in dependencies:
            if dep.dependency_type == DependencyType.SEQUENTIAL:
                source_state = self.thread_states.get(dep.source_thread)
                if source_state != ThreadState.COMPLETED:
                    return False
            elif dep.dependency_type == DependencyType.CONDITIONAL:
                if dep.condition and not dep.condition(self.data_bus):
                    return False
        return True
```

### 4. 数据流协调机制

```python
class DataFlowCoordinator:
    """数据流协调器"""
    
    def __init__(self):
        self.data_registry: Dict[str, DataSchema] = {}
        self.transformations: Dict[str, Callable] = {}
    
    def register_data_schema(self, thread_name: str, schema: DataSchema) -> None:
        """注册数据模式"""
        self.data_registry[thread_name] = schema
    
    def add_data_transformation(self, source_thread: str, target_thread: str, transform_fn: Callable) -> None:
        """添加数据转换函数"""
        key = f"{source_thread}->{target_thread}"
        self.transformations[key] = transform_fn
    
    def transform_data(self, source_thread: str, target_thread: str, data: Any) -> Any:
        """转换数据"""
        key = f"{source_thread}->{target_thread}"
        if key in self.transformations:
            return self.transformations[key](data)
        return data  # 默认不转换
```

### 5. 错误处理和恢复机制

```python
class DependencyErrorHandler:
    """依赖错误处理器"""
    
    def __init__(self, policy: CoordinationPolicy):
        self.policy = policy
        self.error_history: Dict[str, List[Exception]] = {}
    
    async def handle_error(self, session_id: str, thread_name: str, error: Exception) -> bool:
        """处理线程执行错误"""
        self._record_error(thread_name, error)
        
        if self.policy == CoordinationPolicy.STRICT:
            # 严格模式：立即失败
            return False
        elif self.policy == CoordinationPolicy.BEST_EFFORT:
            # 尽力而为：跳过失败线程，继续执行其他线程
            return await self._handle_best_effort(session_id, thread_name, error)
        elif self.policy == CoordinationPolicy.ADAPTIVE:
            # 自适应：根据错误类型和影响决定
            return await self._handle_adaptive(session_id, thread_name, error)
        
        return False
    
    async def _handle_best_effort(self, session_id: str, thread_name: str, error: Exception) -> bool:
        """尽力而为错误处理"""
        # 标记线程为失败状态
        # 通知依赖此线程的其他线程
        # 尝试继续执行不依赖此线程的其他线程
        return True
    
    async def _handle_adaptive(self, session_id: str, thread_name: str, error: Exception) -> bool:
        """自适应错误处理"""
        # 分析错误严重性
        severity = self._assess_error_severity(error)
        
        if severity == ErrorSeverity.LOW:
            # 低严重性错误，尝试重试或跳过
            return await self._handle_low_severity_error(session_id, thread_name, error)
        else:
            # 高严重性错误，可能需要停止整个会话
            return False
```

## 实施计划

### 阶段1：基础依赖模型（1周）
- 实现DependencyGraph和依赖关系建模
- 实现基本的拓扑排序算法
- 添加依赖验证功能

### 阶段2：协调执行机制（1周）
- 实现ThreadCoordinator协调器
- 实现多种协调策略
- 添加数据流协调功能

### 阶段3：错误处理和测试（1周）
- 实现完整的错误处理机制
- 编写单元测试和集成测试
- 性能优化和文档完善

## 预期效果

1. **执行效率提升** - 智能的线程调度和并行执行
2. **系统可靠性增强** - 完善的错误处理和恢复机制
3. **开发复杂度降低** - 简化的依赖关系管理接口
4. **可扩展性改善** - 支持复杂的多工作流协作场景

## 配置示例

```yaml
# 依赖关系配置示例
dependencies:
  - source_thread: "data_processing"
    target_thread: "analysis"
    type: "sequential"
    data_mapping:
      "processed_data": "input_data"
  
  - source_thread: "analysis"
    target_thread: "report_generation"
    type: "data_flow"
    condition: "lambda data: data.get('analysis_complete', False)"

coordination_policy: "adaptive"
error_handling:
  max_retries: 3
  retry_delay: 1000
```

这个设计方案将为SessionManager提供强大的线程依赖协调能力，显著提升多线程工作流的管理效率。