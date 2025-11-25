# 依赖分析 CLI 工具

## 概述

`StaticDependencyAnalyzer` 是一个**无状态、静态分析工具**，用于分析 DI 容器的依赖关系。它纯粹用于代码分析，不维护任何运行时状态。

## 架构设计

### 工具类 vs 容器服务

- **工具类** (`StaticDependencyAnalyzer`)：
  - 位置：`src/adapters/cli/dependency_analyzer_tool.py`
  - 特点：无状态、所有方法静态化、可复用
  - 用途：静态分析、代码检查、开发辅助
  - 不依赖于容器运行时

- **容器服务** (Enhanced Container)：
  - 位置：`src/services/container/enhanced_container.py`
  - 特点：有状态、跟踪依赖关系
  - 用途：运行时依赖解析、性能监控
  - 可选择继续使用或迁移至工具类

## 核心功能

### 1. 构建依赖图

```python
from src.adapters.cli.dependency_analyzer_tool import StaticDependencyAnalyzer

# 定义服务映射
services = {
    ISessionManager: SessionManagerImpl,
    IWorkflowManager: WorkflowManagerImpl,
    IHistoryStore: SQLiteHistoryStore,
}

# 构建依赖图
graph = StaticDependencyAnalyzer.build_dependency_graph(services)
# 结果: {
#   ISessionManager: {ISessionCore, ISessionRepository},
#   IWorkflowManager: {IWorkflowRegistry, IWorkflowExecutor},
#   ...
# }
```

### 2. 检测循环依赖

```python
circular_deps = StaticDependencyAnalyzer.detect_circular_dependencies(graph)

for cycle in circular_deps:
    print(f"循环: {' -> '.join([t.__name__ for t in cycle])}")
```

### 3. 计算依赖深度

```python
# 计算单个服务的依赖深度
depth = StaticDependencyAnalyzer.calculate_dependency_depth(
    graph, 
    ISessionManager
)
print(f"ISessionManager 的依赖深度: {depth}")

# 获取所有深度统计
stats = StaticDependencyAnalyzer.analyze(graph)
print(f"最大依赖深度: {stats['max_dependency_depth']}")
```

### 4. 拓扑排序

```python
# 获取服务的初始化顺序
order = StaticDependencyAnalyzer.get_topological_order(graph)
print("初始化顺序:")
for service in order:
    print(f"  - {service.__name__}")
```

### 5. 生成可视化报告

```python
# 生成 Graphviz DOT 格式
dot_content = StaticDependencyAnalyzer.generate_dot_diagram(graph)
with open("dependency_graph.dot", "w") as f:
    f.write(dot_content)

# 使用 Graphviz 生成图片
# dot -Tpng dependency_graph.dot -o dependency_graph.png
```

## CLI 命令

### 分析依赖关系

```bash
# 生成文本报告（默认）
python -m src.adapters.cli dependency analyze

# 生成JSON报告
python -m src.adapters.cli dependency analyze --format json

# 保存到文件
python -m src.adapters.cli dependency analyze --format json --output report.json

# 生成Graphviz DOT格式
python -m src.adapters.cli dependency analyze --format dot --output graph.dot
```

### 检查循环依赖

```bash
python -m src.adapters.cli dependency check-circular
```

输出示例：
```
✓ 未检测到循环依赖
```

或：
```
✗ 检测到循环依赖:
  ServiceA -> ServiceB -> ServiceC -> ServiceA
  ServiceX -> ServiceY -> ServiceX
```

## 使用示例

### 场景 1：分析现有容器

```python
from src.adapters.cli import StaticDependencyAnalyzer, DependencyAnalysisCommand

# 从容器收集服务注册信息
services = {
    ISessionManager: SessionManagerImpl,
    IWorkflowManager: WorkflowManagerImpl,
    ILLMService: OpenAILLMService,
}

# 创建分析命令
command = DependencyAnalysisCommand()
command.analyze_services(services)

# 获取分析结果
stats = command.get_analysis_stats()
print(f"总服务数: {stats['total_services']}")
print(f"循环依赖数: {stats['circular_dependencies_count']}")

# 生成报告
report = command.generate_text_report()
print(report)
```

### 场景 2：自动化检查

```python
from src.adapters.cli import DependencyAnalysisCommand

command = DependencyAnalysisCommand()
command.analyze_services(services_dict)

# 检查是否有循环依赖
if command.check_circular_dependencies():
    raise RuntimeError("检测到循环依赖！")

# 检查最大深度
stats = command.get_analysis_stats()
if stats['max_dependency_depth'] > 10:
    print("警告：依赖链过深")
```

### 场景 3：生成文档

```python
command = DependencyAnalysisCommand()
command.analyze_services(services)

# 生成不同格式的报告
command.export_report("report.json", format="json")
command.export_report("report.txt", format="text")
command.export_report("graph.dot", format="dot")
```

## 数据结构

### DependencyAnalysisResult

```python
@dataclass
class DependencyAnalysisResult:
    dependency_graph: Dict[Type, Set[Type]]      # 完整的依赖图
    circular_dependencies: List[CircularDependency]  # 循环依赖列表
    max_dependency_depth: int                     # 最大依赖深度
    orphaned_services: List[Type]                # 孤立服务列表
```

### CircularDependency

```python
class CircularDependency:
    dependency_chain: List[Type]  # 循环链中的类型列表
    description: str              # 可读的描述
```

## 性能考虑

### 无状态设计优势

1. **内存效率**：不维护任何长期状态，适合大型应用
2. **线程安全**：无共享状态，天然线程安全
3. **易于测试**：纯函数式，易于单元测试
4. **可重用性**：可在多个容器间复用

### 缓存机制

某些方法（如 `calculate_dependency_depth`）可选择传入缓存字典以避免重复计算：

```python
cache = {}
for service in services:
    depth = StaticDependencyAnalyzer.calculate_dependency_depth(
        graph, 
        service,
        cache  # 复用缓存，加快计算
    )
```

## 迁移指南

如果现有代码使用 `DependencyAnalyzer` 容器服务：

### 旧代码
```python
container = get_global_container()
analyzer = container.get(IDependencyAnalyzer)
result = analyzer.analyze()
```

### 新代码
```python
from src.adapters.cli import StaticDependencyAnalyzer

graph = StaticDependencyAnalyzer.build_dependency_graph(services)
result = StaticDependencyAnalyzer.analyze(graph)
```

## 开发建议

1. **不要在容器中注册** `StaticDependencyAnalyzer` 为服务
   - 它是工具，不是业务服务
   - 直接调用静态方法

2. **在 CI/CD 中集成**
   ```bash
   python -m src.adapters.cli dependency check-circular || exit 1
   ```

3. **定期生成报告**
   ```bash
   python -m src.adapters.cli dependency analyze --format json \
     --output reports/dependencies-$(date +%Y%m%d).json
   ```

4. **文档化依赖关系**
   ```bash
   python -m src.adapters.cli dependency analyze --format dot \
     --output docs/architecture.dot
   ```

## 常见问题

### Q: 如何只分析特定的服务子集？

A: 在调用前过滤服务字典：
```python
filtered_services = {
    k: v for k, v in services.items() 
    if k.__module__.startswith('src.services')
}
graph = StaticDependencyAnalyzer.build_dependency_graph(filtered_services)
```

### Q: 如何定制分析结果的输出格式？

A: 使用 `export_analysis_to_dict` 方法获取可序列化的字典，然后自定义格式化：
```python
result = StaticDependencyAnalyzer.get_analysis_result(graph)
data = StaticDependencyAnalyzer.export_analysis_to_dict(result)
# 自定义格式化 data
```

### Q: 与容器服务冲突吗？

A: 不冲突。新工具纯粹用于静态分析，不依赖运行时容器。可以同时存在。
