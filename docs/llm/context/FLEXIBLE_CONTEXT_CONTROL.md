# 提示词存储与构建模块及灵活上下文控制

## 概述

本项目采用分层架构管理提示词系统，支持静态提示词存储、动态提示词构建和灵活的上下文控制。通过提示词注册表、加载器和注入器实现提示词的统一管理，通过状态转换机制实现上下文的灵活控制。

## 提示词存储模块

### 1. 静态提示词文件
- **位置**: `configs/prompts/`
- **目录结构**:
  - `system/`: 系统提示词 (assistant.md, coder/)
  - `rules/`: 规则提示词 (safety.md, format.md)  
  - `user_commands/`: 用户指令 (data_analysis.md, code_review.md)
- **格式支持**:
  - **简单提示词**: 单个Markdown文件
  - **复合提示词**: 目录结构，包含index.md和章节文件（如01_code_style.md）
  - **元信息**: 支持YAML front matter定义描述等元信息

### 2. 配置文件
- **文件**: `configs/prompts.yaml`
- **功能**: 定义提示词注册表，将提示词名称映射到文件路径
- **配置示例**:
```yaml
system:
  - name: assistant
    path: configs/prompts/system/assistant.md
    description: 通用助手系统提示词
  - name: coder
    path: configs/prompts/system/coder/
    description: 代码生成专家系统提示词
    is_composite: true
```

## 提示词构建模块

### 1. PromptRegistry（提示词注册表）
- **功能**: 管理所有可用提示词的元信息
- **接口**: `IPromptRegistry`
- **核心方法**:
  - `get_prompt_meta(category, name)`: 获取提示词元信息
  - `list_prompts(category)`: 列出指定类别的所有提示词
  - `register_prompt(category, meta)`: 注册新提示词
- **特点**: 从配置文件加载，支持运行时验证

### 2. PromptLoader（提示词加载器）
- **功能**: 从文件系统加载提示词内容，支持缓存
- **接口**: `IPromptLoader`
- **核心方法**:
  - `load_prompt(category, name)`: 加载指定提示词内容
  - `load_simple_prompt(file_path)`: 加载简单提示词
  - `load_composite_prompt(dir_path)`: 加载复合提示词（合并目录下所有章节）
  - `clear_cache()`: 清空缓存
- **特点**: 自动缓存以提升性能，支持复合提示词的合并

### 3. PromptInjector（提示词注入器）
- **功能**: 将提示词注入工作流状态
- **接口**: `IPromptInjector`
- **核心方法**:
  - `inject_prompts(state, config)`: 批量注入多种类型提示词
  - `inject_system_prompt(state, prompt_name)`: 注入系统提示词
  - `inject_rule_prompts(state, rule_names)`: 注入规则提示词
  - `inject_user_command(state, command_name)`: 注入用户指令
- **特点**: 按照预定义顺序插入消息列表，确保正确的提示词结构

### 4. PromptConfig（提示词配置）
- **功能**: 定义提示词注入的配置
- **字段**:
  - `system_prompt`: 系统提示词名称
  - `rules`: 规则提示词列表
  - `user_command`: 用户指令名称
  - `cache_enabled`: 是否启用缓存

### 5. LangGraph集成
- **功能**: 在工作流中集成提示词管理
- **实现**: `langgraph_integration.py`
- **组件**:
  - `create_agent_workflow()`: 创建包含提示词注入节点的工作流
  - `create_simple_workflow()`: 创建简单提示词注入工作流

## 灵活上下文控制机制

### 1. 工具执行结果格式化与使用
- **存储**: 工具执行结果存储在状态的 `tool_results` 字段中
- **格式化**: `LLMNode._format_tool_results()` 方法将结果格式化为文本
- **插入**: 在构建系统提示词时，可通过配置 `include_tool_results` 选项决定是否包含工具结果
- **控制**: 支持自定义格式化逻辑和选择性包含

### 2. 消息历史管理
- **存储**: 消息存储在状态的 `messages` 列表中
- **类型**: 支持 SystemMessage、HumanMessage、AIMessage、ToolMessage
- **截断**: `LLMNode._truncate_messages_for_context()` 支持根据上下文窗口大小截断历史消息
- **配置**: 可通过 `context_window_size` 和 `max_message_history` 配置控制消息数量

### 3. 动态模板替换
- **实现**: `LLMNode._process_prompt_template()` 方法
- **变量**: 支持如下动态变量替换:
  - `{max_iterations}`: 最大迭代次数
  - `{current_step}`: 当前步骤
  - `{tool_results_count}`: 工具结果数量
  - `{messages_count}`: 消息数量
- **扩展**: 支持自定义模板变量

### 4. 选择性上下文提取

#### 4.1 提取特定工具调用结果
- **实现**: `ToolNode._extract_tool_calls()` 方法从最后一条消息中提取工具调用
- **支持格式**:
  - LangChain标准格式的 `tool_calls`
  - OpenAI格式的 `additional_kwargs["tool_calls"]`
  - 字典格式的 `tool_calls`
  - 文本解析（后备方案）
- **自定义**: 可以扩展此方法以支持特定工具结果的过滤

#### 4.2 获取LLM节点最后一次回复
- **实现**: 访问 `state["messages"][-1]` 获取最后一条消息
- **过滤**: 通过消息类型判断是否为AI回复
- **代码示例**:
```python
def get_last_ai_response(state: WorkflowState) -> Optional[str]:
    """获取最后一次AI回复"""
    messages = state.get("messages", [])
    for message in reversed(messages):
        if (hasattr(message, 'type') and message.type == 'ai') or \
           (isinstance(message, dict) and message.get('type') == 'ai'):
            return message.content
    return None
```

#### 4.3 提取全局参数
- **存储位置**: 
  - `state["metadata"]`: 元数据
  - `state["execution_context"]`: 执行上下文
  - `state["custom_fields"]`: 自定义字段
- **访问方式**: 通过标准字典访问 `state["field_name"]`

### 5. 状态适配器上下文控制
- **实现**: `StateAdapter` 类提供状态转换
- **功能**: 
  - 在图状态与域状态间转换
  - 支持自定义字段映射
  - 保持上下文完整性

### 6. 自定义上下文过滤器
可以实现自定义过滤器以实现更精细的控制：

```python
# 示例：只使用最近一次AI回复和特定工具结果的上下文过滤器
def custom_context_filter(state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
    """自定义上下文过滤器"""
    filtered_state = state.copy()
    
    # 只保留最后一次AI消息
    if config.get("use_last_ai_response_only", False):
        messages = state.get("messages", [])
        last_ai_message = None
        for message in reversed(messages):
            if hasattr(message, 'type') and message.type == 'ai':
                last_ai_message = message
                break
        if last_ai_message:
            filtered_state["messages"] = [last_ai_message]
    
    # 只保留特定工具结果
    if "specific_tool_results" in config:
        tool_results = state.get("tool_results", [])
        specific_tools = config["specific_tool_results"]
        filtered_tool_results = [
            tr for tr in tool_results
            if tr.get("tool_name") in specific_tools
        ]
        filtered_state["tool_results"] = filtered_tool_results
    
    # 只保留特定全局参数
    if "required_globals" in config:
        required_keys = config["required_globals"]
        filtered_metadata = {
            k: v for k, v in state.get("metadata", {}).items()
            if k in required_keys
        }
        filtered_state["metadata"] = filtered_metadata
    
    return filtered_state
```

## 最佳实践

1. **提示词组织**: 按功能和用途分类存储在不同目录
2. **复合提示词**: 使用数字前缀文件组织章节顺序
3. **模板变量**: 使用有意义的变量名便于维护
4. **上下文控制**: 根据场景需求合理配置上下文大小
5. **缓存策略**: 对于频繁使用的提示词启用缓存
6. **错误处理**: 提供后备方案处理提示词加载失败

## 总结

本项目通过模块化的提示词管理系统，实现了从静态存储到动态构建的完整流程，并通过灵活的状态管理机制支持多样化的上下文控制需求。通过组合使用提示词模块、消息过滤机制和自定义过滤器，可以实现精确的上下文控制，满足各种复杂的AI工作流需求。