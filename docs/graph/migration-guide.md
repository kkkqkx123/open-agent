# Graph 组件迁移指南

## 快速参考

### 迁移清单

#### ✅ 应该迁移到基础设施层的组件

| 组件类型 | 源路径 | 目标路径 | 优先级 |
|---------|--------|----------|--------|
| 图核心实现 | `src/core/workflow/graph/graph.py` | `src/infrastructure/graph/core/graph.py` | 高 |
| 节点基类 | `src/core/workflow/graph/nodes/base.py` | `src/infrastructure/graph/nodes/base.py` | 高 |
| 边基类 | `src/core/workflow/graph/edges/base.py` | `src/infrastructure/graph/edges/base.py` | 高 |
| 简单节点 | `src/core/workflow/graph/nodes/simple_*.py` | `src/infrastructure/graph/nodes/` | 高 |
| 简单边 | `src/core/workflow/graph/edges/*.py` | `src/infrastructure/graph/edges/` | 高 |
| 构建器 | `src/core/workflow/graph/builder/` | `src/infrastructure/graph/builders/` | 中 |
| 注册表 | `src/core/workflow/graph/registry/` | `src/infrastructure/graph/registry/` | 中 |
| 路由函数 | `src/core/workflow/graph/route_functions/` | `src/infrastructure/graph/functions/routing/` | 中 |
| 节点函数 | `src/core/workflow/graph/node_functions/` | `src/infrastructure/graph/functions/nodes/` | 中 |

#### ❌ 应该保留在核心层的组件

| 组件类型 | 路径 | 原因 |
|---------|------|------|
| 图服务 | `src/core/workflow/graph/service.py` | 包含业务逻辑 |
| 业务节点 | `src/core/workflow/graph/nodes/llm_node.py` | 特定业务逻辑 |
| 业务节点 | `src/core/workflow/graph/nodes/tool_node.py` | 特定业务逻辑 |
| 业务节点 | `src/core/workflow/graph/nodes/condition_node.py` | 特定业务逻辑 |
| 扩展系统 | `src/core/workflow/graph/extensions/` | 业务扩展机制 |
| 状态机 | `src/core/workflow/graph/nodes/state_machine/` | 业务逻辑 |

## 迁移步骤

### 第一阶段：基础组件（1-2天）

1. **创建目录结构**
   ```bash
   mkdir -p src/infrastructure/graph/nodes
   mkdir -p src/infrastructure/graph/edges
   ```

2. **迁移基础类**
   ```bash
   # 迁移节点基类
   cp src/core/workflow/graph/nodes/base.py src/infrastructure/graph/nodes/
   
   # 迁移边基类
   cp src/core/workflow/graph/edges/base.py src/infrastructure/graph/edges/
   ```

3. **更新导入**
   ```python
   # 在核心层组件中更新导入
   from src.infrastructure.graph.nodes.base import BaseNode
   from src.infrastructure.graph.edges.base import BaseEdge
   ```

4. **运行测试**
   ```bash
   uv run pytest tests/core/workflow/graph/
   ```

### 第二阶段：简单实现（2-3天）

1. **迁移简单节点**
   ```bash
   cp src/core/workflow/graph/nodes/simple_node.py src/infrastructure/graph/nodes/
   cp src/core/workflow/graph/nodes/async_node.py src/infrastructure/graph/nodes/
   cp src/core/workflow/graph/nodes/start_node.py src/infrastructure/graph/nodes/
   cp src/core/workflow/graph/nodes/end_node.py src/infrastructure/graph/nodes/
   ```

2. **迁移简单边**
   ```bash
   cp src/core/workflow/graph/edges/simple_edge.py src/infrastructure/graph/edges/
   cp src/core/workflow/graph/edges/conditional_edge.py src/infrastructure/graph/edges/
   cp src/core/workflow/graph/edges/flexible_edge.py src/infrastructure/graph/edges/
   ```

3. **更新所有导入**
   - 搜索并替换所有相关导入
   - 确保只依赖接口层

### 第三阶段：构建器和注册表（3-4天）

1. **迁移构建器**
   ```bash
   mkdir -p src/infrastructure/graph/builders
   cp src/core/workflow/graph/builder/* src/infrastructure/graph/builders/
   ```

2. **迁移注册表**
   ```bash
   mkdir -p src/infrastructure/graph/registry
   cp src/core/workflow/graph/registry/* src/infrastructure/graph/registry/
   ```

3. **迁移函数管理**
   ```bash
   mkdir -p src/infrastructure/graph/functions/routing
   mkdir -p src/infrastructure/graph/functions/nodes
   cp src/core/workflow/graph/route_functions/* src/infrastructure/graph/functions/routing/
   cp src/core/workflow/graph/node_functions/* src/infrastructure/graph/functions/nodes/
   ```

### 第四阶段：图引擎整合（5-7天）

1. **分析现有图引擎**
   - 比较 `graph.py` 和 `StateGraphEngine`
   - 识别重叠功能

2. **整合实现**
   - 创建统一的图接口
   - 保持向后兼容性

3. **更新服务层**
   - 修改 `service.py` 使用新引擎
   - 确保业务逻辑不变

## 常见问题

### Q: 如何处理循环依赖？
A: 使用 `TYPE_CHECKING` 避免运行时循环依赖：
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.interfaces.workflow.graph import INode
```

### Q: 如何保持向后兼容？
A: 使用适配器模式：
```python
# 在核心层创建适配器
from src.infrastructure.graph.nodes.base import BaseNode as InfraBaseNode

class BaseNode(InfraBaseNode):
    """向后兼容的节点基类"""
    pass
```

### Q: 如何验证迁移成功？
A: 运行完整的测试套件：
```bash
uv run pytest tests/core/workflow/graph/ -v
uv run pytest tests/infrastructure/graph/ -v
```

## 验证检查点

- [ ] 所有导入正确更新
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试通过
- [ ] 代码审查完成
- [ ] 文档更新完成

## 回滚计划

如果迁移出现问题，可以按以下步骤回滚：

1. **恢复原始文件**
   ```bash
   git checkout HEAD~1 -- src/core/workflow/graph/
   ```

2. **删除迁移的文件**
   ```bash
   rm -rf src/infrastructure/graph/nodes
   rm -rf src/infrastructure/graph/edges
   ```

3. **重新运行测试**
   ```bash
   uv run pytest tests/core/workflow/graph/
   ```

## 联系方式

如有问题，请联系架构团队或查看详细分析文档：
`docs/graph/core-to-infrastructure-migration-analysis.md`