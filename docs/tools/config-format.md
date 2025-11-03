<write_file>
<args>
  <file>
    <path>docs/tools/tool-configuration-format-analysis.md</path>
  </file>
</args>
<content>
# 工具配置格式分析报告

## 概述

本报告分析了 `src\domain\tools\types\builtin` 和 `src\domain\tools\types\native` 目录下工具的配置文件格式，发现了格式不一致的问题，并提出了正确的配置格式规范。

## 工具配置文件格式不一致问题分析

### 1. function_path 字段不一致

通过对比分析现有的工具配置文件，发现 `function_path` 字段存在以下不一致问题：

1. **calculator.yaml**:
   ```yaml
   function_path: src.domain.tools.builtin.calculator:calculate
   ```

2. **hash_convert.yaml**:
   ```yaml
   function_path: src.domain.tools.builtin.tools.hash_convert:hash_convert
   ```

3. **sequentialthinking.yaml**:
   ```yaml
   function_path: definition.tools.sequentialthinking:sequentialthinking
   ```

4. **fetch.yaml**:
   ```yaml
   function_path: src.domain.tools.native.tools.fetch:fetch_url
   ```

**问题**：
- `sequentialthinking.yaml` 中的 `function_path` 与其他工具的格式不一致
- `sequentialthinking.yaml` 中的路径指向不存在的模块位置
- `hash_convert.yaml` 和 `fetch.yaml` 中包含了额外的 `tools` 子目录，与其他工具不一致

### 2. 原生工具配置不一致

1. **duckduckgo_search.yaml**:
   ```yaml
   tool_type: native
   # 没有 function_path 字段
   # 有 api_url, method, headers 等字段
   ```

2. **fetch.yaml**:
   ```yaml
   tool_type: native
   # 有 function_path 字段
   # 没有 api_url, method, headers 等字段
   ```

**问题**：
- 同样是原生工具，但配置字段不一致
- `duckduckgo_search.yaml` 使用 API 调用配置
- `fetch.yaml` 使用函数包装配置

### 3. 描述字段格式不一致

1. **calculator.yaml**:
   ```yaml
   description: A tool for performing basic mathematical calculations
   ```

2. **sequentialthinking.yaml**:
   ```yaml
   description: |
     A detailed tool for dynamic and reflective problem-solving through thoughts.
     This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
     # 多行描述
   ```

**问题**：
- 描述格式不一致，有的使用单行，有的使用多行
- 缺乏统一的描述格式规范

## 正确的工具配置文件格式

基于分析，我确定以下正确的工具配置文件格式：

### 1. 内置工具 (Builtin Tool) 格式

```yaml
# 工具名称配置
name: [工具名称]
tool_type: builtin
description: [工具描述，可以是单行或多行]
function_path: src.domain.tools.builtin.[模块名]:[函数名]
enabled: true
timeout: [超时时间，秒]
parameters_schema:
  type: object
  properties:
    [参数名]:
      type: [数据类型]
      description: [参数描述]
      enum: [可选值列表]  # 可选
      default: [默认值]  # 可选
      minimum: [最小值]  # 可选，用于数字类型
      maximum: [最大值]  # 可选，用于数字类型
  required:
    - [必需参数名]
metadata:
  category: "[工具类别]"
  tags: ["[标签1]", "[标签2]"]
  documentation_url: "[文档URL]"  # 可选
```

### 2. 原生工具 (Native Tool) 格式

原生工具有两种子类型：

#### 2.1 API调用型原生工具

```yaml
# 工具名称配置
name: [工具名称]
tool_type: native
description: [工具描述]
enabled: true
timeout: [超时时间，秒]
api_url: "[API URL]"
method: [HTTP方法，如 GET, POST]
headers:
  [Header名]: "[Header值]"
auth_method: [认证方法，如 api_key, api_key_header, oauth, none]
api_key: "${[API密钥环境变量名]}"  # 可选
retry_count: [重试次数]
retry_delay: [重试延迟，秒]
rate_limit:
  requests_per_minute: [每分钟请求数限制]
parameters_schema:
  type: object
  properties:
    [参数名]:
      type: [数据类型]
      description: [参数描述]
      # 其他参数属性...
  required:
    - [必需参数名]
metadata:
  category: "[工具类别]"
  tags: ["[标签1]", "[标签2]"]
  documentation_url: "[文档URL]"  # 可选
```

#### 2.2 函数包装型原生工具

```yaml
# 工具名称配置
name: [工具名称]
tool_type: native
description: [工具描述]
function_path: src.domain.tools.native.[模块名]:[函数名]
enabled: true
timeout: [超时时间，秒]
parameters_schema:
  type: object
  properties:
    [参数名]:
      type: [数据类型]
      description: [参数描述]
      # 其他参数属性...
  required:
    - [必需参数名]
metadata:
  category: "[工具类别]"
  tags: ["[标签1]", "[标签2]"]
  documentation_url: "[文档URL]"  # 可选
```

## 配置格式规范

### 1. 命名规范

- **工具名称**：使用小写字母和下划线，如 `calculator`、`hash_convert`
- **文件名**：与工具名称相同，使用 `.yaml` 扩展名，如 `calculator.yaml`

### 2. 路径规范

- **内置工具函数路径**：`src.domain.tools.builtin.[模块名]:[函数名]`
- **原生工具函数路径**：`src.domain.tools.native.[模块名]:[函数名]`

### 3. 描述规范

- **简单工具**：使用单行描述
- **复杂工具**：使用多行描述，以 `|` 开头

### 4. 参数规范

- **必需参数**：在 `required` 列表中列出
- **可选参数**：提供 `default` 值
- **枚举值**：使用 `enum` 列表限制

### 5. 元数据规范

- **category**：工具类别，如 `math`、`web`、`search`
- **tags**：工具标签列表，便于分类和搜索
- **documentation_url**：可选，指向工具文档

## 工具配置文件修复建议

### 1. sequentialthinking.yaml 修复

```yaml
# Sequential Thinking Tool Configuration
name: sequentialthinking
tool_type: builtin
description: A detailed tool for dynamic and reflective problem-solving through thoughts
function_path: src.domain.tools.builtin.sequentialthinking:sequentialthinking
enabled: true
timeout: 30
# 其余配置保持不变...
```

### 2. fetch.yaml 修复

```yaml
# 网页内容获取工具配置
name: fetch
tool_type: native
description: A tool for fetching web page content from URLs and optionally extracting it as markdown
enabled: true
timeout: 30
# 移除 function_path，因为这是API调用型工具
api_url: "http://example.com/api/fetch"  # 替换为实际API URL
method: GET
headers:
  User-Agent: "ModularAgent/1.0"
  Content-Type: "application/json"
# 其余配置保持不变...
```

### 3. hash_convert.yaml 修复

```yaml
# Hash转换工具配置
name: hash_convert
tool_type: builtin
description: A tool for converting text to various hash values, supporting MD5, SHA1, SHA256, SHA512 algorithms
function_path: src.domain.tools.builtin.hash_convert:hash_convert
enabled: true
timeout: 10
# 其余配置保持不变...
```

## 工具配置加载机制

### 1. 工具加载流程

1. **配置文件加载**：
   - 工具管理器使用 `DefaultToolLoader` 从 `configs/tools` 目录加载所有 `.yaml` 文件
   - 解析每个配置文件，创建对应的工具配置对象

2. **工具实例创建**：
   - 根据配置中的 `tool_type` 字段确定工具类型
   - 对于内置工具 (`builtin`)，通过 `function_path` 动态加载函数
   - 对于原生工具 (`native`)，根据配置创建 `NativeTool` 实例

3. **工具注册**：
   - 将创建的工具实例注册到工具管理器中
   - 工具管理器提供统一的工具访问接口

### 2. 工具配置给节点

工具通过工作流配置文件配置给节点：

```yaml
nodes:
  react_agent:
    type: react_agent_node
    config:
      name: react_agent
      system_prompt: 你是一个使用ReAct算法的智能助手
      max_iterations: 5
      tools: [calculator, duckduckgo_search]  # 工具列表
      llm_client: mock
      next_node_on_complete: final_response
      next_node_on_error: error_handler
    description: ReAct Agent节点，执行推理和行动
```

### 3. 工具执行流程

1. **工具调用解析**：
   - LLM节点生成包含工具调用的响应
   - 工具节点从消息中解析工具调用请求

2. **工具执行**：
   - 工具节点使用工具管理器获取对应的工具实例
   - 执行工具调用并处理结果

3. **结果处理**：
   - 工具执行结果被存储到状态中
   - LLM节点获取工具执行结果并生成最终响应

## 总结

通过统一工具配置文件格式，可以提高工具系统的一致性和可维护性。建议：

1. **修复现有配置文件**：按照上述规范修复不一致的配置文件
2. **建立配置验证机制**：在工具加载时验证配置文件格式
3. **创建配置模板**：为每种工具类型提供标准配置模板
4. **完善文档**：提供详细的工具配置指南和示例

这些改进将使工具系统更加健壮、易于维护和扩展。