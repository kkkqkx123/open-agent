# 迭代管理器使用指南

## 概述

迭代管理器（IterationManager）是Open-Agent框架中统一管理图节点迭代次数的核心组件，提供全局和节点级别的迭代控制功能。

## 核心组件

### IterationManager
- 统一管理所有迭代相关的逻辑
- 提供全局工作流级别的迭代控制
- 支持节点级别的迭代限制
- 记录详细的迭代历史和统计信息

### 主要类型
- `IterationRecord`: 记录单次迭代的详细信息
- `NodeIterationStats`: 存储节点级别的迭代统计

## 配置说明

### 全局配置
在工作流配置中设置全局迭代限制：

```yaml
name: "react_workflow"
description: "ReAct工作流"
additional_config:
  max_iterations: 10           # 全局最大迭代次数
  cycle_completer_node: "observe_node"  # 完成一次循环的节点

nodes:
  think_node:
    function: "think_node"
    config:
      max_iterations: 15       # think_node最大迭代次数
    description: "思考节点"
  
  act_node:
    function: "act_node"
    # 无特定限制，只受全局限制
    description: "行动节点"
  
  observe_node:
    function: "observe_node"
    config:
      max_iterations: 8        # observe_node最大迭代次数
    description: "观察节点"
```

### 迭代记录字段
增强的`WorkflowState`包含以下迭代管理字段：
- `iteration_history`: 存储所有迭代的历史记录
- `node_iterations`: 存储节点级别的迭代统计
- `workflow_iteration_count`: 全局迭代计数
- `workflow_max_iterations`: 全局最大迭代次数

## 使用示例

### 1. 基本使用
```python
from src.infrastructure.graph import (
    IterationAwareGraphBuilder, 
    IterationManager, 
    GraphConfig
)

# 创建图配置
config = GraphConfig.from_dict({
    "name": "test_workflow",
    "description": "测试工作流",
    "additional_config": {
        "max_iterations": 5,
        "cycle_completer_node": "observe_node"
    },
    "nodes": {
        "think_node": {
            "function": "think_node",
            "config": {"max_iterations": 3}
        },
        "act_node": {
            "function": "act_node",
            # 无特定限制
        }
    },
    "edges": [
        # 边的配置...
    ]
})

# 使用迭代感知构建器
builder = IterationAwareGraphBuilder()
graph = builder.build_graph(config)
```

### 2. 访问迭代统计
```python
from src.infrastructure.graph import get_iteration_stats

# 在工作流执行后获取统计信息
stats = iteration_manager.get_iteration_stats(state)
print(f"工作流迭代次数: {stats['workflow_iteration_count']}")
print(f"节点迭代统计: {stats['node_iterations']}")
print(f"总迭代历史: {len(stats['iteration_history'])}")
```

## 主要特性

### 1. 分层迭代控制
- **全局控制**: 限制整个工作流的迭代次数
- **节点控制**: 限制特定节点的执行次数
- **灵活配置**: 支持不同节点设置不同的迭代限制

### 2. 详细的迭代追踪
- **时间记录**: 记录每次迭代的开始和结束时间
- **状态追踪**: 记录每次迭代的成功或失败状态
- **错误记录**: 保存迭代失败时的错误信息

### 3. 高级功能
- **工作流隔离**: 不同工作流实例的迭代管理完全隔离
- **性能监控**: 提供详细的迭代性能指标
- **可扩展性**: 支持扩展新的迭代控制策略

## 与旧系统的兼容性

新系统保持与旧系统的向后兼容：
- 保留了旧的`increment_workflow_iteration`函数
- 保留了旧的`has_workflow_reached_max_iterations`函数
- 新系统使用增强的字段，但不影响现有功能

## 最佳实践

1. **使用IterationAwareGraphBuilder**：在需要高级迭代控制的工作流中使用此构建器
2. **合理设置迭代限制**：根据业务需求设置全局和节点特定的迭代限制
3. **监控迭代统计**：定期检查迭代统计信息来优化工作流性能
4. **选择循环完成节点**：正确配置完成一次循环的节点

## 故障排除

### 常见问题

1. **迭代计数不准确**：检查是否正确使用了`IterationAwareGraphBuilder`
2. **达到迭代限制但工作流未停止**：检查配置中的`cycle_completer_node`是否正确设置
3. **性能下降**：大量的迭代记录可能影响性能，考虑调整日志级别或清理旧记录

## 扩展性

迭代管理器设计支持扩展新的迭代策略，如基于时间、资源消耗或业务指标的迭代控制。