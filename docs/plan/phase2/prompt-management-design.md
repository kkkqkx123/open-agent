# 提示词管理模块详细设计

## 模块概述

**模块名称**：提示词管理  
**开发周期**：4天  
**依赖模块**：配置系统、基础架构  
**目标**：实现提示词的资产化管理，支持简单/复合提示词，提供统一的注册、加载、合并机制

## 1. 架构设计

### 1.1 模块结构
```
src/prompts/
├── __init__.py
├── interfaces.py          # 核心接口定义
├── registry.py           # PromptRegistry实现
├── loader.py             # PromptLoader实现
├── injector.py           # PromptInjector实现
├── models.py             # 数据模型定义
├── assets/               # 提示词资产目录
│   ├── system/           # 系统提示词
│   ├── rules/            # 规则提示词
│   └── user_commands/    # 用户指令
└── utils/
    ├── __init__.py
    ├── file_loader.py    # 文件加载工具
    └── merger.py         # 提示词合并工具
```

### 1.2 核心接口定义

#### IPromptRegistry
```python
class IPromptRegistry(ABC):
    """提示词注册表接口"""
    
    @abstractmethod
    def get_prompt_meta(self, category: str, name: str) -> PromptMeta:
        """获取提示词元信息"""
        pass
        
    @abstractmethod
    def list_prompts(self, category: str) -> list[PromptMeta]:
        """列出指定类别的所有提示词"""
        pass
        
    @abstractmethod
    def register_prompt(self, category: str, meta: PromptMeta) -> None:
        """注册提示词"""
        pass
        
    @abstractmethod
    def validate_registry(self) -> bool:
        """验证注册表完整性"""
        pass
```

#### IPromptLoader
```python
class IPromptLoader(ABC):
    """提示词加载器接口"""
    
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        """加载提示词内容"""
        pass
        
    @abstractmethod
    def load_simple_prompt(self, file_path: Path) -> str:
        """加载简单提示词"""
        pass
        
    @abstractmethod
    def load_composite_prompt(self, dir_path: Path) -> str:
        """加载复合提示词"""
        pass
        
    @abstractmethod
    def clear_cache(self) -> None:
        """清空缓存"""
        pass
```

#### IPromptInjector
```python
class IPromptInjector(ABC):
    """提示词注入器接口"""
    
    @abstractmethod
    def inject_prompts(self, state: AgentState, config: AgentConfig) -> AgentState:
        """将提示词注入Agent状态"""
        pass
        
    @abstractmethod
    def inject_system_prompt(self, state: AgentState, prompt_name: str) -> AgentState:
        """注入系统提示词"""
        pass
        
    @abstractmethod
    def inject_rule_prompts(self, state: AgentState, rule_names: list[str]) -> AgentState:
        """注入规则提示词"""
        pass
        
    @abstractmethod
    def inject_user_command(self, state: AgentState, command_name: str) -> AgentState:
        """注入用户指令"""
        pass
```

## 2. 数据模型

### 2.1 提示词元信息
```python
@dataclass
class PromptMeta:
    """提示词元信息"""
    name: str                    # 提示词名称
    category: str               # 类别：system/rules/user_commands
    path: Path                  # 文件或目录路径
    description: str            # 描述
    is_composite: bool          # 是否为复合提示词
    created_at: datetime        # 创建时间
    updated_at: datetime        # 更新时间
    
    def validate_path(self) -> bool:
        """验证路径是否存在"""
        return self.path.exists()
```

### 2.2 提示词配置
```python
@dataclass
class PromptConfig:
    """提示词配置"""
    system_prompt: Optional[str] = None      # 系统提示词名称
    rules: list[str] = field(default_factory=list)  # 规则提示词列表
    user_command: Optional[str] = None       # 用户指令名称
    cache_enabled: bool = True               # 是否启用缓存
```

## 3. 提示词资产结构

### 3.1 目录结构
```
prompts/
├── system/                   # 系统提示词
│   ├── assistant.md         # 简单提示词
│   └── coder/               # 复合提示词目录
│       ├── index.md         # 主文件
│       ├── 01_code_style.md # 子章节1
│       └── 02_error_handling.md # 子章节2
├── rules/                   # 规则提示词
│   ├── safety.md           # 安全规则
│   └── format.md           # 格式规则
└── user_commands/          # 用户指令
    ├── data_analysis.md    # 数据分析指令
    └── code_review.md      # 代码审查指令
```

### 3.2 简单提示词格式
```markdown
---
description: 通用助手提示词，定义Agent基础角色
---
你是一个通用助手，负责解答用户问题，语言简洁明了。
```

### 3.3 复合提示词格式
```markdown
# coder/index.md
---
description: 代码生成专家系统提示词
---
你是一个代码生成专家，负责生成高质量、可维护的代码。

# coder/01_code_style.md
---
description: 代码风格规范
---
请遵循以下代码风格：
- 使用PEP8规范
- 添加适当的注释
- 使用有意义的变量名

# coder/02_error_handling.md
---
description: 错误处理规范
---
代码中必须包含适当的错误处理逻辑：
- 使用try-except处理可能失败的代码
- 提供有意义的错误信息
- 确保资源正确释放
```

## 4. 注册表实现

### 4.1 注册表配置
```yaml
# configs/prompt_registry.yaml
system:
  - name: assistant
    path: prompts/system/assistant.md
    description: 通用助手系统提示词
  - name: coder
    path: prompts/system/coder/
    description: 代码生成专家系统提示词
    is_composite: true

rules:
  - name: safety
    path: prompts/rules/safety.md
    description: 安全规则提示词
  - name: format
    path: prompts/rules/format.md
    description: 输出格式规则提示词

user_commands:
  - name: data_analysis
    path: prompts/user_commands/data_analysis.md
    description: 数据分析用户指令
  - name: code_review
    path: prompts/user_commands/code_review.md
    description: 代码审查用户指令
```

### 4.2 PromptRegistry实现
```python
class PromptRegistry(IPromptRegistry):
    """提示词注册表实现"""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self._registry: dict[str, dict[str, PromptMeta]] = {
            "system": {},
            "rules": {},
            "user_commands": {}
        }
        self._load_registry()
        
    def _load_registry(self) -> None:
        """加载注册表配置"""
        registry_config = self.config_loader.load_prompt_registry()
        
        for category, prompts in registry_config.items():
            for prompt_data in prompts:
                meta = PromptMeta(
                    name=prompt_data["name"],
                    category=category,
                    path=Path(prompt_data["path"]),
                    description=prompt_data["description"],
                    is_composite=prompt_data.get("is_composite", False),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 检查重名
                if meta.name in self._registry[category]:
                    raise ValueError(f"提示词名称重复: {category}.{meta.name}")
                    
                self._registry[category][meta.name] = meta
                
    def validate_registry(self) -> bool:
        """验证注册表完整性"""
        for category, prompts in self._registry.items():
            for name, meta in prompts.items():
                if not meta.validate_path():
                    raise FileNotFoundError(f"提示词文件不存在: {meta.path}")
                    
        return True
```

## 5. 加载器实现

### 5.1 PromptLoader实现
```python
class PromptLoader(IPromptLoader):
    """提示词加载器实现"""
    
    def __init__(self, registry: IPromptRegistry):
        self.registry = registry
        self._cache: dict[str, str] = {}
        
    def load_prompt(self, category: str, name: str) -> str:
        """加载提示词内容"""
        cache_key = f"{category}.{name}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        # 获取元信息
        meta = self.registry.get_prompt_meta(category, name)
        
        # 加载提示词
        if meta.is_composite:
            content = self.load_composite_prompt(meta.path)
        else:
            content = self.load_simple_prompt(meta.path)
            
        # 缓存结果
        self._cache[cache_key] = content
        return content
        
    def load_simple_prompt(self, file_path: Path) -> str:
        """加载简单提示词"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # 移除元信息部分（如果有）
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
                
        return content
        
    def load_composite_prompt(self, dir_path: Path) -> str:
        """加载复合提示词"""
        # 加载主文件
        index_file = dir_path / "index.md"
        if not index_file.exists():
            raise FileNotFoundError(f"复合提示词缺少index.md: {dir_path}")
            
        content = self.load_simple_prompt(index_file)
        
        # 加载子章节文件
        chapter_files = []
        for file_path in dir_path.iterdir():
            if file_path.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                chapter_files.append(file_path)
                
        # 按文件名排序
        chapter_files.sort()
        
        # 合并内容
        for chapter_file in chapter_files:
            chapter_content = self.load_simple_prompt(chapter_file)
            content += f"\n\n---\n\n{chapter_content}"
            
        return content
```

## 6. 注入器实现

### 6.1 PromptInjector实现
```python
class PromptInjector(IPromptInjector):
    """提示词注入器实现"""
    
    def __init__(self, loader: IPromptLoader):
        self.loader = loader
        
    def inject_prompts(self, state: AgentState, config: AgentConfig) -> AgentState:
        """将提示词注入Agent状态"""
        # 注入系统提示词
        if config.system_prompt:
            state = self.inject_system_prompt(state, config.system_prompt)
            
        # 注入规则提示词
        if config.rules:
            state = self.inject_rule_prompts(state, config.rules)
            
        # 注入用户指令
        if config.user_command:
            state = self.inject_user_command(state, config.user_command)
            
        return state
        
    def inject_system_prompt(self, state: AgentState, prompt_name: str) -> AgentState:
        """注入系统提示词"""
        prompt_content = self.loader.load_prompt("system", prompt_name)
        system_message = SystemMessage(content=prompt_content)
        state.messages.insert(0, system_message)  # 系统消息在最前面
        return state
        
    def inject_rule_prompts(self, state: AgentState, rule_names: list[str]) -> AgentState:
        """注入规则提示词"""
        for rule_name in rule_names:
            rule_content = self.loader.load_prompt("rules", rule_name)
            rule_message = SystemMessage(content=rule_content)
            state.messages.append(rule_message)  # 规则消息在系统消息之后
            
        return state
        
    def inject_user_command(self, state: AgentState, command_name: str) -> AgentState:
        """注入用户指令"""
        command_content = self.loader.load_prompt("user_commands", command_name)
        user_message = HumanMessage(content=command_content)
        state.messages.append(user_message)  # 用户指令在最后
        return state
```

## 7. LangGraph集成

### 7.1 Agent状态定义
```python
@dataclass
class AgentState:
    """Agent状态定义"""
    messages: list[BaseMessage] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    current_step: str = ""
    max_iterations: int = 10
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self.messages.append(message)
```

### 7.2 工作流节点集成
```python
def create_agent_workflow(
    prompt_injector: IPromptInjector,
    tool_executor: IToolExecutor,
    llm_client: ILLMClient
) -> StateGraph:
    """创建Agent工作流"""
    
    def inject_prompts_node(state: AgentState) -> AgentState:
        """提示词注入节点"""
        config = get_agent_config()  # 从配置获取
        return prompt_injector.inject_prompts(state, config)
        
    def call_llm_node(state: AgentState) -> AgentState:
        """LLM调用节点"""
        # 使用注入后的提示词调用LLM
        response = llm_client.generate(state.messages)
        state.add_message(response)
        return state
        
    # 构建工作流
    workflow = StateGraph(AgentState)
    
    workflow.add_node("inject_prompts", inject_prompts_node)
    workflow.add_node("call_llm", call_llm_node)
    
    workflow.set_entry_point("inject_prompts")
    workflow.add_edge("inject_prompts", "call_llm")
    
    return workflow.compile()
```

## 8. 配置管理

### 8.1 Agent配置示例
```yaml
# configs/agents/data_analyst.yaml
name: data_analyst
description: 数据分析专家Agent
system_prompt: coder
rules:
  - safety
  - format
user_command: data_analysis
llm_config: openai-gpt4
tool_sets:
  - data_analysis_set
```

## 9. 测试策略

### 9.1 单元测试
```python
class TestPromptRegistry:
    def test_registry_loading(self):
        """测试注册表加载"""
        registry = PromptRegistry(mock_config_loader)
        assert registry.validate_registry()
        
    def test_duplicate_prompt(self):
        """测试重复提示词检测"""
        # 测试重名提示词的检测
        pass

class TestPromptLoader:
    def test_simple_prompt_loading(self):
        """测试简单提示词加载"""
        loader = PromptLoader(mock_registry)
        content = loader.load_prompt("system", "assistant")
        assert len(content) > 0
        
    def test_composite_prompt_loading(self):
        """测试复合提示词加载"""
        loader = PromptLoader(mock_registry)
        content = loader.load_prompt("system", "coder")
        assert "代码生成专家" in content
        assert "PEP8规范" in content
```

### 9.2 集成测试
```python
class TestPromptIntegration:
    def test_end_to_end_injection(self):
        """测试端到端提示词注入"""
        registry = PromptRegistry(config_loader)
        loader = PromptLoader(registry)
        injector = PromptInjector(loader)
        
        state = AgentState()
        config = AgentConfig(
            system_prompt="assistant",
            rules=["safety"],
            user_command="data_analysis"
        )
        
        state = injector.inject_prompts(state, config)
        assert len(state.messages) == 3  # 系统 + 规则 + 用户指令
```

## 10. 实施计划

### 第1天：基础架构
- 定义核心接口和数据模型
- 实现提示词注册表
- 创建示例提示词资产

### 第2天：加载器实现
- 实现简单提示词加载
- 实现复合提示词加载和合并
- 添加缓存机制

### 第3天：注入器实现
- 实现提示词注入器
- 集成LangGraph工作流
- 配置管理和验证

### 第4天：测试和优化
- 编写单元测试和集成测试
- 性能测试和缓存优化
- 创建使用示例和文档

## 11. 关键特性

### 11.1 缓存机制
- 内存缓存避免重复文件读取
- 支持手动清空缓存
- 缓存键基于类别和名称

### 11.2 错误处理
- 文件不存在时的明确错误信息
- 重名提示词的检测和报错
- 格式错误的优雅处理

### 11.3 性能优化
- 懒加载机制
- 缓存命中率监控
- 大文件的分块读取

---
*文档版本：V1.0*
*创建日期：2025-10-19*