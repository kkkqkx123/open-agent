# 工具定义指南

## 概述

本项目采用模块化工具系统，支持三种类型的工具：
1. **内置工具 (Builtin Tool)** - 项目内部的Python函数
2. **原生工具 (Native Tool)** - 外部API调用
3. **MCP工具 (MCP Tool)** - 通过MCP服务器提供的工具

## 工具系统架构

### 核心接口

- `ITool` - 工具核心接口，定义了工具的基本行为
- `IToolManager` - 工具管理器接口，负责工具的加载、注册和管理
- `IToolExecutor` - 工具执行器接口，负责执行工具调用
- `IToolRegistry` - 工具注册表接口，管理工具注册

### 工具类型实现

1. `BuiltinTool` - 包装Python函数的内置工具，实现在 `src/domain/tools/types/builtin_tool.py`
2. `NativeTool` - 调用外部API的原生工具，实现在 `src/domain/tools/types/native_tool.py`
3. `MCPTool` - 通过MCP服务器通信的工具，实现在 `src/domain/tools/types/mcp_tool.py`

- **builtin**: 使用本地Python函数实现，通过 `function_path` 指定函数路径
- **native**: 调用外部API，通过 `api_url`、`method` 等配置HTTP请求
- **mcp**: 通过MCP服务器通信，通过 `mcp_url` 等配置参数

## 工具相关的提示词处理

工具系统与提示词管理系统集成，通过以下方式处理提示词：

1. **工具格式化**: `ToolFormatter` 将工具信息格式化为LLM可理解的提示词
2. **动态提示词生成**: 根据可用工具动态生成调用指导提示词
3. **策略检测**: 自动检测LLM支持的工具调用策略

```python
# 在 src/infrastructure/tools/formatter.py 中
def format_for_llm(self, tools: Sequence[ITool]) -> Dict[str, Any]:
    """将工具格式化为LLM可识别的格式"""
    prompt: str = f"""
请按以下JSON格式调用工具：

{self._generate_tool_schema(tools)}

请严格按照上述格式调用工具，不要添加其他内容。
"""
    return {"prompt": prompt}
```

## 工具加载机制

### 配置文件加载

工具配置文件位于 `configs/tools/` 目录下，系统通过以下方式加载：

1. **配置加载器**: 使用 `YamlConfigLoader` 加载YAML配置文件
2. **工具管理器**: `ToolManager` 负责解析配置并创建工具实例
3. **目录遍历**: 当前实现只加载直接子目录下的配置文件，不递归加载子目录

```python
# 在 src/infrastructure/tools/manager.py 中
def load_from_config(self, config_path: str) -> List[ToolConfig]:
    # 只查找直接子目录下的.yaml文件
    config_files = list(tools_config_dir.glob("*.yaml"))
```

### 如果在子目录中放置配置文件

如果在 `configs/tools/folder1/` 目录下放置配置文件，当前系统**不会自动加载**这些配置文件。

要支持子目录配置文件加载，需要修改工具加载器代码：

```python
# 修改为递归查找所有子目录
config_files = list(tools_config_dir.rglob("*.yaml"))
```

## 如何定义新工具

### 1. 内置工具 (Builtin Tool)

内置工具是项目内部的Python函数，通过配置文件定义。实现类位于 `src/domain/tools/types/builtin_tool.py`。

#### 步骤1: 创建Python函数

在适当的位置创建Python函数，例如在 `examples/tools/calculator.py` 中：

```python
def calculate(expression: str, precision: int = 2) -> Dict[str, Any]:
    """计算数学表达式
    
    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
        precision: 结果的小数位数，默认为2
        
    Returns:
        Dict[str, Any]: 计算结果
    """
    # 实现函数逻辑
    result = eval(expression)  # 注意：实际项目中应使用安全的计算方法
    if isinstance(result, float) and precision >= 0:
        result = round(result, precision)
        
    return {
        "expression": expression,
        "result": result,
        "precision": precision,
        "type": type(result).__name__
    }
```

#### 步骤2: 创建配置文件

在 `configs/tools/` 目录下创建YAML配置文件，例如 `calculator.yaml`：

```yaml
# 计算器工具配置
name: calculator
tool_type: builtin
description: 执行基本数学计算的工具
function_path: examples.tools.calculator:calculate
enabled: true
timeout: 10
parameters_schema:
  type: object
  properties:
    expression:
      type: string
      description: 要计算的数学表达式，如 "2 + 3 * 4"
    precision:
      type: integer
      description: 结果的小数位数，默认为2
      default: 2
  required:
    - expression
metadata:
  category: "math"
  tags: ["calculator", "math", "basic"]
```

#### 配置参数说明

- `name`: 工具名称，必须唯一
- `tool_type`: 工具类型，对于内置工具为 "builtin"
- `description`: 工具描述
- `function_path`: 函数路径，格式为 "module.submodule:function_name"
- `enabled`: 是否启用工具
- `timeout`: 超时时间（秒）
- `parameters_schema`: 参数Schema，定义工具接受的参数
- `metadata`: 额外的元数据信息

### 2. 原生工具 (Native Tool)

原生工具用于调用外部API。

#### 配置示例

```yaml
# 天气查询工具配置
name: weather
tool_type: native
description: 查询指定城市的天气信息
enabled: true
timeout: 15
api_url: "https://api.openweathermap.org/data/2.5/weather"
method: GET
auth_method: api_key
api_key: "${OPENWEATHER_API_KEY}"
headers:
  User-Agent: "ModularAgent/1.0"
  Content-Type: "application/json"
retry_count: 3
retry_delay: 1.0
parameters_schema:
  type: object
  properties:
    q:
      type: string
      description: 城市名称，如 "Beijing,CN" 或 "London"
    units:
      type: string
      description: 温度单位，可选值: metric(摄氏度), imperial(华氏度), kelvin(开尔文)
      enum: ["metric", "imperial", "kelvin"]
      default: "metric"
    lang:
      type: string
      description: 返回结果的语言，如 "zh_cn", "en"
      default: "zh_cn"
  required:
    - q
metadata:
  category: "weather"
  tags: ["weather", "api", "external"]
  documentation_url: "https://openweathermap.org/api"
```

#### 配置参数说明

- `api_url`: API的URL地址
- `method`: HTTP方法 (GET, POST, PUT, DELETE等)
- `auth_method`: 认证方法 ("api_key", "api_key_header", "oauth", "none")
- `api_key`: API密钥
- `headers`: HTTP请求头
- `retry_count`: 重试次数
- `retry_delay`: 重试延迟时间

### 3. MCP工具 (MCP Tool)

MCP工具通过MCP服务器提供功能。

#### 配置示例

```yaml
# 数据库查询工具配置
name: database_query
tool_type: mcp
description: 通过MCP服务器执行数据库查询
enabled: true
timeout: 30
mcp_server_url: "http://localhost:8080/mcp"
dynamic_schema: true
refresh_interval: 300  # 5分钟刷新一次Schema
parameters_schema:
  type: object
  properties:
    query:
      type: string
      description: SQL查询语句
    database:
      type: string
      description: 数据库名称
      default: "default"
    limit:
      type: integer
      description: 返回结果的最大行数
      default: 100
  required:
    - query
metadata:
  category: "database"
  tags: ["database", "sql", "mcp"]
  server_info: "本地MCP数据库服务器"
```

#### 配置参数说明

- `mcp_server_url`: MCP服务器URL
- `dynamic_schema`: 是否动态获取Schema
- `refresh_interval`: Schema刷新间隔（秒）

## 工具参数Schema

工具参数Schema遵循JSON Schema规范，定义了工具接受的参数格式：

```yaml
parameters_schema:
  type: object
  properties:
    parameter_name:
      type: string  # 数据类型: string, integer, number, boolean, array, object
      description: 参数描述
      enum: [可选值列表]  # 限制可选值
      default: 默认值
  required:
    - 必需参数名称
```

## 工具集 (Tool Sets)

工具集允许将多个工具组合在一起，便于管理和使用。

在 `configs/tool-sets/` 目录下创建工具集配置文件：

```yaml
name: math_tools
description: 数学计算工具集
tools:
  - calculator
  - advanced_calculator
enabled: true
metadata:
  category: "mathematics"
  tags: ["math", "calculation"]
```

## 工具验证

工具系统会自动验证：

1. 工具配置格式是否正确
2. 必需参数是否提供
3. 参数类型是否匹配
4. 工具名称是否唯一

## 最佳实践

1. **安全性**: 对于内置工具，确保函数实现是安全的，避免代码注入
2. **错误处理**: 工具应提供清晰的错误信息
3. **参数验证**: 使用适当的参数Schema验证输入
4. **文档**: 提供清晰的工具描述和参数说明
5. **性能**: 考虑工具的执行时间和资源消耗
6. **配置管理**: 使用环境变量管理敏感信息（如API密钥）

## 工具生命周期

1. **定义**: 在配置文件中定义工具
2. **加载**: 工具管理器从配置文件加载工具
3. **注册**: 将工具注册到工具管理器
4. **执行**: 通过工具执行器执行工具调用
5. **结果处理**: 处理工具执行结果