# 工具系统使用指南

本文档介绍如何使用工具系统，包括工具的创建、配置、管理和执行。

## 概述

工具系统是框架的核心组件之一，提供了统一的工具管理、执行和格式化功能。支持三种工具类型：
- **原生工具 (NativeTool)**：调用外部API的工具
- **MCP工具 (MCPTool)**：通过MCP服务器提供的工具
- **内置工具 (BuiltinTool)**：项目内部Python函数工具

## 基本使用

### 1. 创建内置工具

最简单的方式是使用装饰器创建内置工具：

```python
from src.tools.types.builtin_tool import BuiltinTool

@BuiltinTool.create_tool(
    name="calculator",
    description="执行基本数学计算",
    parameters_schema={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        },
        "required": ["expression"]
    }
)
def calculate(expression: str):
    """计算数学表达式"""
    # 实现计算逻辑
    return eval(expression)  # 注意：实际应用中应使用安全的表达式解析器
```

### 2. 使用工具管理器

```python
from src.infrastructure import TestContainer
from src.tools.manager import ToolManager

# 使用测试容器
with TestContainer() as container:
    # 获取工具管理器
    tool_manager = container.get_tool_manager()
    
    # 加载所有工具
    tools = tool_manager.load_tools()
    
    # 获取特定工具
    calculator = tool_manager.get_tool("calculator")
    
    # 执行工具
    result = calculator.execute(expression="2 + 3 * 4")
    print(f"计算结果: {result}")
```

### 3. 使用工具执行器

```python
from src.tools.executor import ToolExecutor
from src.tools.interfaces import ToolCall

# 创建工具执行器
executor = ToolExecutor(tool_manager, logger)

# 创建工具调用
tool_call = ToolCall(
    name="calculator",
    arguments={"expression": "2 + 3 * 4"}
)

# 执行工具
result = executor.execute(tool_call)
if result.success:
    print(f"执行成功: {result.output}")
else:
    print(f"执行失败: {result.error}")
```

## 高级使用

### 1. 并行执行多个工具

```python
# 创建多个工具调用
tool_calls = [
    ToolCall(name="calculator", arguments={"expression": "2 + 3"}),
    ToolCall(name="calculator", arguments={"expression": "4 * 5"}),
    ToolCall(name="calculator", arguments={"expression": "10 / 2"})
]

# 并行执行
results = executor.execute_parallel(tool_calls)

# 处理结果
for result in results:
    if result.success:
        print(f"结果: {result.output}, 耗时: {result.execution_time:.2f}秒")
    else:
        print(f"错误: {result.error}")
```

### 2. 异步执行

```python
import asyncio

async def async_example():
    # 异步执行单个工具
    result = await executor.execute_async(tool_call)
    
    # 异步并行执行多个工具
    results = await executor.execute_parallel_async(tool_calls)
    
    return results

# 运行异步代码
results = asyncio.run(async_example())
```

### 3. 工具格式化

```python
from src.tools.formatter import ToolFormatter

# 创建格式化器
formatter = ToolFormatter()

# 格式化工具为LLM可识别的格式
tools = [calculator]
formatted = formatter.format_for_llm(tools)

# 检测模型支持的策略
strategy = formatter.detect_strategy(llm_client)

# 解析LLM响应
tool_call = formatter.parse_llm_response(llm_response)
```

## 配置管理

### 1. 工具配置文件

在 `configs/tools/` 目录下创建YAML配置文件：

```yaml
# configs/tools/my_tool.yaml
name: my_tool
tool_type: builtin
description: 我的自定义工具
function_path: my_module:my_function
enabled: true
timeout: 30
parameters_schema:
  type: object
  properties:
    param1:
      type: string
      description: 参数1
    param2:
      type: integer
      description: 参数2
      default: 10
  required:
    - param1
metadata:
  category: "custom"
  tags: ["example", "demo"]
```

### 2. 工具集配置

在 `configs/tool-sets/` 目录下创建工具集配置：

```yaml
# configs/tool-sets/my_tool_set.yaml
name: my_tool_set
description: 我的工具集
enabled: true
tools:
  - calculator
  - my_tool
metadata:
  version: "1.0.0"
  author: "My Name"
```

## 工具类型详解

### 1. 原生工具 (NativeTool)

用于调用外部API的工具：

```python
from src.tools.types.native_tool import NativeTool
from src.tools.config import NativeToolConfig

config = NativeToolConfig(
    name="weather_api",
    description="查询天气信息",
    api_url="https://api.openweathermap.org/data/2.5/weather",
    method="GET",
    auth_method="api_key",
    api_key="your_api_key",
    parameters_schema={
        "type": "object",
        "properties": {
            "q": {"type": "string", "description": "城市名称"}
        },
        "required": ["q"]
    }
)

tool = NativeTool(config)
result = tool.execute(q="Beijing")
```

### 2. MCP工具 (MCPTool)

通过MCP服务器提供的工具：

```python
from src.tools.types.mcp_tool import MCPTool
from src.tools.config import MCPToolConfig

config = MCPToolConfig(
    name="database_query",
    description="数据库查询工具",
    mcp_server_url="http://localhost:8080/mcp",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "SQL查询"}
        },
        "required": ["query"]
    }
)

tool = MCPTool(config)
result = await tool.execute_async(query="SELECT * FROM users")
```

### 3. 内置工具 (BuiltinTool)

包装Python函数的工具：

```python
from src.tools.types.builtin_tool import BuiltinTool
from src.tools.config import BuiltinToolConfig

def my_function(param1: str, param2: int = 10):
    return f"结果: {param1}, {param2}"

config = BuiltinToolConfig(
    name="my_function_tool",
    description="我的函数工具",
    parameters_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer", "default": 10}
        },
        "required": ["param1"]
    }
)

tool = BuiltinTool(my_function, config)
result = tool.execute(param1="test", param2=20)
```

## 最佳实践

### 1. 错误处理

```python
# 使用安全执行方法
result = tool.safe_execute(param1="value")
if not result.success:
    print(f"工具执行失败: {result.error}")

# 使用带验证的执行
result = executor.execute_with_validation(tool_call)
if not result.success:
    print(f"验证或执行失败: {result.error}")
```

### 2. 超时控制

```python
# 设置工具超时
tool_call = ToolCall(
    name="slow_tool",
    arguments={"param1": "value"},
    timeout=10  # 10秒超时
)

# 创建带默认超时的执行器
executor = ToolExecutor(tool_manager, logger, default_timeout=30)
```

### 3. 日志记录

```python
# 工具系统会自动记录执行日志
# 可以通过日志查看工具调用情况
logger.info("开始执行工具")
result = executor.execute(tool_call)
logger.info(f"工具执行完成: {result.success}")
```

### 4. 性能优化

```python
# 对于大量工具调用，使用并行执行
results = executor.execute_parallel(tool_calls)

# 对于异步操作，使用异步执行
results = await executor.execute_parallel_async(tool_calls)

# 缓存工具结果（如果适用）
# 可以在工具实现中添加缓存逻辑
```

## 故障排除

### 1. 常见错误

- **工具不存在**：检查工具名称和注册情况
- **参数验证失败**：检查参数类型和必需参数
- **超时错误**：增加超时时间或优化工具性能
- **API调用失败**：检查API配置和网络连接

### 2. 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查工具信息
tool_info = tool_manager.get_tool_info("tool_name")
print(f"工具信息: {tool_info}")

# 检查工具集信息
tool_set_info = tool_manager.get_tool_set_info("tool_set_name")
print(f"工具集信息: {tool_set_info}")
```

## 扩展开发

### 1. 自定义工具类型

可以通过继承BaseTool类创建自定义工具类型：

```python
from src.tools.base import BaseTool

class CustomTool(BaseTool):
    def __init__(self, config):
        super().__init__(
            name=config.name,
            description=config.description,
            parameters_schema=config.parameters_schema
        )
        # 自定义初始化逻辑
        
    def execute(self, **kwargs):
        # 自定义执行逻辑
        pass
        
    async def execute_async(self, **kwargs):
        # 自定义异步执行逻辑
        pass
```

### 2. 自定义格式化策略

可以通过实现IToolFormatter接口创建自定义格式化策略：

```python
from src.tools.interfaces import IToolFormatter

class CustomFormatter(IToolFormatter):
    def format_for_llm(self, tools):
        # 自定义格式化逻辑
        pass
        
    def detect_strategy(self, llm_client):
        # 自定义策略检测逻辑
        pass
        
    def parse_llm_response(self, response):
        # 自定义响应解析逻辑
        pass
```

## 总结

工具系统提供了灵活、强大的工具管理功能，支持多种工具类型和执行模式。通过合理使用工具系统，可以轻松扩展Agent的能力，实现各种复杂的功能。

更多详细信息请参考API文档和源代码。