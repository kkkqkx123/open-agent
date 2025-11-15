# 配置文件结构和示例

## 概述

本文档提供了灵活条件边系统的完整配置文件结构和示例，包括路由函数配置、边配置和工作流配置。

## 配置文件结构

```
configs/edges/
├── _group.yaml                    # 边配置组配置
├── route_functions/               # 路由函数配置目录
│   ├── _group.yaml               # 路由函数组配置
│   ├── builtin.yaml              # 内置路由函数
│   ├── tool_based.yaml           # 基于工具的路由函数
│   ├── state_based.yaml          # 基于状态的路由函数
│   ├── message_based.yaml        # 基于消息的路由函数
│   └── custom.yaml               # 自定义路由函数
├── edge_types/                   # 边类型配置目录
│   ├── _group.yaml               # 边类型组配置
│   ├── conditional.yaml          # 条件边配置
│   └── simple.yaml               # 简单边配置
└── examples/                     # 配置示例目录
    ├── basic_workflow.yaml       # 基本工作流示例
    ├── complex_routing.yaml      # 复杂路由示例
    └── migration_example.yaml    # 迁移示例
```

## 配置文件详细内容

### 1. 边配置组配置

```yaml
# configs/edges/_group.yaml
name: "边配置组"
description: "边和路由函数的全局配置"
version: "1.0"

# 全局设置
global_settings:
  enable_validation: true
  strict_mode: false
  cache_functions: true
  auto_discovery: true

# 边类型定义
edge_types:
  - name: "simple"
    description: "简单边，直接连接两个节点"
    implementation: "builtin.simple"
    
  - name: "conditional"
    description: "条件边，基于路由函数决定路径"
    implementation: "builtin.conditional"
    required_fields:
      - "route_function"
    optional_fields:
      - "route_parameters"
      - "path_map"
      - "description"

# 路由函数分类
route_function_categories:
  - name: "builtin"
    description: "内置路由函数"
    path: "route_functions/builtin.yaml"
    
  - name: "tool"
    description: "基于工具的路由函数"
    path: "route_functions/tool_based.yaml"
    
  - name: "state"
    description: "基于状态的路由函数"
    path: "route_functions/state_based.yaml"
    
  - name: "message"
    description: "基于消息的路由函数"
    path: "route_functions/message_based.yaml"
    
  - name: "custom"
    description: "自定义路由函数"
    path: "route_functions/custom.yaml"

# 验证规则
validation_rules:
  route_function:
    - rule: "name_required"
      message: "路由函数名称不能为空"
    - rule: "name_pattern"
      pattern: "^[a-zA-Z][a-zA-Z0-9_]*$"
      message: "路由函数名称必须以字母开头，只能包含字母、数字和下划线"
      
  edge:
    - rule: "from_node_required"
      message: "起始节点不能为空"
    - rule: "conditional_requires_route_function"
      message: "条件边必须指定路由函数"
```

### 2. 路由函数组配置

```yaml
# configs/edges/route_functions/_group.yaml
name: "路由函数组配置"
description: "路由函数的全局配置和分类"

# 全局设置
global_settings:
  enable_parameter_validation: true
  strict_return_type_checking: false
  cache_enabled: true
  default_timeout: 30

# 参数类型定义
parameter_types:
  string:
    python_type: "str"
    validation:
      - type: "string"
  integer:
    python_type: "int"
    validation:
      - type: "integer"
  number:
    python_type: "float"
    validation:
      - type: "number"
  boolean:
    python_type: "bool"
    validation:
      - type: "boolean"
  array:
    python_type: "list"
    validation:
      - type: "array"
  object:
    python_type: "dict"
    validation:
      - type: "object"

# 返回值类型定义
return_value_types:
  - "continue"
  - "end"
  - "error"
  - "retry"
  - "skip"
  - "branch_1"
  - "branch_2"
  - "branch_3"

# 内置函数映射
builtin_functions:
  has_tool_calls: "src.infrastructure.graph.edges.builtin_routes.has_tool_calls"
  no_tool_calls: "src.infrastructure.graph.edges.builtin_routes.no_tool_calls"
  has_tool_results: "src.infrastructure.graph.edges.builtin_routes.has_tool_results"
  max_iterations_reached: "src.infrastructure.graph.edges.builtin_routes.max_iterations_reached"
  has_errors: "src.infrastructure.graph.edges.builtin_routes.has_errors"
  no_errors: "src.infrastructure.graph.edges.builtin_routes.no_errors"
```

### 3. 内置路由函数配置

```yaml
# configs/edges/route_functions/builtin.yaml
name: "内置路由函数"
description: "系统提供的内置路由函数"
category: "builtin"

route_functions:
  has_tool_calls:
    description: "检查是否有工具调用"
    parameters: {}
    return_values: ["continue", "end"]
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["tool", "basic"]
    
  no_tool_calls:
    description: "检查是否没有工具调用"
    parameters: {}
    return_values: ["continue", "end"]
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["tool", "basic"]
    
  has_tool_results:
    description: "检查是否有工具执行结果"
    parameters: {}
    return_values: ["continue", "end"]
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["tool", "result"]
    
  max_iterations_reached:
    description: "检查是否达到最大迭代次数"
    parameters:
      type: "object"
      properties:
        max_iterations:
          type: "integer"
          description: "最大迭代次数"
          default: 10
    return_values: ["continue", "end"]
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["iteration", "control"]
    
  has_errors:
    description: "检查是否有错误"
    parameters: {}
    return_values: ["continue", "error"]
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["error", "basic"]
    
  no_errors:
    description: "检查是否没有错误"
    parameters: {}
    return_values: ["continue", "error"]
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["error", "basic"]
```

### 4. 基于工具的路由函数

```yaml
# configs/edges/route_functions/tool_based.yaml
name: "基于工具的路由函数"
description: "基于工具调用状态的路由函数集合"
category: "tool"

route_functions:
  tool_call_count:
    description: "基于工具调用数量的路由"
    parameters:
      type: "object"
      properties:
        threshold:
          type: "integer"
          description: "阈值"
          default: 1
        comparison:
          type: "string"
          enum: ["equals", "greater_than", "less_than"]
          default: "greater_than"
      required: ["threshold"]
    return_values: ["single", "multiple", "none"]
    implementation: "config"
    type: "tool_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["tool", "count"]
    
  tool_type_router:
    description: "基于工具类型的路由"
    parameters:
      type: "object"
      properties:
        type_mapping:
          type: "object"
          description: "工具类型到路由的映射"
          default:
            "calculator": "calc_handler"
            "search": "search_handler"
            "database": "db_handler"
        default_route:
          type: "string"
          description: "默认路由"
          default: "default_handler"
    return_values: ["calc_handler", "search_handler", "db_handler", "default_handler"]
    implementation: "config"
    type: "tool_type_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["tool", "type"]
    
  tool_result_status:
    description: "基于工具执行结果状态的路由"
    parameters:
      type: "object"
      properties:
        check_success:
          type: "boolean"
          description: "是否检查成功状态"
          default: true
        check_error:
          type: "boolean"
          description: "是否检查错误状态"
          default: true
    return_values: ["success", "error", "partial", "no_results"]
    implementation: "config"
    type: "tool_result_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["tool", "result", "status"]
```

### 5. 基于状态的路由函数

```yaml
# configs/edges/route_functions/state_based.yaml
name: "基于状态的路由函数"
description: "基于工作流状态的路由函数集合"
category: "state"

route_functions:
  iteration_check:
    description: "基于迭代次数的路由"
    parameters:
      type: "object"
      properties:
        max_iterations:
          type: "integer"
          description: "最大迭代次数"
          default: 10
        comparison:
          type: "string"
          enum: ["equals", "greater_than", "greater_equal", "less_than", "less_equal"]
          default: "greater_equal"
      required: ["max_iterations"]
    return_values: ["continue", "max_reached", "exceeded"]
    implementation: "config"
    type: "state_check"
    state_key: "iteration_count"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["iteration", "control"]
    
  status_router:
    description: "基于状态值的路由"
    parameters:
      type: "object"
      properties:
        state_key:
          type: "string"
          description: "状态键名"
          default: "status"
        value_mapping:
          type: "object"
          description: "状态值到路由的映射"
          default:
            "success": "complete"
            "error": "error_handler"
            "pending": "continue"
            "failed": "retry"
        default_route:
          type: "string"
          description: "默认路由"
          default: "default_handler"
    return_values: ["complete", "error_handler", "continue", "retry", "default_handler"]
    implementation: "config"
    type: "state_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["state", "status"]
    
  threshold_check:
    description: "基于阈值的路由"
    parameters:
      type: "object"
      properties:
        state_key:
          type: "string"
          description: "状态键名"
        threshold:
          type: "number"
          description: "阈值"
        comparison:
          type: "string"
          enum: ["greater_than", "less_than", "equals"]
          default: "greater_than"
        true_route:
          type: "string"
          description: "条件为真时的路由"
          default: "above_threshold"
        false_route:
          type: "string"
          description: "条件为假时的路由"
          default: "below_threshold"
      required: ["state_key", "threshold"]
    return_values: ["above_threshold", "below_threshold"]
    implementation: "config"
    type: "state_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["state", "threshold"]
```

### 6. 基于消息的路由函数

```yaml
# configs/edges/route_functions/message_based.yaml
name: "基于消息的路由函数"
description: "基于消息内容的路由函数集合"
category: "message"

route_functions:
  keyword_match:
    description: "基于关键词匹配的路由"
    parameters:
      type: "object"
      properties:
        keywords:
          type: "array"
          items:
            type: "string"
          description: "关键词列表"
        case_sensitive:
          type: "boolean"
          description: "是否区分大小写"
          default: false
        match_all:
          type: "boolean"
          description: "是否需要匹配所有关键词"
          default: false
        message_index:
          type: "integer"
          description: "消息索引（-1表示最后一条消息）"
          default: -1
      required: ["keywords"]
    return_values: ["matched", "not_matched"]
    implementation: "config"
    type: "message_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["message", "keyword"]
    
  sentiment_router:
    description: "基于情感分析的路由"
    parameters:
      type: "object"
      properties:
        sentiment_threshold:
          type: "number"
          description: "情感阈值"
          default: 0.5
        neutral_range:
          type: "array"
          items:
            type: "number"
          description: "中性情感范围"
          default: [0.4, 0.6]
        model_name:
          type: "string"
          description: "情感分析模型名称"
          default: "default"
    return_values: ["positive", "negative", "neutral"]
    implementation: "custom.sentiment_router"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["message", "sentiment", "ai"]
    
  message_length_router:
    description: "基于消息长度的路由"
    parameters:
      type: "object"
      properties:
        short_threshold:
          type: "integer"
          description: "短消息阈值"
          default: 50
        long_threshold:
          type: "integer"
          description: "长消息阈值"
          default: 500
        message_index:
          type: "integer"
          description: "消息索引（-1表示最后一条消息）"
          default: -1
    return_values: ["short", "medium", "long"]
    implementation: "config"
    type: "message_length_check"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["message", "length"]
```

### 7. 自定义路由函数

```yaml
# configs/edges/route_functions/custom.yaml
name: "自定义路由函数"
description: "用户自定义的路由函数集合"
category: "custom"

route_functions:
  complex_business_logic:
    description: "复杂业务逻辑路由"
    parameters:
      type: "object"
      properties:
        business_rules:
          type: "array"
          items:
            type: "object"
            properties:
              rule_id:
                type: "string"
              condition:
                type: "string"
              priority:
                type: "integer"
          description: "业务规则列表"
        default_outcome:
          type: "string"
          description: "默认结果"
          default: "review"
      required: ["business_rules"]
    return_values: ["approve", "reject", "review", "escalate"]
    implementation: "custom.business_logic_router"
    metadata:
      author: "business_team"
      version: "2.1"
      tags: ["business", "complex"]
    
  ml_model_prediction:
    description: "基于机器学习模型预测的路由"
    parameters:
      type: "object"
      properties:
        model_name:
          type: "string"
          description: "模型名称"
        model_version:
          type: "string"
          description: "模型版本"
          default: "latest"
        confidence_threshold:
          type: "number"
          description: "置信度阈值"
          default: 0.8
        input_features:
          type: "array"
          items:
            type: "string"
          description: "输入特征列表"
      required: ["model_name"]
    return_values: ["high_confidence", "low_confidence", "error"]
    implementation: "custom.ml_model_router"
    metadata:
      author: "ml_team"
      version: "1.5"
      tags: ["ml", "prediction", "ai"]
    
  time_based_router:
    description: "基于时间的路由"
    parameters:
      type: "object"
      properties:
        time_ranges:
          type: "array"
          items:
            type: "object"
            properties:
              start:
                type: "string"
                pattern: "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
              end:
                type: "string"
                pattern: "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
              route:
                type: "string"
          description: "时间范围和对应路由"
        timezone:
          type: "string"
          description: "时区"
          default: "UTC"
        default_route:
          type: "string"
          description: "默认路由"
          default: "after_hours"
      required: ["time_ranges"]
    return_values: ["business_hours", "after_hours", "weekend"]
    implementation: "custom.time_based_router"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["time", "schedule"]
```

## 工作流配置示例

### 1. 基本工作流示例

```yaml
# configs/edges/examples/basic_workflow.yaml
name: "基本工作流示例"
description: "展示灵活条件边的基本用法"
version: "1.0"

# 节点定义
nodes:
  agent:
    function: "llm_node"
    description: "代理节点"
    
  tool_executor:
    function: "tool_node"
    description: "工具执行节点"
    
  response_generator:
    function: "llm_node"
    description: "响应生成节点"
    
  error_handler:
    function: "error_node"
    description: "错误处理节点"

# 边定义
edges:
  # 简单边
  - from: "__start__"
    to: "agent"
    type: "simple"
    description: "开始代理"
    
  # 条件边 - 使用内置路由函数
  - from: "agent"
    type: "conditional"
    route_function: "has_tool_calls"
    route_parameters: {}
    path_map:
      continue: "tool_executor"
      end: "response_generator"
    description: "根据是否有工具调用决定路由"
    
  # 条件边 - 使用配置路由函数
  - from: "tool_executor"
    type: "conditional"
    route_function: "tool_result_status"
    route_parameters:
      check_success: true
      check_error: true
    path_map:
      success: "response_generator"
      error: "error_handler"
      partial: "agent"
      no_results: "response_generator"
    description: "根据工具执行结果状态路由"
    
  # 简单边
  - from: "response_generator"
    to: "__end__"
    type: "simple"
    description: "结束工作流"
    
  - from: "error_handler"
    to: "__end__"
    type: "simple"
    description: "错误处理结束"
```

### 2. 复杂路由示例

```yaml
# configs/edges/examples/complex_routing.yaml
name: "复杂路由示例"
description: "展示多条件和复杂路由逻辑"
version: "1.0"

# 节点定义
nodes:
  input_processor:
    function: "process_input"
    description: "输入处理节点"
    
  classifier:
    function: "classify_content"
    description: "内容分类节点"
    
  urgent_handler:
    function: "handle_urgent"
    description: "紧急处理节点"
    
  normal_processor:
    function: "process_normal"
    description: "常规处理节点"
    
  error_handler:
    function: "handle_error"
    description: "错误处理节点"
    
  review_node:
    function: "review_content"
    description: "内容审核节点"
    
  escalation_node:
    function: "escalate_issue"
    description: "问题升级节点"
    
  response_generator:
    function: "generate_response"
    description: "响应生成节点"

# 边定义
edges:
  # 简单边
  - from: "__start__"
    to: "input_processor"
    type: "simple"
    
  - from: "input_processor"
    to: "classifier"
    type: "simple"
    
  # 复杂条件边 - 使用自定义路由函数
  - from: "classifier"
    type: "conditional"
    route_function: "complex_business_logic"
    route_parameters:
      business_rules:
        - rule_id: "priority_check"
          condition: "priority == 'high'"
          priority: 1
        - rule_id: "content_check"
          condition: "contains_sensitive_content"
          priority: 2
        - rule_id: "error_check"
          condition: "has_processing_errors"
          priority: 3
      default_outcome: "review"
    path_map:
      approve: "normal_processor"
      reject: "error_handler"
      review: "review_node"
      escalate: "escalation_node"
    description: "基于复杂业务逻辑的路由"
    
  # 基于状态的路由
  - from: "normal_processor"
    type: "conditional"
    route_function: "status_router"
    route_parameters:
      state_key: "processing_status"
      value_mapping:
        "success": "response_generator"
        "partial": "normal_processor"
        "failed": "error_handler"
      default_route: "review_node"
    path_map:
      success: "response_generator"
      partial: "normal_processor"
      failed: "error_handler"
      default_handler: "review_node"
    description: "基于处理状态的路由"
    
  # 基于消息的路由
  - from: "review_node"
    type: "conditional"
    route_function: "keyword_match"
    route_parameters:
      keywords: ["approve", "reject", "escalate"]
      case_sensitive: false
    path_map:
      matched: "response_generator"
      not_matched: "escalation_node"
    description: "基于审核关键词的路由"
    
  # 基于时间的路由
  - from: "escalation_node"
    type: "conditional"
    route_function: "time_based_router"
    route_parameters:
      time_ranges:
        - start: "09:00"
          end: "17:00"
          route: "business_hours"
        - start: "17:00"
          end: "09:00"
          route: "after_hours"
      timezone: "Asia/Shanghai"
      default_route: "after_hours"
    path_map:
      business_hours: "response_generator"
      after_hours: "response_generator"
      weekend: "response_generator"
    description: "基于时间的路由"
    
  # 结束边
  - from: "response_generator"
    to: "__end__"
    type: "simple"
    
  - from: "error_handler"
    to: "__end__"
    type: "simple"
    
  - from: "urgent_handler"
    to: "response_generator"
    type: "simple"
```

### 3. 迁移示例

```yaml
# configs/edges/examples/migration_example.yaml
name: "迁移示例"
description: "展示从传统条件边迁移到灵活条件边的示例"
version: "1.0"

# 传统条件边配置（旧格式）
traditional_edges:
  - from: "agent"
    to: "tool_executor"
    type: "conditional"
    condition: "has_tool_calls"
    path_map:
      continue: "tool_executor"
      end: "__end__"
    description: "传统条件边"
    
  - from: "tool_executor"
    to: "response_generator"
    type: "conditional"
    condition: "max_iterations:10"
    path_map:
      continue: "response_generator"
      end: "__end__"
    description: "带参数的传统条件边"

# 灵活条件边配置（新格式）
flexible_edges:
  - from: "agent"
    type: "conditional"
    route_function: "has_tool_calls"
    route_parameters: {}
    path_map:
      continue: "tool_executor"
      end: "__end__"
    description: "灵活条件边 - 基本用法"
    
  - from: "tool_executor"
    type: "conditional"
    route_function: "iteration_check"
    route_parameters:
      max_iterations: 10
      comparison: "greater_equal"
    path_map:
      continue: "response_generator"
      max_reached: "__end__"
      exceeded: "__end__"
    description: "灵活条件边 - 带参数"

# 迁移映射
migration_mapping:
  "has_tool_calls":
    route_function: "has_tool_calls"
    route_parameters: {}
    
  "max_iterations:10":
    route_function: "iteration_check"
    route_parameters:
      max_iterations: 10
      comparison: "greater_equal"
      
  "message_contains:error":
    route_function: "keyword_match"
    route_parameters:
      keywords: ["error"]
      case_sensitive: false
```

## 配置验证示例

### 1. 路由函数验证

```yaml
# configs/edges/examples/validation_example.yaml
name: "配置验证示例"
description: "展示配置验证的各种情况"
version: "1.0"

# 有效配置示例
valid_edges:
  - from: "node1"
    type: "conditional"
    route_function: "has_tool_calls"
    route_parameters: {}
    path_map:
      continue: "node2"
      end: "__end__"
      
  - from: "node2"
    type: "conditional"
    route_function: "tool_call_count"
    route_parameters:
      threshold: 5
      comparison: "greater_than"
    path_map:
      single: "node3"
      multiple: "node4"
      none: "__end__"

# 无效配置示例
invalid_edges:
  # 缺少路由函数
  - from: "node1"
    type: "conditional"
    # route_function: "has_tool_calls"  # 缺少
    route_parameters: {}
    path_map:
      continue: "node2"
      
  # 路由函数不存在
  - from: "node2"
    type: "conditional"
    route_function: "non_existent_function"
    route_parameters: {}
    path_map:
      continue: "node3"
      
  # 参数类型错误
  - from: "node3"
    type: "conditional"
    route_function: "tool_call_count"
    route_parameters:
      threshold: "not_a_number"  # 应该是数字
    path_map:
      single: "node4"
      
  # 缺少必需参数
  - from: "node4"
    type: "conditional"
    route_function: "tool_call_count"
    route_parameters: {}  # 缺少必需的 threshold 参数
    path_map:
      single: "node5"

# 验证规则
validation_rules:
  required_fields:
    conditional:
      - "route_function"
      - "path_map"
      
  parameter_types:
    tool_call_count:
      threshold: "integer"
      comparison: "string"
      
  allowed_values:
    tool_call_count:
      comparison: ["equals", "greater_than", "less_than"]
```

## 总结

通过以上配置文件结构和示例，我们可以看到灵活条件边系统提供了：

1. **模块化配置**：路由函数、边类型和工作流配置分离
2. **丰富的路由函数**：内置、配置驱动和自定义路由函数
3. **灵活的参数系统**：支持复杂参数类型和验证
4. **清晰的迁移路径**：从传统条件边到灵活条件边的平滑迁移
5. **完整的验证机制**：确保配置的正确性和一致性

这种设计使得条件边配置更加灵活、可维护和可扩展。