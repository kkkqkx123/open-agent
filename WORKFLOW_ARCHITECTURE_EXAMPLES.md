# 新架构使用示例

本文档展示了重构后的工作流架构的使用方法，包括如何使用新的 WorkflowManager、验证器和执行器。

## 1. 基本使用示例

### 1.1 创建和执行工作流

```python
from src.core.workflow import (
    create_workflow_manager, 
    create_workflow,
    GraphConfig,
    NodeConfig,
    EdgeConfig
)
from src.core.state.implementations.workflow_state import WorkflowState

# 创建工作流配置
config = GraphConfig(
    name="example_workflow",
    description="示例工作流",
    version="1.0.0",
    entry_point="start_node"
)

# 添加节点配置
config.nodes = {
    "start_node": NodeConfig(
        function="start_function",
        description="开始节点",
        type="start"
    ),
    "process_node": NodeConfig(
        function="process_function", 
        description="处理节点",
        type="process"
    ),
    "end_node": NodeConfig(
        function="end_function",
        description="结束节点", 
        type="end"
    )
}

# 添加边配置
config.edges = [
    EdgeConfig(
        from_node="start_node",
        to_node="process_node",
        type="simple"
    ),
    EdgeConfig(
        from_node="process_node", 
        to_node="end_node",
        type="simple"
    )
]

# 使用新的工作流管理器
workflow_manager = create_workflow_manager()

# 创建工作流（包含验证）
workflow = workflow_manager.create_workflow(config)

# 创建初始状态
initial_state = WorkflowState(
    workflow_id=workflow.workflow_id,
    execution_id="exec_001",
    status="running",
    data={"input": "example_data"}
)

# 执行工作流
result_state = workflow_manager.execute_workflow(workflow, initial_state)

print(f"执行结果: {result_state.data}")
```

### 1.2 异步执行工作流

```python
import asyncio
from src.core.workflow import create_workflow_manager

async def async_workflow_example():
    workflow_manager = create_workflow_manager()
    
    # 创建工作流（同上）
    workflow = workflow_manager.create_workflow(config)
    
    # 异步执行
    result_state = await workflow_manager.execute_workflow_async(
        workflow, initial_state
    )
    
    print(f"异步执行结果: {result_state.data}")

# 运行异步示例
asyncio.run(async_workflow_example())
```

## 2. 验证功能示例

### 2.1 工作流验证

```python
from src.core.workflow import create_workflow_validator, get_workflow_validator

# 获取验证器实例
validator = get_workflow_validator()

# 验证工作流配置
validation_result = validator.validate_config(config)

if validation_result.is_valid:
    print("工作流配置验证通过")
else:
    print("工作流配置验证失败:")
    for error in validation_result.errors:
        print(f"  错误: {error}")
    
for warning in validation_result.warnings:
    print(f"  警告: {warning}")

# 验证完整的工作流
workflow = create_workflow(config)
workflow_validation = validator.validate(workflow)

if not workflow_validation.is_valid:
    print("工作流验证失败，需要修复后才能执行")
```

### 2.2 自定义验证规则

```python
from src.core.workflow.validation import WorkflowValidator
from src.interfaces.workflow.core import ValidationResult

class CustomWorkflowValidator(WorkflowValidator):
    """自定义工作流验证器"""
    
    def _validate_custom_rules(self, workflow, result):
        """添加自定义验证规则"""
        # 示例：检查工作流是否包含特定类型的节点
        nodes = workflow.get_nodes()
        has_llm_node = any(
            getattr(node, 'type', None) == 'llm_node' 
            for node in nodes.values()
        )
        
        if not has_llm_node:
            result.warnings.append("工作流不包含LLM节点，可能无法处理自然语言")
        
        # 示例：检查边的数量限制
        edges = workflow.get_edges()
        if len(edges) > 10:
            result.warnings.append("工作流边数量过多，可能影响性能")

# 使用自定义验证器
custom_validator = CustomWorkflowValidator()
validation_result = custom_validator.validate(workflow)
```

## 3. 流式执行示例

### 3.1 同步流式执行

```python
async def stream_execution_example():
    workflow_manager = create_workflow_manager()
    workflow = workflow_manager.create_workflow(config)
    
    # 流式执行
    async for event in workflow_manager.executor.execute_stream(
        workflow, initial_state
    ):
        event_type = event["type"]
        print(f"事件类型: {event_type}")
        
        if event_type == "execution_start":
            print(f"工作流开始执行: {event['workflow_id']}")
        elif event_type == "execution_complete":
            print(f"工作流执行完成，结果: {event['result']}")
        elif event_type == "execution_error":
            print(f"工作流执行失败: {event['error']}")

# 运行流式示例
asyncio.run(stream_execution_example())
```

## 4. 工作流状态管理示例

### 4.1 获取工作流状态

```python
from src.core.workflow import create_workflow_manager

workflow_manager = create_workflow_manager()
workflow = workflow_manager.create_workflow(config)

# 获取工作流状态信息
status_info = workflow_manager.get_workflow_status(workflow)

print(f"工作流ID: {status_info['workflow_id']}")
print(f"工作流名称: {status_info['name']}")
print(f"状态: {status_info['status']}")
print(f"节点数量: {status_info['node_count']}")
print(f"边数量: {status_info['edge_count']}")
print(f"是否已编译: {status_info['has_compiled_graph']}")
```

### 4.2 执行状态监控

```python
from src.core.workflow.execution.executor import WorkflowExecutor

executor = WorkflowExecutor()

# 执行工作流
result_state = executor.execute(workflow, initial_state)

# 获取执行统计信息
stats = executor.get_executor_statistics()
print(f"活跃执行数量: {stats['active_executions']}")

# 列出所有活跃执行
active_executions = executor.list_active_executions()
for exec_info in active_executions:
    print(f"执行ID: {exec_info['execution_id']}, 状态: {exec_info['status']}")
```

## 5. 高级使用示例

### 5.1 自定义工作流管理器

```python
from src.core.workflow.validation import WorkflowManager, WorkflowValidator
from src.core.workflow.execution.executor import WorkflowExecutor
from src.core.workflow.core.builder import WorkflowBuilder

class CustomWorkflowManager(WorkflowManager):
    """自定义工作流管理器"""
    
    def __init__(self):
        # 使用自定义组件初始化
        super().__init__(
            executor=WorkflowExecutor(),
            builder=WorkflowBuilder(),
            validator=CustomWorkflowValidator()  # 使用自定义验证器
        )
    
    def execute_workflow_with_logging(self, workflow, initial_state, context=None):
        """带日志记录的工作流执行"""
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"开始执行工作流: {workflow.workflow_id}")
        
        try:
            result = self.execute_workflow(workflow, initial_state, context)
            logger.info(f"工作流执行成功: {workflow.workflow_id}")
            return result
        except Exception as e:
            logger.error(f"工作流执行失败: {workflow.workflow_id}, 错误: {e}")
            raise

# 使用自定义管理器
custom_manager = CustomWorkflowManager()
result = custom_manager.execute_workflow_with_logging(workflow, initial_state)
```

### 5.2 工作流组合

```python
def create_sub_workflow(name: str, node_function: str):
    """创建子工作流"""
    config = GraphConfig(
        name=name,
        description=f"子工作流: {name}",
        entry_point="input_node"
    )
    
    config.nodes = {
        "input_node": NodeConfig(
            function=node_function,
            description="输入节点",
            type="process"
        ),
        "output_node": NodeConfig(
            function="output_function",
            description="输出节点", 
            type="end"
        )
    }
    
    config.edges = [
        EdgeConfig(
            from_node="input_node",
            to_node="output_node",
            type="simple"
        )
    ]
    
    return config

# 创建主工作流
main_config = GraphConfig(
    name="main_workflow",
    description="主工作流",
    entry_point="start_node"
)

# 添加子工作流节点
sub_config1 = create_sub_workflow("sub_workflow_1", "process_function_1")
sub_config2 = create_sub_workflow("sub_workflow_2", "process_function_2")

main_config.nodes = {
    "start_node": NodeConfig(
        function="start_function",
        description="开始节点",
        type="start"
    ),
    "sub_node_1": NodeConfig(
        function="sub_workflow_executor",
        description="子工作流1",
        type="process",
        config={"sub_workflow_config": sub_config1}
    ),
    "sub_node_2": NodeConfig(
        function="sub_workflow_executor", 
        description="子工作流2",
        type="process",
        config={"sub_workflow_config": sub_config2}
    ),
    "end_node": NodeConfig(
        function="end_function",
        description="结束节点",
        type="end"
    )
}

# 执行组合工作流
workflow_manager = create_workflow_manager()
main_workflow = workflow_manager.create_workflow(main_config)
result = workflow_manager.execute_workflow(main_workflow, initial_state)
```

## 6. 错误处理示例

### 6.1 验证错误处理

```python
from src.core.workflow import create_workflow_manager

workflow_manager = create_workflow_manager()

try:
    # 创建无效配置（缺少入口点）
    invalid_config = GraphConfig(
        name="invalid_workflow",
        description="无效工作流"
        # 缺少 entry_point
    )
    
    workflow = workflow_manager.create_workflow(invalid_config)
    
except ValueError as e:
    print(f"工作流创建失败: {e}")
    
    # 获取详细的验证错误
    validator = workflow_manager.validator
    validation_result = validator.validate_config(invalid_config)
    
    print("详细错误信息:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

### 6.2 执行错误处理

```python
try:
    result = workflow_manager.execute_workflow(workflow, initial_state)
    
except Exception as e:
    print(f"工作流执行失败: {e}")
    
    # 获取执行状态
    status = workflow_manager.get_workflow_status(workflow)
    print(f"工作流状态: {status['status']}")
    
    # 检查执行器状态
    executor_stats = workflow_manager.executor.get_executor_statistics()
    print(f"执行器统计: {executor_stats}")
```

## 7. 性能优化示例

### 7.1 预编译工作流

```python
from src.core.workflow import create_workflow_manager

workflow_manager = create_workflow_manager()

# 创建并预编译工作流
workflow = workflow_manager.create_workflow(config)

# 手动编译（可选，执行时会自动编译）
if not workflow.compiled_graph:
    workflow_manager.compile_workflow(workflow)

# 现在可以快速执行多次
for i in range(10):
    initial_state = WorkflowState(
        workflow_id=workflow.workflow_id,
        execution_id=f"batch_exec_{i}",
        status="running",
        data={"batch_id": i, "input": f"data_{i}"}
    )
    
    result = workflow_manager.execute_workflow(workflow, initial_state)
    print(f"批次 {i} 执行完成")
```

### 7.2 批量执行

```python
import asyncio
from typing import List

async def batch_execute_workflows(
    workflow_manager, 
    workflow: Workflow, 
    inputs: List[dict]
) -> List[WorkflowState]:
    """批量执行工作流"""
    
    tasks = []
    for i, input_data in enumerate(inputs):
        initial_state = WorkflowState(
            workflow_id=workflow.workflow_id,
            execution_id=f"batch_{i}",
            status="running",
            data=input_data
        )
        
        task = workflow_manager.execute_workflow_async(workflow, initial_state)
        tasks.append(task)
    
    # 并行执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"批次 {i} 执行失败: {result}")
        else:
            successful_results.append(result)
    
    return successful_results

# 使用批量执行
inputs = [{"input": f"data_{i}"} for i in range(100)]
results = await batch_execute_workflows(workflow_manager, workflow, inputs)
print(f"成功执行 {len(results)} 个批次")
```

## 总结

新的工作流架构提供了以下优势：

1. **职责清晰**：WorkflowManager 负责管理，WorkflowExecutor 负责执行，WorkflowValidator 负责验证
2. **易于使用**：提供了简洁的 API 和便捷函数
3. **扩展性强**：支持自定义验证器、管理器和执行策略
4. **错误处理完善**：提供了详细的验证和执行错误信息
5. **性能优化**：支持预编译、批量执行和流式处理

通过这些示例，开发者可以快速上手新的工作流架构，并根据具体需求进行定制和扩展。