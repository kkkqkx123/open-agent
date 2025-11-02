# 节点继承 HookableNode 指南

## 概述

本文档详细说明了在 Modular Agent Framework 中，节点如何通过继承 `HookableNode` 来支持添加 hook。

## 架构设计

### HookableNode 核心功能

`HookableNode` 提供了以下核心功能：

1. **Hook 管理器集成**：自动管理 Hook 的注册和执行
2. **Hook 执行点**：
   - `BEFORE_EXECUTE`：节点执行前
   - `AFTER_EXECUTE`：节点执行后  
3. **错误处理**：统一的异常处理和错误 Hook 执行

### 继承方式对比

| 方式 | 适用场景 | 优点 | 缺点 |
|------|-----------|------|------|
| 直接继承 | 新节点开发 | 代码简洁，直接集成 | 需要修改现有代码 |
| 包装器模式 | 现有系统集成 | 无需修改原节点代码 | 增加了包装层 |

## 方式一：直接继承 HookableNode

### 适用场景
- 新开发的节点
- 需要完全控制 Hook 行为的节点
- 性能要求高的场景

### 实现示例

```python
"""新节点直接继承 HookableNode 示例"""

from typing import Dict, Any, Optional
from src.infrastructure.graph.nodes.hookable_node import HookableNode
from src.domain.agent.state import AgentState
from ..registry import NodeExecutionResult

class MyNewNode(HookableNode):
    """新的节点类直接继承 HookableNode"""
    
    def __init__(self, hook_manager: Optional[IHookManager] = None):
    """初始化新节点
    
    Args:
        hook_manager: Hook 管理器实例
    """
    super().__init__(hook_manager)
    
@property
def node_type(self) -> str:
    """节点类型标识"""
    return "my_new_node"

def _execute_core(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
    """执行节点核心逻辑（子类必须实现）
    
    Args:
        state: 当前 Agent 状态
        config: 节点配置
        
    Returns:
        NodeExecutionResult: 执行结果
    """
    # 节点业务逻辑实现
    result = self._do_business_logic(state, config)
    
    return NodeExecutionResult(
        state=result.state,
        next_node=result.next_node or "default_next",
        metadata=result.metadata or {}
    }
```

### Hook 执行流程

1. **前置 Hook**：`before_execute` - 可以修改状态或中断执行
2. **核心逻辑**：`_execute_core` - 节点实际业务逻辑
3. **后置 Hook**：`after_execute` - 可以修改执行结果
4. **错误 Hook**：`on_error` - 可以处理异常

## 方式二：使用 create_hookable_node_class 包装

### 适用场景
- 现有节点系统集成
- 不修改原节点代码
- 快速原型开发

### 实现示例

```python
from src.infrastructure.graph.nodes.hookable_node import create_hookable_node_class
from src.infrastructure.graph.nodes import ToolNode, LLMNode

### 包装现有节点类

```python
# 创建支持 Hook 的节点类
HookableToolNode = create_hookable_node_class(ToolNode, hook_manager)

# 创建节点实例
node_instance = HookableToolNode(hook_manager=hook_manager)
```

### HookAwareGraphBuilder 自动转换

在 `HookAwareGraphBuilder._get_node_function` 方法中，系统自动将普通节点包装为支持 Hook 的节点

## 配置集成

### 全局 Hook 配置

```yaml
# configs/hooks/global_hooks.yaml
global_hooks:
  - type: "logging"
    enabled: true
    config:
      log_level: "INFO"
      format: "json"
```

### 节点特定 Hook 配置

```yaml
# configs/hooks/llm_node_hooks.yaml
node_type: "llm_node"
inherit_global: true
hooks:
  - type: "performance_monitoring"
    enabled: true
    config:
      metrics: ["execution_time", "token_usage"]
```

## 实施步骤

### 新节点开发

1. 导入 `HookableNode`
2. 继承 `HookableNode`
3. 实现 `_execute_core` 方法

## 最佳实践

### 1. Hook 管理器注入

```python
def __init__(self, hook_manager: Optional[IHookManager] = None):
    super().__init__(hook_manager)

4. 实现 `node_type` 属性

### 现有节点改造

1. 使用 `create_hookable_node_class` 函数包装现有节点类

### 2. 配置驱动

- 使用 YAML 配置文件管理 Hook
- 支持环境变量注入
- 支持多环境配置

## 性能考虑

### 直接继承 vs 包装器模式

| 指标 | 直接继承 | 包装器模式 |
|------|-----------|------------|
| 执行速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 内存使用 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 代码复杂度 | 低 | 中等 |

## 故障排除

### 常见问题

1. **Hook 管理器未初始化**：检查依赖注入配置
2. **Hook 配置加载失败**：验证 YAML 文件语法
3. **Hook 执行异常**：检查 Hook 实现逻辑

## 总结

通过继承 `HookableNode`，节点可以：

- ✅ 支持前置、后置、错误 Hook
- ✅ 保持向后兼容性
- ✅ 配置驱动，易于管理

建议新节点直接继承 `HookableNode`，现有节点使用包装器模式进行渐进式改造。
