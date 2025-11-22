# 提示词与工作流集成重构计划

## 概述

本文档详细分析了 `src\services\prompts\langgraph_integration.py` 模块的架构问题，并提供了完整的重构方案。该模块当前存在职责混乱、功能冗余和架构违反等问题，需要进行系统性重构。

## 问题分析

### 1. 当前架构问题

#### 1.1 职责混乱
- **位置不当**：模块位于 `src/services/prompts/` 目录，但主要功能是创建LangGraph工作流
- **功能混杂**：既处理提示词注入又处理工作流构建，违反单一职责原则
- **依赖倒置**：高层模块（提示词服务）依赖低层模块（工作流构建）

#### 1.2 功能冗余
- **与 `UnifiedGraphBuilder` 重叠**：两者都创建LangGraph工作流，处理节点添加和边连接
- **与 `LangGraphAdapter` 重叠**：都提供LangGraph集成和图转换功能
- **与工作流模板系统重叠**：与 `ReActWorkflowTemplate` 等模板模式相似

#### 1.3 架构违反
- **违反扁平化架构原则**：工作流相关功能应集中在工作流层
- **违反依赖倒置原则**：形成了反向依赖关系
- **违反开闭原则**：添加新的工作流类型需要修改该模块

### 2. 现有系统分析

#### 2.1 工作流模板系统架构

```
src/core/workflow/templates/
├── base.py              # 基础模板抽象类
├── react.py             # ReAct模板实现
├── plan_execute.py      # 计划执行模板
├── registry.py          # 模板注册表
└── __init__.py
```

**设计模式**：
- **模板方法模式**：`BaseWorkflowTemplate` 定义算法骨架
- **工厂模式**：模板创建工作流实例
- **注册表模式**：`WorkflowTemplateRegistry` 管理模板

**核心接口**：
```python
class IWorkflowTemplate(ABC):
    def create_workflow(name: str, description: str, config: Dict[str, Any]) -> IWorkflow
    def get_parameters() -> List[Dict[str, Any]]
    def validate_parameters(config: Dict[str, Any]) -> List[str]
```

#### 2.2 提示词注入系统架构

```
src/services/prompts/
├── injector.py          # 提示词注入器实现
├── loader.py            # 提示词加载器
├── registry.py          # 提示词注册表
├── langgraph_integration.py  # 问题模块
└── __init__.py
```

**核心接口**：
```python
class IPromptInjector(ABC):
    def inject_prompts(state: IWorkflowState, config: PromptConfig) -> IWorkflowState
    def inject_system_prompt(state: IWorkflowState, prompt_name: str) -> IWorkflowState
    def inject_rule_prompts(state: IWorkflowState, rule_names: List[str]) -> IWorkflowState
    def inject_user_command(state: IWorkflowState, command_name: str) -> IWorkflowState
```

## 重构方案

### 1. 设计原则

#### 1.1 遵循扁平化架构
- **Core层**：核心实体和接口定义
- **Services层**：业务逻辑实现
- **Adapters层**：外部框架适配

#### 1.2 单一职责原则
- 工作流构建功能移至工作流层
- 提示词配置保留在提示词服务
- 清晰分离关注点

#### 1.3 依赖倒置原则
- 高层模块不依赖低层模块
- 都依赖于抽象接口
- 接口隔离原则

### 2. 重构架构设计

#### 2.1 新的模块结构

```
src/core/workflow/templates/
├── base.py                    # 基础模板（保持不变）
├── react.py                   # ReAct模板（保持不变）
├── plan_execute.py            # 计划执行模板（保持不变）
├── prompt_agent.py            # 新增：提示词代理模板
├── prompt_integration.py      # 新增：提示词集成基类
├── registry.py                # 模板注册表（扩展）
└── __init__.py

src/services/prompts/
├── injector.py               # 提示词注入器（保持不变）
├── loader.py                 # 提示词加载器（保持不变）
├── registry.py               # 提示词注册表（保持不变）
├── config.py                 # 新增：提示词配置管理
└── __init__.py

src/interfaces/workflow/
├── templates.py              # 新增：模板接口定义
└── __init__.py
```

#### 2.2 核心设计

##### 2.2.1 提示词集成基类

```python
# src/core/workflow/templates/prompt_integration.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ...interfaces.prompts import IPromptInjector, PromptConfig

class PromptIntegratedTemplate(ABC):
    """提示词集成模板基类
    
    提供提示词注入功能的基础实现，供具体模板继承。
    """
    
    def __init__(self, prompt_injector: Optional[IPromptInjector] = None):
        """初始化提示词集成模板
        
        Args:
            prompt_injector: 提示词注入器实例
        """
        self.prompt_injector = prompt_injector
    
    @abstractmethod
    def get_default_prompt_config(self) -> PromptConfig:
        """获取默认提示词配置
        
        Returns:
            PromptConfig: 默认提示词配置
        """
        pass
    
    def inject_prompts_to_state(self, state: Dict[str, Any], 
                               config: Optional[PromptConfig] = None) -> Dict[str, Any]:
        """将提示词注入到状态中
        
        Args:
            state: 工作流状态
            config: 提示词配置，如果为None则使用默认配置
            
        Returns:
            Dict[str, Any]: 注入提示词后的状态
        """
        if self.prompt_injector is None:
            return state
            
        prompt_config = config or self.get_default_prompt_config()
        return self.prompt_injector.inject_prompts(state, prompt_config)
```

##### 2.2.2 提示词代理模板

```python
# src/core/workflow/templates/prompt_agent.py

from typing import Dict, Any, Optional, List
from .base import BaseWorkflowTemplate
from .prompt_integration import PromptIntegratedTemplate
from ..workflow import Workflow
from ..value_objects import WorkflowStep, WorkflowTransition, StepType, TransitionType
from ...interfaces.prompts import IPromptInjector, PromptConfig

class PromptAgentTemplate(BaseWorkflowTemplate, PromptIntegratedTemplate):
    """提示词代理工作流模板
    
    基于提示词注入的简单代理工作流模板。
    """
    
    def __init__(self, prompt_injector: Optional[IPromptInjector] = None):
        """初始化提示词代理模板
        
        Args:
            prompt_injector: 提示词注入器实例
        """
        BaseWorkflowTemplate.__init__(self)
        PromptIntegratedTemplate.__init__(self, prompt_injector)
        self._name = "prompt_agent"
        self._description = "基于提示词注入的代理工作流模板"
        self._category = "agent"
        self._version = "1.0"
        
        # 更新参数定义
        self._parameters = [
            {
                "name": "llm_client",
                "type": "string",
                "description": "LLM客户端标识",
                "required": False,
                "default": "default"
            },
            {
                "name": "system_prompt",
                "type": "string",
                "description": "系统提示词名称",
                "required": False,
                "default": "assistant"
            },
            {
                "name": "rules",
                "type": "array",
                "description": "规则提示词列表",
                "required": False,
                "default": ["safety", "format"]
            },
            {
                "name": "user_command",
                "type": "string",
                "description": "用户指令名称",
                "required": False,
                "default": "data_analysis"
            },
            {
                "name": "cache_enabled",
                "type": "boolean",
                "description": "是否启用提示词缓存",
                "required": False,
                "default": True
            }
        ]
    
    def get_default_prompt_config(self) -> PromptConfig:
        """获取默认提示词配置
        
        Returns:
            PromptConfig: 默认提示词配置
        """
        return PromptConfig(
            system_prompt="assistant",
            rules=["safety", "format"],
            user_command="data_analysis",
            cache_enabled=True
        )
    
    def _build_workflow_structure(self, workflow: Workflow, config: Dict[str, Any]) -> None:
        """构建提示词代理工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 获取配置参数
        llm_client = config.get("llm_client", "default")
        system_prompt = config.get("system_prompt", "assistant")
        rules = config.get("rules", ["safety", "format"])
        user_command = config.get("user_command", "data_analysis")
        cache_enabled = config.get("cache_enabled", True)
        
        # 创建提示词注入节点
        inject_prompts_step = self._create_step(
            step_id="inject_prompts",
            step_name="inject_prompts",
            step_type=StepType.PREPROCESSING,
            description="注入提示词到工作流状态",
            config={
                "prompt_config": {
                    "system_prompt": system_prompt,
                    "rules": rules,
                    "user_command": user_command,
                    "cache_enabled": cache_enabled
                },
                "prompt_injector": self.prompt_injector
            }
        )
        workflow.add_step(inject_prompts_step)
        
        # 创建LLM调用节点
        llm_step = self._create_step(
            step_id="call_llm",
            step_name="call_llm",
            step_type=StepType.EXECUTION,
            description="调用LLM生成响应",
            config={
                "llm_client": llm_client,
                "timeout": 30,
                "retry_on_failure": True,
                "max_retries": 3
            }
        )
        workflow.add_step(llm_step)
        
        # 创建转换：提示词注入 -> LLM调用
        inject_to_llm = self._create_transition(
            transition_id="inject_to_llm",
            from_step="inject_prompts",
            to_step="call_llm",
            transition_type=TransitionType.SIMPLE,
            description="注入提示词后调用LLM"
        )
        workflow.add_transition(inject_to_llm)
        
        # 设置入口点
        workflow.set_entry_point("inject_prompts")
```

##### 2.2.3 提示词配置管理

```python
# src/services/prompts/config.py

from typing import Dict, Any, Optional
from ...interfaces.prompts import PromptConfig

class PromptConfigManager:
    """提示词配置管理器
    
    管理提示词配置的创建、验证和缓存。
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self._config_cache: Dict[str, PromptConfig] = {}
    
    def create_config(self, system_prompt: Optional[str] = None,
                     rules: Optional[List[str]] = None,
                     user_command: Optional[str] = None,
                     cache_enabled: bool = True) -> PromptConfig:
        """创建提示词配置
        
        Args:
            system_prompt: 系统提示词名称
            rules: 规则提示词列表
            user_command: 用户指令名称
            cache_enabled: 是否启用缓存
            
        Returns:
            PromptConfig: 提示词配置
        """
        return PromptConfig(
            system_prompt=system_prompt,
            rules=rules or [],
            user_command=user_command,
            cache_enabled=cache_enabled
        )
    
    def create_from_dict(self, config_dict: Dict[str, Any]) -> PromptConfig:
        """从字典创建提示词配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            PromptConfig: 提示词配置
        """
        return self.create_config(
            system_prompt=config_dict.get("system_prompt"),
            rules=config_dict.get("rules", []),
            user_command=config_dict.get("user_command"),
            cache_enabled=config_dict.get("cache_enabled", True)
        )
    
    def get_agent_config(self) -> PromptConfig:
        """获取默认Agent配置
        
        Returns:
            PromptConfig: 默认Agent配置
        """
        cache_key = "default_agent"
        if cache_key not in self._config_cache:
            self._config_cache[cache_key] = self.create_config(
                system_prompt="assistant",
                rules=["safety", "format"],
                user_command="data_analysis",
                cache_enabled=True
            )
        return self._config_cache[cache_key]
```

##### 2.2.4 模板接口扩展

```python
# src/interfaces/workflow/templates.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ...interfaces.prompts import IPromptInjector, PromptConfig

class IPromptIntegratedTemplate(ABC):
    """提示词集成模板接口
    
    为需要提示词注入功能的模板提供统一接口。
    """
    
    @abstractmethod
    def set_prompt_injector(self, injector: IPromptInjector) -> None:
        """设置提示词注入器
        
        Args:
            injector: 提示词注入器实例
        """
        pass
    
    @abstractmethod
    def get_prompt_injector(self) -> Optional[IPromptInjector]:
        """获取提示词注入器
        
        Returns:
            Optional[IPromptInjector]: 提示词注入器实例
        """
        pass
    
    @abstractmethod
    def create_prompt_config(self, config: Dict[str, Any]) -> PromptConfig:
        """从配置创建提示词配置
        
        Args:
            config: 工作流配置
            
        Returns:
            PromptConfig: 提示词配置
        """
        pass
```

### 3. 重构实施计划

#### 3.1 第一阶段：创建新模块

1. **创建提示词集成基类**
   - 文件：`src/core/workflow/templates/prompt_integration.py`
   - 功能：提供提示词注入的基础功能

2. **创建提示词代理模板**
   - 文件：`src/core/workflow/templates/prompt_agent.py`
   - 功能：实现基于提示词的代理工作流

3. **创建提示词配置管理器**
   - 文件：`src/services/prompts/config.py`
   - 功能：管理提示词配置的创建和缓存

4. **扩展模板接口**
   - 文件：`src/interfaces/workflow/templates.py`
   - 功能：定义提示词集成模板的接口

#### 3.2 第二阶段：更新现有模块

1. **更新模板注册表**
   - 修改：`src/core/workflow/templates/registry.py`
   - 功能：注册新的提示词代理模板

2. **更新提示词服务**
   - 修改：`src/services/prompts/__init__.py`
   - 功能：导出新的配置管理器

3. **创建节点函数**
   - 文件：`src/core/workflow/graph/node_functions/prompt_nodes.py`
   - 功能：实现提示词注入和LLM调用节点

#### 3.3 第三阶段：迁移和清理

1. **迁移功能**
   - 将 `langgraph_integration.py` 中的功能迁移到新模块
   - 更新所有引用该模块的代码

2. **删除冗余模块**
   - 删除：`src/services/prompts/langgraph_integration.py`
   - 清理相关导入和引用

3. **更新测试**
   - 更新相关单元测试
   - 添加新模块的测试

### 4. 使用示例

#### 4.1 创建提示词代理工作流

```python
from src.core.workflow.templates.prompt_agent import PromptAgentTemplate
from src.services.prompts.injector import PromptInjector
from src.services.prompts.loader import PromptLoader
from src.services.prompts.registry import PromptRegistry

# 创建提示词注入器
registry = PromptRegistry(config_loader)
loader = PromptLoader(registry)
injector = PromptInjector(loader)

# 创建模板
template = PromptAgentTemplate(prompt_injector=injector)

# 创建工作流
config = {
    "llm_client": "gpt-4",
    "system_prompt": "assistant",
    "rules": ["safety", "format"],
    "user_command": "data_analysis"
}

workflow = template.create_workflow(
    name="my_agent",
    description="基于提示词的代理工作流",
    config=config
)
```

#### 4.2 使用模板注册表

```python
from src.core.workflow.templates.registry import get_global_template_registry

# 获取全局注册表
registry = get_global_template_registry()

# 使用模板创建工作流
workflow = registry.create_workflow_from_template(
    template_name="prompt_agent",
    name="my_agent",
    description="基于提示词的代理工作流",
    config={
        "llm_client": "gpt-4",
        "system_prompt": "assistant",
        "rules": ["safety", "format"],
        "user_command": "data_analysis"
    }
)
```

### 5. 优势分析

#### 5.1 架构优势

1. **职责清晰**：每个模块都有明确的单一职责
2. **依赖正确**：遵循依赖倒置原则，高层模块不依赖低层模块
3. **扩展性好**：新的提示词集成模板可以轻松添加
4. **复用性高**：提示词集成功能可以被多个模板复用

#### 5.2 维护优势

1. **代码集中**：相关功能集中在合适的模块中
2. **测试简单**：每个模块可以独立测试
3. **文档清晰**：架构和接口都有清晰的文档
4. **调试容易**：问题定位更加精确

#### 5.3 性能优势

1. **缓存优化**：提示词配置和内容都有缓存机制
2. **懒加载**：模板和组件都支持懒加载
3. **资源管理**：更好的资源管理和生命周期控制

### 6. 风险评估与缓解

#### 6.1 潜在风险

1. **向后兼容性**：现有代码可能依赖旧模块
2. **测试覆盖**：新模块需要充分的测试
3. **性能影响**：重构可能影响现有性能

#### 6.2 缓解措施

1. **渐进式迁移**：分阶段进行重构，保持系统稳定
2. **适配器模式**：为旧接口提供适配器
3. **全面测试**：确保每个阶段都有充分的测试
4. **性能监控**：持续监控性能指标

### 7. 总结

本重构方案解决了 `src\services\prompts\langgraph_integration.py` 模块的所有架构问题：

1. **职责分离**：将工作流构建功能移至工作流层，提示词配置保留在服务层
2. **消除冗余**：利用现有的模板系统和构建器，避免功能重复
3. **架构合规**：遵循扁平化架构原则，保持正确的依赖关系
4. **提高可维护性**：清晰的模块划分和接口设计

通过这个重构方案，系统将具有更好的可扩展性、可维护性和可测试性。新架构完全移除了历史包袱，提供了清晰、现代化的设计。