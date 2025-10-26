# Graph架构分离实施指南

## 1. 概述

本指南详细说明如何将Graph相关代码从Application层迁移到Infrastructure层，实现业务工作流与LangGraph技术实现的清晰分离。实施过程分为三个阶段，预计总耗时5-7天。

## 2. 实施前准备

### 2.1 环境检查
- 确保所有现有测试通过
- 备份当前代码（创建分支）
- 确认团队了解迁移计划

### 2.2 工具准备
- IDE支持重命名和查找引用
- 测试框架就绪
- 版本控制工具

## 3. 阶段一：创建Infrastructure Graph模块（2天）

### 3.1 第一天任务

#### 上午：创建目录结构
```bash
# 创建基础设施Graph模块目录
mkdir -p src/infrastructure/graph/nodes
mkdir -p src/infrastructure/graph/edges
mkdir -p src/infrastructure/graph/triggers
```

#### 下午：迁移核心文件
```bash
# 迁移核心配置文件
mv src/application/workflow/config.py src/infrastructure/graph/
mv src/application/workflow/registry.py src/infrastructure/graph/
mv src/application/workflow/builder.py src/infrastructure/graph/
mv src/application/workflow/state.py src/infrastructure/graph/
```

#### 文件重命名建议（可选但推荐）：
```bash
# 重命名类以明确技术边界
# config.py 中的 WorkflowConfig → GraphConfig
# registry.py 中的 NodeRegistry 保持（但属于Graph范畴）
# builder.py 中的 WorkflowBuilder → GraphBuilder
```

### 3.2 第二天任务

#### 上午：迁移节点和边目录
```bash
# 迁移节点实现
mv src/application/workflow/nodes/ src/infrastructure/graph/
mv src/application/workflow/edges/ src/infrastructure/graph/
mv src/application/workflow/triggers/ src/infrastructure/graph/
```

#### 下午：更新导入路径
1. **更新被移动文件中的导入**：
   ```python
   # 在 src/infrastructure/graph/config.py 中
   # 原：from src.application.workflow.state import WorkflowState
   # 改为：from ..state import WorkflowState  # 但需要进一步调整
   ```

2. **更安全的做法**：使用完整路径更新
   ```python
   # 在所有被移动的文件中，更新相对路径为绝对路径
   # 例如：from src.infrastructure.graph.state import GraphState
   ```

3. **运行基本语法检查**：
   ```bash
   python -m py_compile src/infrastructure/graph/*.py
   ```

## 4. 阶段二：重构Application Workflow服务（3天）

### 4.1 第三天任务

#### 重构 factory.py
```python
# src/application/workflow/factory.py
# 移除直接的Graph构建逻辑，改为使用GraphBuilder

from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.config import GraphConfig

class WorkflowFactory:
    def __init__(self, graph_builder: GraphBuilder):
        self.graph_builder = graph_builder
        
    def create_from_config(self, config: WorkflowConfig) -> Any:
        # 将业务WorkflowConfig转换为GraphConfig
        graph_config = self._convert_to_graph_config(config)
        return self.graph_builder.build(graph_config)
        
    def _convert_to_graph_config(self, config: WorkflowConfig) -> GraphConfig:
        # 转换逻辑（后续会移到专门的转换器）
        pass
```

#### 更新依赖注入配置
```python
# 在DI容器配置中（如src/main/container.py）
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.registry import get_global_registry

def setup_di_container():
    # 注册Graph服务
    container.register(GraphBuilder, lambda: GraphBuilder(get_global_registry()))
    
    # 注册WorkflowFactory
    container.register(WorkflowFactory, lambda: WorkflowFactory(container.get(GraphBuilder)))
```

### 4.2 第四天任务

#### 创建转换器服务
```python
# src/application/workflow/converter.py
from src.domain.workflow.entities import BusinessWorkflow
from src.infrastructure.graph.config import GraphConfig

class WorkflowConverter:
    """业务工作流到Graph配置的转换服务"""
    
    def to_graph_config(self, business_workflow: BusinessWorkflow) -> GraphConfig:
        # 实现转换逻辑
        graph_config = GraphConfig(
            name=business_workflow.name,
            description=business_workflow.description,
            # 转换节点和边
            nodes=self._convert_nodes(business_workflow.steps),
            edges=self._convert_edges(business_workflow.transitions)
        )
        return graph_config
```

#### 重构 manager.py
```python
# src/application/workflow/manager.py
class WorkflowManager:
    def __init__(self, workflow_factory: WorkflowFactory, converter: WorkflowConverter):
        self.workflow_factory = workflow_factory
        self.converter = converter
        
    def execute_workflow(self, business_workflow: BusinessWorkflow):
        # 转换业务工作流为Graph配置
        graph_config = self.converter.to_graph_config(business_workflow)
        # 创建并执行Graph
        graph = self.workflow_factory.create_from_config(graph_config)
        return graph.run()
```

### 4.3 第五天任务

#### 全面测试验证
1. **单元测试**：确保每个重构的组件功能正常
2. **集成测试**：验证层间协作
3. **回归测试**：确保现有功能不受影响

```bash
# 运行测试套件
pytest tests/application/workflow/test_factory.py -v
pytest tests/application/workflow/test_manager.py -v
pytest tests/infrastructure/graph/ -v
```

## 5. 阶段三：创建领域工作流模型（2天）

### 5.1 第六天任务

#### 创建Domain层工作流实体
```python
# src/domain/workflow/entities.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class BusinessWorkflow:
    """业务工作流领域实体"""
    id: str
    name: str
    description: str
    steps: List['WorkflowStep']
    rules: List['WorkflowRule']
    version: str = "1.0"
    
    def validate(self) -> List[str]:
        """验证业务规则"""
        errors = []
        # 验证步骤完整性
        if not self.steps:
            errors.append("工作流必须包含步骤")
        # 验证规则
        for rule in self.rules:
            errors.extend(rule.validate())
        return errors

@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    type: str  # "analysis", "execution", "decision", etc.
    config: Dict[str, Any]
    next_steps: List[str] = None
```

### 5.2 第七天任务

#### 完善转换逻辑
```python
# 在WorkflowConverter中实现完整转换
def _convert_nodes(self, steps: List[WorkflowStep]) -> Dict[str, Any]:
    nodes = {}
    for step in steps:
        # 根据步骤类型映射到不同的Graph节点
        if step.type == "analysis":
            nodes[step.name] = {
                "type": "analysis_node",
                "config": step.config
            }
        elif step.type == "execution":
            nodes[step.name] = {
                "type": "tool_node", 
                "config": step.config
            }
    return nodes

def _convert_edges(self, transitions: List[Transition]) -> List[Dict[str, Any]]:
    edges = []
    for transition in transitions:
        edges.append({
            "from": transition.from_step,
            "to": transition.to_step,
            "type": "simple"  # 或 "conditional"
        })
    return edges
```

#### 更新测试用例
创建领域模型的测试：
```python
# tests/domain/workflow/test_entities.py
def test_business_workflow_validation():
    workflow = BusinessWorkflow(
        id="test",
        name="Test Workflow",
        description="Test",
        steps=[],
        rules=[]
    )
    errors = workflow.validate()
    assert "工作流必须包含步骤" in errors
```

## 6. 测试策略

### 6.1 测试金字塔
- **单元测试**：70% - 测试每个组件单独的功能
- **集成测试**：20% - 测试层与层之间的集成
- **端到端测试**：10% - 测试完整工作流执行

### 6.2 测试重点
1. **路径变更测试**：确保所有导入路径正确
2. **功能回归测试**：确保现有功能不变
3. **接口契约测试**：确保层间接口符合预期
4. **错误处理测试**：验证异常情况处理

## 7. 常见问题与解决方案

### 7.1 导入错误
- **问题**：移动文件后导入路径错误
- **解决**：使用IDE的全局查找替换功能，批量更新导入

### 7.2 循环依赖
- **问题**：层间出现循环依赖
- **解决**：检查依赖方向，确保Domain层不依赖Infrastructure层

### 7.3 测试失败
- **问题**：迁移后测试失败
- **解决**：优先修复单元测试，然后集成测试

## 8. 验收标准

1. ✅ 所有现有测试通过
2. ✅ 新的架构层级清晰
3. ✅ 业务逻辑与技术实现分离
4. ✅ 性能无明显下降
5. ✅ 代码可读性提高
6. ✅ 团队理解新架构

## 9. 回滚方案

如果迁移过程中出现严重问题，可执行回滚：
```bash
# 回滚到迁移前的状态
git reset --hard <迁移前提交>
git push -f
```

## 10. 后续优化建议

1. **性能监控**：监控新架构的执行性能
2. **文档完善**：补充详细的设计文档和API文档
3. **代码评审**：团队内部评审新架构
4. **持续重构**：根据使用反馈持续优化

---
*实施过程中如遇问题，请及时与架构团队沟通*