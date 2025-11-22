# 提示词与工作流集成迁移指南

## 概述

本指南帮助开发者从旧的 `src/services/prompts/langgraph_integration.py` 模块迁移到新的模板系统。

## 迁移时间表

- **阶段1（立即）**：新代码使用新的模板系统
- **阶段2（3个月内）**：现有代码逐步迁移
- **阶段3（6个月后）**：废弃旧接口，仅保留兼容性适配器
- **阶段4（1年后）**：完全移除旧接口

## 迁移步骤

### 1. 识别使用旧接口的代码

搜索以下模式：
```python
# 旧的导入方式
from src.services.prompts.langgraph_integration import (
    create_agent_workflow,
    create_simple_workflow,
    get_agent_config
)

# 或者
from src.services.prompts import (
    create_agent_workflow,
    create_simple_workflow,
    get_agent_config
)
```

### 2. 迁移到新的模板系统

#### 2.1 替换 `create_agent_workflow`

**旧代码：**
```python
from src.services.prompts import create_agent_workflow

# 创建工作流
workflow = create_agent_workflow(
    prompt_injector=injector,
    llm_client="gpt-4"
)
```

**新代码：**
```python
from src.services.prompts import create_prompt_agent_workflow

# 创建工作流（推荐方式）
workflow = create_prompt_agent_workflow(
    prompt_injector=injector,
    llm_client="gpt-4",
    system_prompt="assistant",
    rules=["safety", "format"],
    user_command="data_analysis",
    cache_enabled=True
)
```

**或者使用模板直接：**
```python
from src.core.workflow.templates import PromptAgentTemplate

# 创建模板
template = PromptAgentTemplate(prompt_injector=injector)

# 创建工作流
workflow = template.create_workflow(
    name="my_agent",
    description="我的代理工作流",
    config={
        "llm_client": "gpt-4",
        "system_prompt": "assistant",
        "rules": ["safety", "format"],
        "user_command": "data_analysis"
    }
)
```

#### 2.2 替换 `create_simple_workflow`

**旧代码：**
```python
from src.services.prompts import create_simple_workflow

# 创建简单工作流
workflow = create_simple_workflow(prompt_injector=injector)
result = workflow["run"](initial_state)
```

**新代码：**
```python
from src.services.prompts import create_simple_prompt_agent_workflow

# 创建简单工作流（推荐方式）
workflow = create_simple_prompt_agent_workflow(
    prompt_injector=injector,
    system_prompt="assistant"
)

# 执行工作流
result = workflow.execute(initial_state)
```

#### 2.3 替换 `get_agent_config`

**旧代码：**
```python
from src.services.prompts import get_agent_config

config = get_agent_config()
```

**新代码：**
```python
from src.services.prompts import PromptConfigManager

manager = PromptConfigManager()
config = manager.get_agent_config()

# 或者使用全局管理器
from src.services.prompts import get_global_config_manager

manager = get_global_config_manager()
config = manager.get_agent_config()
```

### 3. 使用模板注册表

**新代码：**
```python
from src.core.workflow.templates.registry import get_global_template_registry

# 获取注册表
registry = get_global_template_registry()

# 使用模板创建工作流
workflow = registry.create_workflow_from_template(
    template_name="prompt_agent",
    name="my_agent",
    description="我的代理工作流",
    config={
        "llm_client": "gpt-4",
        "system_prompt": "assistant",
        "rules": ["safety", "format"],
        "user_command": "data_analysis"
    }
)
```

## 配置迁移

### 1. 配置格式变化

**旧配置格式：**
```python
config = get_agent_config()
# 返回：{"system_prompt": "assistant", "rules": ["safety", "format"], ...}
```

**新配置格式：**
```python
from src.services.prompts import PromptConfigManager

manager = PromptConfigManager()
config = manager.get_agent_config()
# 返回：PromptConfig 实例
```

### 2. 配置验证

**新代码：**
```python
from src.services.prompts import PromptConfigManager

manager = PromptConfigManager()
config = manager.create_from_dict({
    "system_prompt": "assistant",
    "rules": ["safety", "format"],
    "user_command": "data_analysis"
})

# 验证配置
errors = manager.validate_config(config)
if errors:
    print(f"配置错误: {errors}")
```

## 测试迁移

### 1. 更新测试用例

**旧测试：**
```python
def test_create_agent_workflow():
    workflow = create_agent_workflow(mock_injector)
    assert workflow is not None
```

**新测试：**
```python
def test_create_prompt_agent_workflow():
    workflow = create_prompt_agent_workflow(mock_injector)
    assert workflow is not None
    assert workflow.name == "prompt_agent_workflow"

def test_prompt_agent_template():
    template = PromptAgentTemplate(mock_injector)
    workflow = template.create_workflow(
        name="test",
        description="测试工作流",
        config={"llm_client": "test"}
    )
    assert workflow.name == "test"
```

### 2. 兼容性测试

```python
import warnings

def test_legacy_compatibility():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # 测试旧接口仍然工作
        workflow = create_agent_workflow(mock_injector)
        assert workflow is not None
        
        # 验证废弃警告
        assert len(w) > 0
        assert issubclass(w[0].category, DeprecationWarning)
```

## 性能优化

### 1. 缓存优化

**新代码：**
```python
from src.services.prompts import get_global_config_manager

# 使用全局配置管理器（自动缓存）
manager = get_global_config_manager()
config = manager.get_agent_config()  # 从缓存获取

# 清空缓存
manager.clear_cache()
```

### 2. 模板缓存

**新代码：**
```python
from src.core.workflow.templates.registry import get_global_template_registry

# 模板注册表自动缓存编译后的工作流
registry = get_global_template_registry()
workflow = registry.create_workflow_from_template(
    template_name="prompt_agent",
    name="my_agent",
    description="我的代理工作流",
    config=config
)
```

## 常见问题

### Q1: 旧接口什么时候会被移除？

**A:** 旧接口将在6个月后废弃，1年后完全移除。建议尽快迁移到新接口。

### Q2: 新系统是否支持所有旧功能？

**A:** 是的，新系统完全支持旧系统的所有功能，并提供了更多特性。

### Q3: 迁移过程中如何保证系统稳定？

**A:** 
1. 使用向后兼容适配器
2. 分阶段迁移
3. 充分的测试覆盖
4. 监控系统性能

### Q4: 新系统有什么优势？

**A:**
- 更好的架构设计
- 更强的扩展性
- 更好的性能
- 更清晰的接口
- 更完善的测试支持

## 迁移检查清单

### 代码迁移
- [ ] 替换所有 `create_agent_workflow` 调用
- [ ] 替换所有 `create_simple_workflow` 调用
- [ ] 替换所有 `get_agent_config` 调用
- [ ] 更新导入语句
- [ ] 使用新的配置管理方式

### 测试更新
- [ ] 更新单元测试
- [ ] 更新集成测试
- [ ] 添加兼容性测试
- [ ] 验证性能回归

### 文档更新
- [ ] 更新API文档
- [ ] 更新使用示例
- [ ] 更新迁移指南
- [ ] 更新架构文档

### 部署准备
- [ ] 验证开发环境
- [ ] 验证测试环境
- [ ] 准备回滚计划
- [ ] 监控部署过程

## 支持和帮助

如果在迁移过程中遇到问题，可以：

1. 查看详细的重构计划：`docs/architecture/prompt_workflow_integration_refactoring_plan.md`
2. 查看影响分析：`docs/architecture/prompt_workflow_integration_impact_analysis.md`
3. 查看新系统的API文档
4. 联系架构团队获取支持

## 总结

通过遵循本迁移指南，您可以平滑地从旧系统迁移到新的模板系统，获得更好的架构和性能。迁移过程是渐进式的，确保系统稳定性的同时逐步提升代码质量。