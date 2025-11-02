# Graph Hook 系统文档

## 概述

本目录包含 Modular Agent Framework 中 Graph Hook 系统的完整文档。

## 文档列表

### 核心概念
- **[节点继承HookableNode指南.md](节点继承HookableNode指南.md)** - 详细说明节点如何继承 HookableNode 来支持添加 hook。

### 实现示例
- **[代码实现示例.md](代码实现示例.md)** - 具体的代码实现示例和配置说明。

## 快速开始

### 新节点开发

```python
from src.infrastructure.graph.nodes.hookable_node import HookableNode

class MyNewNode(HookableNode):
    def _execute_core(self, state, config) -> NodeExecutionResult:
    # 实现节点核心逻辑
    return NodeExecutionResult(state=state)
```

### 现有节点改造

```python
from src.infrastructure.graph.nodes.hookable_node import create_hookable_node_class
from src.infrastructure.graph.nodes import ToolNode

# 包装现有节点
HookableToolNode = create_hookable_node_class(ToolNode, hook_manager)
```

## 关键特性

- ✅ **多继承方式**：直接继承或包装器模式
- ✅ **配置驱动**：YAML 配置文件管理
- ✅ **向后兼容**：现有节点无需修改
- ✅ **性能优化**：直接继承方式无额外开销

## 架构优势

1. **松耦合设计**：Hook 系统与节点逻辑分离
2. **可扩展性**：轻松添加新的 Hook 类型
3. **易于维护**：清晰的接口定义和实现分离

## 使用场景

- **性能监控**：记录节点执行时间和资源使用
- **日志记录**：统一格式的日志输出
- **错误处理**：统一的异常捕获和处理

## 最佳实践

1. 新节点直接继承 `HookableNode`
2. 现有节点使用 `create_hookable_node_class` 包装

---

*文档维护：架构团队*  
*最后更新：2025-11-02*