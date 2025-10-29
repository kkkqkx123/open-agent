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

### 3. 简化协调策略设计

基于对当前项目实际需求的分析，建议采用简化版的协调策略，避免过度工程化。

#### 协调策略选择
```python
class CoordinationPolicy(Enum):
    """简化协调策略"""
    BEST_EFFORT = "best_effort"  # 尽力而为：优先保证系统可用性，允许部分失败
    STRICT = "strict"            # 严格模式：所有依赖必须满足（可选）
    # ADAPTIVE模式在当前场景下复杂度过高，建议暂不实现
```

#### 简化版线程协调器
```python
class SimplifiedThreadCoordinator:
    """简化版线程协调器 - 专注于核心需求"""
    
    def __init__(self, policy: str = "best_effort", max_parallel_threads: int = 5):
        self.policy = policy
        self.max_parallel_threads = max_parallel_threads
        self._execution_semaphore = asyncio.Semaphore(max_parallel_threads)
    
    async def coordinate_execution(self, session_id: str) -> Dict[str, Any]:
        """简化协调执行 - 基于实际需求优化"""
        
        # 1. 获取线程信息和依赖关系
        thread_info = await self._get_session_threads(session_id)
        dependencies = await self._get_thread_dependencies(session_id)
        
        # 2. 简化的拓扑排序（仅支持顺序依赖）
        execution_order = self._simple_topological_sort(dependencies)
        
        # 3. 按顺序执行，支持容错和并发控制
        results = {}
        failed_threads = []
        
        for thread_name in execution_order:
            async with self._execution_semaphore:
                try:
                    result = await self._execute_thread_safely(thread_name, thread_info)
                    results[thread_name] = result
                    logger.info(f"线程执行成功: {thread_name}")
                except Exception as e:
                    logger.warning(f"线程执行失败: {thread_name}, 错误: {e}")
                    failed_threads.append(thread_name)
                    
                    # 根据策略决定是否继续
                    if self.policy == "strict":
                        raise ThreadExecutionError(f"严格模式下线程失败: {thread_name}") from e
                    # best_effort模式继续执行其他线程
        
        # 4. 返回结果和失败信息
        return {
            "successful_threads": results,
            "failed_threads": failed_threads,
            "total_executed": len(execution_order),
            "success_rate": len(results) / len(execution_order) if execution_order else 1.0
        }
    
    def _simple_topological_sort(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """简化拓扑排序 - 仅处理顺序依赖"""
        # 实现基本的拓扑排序算法
        # 复杂度：O(V+E)，适用于大多数实际场景
        in_degree = {}
        graph = {}
        
        # 构建图结构
        for thread, deps in dependencies.items():
            in_degree[thread] = len(deps)
            for dep in deps:
                if dep not in graph:
                    graph[dep] = []
                graph[dep].append(thread)
        
        # 拓扑排序
        queue = deque([t for t, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            thread = queue.popleft()
            result.append(thread)
            
            if thread in graph:
                for neighbor in graph[thread]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        return result
    
    async def _execute_thread_safely(self, thread_name: str, thread_info: Dict[str, Any]) -> Any:
        """安全执行线程，包含超时和错误处理"""
        try:
            # 设置执行超时（默认5分钟）
            async with timeout(300):  # 5分钟超时
                return await self._execute_single_thread(thread_name, thread_info)
        except asyncio.TimeoutError:
            raise ThreadTimeoutError(f"线程执行超时: {thread_name}")
        except Exception as e:
            raise ThreadExecutionError(f"线程执行错误: {thread_name}") from e
```

#### 配置建议
```yaml
# configs/threads.yaml 新增配置
coordination:
  enabled: false  # 默认禁用，需要时开启
  policy: "best_effort"  # 协调策略
  max_parallel_threads: 5  # 最大并行线程数
  timeout: 300  # 线程执行超时时间（秒）
  enable_retry: true  # 是否启用重试机制
  max_retries: 3  # 最大重试次数
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

## 简化实施计划

基于实际需求分析，建议采用简化的分阶段实施策略：

### 阶段1：核心功能实现（1周）
- 实现简化的依赖关系建模（仅支持顺序依赖）
- 实现基本拓扑排序算法（简化版）
- 添加依赖验证和循环检测功能
- **交付物**：SimplifiedThreadCoordinator基础版本

### 阶段2：协调策略集成（0.5周）
- 实现BEST_EFFORT协调策略（优先保证系统可用性）
- 添加STRICT模式支持（可选）
- 实现基本的错误处理和容错机制
- **交付物**：支持两种协调策略的简化协调器

### 阶段3：测试和优化（0.5周）
- 编写单元测试和集成测试
- 性能基准测试和优化
- 文档完善和配置示例
- **交付物**：稳定可用的线程协调功能

## 预期效果（调整后）

1. **系统可用性提升** - 通过BEST_EFFORT策略保证核心功能可用
2. **容错能力增强** - 支持线程失败时的优雅降级
3. **实现复杂度可控** - 避免过度工程化，聚焦核心需求
4. **部署风险降低** - 简化设计减少集成复杂度

## 优先级说明

**建议实施优先级：中等**
- 当前业务需求不明确，可先实现基础功能
- 根据实际使用情况决定是否扩展高级功能
- 避免过早引入复杂协调机制

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