# LLM节点提示词配置实用指南

## 概述

本指南详细介绍如何为工作流中的LLM节点配置专门的提示词，包括各种配置方式、最佳实践和实际示例。

## LLM节点提示词配置方式

### 1. 基础配置方式

#### 1.1 直接系统提示词配置

最简单的方式是直接在节点配置中指定系统提示词：

```yaml
nodes:
  analysis_node:
    type: "llm_node"
    config:
      system_prompt: "你是一个专业的数据分析助手，请分析提供的数据并给出洞察。"
      temperature: 0.3
      max_tokens: 2000
```

**适用场景**:
- 简单的、一次性的提示词
- 不需要复用的特定场景
- 快速原型和测试

**优点**:
- 简单直观
- 无需额外文件
- 配置集中

**缺点**:
- 难以复用
- 不利于维护
- 缺乏版本管理

#### 1.2 提示词ID配置 (推荐)

使用预定义的提示词ID：

```yaml
nodes:
  analysis_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.data_analyst"
      temperature: 0.3
      max_tokens: 2000
```

对应的提示词文件 `configs/prompts/system/data_analyst.md`:

```markdown
---
description: 专业数据分析助手提示词
priority: high
tags: [analysis, data, professional]
variables:
  - name: analysis_type
    type: string
    description: 分析类型
  - name: data_format
    type: string
    description: 数据格式
---

你是一个专业的数据分析助手，具有以下能力：
1. 深度分析各种类型的数据
2. 发现数据中的模式和趋势
3. 提供数据驱动的洞察和建议
4. 清晰地解释分析结果

当前分析类型: {{analysis_type}}
数据格式: {{data_format}}

请基于提供的数据进行全面分析。
```

**适用场景**:
- 需要复用的提示词
- 复杂的提示词逻辑
- 需要版本管理的场景

**优点**:
- 可复用性强
- 易于维护和更新
- 支持变量和模板
- 集中管理

**缺点**:
- 需要额外的文件管理
- 学习成本稍高

### 2. 高级配置方式

#### 2.1 混合配置

结合直接配置和ID配置：

```yaml
nodes:
  analysis_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.data_analyst"
      user_input: "请分析以下{{data_type}}数据: {{raw_data}}"
      prompt_variables:
        analysis_type: "statistical"
        data_format: "json"
        data_type: "销售"
        raw_data: "{{workflow.input_data}}"
```

#### 2.2 多提示词组合

使用多个提示词ID构建复杂提示：

```yaml
nodes:
  code_review_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.code_reviewer"
      prompt_ids:
        - "rules.code_style"
        - "rules.security"
        - "user_commands.code_review"
      prompt_variables:
        language: "python"
        focus_areas: ["performance", "security", "readability"]
```

#### 2.3 条件提示词配置

基于条件选择不同的提示词：

```yaml
nodes:
  adaptive_node:
    type: "llm_node"
    config:
      system_prompt_id: "{{#if state.complexity}}system.expert_analyst{{else}}system.basic_assistant{{/if}}"
      prompt_variables:
        complexity: "{{workflow.task_complexity}}"
```

## 提示词变量系统

### 1. 变量类型

#### 1.1 系统变量

自动提供的系统变量：

```yaml
nodes:
  example_node:
    type: "llm_node"
    config:
      system_prompt: |
        节点ID: {{node_id}}
        工作流ID: {{workflow_id}}
        工作流名称: {{workflow_name}}
        执行时间: {{timestamp}}
```

#### 1.2 状态变量

从工作流状态中获取的变量：

```yaml
nodes:
  context_node:
    type: "llm_node"
    config:
      system_prompt: |
        用户查询: {{state.user_query}}
        上下文: {{state.context}}
        历史消息数: {{state.messages.length}}
```

#### 1.3 配置变量

在节点配置中定义的变量：

```yaml
nodes:
  configured_node:
    type: "llm_node"
    config:
      system_prompt: |
        任务类型: {{task_type}}
        专业领域: {{domain}}
        输出格式: {{output_format}}
      prompt_variables:
        task_type: "数据分析"
        domain: "金融"
        output_format: "markdown"
```

### 2. 变量处理

#### 2.1 默认值

为变量提供默认值：

```yaml
nodes:
  node_with_defaults:
    type: "llm_node"
    config:
      system_prompt: |
        语言: {{language | default: "中文"}}
        详细程度: {{detail_level | default: "中等"}}
```

#### 2.2 变量转换

对变量进行格式转换：

```yaml
nodes:
  transformed_node:
    type: "llm_node"
    config:
      system_prompt: |
        金额: {{amount | currency: "CNY"}}
        日期: {{date | date: "YYYY-MM-DD"}}
        列表: {{items | join: ", "}}
```

#### 2.3 条件变量

基于条件显示不同内容：

```yaml
nodes:
  conditional_node:
    type: "llm_node"
    config:
      system_prompt: |
        {{#if is_expert_mode}}
        你是专家级别的助手，请提供深度分析。
        {{else}}
        你是普通助手，请提供简洁回答。
        {{/if}}
```

## 提示词引用系统

### 1. 基础引用

引用其他提示词：

```yaml
nodes:
  reference_node:
    type: "llm_node"
    config:
      system_prompt: |
        {{ref:system.base_assistant}}
        
        特别注意：{{ref:rules.safety}}
```

### 2. 参数化引用

向引用的提示词传递参数：

```yaml
nodes:
  param_ref_node:
    type: "llm_node"
    config:
      system_prompt: |
        {{ref:system.domain_expert:domain="金融",level="高级"}}
        
        请遵循以下规则：{{ref:rules.professional:field="金融"}}
```

### 3. 嵌套引用

引用的提示词可以包含其他引用：

```markdown
<!-- configs/prompts/system/comprehensive_analyst.md -->
---
description: 综合分析师提示词
---

你是一个综合分析师，具备以下专业能力：

{{ref:system.data_analyst}}
{{ref:system.business_analyst}}
{{ref:system.technical_analyst}}

请综合运用以上能力进行全面分析。
```

## 实际应用示例

### 1. 数据分析工作流

#### 1.1 工作流配置

```yaml
workflow:
  name: "data_analysis_workflow"
  description: "数据分析工作流"

nodes:
  data_validation_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.data_validator"
      prompt_variables:
        data_types: ["csv", "json", "xml"]
        validation_rules: ["completeness", "consistency", "accuracy"]

  analysis_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.data_analyst"
      prompt_ids:
        - "rules.analysis_methodology"
        - "user_commands.data_analysis"
      prompt_variables:
        analysis_type: "{{workflow.analysis_type}}"
        focus_areas: "{{workflow.focus_areas}}"

  report_generation_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.report_generator"
      user_input: |
        基于以下分析结果生成报告：
        {{state.analysis_results}}
        
        报告要求：
        - 格式：{{report_format}}
        - 详细程度：{{detail_level}}
        - 目标受众：{{audience}}
      prompt_variables:
        report_format: "markdown"
        detail_level: "详细"
        audience: "业务决策者"
```

#### 1.2 提示词文件

**configs/prompts/system/data_validator.md**:
```markdown
---
description: 数据验证助手
priority: high
---

你是一个数据验证专家，负责检查数据质量和完整性。

验证标准：
{{#each validation_rules}}
- {{this}}
{{/each}}

支持的数据类型：
{{#each data_types}}
- {{this}}
{{/each}}

请仔细检查提供的数据，识别任何问题并提供修复建议。
```

**configs/prompts/system/data_analyst.md**:
```markdown
---
description: 数据分析助手
priority: high
---

你是一个专业的数据分析师，擅长从数据中发现洞察和模式。

分析方法：
1. 数据概览和描述性统计
2. 趋势分析和模式识别
3. 异常值检测和处理
4. 相关性分析和因果推断
5. 可视化建议

当前分析类型：{{analysis_type}}
重点关注：{{focus_areas}}

请提供全面的数据分析报告。
```

### 2. 代码审查工作流

#### 2.1 工作流配置

```yaml
workflow:
  name: "code_review_workflow"
  description: "自动化代码审查工作流"

nodes:
  syntax_check_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.syntax_checker"
      prompt_variables:
        language: "{{workflow.language}}"
        framework: "{{workflow.framework}}"

  security_review_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.security_reviewer"
      prompt_ids:
        - "rules.security"
        - "rules.{{workflow.language}}_security"
      prompt_variables:
        security_level: "high"

  performance_review_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.performance_reviewer"
      user_input: |
        代码片段：
        {{workflow.code_snippet}}
        
        请分析性能并提供优化建议。
      prompt_variables:
        optimization_targets: ["speed", "memory", "scalability"]

  final_review_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.final_reviewer"
      prompt_ids:
        - "rules.code_style"
        - "rules.best_practices"
      user_input: |
        综合以下审查结果：
        语法检查：{{state.syntax_results}}
        安全审查：{{state.security_results}}
        性能审查：{{state.performance_results}}
        
        请提供最终的代码审查报告。
```

### 3. 多语言客服工作流

#### 3.1 工作流配置

```yaml
workflow:
  name: "multilingual_support_workflow"
  description: "多语言客服工作流"

nodes:
  language_detection_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.language_detector"
      user_input: "检测以下消息的语言：{{workflow.user_message}}"
      prompt_variables:
        supported_languages: ["中文", "英文", "日文", "韩文"]

  intent_analysis_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.intent_analyzer"
      prompt_variables:
        language: "{{state.detected_language}}"
        intent_categories: ["查询", "投诉", "建议", "技术支持"]

  response_generation_node:
    type: "llm_node"
    config:
      system_prompt_id: "system.{{state.detected_language}}_assistant"
      prompt_ids:
        - "rules.{{state.detected_language}}_etiquette"
        - "user_commands.{{state.intent}}_response"
      user_input: |
        用户意图：{{state.intent}}
        用户消息：{{workflow.user_message}}
        上下文：{{state.context}}
      prompt_variables:
        response_style: "专业友好"
        include_suggestions: true
```

## 最佳实践

### 1. 提示词设计原则

#### 1.1 清晰性
- 使用明确的语言和结构
- 避免歧义和模糊表达
- 提供具体的示例和格式要求

#### 1.2 模块化
- 将复杂提示词分解为可重用模块
- 使用引用组合提示词
- 保持单一职责原则

#### 1.3 可维护性
- 使用有意义的命名
- 添加详细的元数据和注释
- 版本控制和变更追踪

### 2. 配置组织

#### 2.1 目录结构
```
configs/prompts/
├── system/              # 系统角色提示词
│   ├── general/         # 通用角色
│   ├── domain/          # 领域专家
│   └── language/        # 多语言助手
├── rules/               # 规则和约束
│   ├── format/          # 格式规则
│   ├── safety/          # 安全规则
│   └── quality/         # 质量标准
├── user_commands/       # 用户命令
│   ├── analysis/        # 分析任务
│   ├── generation/      # 生成任务
│   └── review/          # 审查任务
└── templates/           # 模板和片段
    ├── common/          # 通用模板
    └── specific/        # 特定模板
```

#### 2.2 命名规范
- 使用层次化命名：`category.subcategory.name`
- 保持描述性和一致性
- 使用下划线分隔单词

#### 2.3 版本管理
- 使用语义化版本号
- 记录变更历史
- 支持向后兼容

### 3. 性能优化

#### 3.1 缓存策略
- 缓存常用的提示词组合
- 使用适当的缓存过期策略
- 监控缓存命中率

#### 3.2 延迟加载
- 按需加载提示词文件
- 避免初始化时加载所有内容
- 使用异步加载

#### 3.3 预编译模板
- 预编译常用的模板
- 缓存编译结果
- 减少运行时开销

## 故障排除

### 1. 常见问题

#### 1.1 提示词未找到
**错误**: `PromptNotFoundError: 提示词 'xxx' 未找到`

**解决方案**:
1. 检查提示词ID是否正确
2. 确认提示词文件存在
3. 验证文件路径和命名
4. 检查配置文件中的扫描规则

#### 1.2 变量未解析
**错误**: 提示词中包含未解析的变量 `{{variable_name}}`

**解决方案**:
1. 检查变量名是否正确
2. 确认变量在上下文中存在
3. 验证变量传递路径
4. 检查变量作用域

#### 1.3 引用循环
**错误**: `CircularReferenceError: 检测到循环引用`

**解决方案**:
1. 检查引用链是否存在循环
2. 重构提示词结构
3. 使用条件引用避免循环
4. 简化引用关系

### 2. 调试技巧

#### 2.1 启用详细日志
```yaml
logging:
  level: "DEBUG"
  modules:
    - "src.core.workflow.services.prompt_service"
    - "src.services.config.prompt_config_service"
```

#### 2.2 验证配置
```python
from src.core.workflow.services.prompt_service import WorkflowPromptService

prompt_service = WorkflowPromptService()
errors = await prompt_service.validate_prompt_configuration(config)
if errors:
    print("配置错误:", errors)
```

#### 2.3 测试提示词
```python
from src.services.config import create_prompt_config_service

config_service = await create_prompt_config_service()
registry = await config_service.get_prompt_registry()

prompt = await registry.get("system.assistant")
print("提示词内容:", prompt.content)
```

## 总结

通过本指南，我们了解了LLM节点提示词配置的各种方式和最佳实践。关键要点：

1. **选择合适的配置方式**: 根据场景选择直接配置、ID配置或混合配置
2. **充分利用变量系统**: 使用系统变量、状态变量和配置变量
3. **合理使用引用系统**: 通过引用实现提示词的复用和组合
4. **遵循最佳实践**: 保持清晰性、模块化和可维护性
5. **注意性能优化**: 使用缓存、延迟加载和预编译

通过合理配置提示词，可以充分发挥LLM节点的能力，构建强大而灵活的工作流系统。