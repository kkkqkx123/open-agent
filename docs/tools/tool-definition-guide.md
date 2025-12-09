# 工具定义指南

## 概述

本项目采用基于状态管理的模块化工具系统，支持两种主要类别的工具：

1. **无状态工具 (Stateless Tools)**
   - **内置工具 (Builtin Tool)** - 简单的、无状态的Python函数实现

2. **有状态工具 (Stateful Tools)**
   - **原生工具 (Native Tool)** - 复杂的、有状态的项目内实现工具
   - **REST工具 (Rest Tool)** - 技术上有状态但业务逻辑上无状态的REST API调用工具
   - **MCP工具 (MCP Tool)** - 有状态的MCP服务器工具，适用于需要复杂状态管理的场景

### REST工具与有状态工具的区分

#### REST工具的特点

**业务逻辑无状态**
当前系统中的REST工具（如fetch、duckduckgo_search、weather等）在业务逻辑上是无状态的，这意味着：
- 每次工具调用都是独立的，不依赖于之前的调用结果
- 工具的执行结果仅取决于输入参数
- 多次调用之间没有依赖关系

**技术性状态管理**
尽管业务逻辑上是无状态的，但REST工具仍使用状态管理器来：
- 维护HTTP连接复用，提高性能
- 实现请求速率限制
- 跟踪连接状态和错误信息

#### 有状态工具的定义

有状态工具是指在业务逻辑上需要维护状态的工具，例如：
- 浏览器操作工具：需要维护浏览器会话、页面状态、cookies等
- 数据库连接工具：需要维护数据库连接状态
- 会话管理工具：需要跟踪用户会话状态

#### 实现有状态工具的策略

**推荐方案：MCP（Model Context Protocol）**
对于需要真正业务状态管理的工具（如浏览器操作工具），推荐使用MCP协议实现，原因如下：
1. **集中状态管理**：MCP服务器可以更好地管理复杂的状态（如浏览器实例、会话状态）
2. **资源管理**：浏览器实例等资源的创建和销毁可以由专用服务器处理
3. **安全性**：复杂操作（如浏览器操作）可以在隔离的环境中执行
4. **可扩展性**：多个工具实例的管理更适合在专用服务器中处理
5. **故障隔离**：有状态工具的故障不会影响主系统

**不推荐：扩展REST工具**
不建议将当前的REST工具扩展为真正的有状态工具，因为：
- 会破坏REST工具无状态的语义
- 增加系统的复杂性和维护成本
- 可能导致状态管理混乱

### 工具分类策略

- **rest**：业务逻辑无状态的工具（当前所有REST工具）
- **mcp**：需要复杂状态管理的工具（如浏览器操作、数据库连接等）

### 状态管理核心概念

有状态工具支持三种状态类型：

- **CONNECTION** - 连接状态：管理外部连接、会话保持、错误计数等
- **SESSION** - 会话状态：管理用户会话、权限、认证信息等
- **BUSINESS** - 业务状态：管理业务数据、历史记录、版本控制等（REST工具在业务逻辑上无状态）

## 工具系统架构

### 核心接口

- `ITool` - 工具核心接口，定义了工具的基本行为
- `IToolManager` - 工具管理器接口，负责工具的加载、注册和管理
- `IToolExecutor` - 工具执行器接口，负责执行工具调用
- `IToolFactory` - 工具工厂接口，负责创建工具实例
- `IToolStateManager` - 工具状态管理器接口，负责有状态工具的状态管理
- `IToolRegistry` - 工具注册表接口，管理工具注册

### 基础类层次

```
BaseTool (无状态工具基类)
├── BuiltinTool - 内置工具实现

StatefulBaseTool (有状态工具基类，继承自BaseTool)
├── NativeTool - 原生工具实现
├── RestTool - REST工具实现
└── MCPTool - MCP工具实现
```

### 工具类型实现

1. `BuiltinTool` - 包装Python函数的无状态工具，实现在 `src/core/tools/types/builtin_tool.py`
2. `NativeTool` - 包装有状态Python函数的工具，实现在 `src/core/tools/types/native_tool.py`
3. `RestTool` - 调用外部REST API的有状态工具，实现在 `src/core/tools/types/rest_tool.py`
4. `MCPTool` - 通过MCP服务器通信的有状态工具，实现在 `src/core/tools/types/mcp_tool.py`

## 工具类型详细说明

### 无状态工具 (Stateless Tools)

#### 内置工具 (Builtin Tool)

**特点**：
- 简单的、无状态的Python函数包装
- 不需要状态管理，执行速度快
- 适用于计算、转换等简单操作
- 同步执行，不支持异步

**使用场景**：
- 数学计算
- 数据格式转换
- 字符串处理
- 哈希计算

**配置示例**：
```yaml
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
      description: 要计算的数学表达式
    precision:
      type: integer
      description: 结果的小数位数
      default: 2
  required:
    - expression
metadata:
  category: "math"
  tags: ["calculator", "math", "basic"]
```

### 有状态工具 (Stateful Tools)

有状态工具继承自 `StatefulBaseTool`，支持完整的状态管理功能。

#### 原生工具 (Native Tool)

**特点**：
- 包装复杂的、有状态的Python函数
- 支持状态注入和状态更新
- 可以维护业务状态和历史记录
- 支持连接状态管理

**使用场景**：
- 需要维护中间状态的复杂计算
- 需要历史记录的业务逻辑
- 需要状态持久化的工具

**配置示例**：
```yaml
name: sequential_thinking
tool_type: native
description: 序列思考工具，维护思考过程状态
function_path: examples.tools.sequentialthinking:process_thought
enabled: true
timeout: 30
state_injection: true
state_parameter_name: "state"
state_config:
  manager_type: "memory"
  ttl: 3600
  auto_cleanup: true
business_config:
  max_history_size: 100
  versioning: true
  auto_save: true
parameters_schema:
  type: object
  properties:
    thought:
      type: string
      description: 当前思考内容
    step:
      type: integer
      description: 思考步骤编号
  required:
    - thought
metadata:
  category: "ai"
  tags: ["thinking", "sequential", "stateful"]
```

#### REST工具 (Rest Tool)

**特点**：
- 调用外部REST API
- 业务逻辑上无状态，但技术上使用状态管理器维护连接状态
- 支持连接池和重试机制
- 自动处理认证和请求头
- 维护HTTP连接复用，提高性能
- 实现请求速率限制和错误跟踪

**使用场景**：
- 调用外部API服务
- 需要会话保持的Web服务（技术层面）
- 需要连接管理的HTTP请求
- 业务逻辑上无状态的API调用

**注意事项**：
- REST工具在业务逻辑上应保持无状态，避免依赖之前的调用结果
- 不应将REST工具扩展为需要复杂业务状态管理的工具
- 对于需要复杂状态管理的场景，应考虑使用MCP工具

**配置示例**：
```yaml
name: weather_api
tool_type: rest
description: 天气查询API工具
api_url: "https://api.openweathermap.org/data/2.5/weather"
method: GET
enabled: true
timeout: 15
headers:
  User-Agent: "ModularAgent/1.0"
  Content-Type: "application/json"
auth_method: api_key_header
api_key: "${OPENWEATHER_API_KEY}"
state_config:
  manager_type: "memory"
  ttl: 300
  auto_cleanup: true
parameters_schema:
  type: object
  properties:
    q:
      type: string
      description: 城市名称
    units:
      type: string
      enum: ["metric", "imperial", "kelvin"]
      default: "metric"
  required:
    - q
metadata:
  category: "weather"
  tags: ["api", "weather", "external"]
```

#### MCP工具 (MCP Tool)

**特点**：
- 通过MCP服务器提供功能
- 支持动态Schema获取
- 维护服务器连接状态
- 异步执行，支持并发
- 适用于需要复杂业务状态管理的场景
- 提供集中状态管理和资源管理
- 支持故障隔离，不影响主系统

**使用场景**：
- 连接到MCP服务器
- 需要动态工具发现
- 分布式工具调用
- 需要复杂业务状态管理的工具（如浏览器操作、数据库连接等）
- 需要资源隔离和故障隔离的场景

**配置示例**：
```yaml
name: database_query
tool_type: mcp
description: 数据库查询工具
mcp_server_url: "http://localhost:8080/mcp"
enabled: true
timeout: 30
dynamic_schema: true
refresh_interval: 300
state_config:
  manager_type: "memory"
  ttl: 600
  auto_cleanup: true
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
  required:
    - query
metadata:
  category: "database"
  tags: ["database", "sql", "mcp"]
```

## 状态管理系统

### 状态类型

有状态工具支持三种状态类型：

#### 1. 连接状态 (CONNECTION)

管理工具的外部连接状态：

```python
connection_state = {
    'active': False,           # 连接是否活跃
    'created_at': 1234567890,  # 连接创建时间
    'last_used': 1234567890,   # 最后使用时间
    'error_count': 0,          # 错误计数
    'last_error': None,        # 最后错误信息
    'session_active': True,    # 会话是否活跃（REST/MCP工具）
    'request_count': 10        # 请求计数（REST/MCP工具）
}
```

#### 2. 会话状态 (SESSION)

管理用户会话和权限信息：

```python
session_state = {
    'session_id': 'session_12345678',  # 会话ID
    'created_at': 1234567890,          # 会话创建时间
    'last_activity': 1234567890,       # 最后活动时间
    'user_id': 'user_123',             # 用户ID
    'permissions': ['read', 'write'],  # 权限列表
    'auth_token': 'token_abc123'       # 认证令牌
}
```

#### 3. 业务状态 (BUSINESS)

管理业务数据和历史记录：

```python
business_state = {
    'created_at': 1234567890,    # 状态创建时间
    'version': 3,                # 状态版本
    'data': {                    # 业务数据
        'current_step': 5,
        'intermediate_results': [...]
    },
    'history': [                 # 历史记录
        {
            'timestamp': 1234567890,
            'event_type': 'execution_start',
            'data': {...},
            'version': 1
        },
        ...
    ],
    'metadata': {                # 元数据
        'total_executions': 10,
        'success_rate': 0.9
    }
}
```

### 状态管理器配置

状态管理器支持多种配置选项：

```yaml
state_config:
  # 基础配置
  manager_type: "memory"              # 管理器类型: memory, persistent, session, distributed
  ttl: 3600                          # 状态生存时间（秒）
  auto_cleanup: true                 # 自动清理过期状态
  cleanup_interval: 300              # 清理间隔（秒）
  
  # 持久化配置
  persistence_path: "/tmp/tool_state" # 持久化路径
  persistence_format: "json"          # 持久化格式: json, pickle, sqlite
  compression: false                  # 是否压缩存储
  
  # 分布式配置
  redis_url: "redis://localhost:6379" # Redis连接URL
  redis_prefix: "tool_state"          # Redis键前缀
  redis_db: 0                         # Redis数据库编号
  
  # 会话配置
  session_isolation: true             # 会话隔离
  max_states_per_session: 10          # 每会话最大状态数
  session_timeout: 3600               # 会话超时时间（秒）
```

### 业务状态配置

业务状态支持额外的配置选项：

```yaml
business_config:
  # 状态存储配置
  max_history_size: 1000        # 最大历史记录数
  max_state_size: 1048576       # 最大状态大小（字节）
  state_compression: false      # 状态压缩
  
  # 版本控制配置
  versioning: true              # 启用版本控制
  max_versions: 10              # 最大版本数
  auto_save: true               # 自动保存
  
  # 同步配置
  sync_interval: 60             # 同步间隔（秒）
  sync_on_change: true          # 变化时同步
  conflict_resolution: "last_write_wins"  # 冲突解决策略
  
  # 备份配置
  backup_enabled: false         # 启用备份
  backup_interval: 3600         # 备份间隔（秒）
  backup_retention: 7           # 备份保留天数
```

## 工具配置和加载机制

### 配置文件结构

工具配置文件位于 `configs/tools/` 目录下，按工具类型组织：

```
configs/tools/
├── builtin/           # 内置工具配置
│   ├── calculator.yaml
│   └── hash_convert.yaml
├── native/            # 原生工具配置
│   ├── sequential_thinking.yaml
│   └── time_tool.yaml
├── rest/              # REST工具配置
│   ├── weather_api.yaml
│   └── duckduckgo_search.yaml
└── mcp/               # MCP工具配置
    └── database_query.yaml
```

### 工具加载器

系统提供两种工具加载器：

#### 1. DefaultToolLoader

默认工具加载器，支持按类型加载工具：

```python
# 加载所有类型的工具
loader = DefaultToolLoader(config_loader, logger)
tool_configs = loader.load_from_config("tools")

# 加载特定类型的工具
native_configs = loader.load_from_config("native")
```

**注意**：当前实现中，加载所有工具时会加载 `["rest", "native", "mcp"]` 类型的工具，不包括 `builtin` 类型。如需加载 `builtin` 工具，需要单独指定。

#### 2. RegistryBasedToolLoader

基于注册表的工具加载器，支持更灵活的配置：

```python
registry_config = {
    "tool_types": {
        "builtin": {
            "enabled": True,
            "config_directory": "builtin",
            "config_files": ["calculator.yaml", "hash_convert.yaml"]
        },
        "native": {
            "enabled": True,
            "config_directory": "native",
            "config_files": ["sequential_thinking.yaml"]
        }
    }
}

loader = RegistryBasedToolLoader(config_loader, logger, registry_config)
tool_configs = loader.load_all_tools()
```

### 工具工厂

工具工厂负责根据配置创建工具实例：

```python
from src.core.tools.factory import OptimizedToolFactory

# 创建工厂（可提供默认状态管理器）
factory = OptimizedToolFactory(state_manager)

# 创建工具
tool = factory.create_tool(tool_config)

# 注册自定义工具类型
factory.register_tool_type("custom", CustomToolClass)

# 获取支持的类型
supported_types = factory.get_supported_types()
```

### 工具执行器

工具执行器负责实际执行工具调用，支持同步和异步执行：

```python
from src.core.tools.executor import AsyncToolExecutor

# 创建执行器
executor = AsyncToolExecutor()

# 执行单个工具
tool_call = ToolCall(
    name="calculator",
    arguments={"expression": "2 + 3 * 4"},
    call_id="call_123"
)
result = await executor.execute_async(tool_call)

# 并行执行多个工具
tool_calls = [
    ToolCall(name="calculator", arguments={"expression": "2 + 3"}),
    ToolCall(name="calculator", arguments={"expression": "4 * 5"})
]
results = await executor.execute_parallel_async(tool_calls)
```

## 工具集 (Tool Sets)

工具集允许将多个工具组合在一起，便于管理和使用。

### 工具集配置

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

### 使用工具集

```python
# 通过工具管理器加载工具集
tool_set_configs = loader.load_from_config("tool-sets")

# 注册工具集中的所有工具
for tool_set_config in tool_set_configs:
    for tool_name in tool_set_config.tools:
        tool = await tool_manager.get_tool(tool_name)
        if tool:
            # 使用工具...
            pass
```

## 工具定义示例

### 1. 创建内置工具

#### 步骤1: 创建Python函数

在 `examples/tools/calculator.py` 中：

```python
def calculate(expression: str, precision: int = 2) -> Dict[str, Any]:
    """计算数学表达式
    
    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
        precision: 结果的小数位数，默认为2
        
    Returns:
        Dict[str, Any]: 计算结果
    """
    # 实现安全的计算逻辑
    import ast
    import operator
    
    # 安全的数学表达式解析
    def eval_expr(expr):
        node = ast.parse(expr, mode='eval')
        return _eval(node.body)
    
    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return operator.add(left, right)
            elif isinstance(node.op, ast.Sub):
                return operator.sub(left, right)
            elif isinstance(node.op, ast.Mult):
                return operator.mul(left, right)
            elif isinstance(node.op, ast.Div):
                return operator.truediv(left, right)
            else:
                raise ValueError(f"不支持的操作: {node.op}")
        else:
            raise ValueError(f"不支持的表达式类型: {type(node)}")
    
    try:
        result = eval_expr(expression)
        if isinstance(result, float) and precision >= 0:
            result = round(result, precision)
            
        return {
            "expression": expression,
            "result": result,
            "precision": precision,
            "type": type(result).__name__,
            "success": True
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "success": False
        }
```

#### 步骤2: 创建配置文件

在 `configs/tools/builtin/calculator.yaml` 中：

```yaml
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

### 2. 创建有状态原生工具

#### 步骤1: 创建Python函数

在 `examples/tools/sequential_thinking.py` 中：

```python
def process_thought(thought: str, step: int, state: Dict[str, Any] = None) -> Dict[str, Any]:
    """处理思考步骤
    
    Args:
        thought: 当前思考内容
        step: 思考步骤编号
        state: 当前状态（由系统注入）
        
    Returns:
        Dict[str, Any]: 处理结果和更新后的状态
    """
    # 初始化状态
    if state is None:
        state = {
            "steps": [],
            "current_context": "",
            "conclusions": []
        }
    
    # 添加当前思考步骤
    state["steps"].append({
        "step": step,
        "thought": thought,
        "timestamp": time.time()
    })
    
    # 更新上下文
    state["current_context"] += f"步骤{step}: {thought}\n"
    
    # 分析是否得出结论
    if "结论" in thought or "总结" in thought:
        state["conclusions"].append({
            "step": step,
            "conclusion": thought,
            "timestamp": time.time()
        })
    
    # 返回结果和状态更新
    return {
        "step": step,
        "thought": thought,
        "processed": True,
        "total_steps": len(state["steps"]),
        "conclusions_count": len(state["conclusions"]),
        "state": state  # 返回状态以供系统更新
    }
```

#### 步骤2: 创建配置文件

在 `configs/tools/native/sequential_thinking.yaml` 中：

```yaml
name: sequential_thinking
tool_type: native
description: 序列思考工具，维护思考过程状态
function_path: examples.tools.sequentialthinking:process_thought
enabled: true
timeout: 30
state_injection: true
state_parameter_name: "state"
state_config:
  manager_type: "memory"
  ttl: 3600
  auto_cleanup: true
  cleanup_interval: 300
business_config:
  max_history_size: 100
  versioning: true
  auto_save: true
  sync_on_change: true
parameters_schema:
  type: object
  properties:
    thought:
      type: string
      description: 当前思考内容
    step:
      type: integer
      description: 思考步骤编号
  required:
    - thought
    - step
metadata:
  category: "ai"
  tags: ["thinking", "sequential", "stateful"]
```

### 3. 创建REST工具

在 `configs/tools/rest/weather_api.yaml` 中：

```yaml
name: weather_api
tool_type: rest
description: 天气查询API工具
api_url: "https://api.openweathermap.org/data/2.5/weather"
method: GET
enabled: true
timeout: 15
headers:
  User-Agent: "ModularAgent/1.0"
  Content-Type: "application/json"
auth_method: api_key_header
api_key: "${OPENWEATHER_API_KEY}"
state_config:
  manager_type: "memory"
  ttl: 300
  auto_cleanup: true
  session_isolation: true
parameters_schema:
  type: object
  properties:
    q:
      type: string
      description: 城市名称，如 "Beijing,CN" 或 "London"
    units:
      type: string
      description: 温度单位
      enum: ["metric", "imperial", "kelvin"]
      default: "metric"
    lang:
      type: string
      description: 返回结果的语言
      default: "zh_cn"
  required:
    - q
metadata:
  category: "weather"
  tags: ["api", "weather", "external"]
  documentation_url: "https://openweathermap.org/api"
```

### 4. 创建MCP工具

在 `configs/tools/mcp/database_query.yaml` 中：

```yaml
name: database_query
tool_type: mcp
description: 数据库查询工具
mcp_server_url: "http://localhost:8080/mcp"
enabled: true
timeout: 30
dynamic_schema: true
refresh_interval: 300
state_config:
  manager_type: "memory"
  ttl: 600
  auto_cleanup: true
  session_isolation: true
  max_states_per_session: 5
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

## 工具生命周期管理

### 1. 工具初始化

```python
# 获取工具管理器
tool_manager = container.get(IToolManager)

# 初始化工具管理器
await tool_manager.initialize()

# 获取工具实例（自动初始化有状态工具的上下文）
tool = await tool_manager.get_tool("sequential_thinking", session_id="user_123")
```

### 2. 工具执行

```python
# 执行工具
result = await tool_manager.execute_tool(
    name="sequential_thinking",
    arguments={
        "thought": "我需要分析这个问题",
        "step": 1
    },
    context={
        "session_id": "user_123"
    }
)
```

### 3. 状态管理

```python
# 获取工具状态信息
session_info = tool_manager.get_session_info("user_123")

# 清理会话状态
await tool_manager.cleanup_session("user_123")

# 获取工具上下文信息
context_info = tool.get_context_info()
```

## 最佳实践

### 1. 工具设计原则

- **无状态工具**：适用于简单、快速的操作，避免不必要的状态管理开销
- **有状态工具**：适用于需要维护中间状态、历史记录或连接的场景
- **状态隔离**：确保不同会话之间的状态不会相互干扰
- **状态清理**：及时清理过期状态，避免内存泄漏

### 2. 状态管理最佳实践

- **选择合适的状态类型**：
  - CONNECTION：用于外部连接管理
  - SESSION：用于用户会话信息
  - BUSINESS：用于业务数据和逻辑

- **合理设置TTL**：根据工具特性设置合适的生存时间
- **启用自动清理**：避免状态无限增长
- **使用版本控制**：便于状态回滚和冲突解决

### 3. 配置管理

- **环境变量**：敏感信息（如API密钥）使用环境变量
- **配置继承**：利用配置继承减少重复配置
- **参数验证**：确保参数Schema的完整性和准确性
- **元数据**：提供清晰的工具分类和标签

### 4. 错误处理

- **状态恢复**：在错误发生时能够恢复到稳定状态
- **连接重试**：对于网络工具实现合理的重试机制
- **错误记录**：在状态中记录错误信息，便于调试
- **优雅降级**：在部分功能失败时提供基本功能

### 5. 性能优化

- **状态缓存**：合理使用状态缓存提高访问速度
- **连接池**：对于REST工具使用连接池减少连接开销
- **异步执行**：I/O密集型工具优先使用异步执行
- **批量操作**：支持批量操作减少调用次数

## 工具验证

工具系统会自动验证：

1. **配置格式**：工具配置格式是否正确
2. **必需参数**：必需参数是否提供
3. **参数类型**：参数类型是否匹配Schema
4. **工具名称**：工具名称是否唯一
5. **函数路径**：内置/原生工具的函数路径是否有效
6. **API连接**：REST/MCP工具的连接是否可用

## 故障排除

### 常见问题

1. **工具加载失败**
   - 检查配置文件格式是否正确
   - 确认函数路径是否存在
   - 验证API连接是否正常

2. **状态管理问题**
   - 检查状态管理器配置
   - 确认TTL设置是否合理
   - 验证会话隔离是否启用

3. **权限问题**
   - 检查API密钥配置
   - 确认文件访问权限
   - 验证网络连接权限

### 调试技巧

1. **启用详细日志**：调整日志级别获取更多信息
2. **检查状态信息**：使用 `get_context_info()` 查看工具状态
3. **验证配置**：使用 `validate_tool_config()` 验证配置
4. **监控统计**：查看状态管理器的统计信息

## 总结

本工具系统通过基于状态管理的设计，提供了灵活且强大的工具定义和执行能力。无状态工具适用于简单快速的操作，而有状态工具则支持复杂的业务逻辑和状态持久化。

通过明确区分业务逻辑无状态的REST工具和需要复杂状态管理的有状态工具，并推荐使用MCP协议实现后者，系统保持了架构的清晰性和可维护性：

- **REST工具**：专注于业务逻辑上无状态的API调用，技术上使用状态管理器优化连接和性能
- **MCP工具**：适用于需要复杂业务状态管理的场景，如浏览器操作、数据库连接等
- **原生工具**：适用于项目内部需要状态管理的复杂业务逻辑

通过合理的状态管理和配置设计，系统能够满足各种场景下的工具需求，同时保持系统的可扩展性和稳定性。