基于对当前系统的分析，我来详细回答关于提示词系统集成和工具调用提示词引导的设计问题。

## 当前提示词系统集成架构分析

### 1. 提示词系统集成层次

当前系统采用**分层架构**，提示词集成主要在以下层次：

- **接口层** (`src/interfaces/prompts/`)：定义提示词注入器接口 [`IPromptInjector`](src/interfaces/prompts/injector.py:78)
- **核心层** (`src/core/workflow/graph/nodes/llm_node.py`)：LLM节点集成提示词系统
- **服务层** (`src/services/prompts/`)：提供提示词处理服务
- **基础设施层** (`src/infrastructure/tools/formatters/`)：工具格式化器实现

### 2. 工具调用提示词引导的层次定位

根据当前架构，工具调用提示词引导应定位为：

**基础设施层组件**，具体理由：
- 工具格式化器 [`ToolFormatter`](src/infrastructure/tools/formatters/formatter.py:241) 已存在于基础设施层
- 负责将工具信息转换为LLM可理解的格式
- 与具体的LLM客户端实现解耦

### 3. LLM配置中function_calling参数的作用

从 [`configs/llms/provider/openai/common.yaml:28`](configs/llms/provider/openai/common.yaml:28) 可见：
```yaml
features:
  function_calling: true
```

该参数的核心作用：
- **能力检测**：通过 [`supports_function_calling()`](src/core/llm/clients/openai/interfaces.py:69) 方法判断LLM是否支持原生function calling
- **策略选择**：影响工具格式化器选择何种策略（function calling vs 结构化输出）
- **格式适配**：决定是否需要在提示词中添加工具调用引导

### 4. JSONL格式化器集成方案

基于JSONL设计文档，集成方案应：

**策略选择逻辑**：
```python
def detect_tool_calling_support(llm_client: ILLMClient) -> str:
    if llm_client.supports_function_calling():
        return "function_calling"
    elif llm_client.supports_jsonl():  # 新增
        return "jsonl"
    else:
        return "structured_output"
```

**提示词模板层次**：
- **Function Calling**：原生API支持，无需额外提示词
- **JSONL**：需要批量工具调用提示词引导
- **结构化输出**：需要单行JSON提示词引导

### 5. LLM节点工具调用配置选项设计

**必要配置选项**：
```yaml
llm_node:
  tool_calling:
    enabled: true  # 是否启用工具调用
    strategy: "auto"  # auto|function_calling|jsonl|structured_output
    batch_support: true  # 是否支持批量调用
    fallback_on_failure: true  # 失败时是否回退
```

**配置优先级**：
1. 节点级配置（最高优先级）
2. LLM客户端能力检测
3. 系统默认配置

### 6. 提示词系统集成策略

**分层集成策略**：

1. **基础设施层**：实现JSONL格式化器
2. **核心层**：LLM节点添加工具调用配置
3. **服务层**：提示词服务支持工具调用模板
4. **接口层**：扩展工具格式化器接口

**动态提示词生成**：
```python
def generate_tool_prompt(tools: Sequence[ITool], format_type: str) -> str:
    if format_type == "function_calling":
        return ""  # 原生支持，无需提示词
    elif format_type == "jsonl":
        return generate_jsonl_prompt(tools)  # JSONL格式引导
    else:
        return generate_single_json_prompt(tools)  # 单行JSON引导
```

### 7. LLM节点工具使用配置选项必要性分析

**强烈建议添加**，原因：

1. **避免误用**：防止在不支持工具的LLM上错误添加工具提示词
2. **性能优化**：不需要工具的场景避免不必要的提示词处理
3. **灵活性**：支持同一工作流中混合使用支持/不支持工具的LLM节点
4. **向后兼容**：保持现有配置的兼容性

**推荐配置结构**：
```yaml
llm_node:
  tools:
    enabled: false  # 默认关闭，显式启用
    available_tools: []  # 可用工具列表
    calling_strategy: "auto"  # 调用策略
    prompt_injection: "auto"  # 提示词注入策略
```

## 总结

基于当前架构分析，建议：

1. **保持分层架构**：JSONL格式化器作为基础设施层组件
2. **动态策略选择**：基于LLM配置中的function_calling参数和能力检测
3. **显式配置控制**：为LLM节点添加工具使用配置选项，避免误用
4. **渐进式集成**：优先实现JSONL格式化器，再逐步集成到提示词系统

这种设计既保持了架构的一致性，又提供了足够的灵活性来支持不同能力的LLM模型。