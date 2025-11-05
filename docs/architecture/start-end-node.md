实现start、end node，用于提供统一的处理

基于我对代码的分析和LangGraph最佳实践的了解，我现在可以创建一个详细的实现计划。

## 架构分析总结

当前的图节点系统具有以下特点：
1. **节点基类** [`BaseNode`](src/infrastructure/graph/registry.py:26) 定义了统一的接口
2. **节点注册系统** 使用 [`@node`](src/infrastructure/graph/registry.py:324) 装饰器自动注册
3. **支持Hook机制** 通过 [`HookableNode`](src/infrastructure/graph/nodes/hookable_node.py:14) 基类
4. **图构建器** 使用 [`StateGraph`](src/infrastructure/graph/builder.py:34) 和 [`START`/`END`](src/infrastructure/graph/builder.py:34) 常量
5. **配置驱动** 通过YAML配置文件管理节点配置

## LangGraph START/END节点最佳实践

根据Context7 MCP提供的信息，LangGraph中的START和END是特殊节点：
- **START节点**：定义图的入口点，通过 `add_edge(START, "node_name")` 设置
- **END节点**：定义图的终止点，通过 `add_edge("node_name", END)` 设置
- 它们是LangGraph内置的虚拟节点，不需要具体的执行逻辑

## 实现方案设计

```mermaid
graph TD
    A[START节点设计] --> B[StartNode类]
    A --> C[EndNode类]
    
    B --> D[继承BaseNode]
    B --> E[实现空执行逻辑]
    B --> F[配置Schema定义]
    
    C --> G[继承BaseNode]
    C --> H[实现空执行逻辑]
    C --> I[配置Schema定义]
    
    J[注册机制] --> K[@node装饰器注册]
    J --> L[节点类型定义]
    
    M[配置集成] --> N[节点配置组]
    M --> O[默认配置定义]
    
    P[构建器集成] --> Q[自动识别特殊节点]
    P --> R[跳过特殊节点执行]
    
    B --> J
    C --> J
    J --> M
    J --> P
```

## 详细实现计划

### 1. 创建START节点实现
- **文件位置**: [`src/infrastructure/graph/nodes/start_node.py`](src/infrastructure/graph/nodes/start_node.py)
- **节点类型**: `start_node`
- **功能**: 作为图的入口点，不执行实际逻辑

### 2. 创建END节点实现  
- **文件位置**: [`src/infrastructure/graph/nodes/end_node.py`](src/infrastructure/graph/nodes/end_node.py)
- **节点类型**: `end_node`
- **功能**: 作为图的终止点，不执行实际逻辑

### 3. 更新节点注册
- 在 [`src/infrastructure/graph/nodes/__init__.py`](src/infrastructure/graph/nodes/__init__.py) 中导出新节点

### 4. 配置集成
- 在 [`configs/nodes/_group.yaml`](configs/nodes/_group.yaml) 中添加默认配置
- 创建单独的配置文件 [`configs/nodes/start.yaml`](configs/nodes/start.yaml) 和 [`configs/nodes/end.yaml`](configs/nodes/end.yaml)

### 5. 构建器优化
- 在 [`src/infrastructure/graph/builder.py`](src/infrastructure/graph/builder.py) 中处理特殊节点
- 自动识别START/END节点并跳过执行逻辑