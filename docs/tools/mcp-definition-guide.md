# MCP工具配置指南

## 概述

MCP (Model Context Protocol) 工具允许通过MCP服务器提供功能。本指南详细说明如何配置MCP工具，包括支持Stdio、SSE、Streamable HTTP三种方式的配置。

MCP工具的实现类位于 `src/domain/tools/types/mcp_tool.py`，而内置工具的实现类位于 `src/domain/tools/types/builtin_tool.py`，原生工具的实现类位于 `src/domain/tools/types/native_tool.py`。

## MCP配置方式

### 1. Stdio方式配置

Stdio方式通过标准输入输出进行通信。

#### 配置示例

```toml
[mcp]
transport = "stdio"
command = ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
```

```json
{
  "mcp": {
    "transport": "stdio",
    "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
  }
}
```

### 2. SSE方式配置

SSE (Server-Sent Events) 方式通过HTTP进行单向通信。

#### 配置示例

```toml
[mcp]
transport = "sse"
url = "http://localhost:3000/sse"
```

```json
{
  "mcp": {
    "transport": "sse",
    "url": "http://localhost:3000/sse"
  }
}
```

### 3. Streamable HTTP方式配置

Streamable HTTP方式通过HTTP进行双向流式通信。

#### 配置示例

```toml
[mcp]
transport = "http"
url = "http://localhost:3000/http"
```

```json
{
  "mcp": {
    "transport": "http",
    "url": "http://localhost:3000/http"
  }
}
```

## MCP工具配置参数

### 基本配置

```yaml
name: mcp_tool_example
tool_type: mcp
description: 示例MCP工具
enabled: true
timeout: 30
mcp_server_url: "http://localhost:8080/mcp"
dynamic_schema: true
refresh_interval: 300
parameters_schema:
  type: object
  properties:
    # 工具参数定义
  required:
    # 必需参数列表
```

### 参数说明

- `name`: 工具名称
- `tool_type`: 工具类型，必须为 "mcp"
- `description`: 工具描述
- `enabled`: 是否启用工具
- `timeout`: 超时时间（秒）
- `mcp_server_url`: MCP服务器URL
- `dynamic_schema`: 是否动态获取Schema
- `refresh_interval`: Schema刷新间隔（秒）
- `parameters_schema`: 参数Schema

## MCP服务器配置示例

### Sequential Thinking Server

```toml
[mcp.sequentialthinking]
transport = "stdio"
command = ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
```

```json
{
  "mcp": {
    "sequentialthinking": {
      "transport": "stdio",
      "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### Tavily Search Server

```toml
[mcp.tavily]
transport = "stdio"
command = ["npx", "-y", "tavily-mcp@0.2.3"]
```

```json
{
  "mcp": {
    "tavily": {
      "transport": "stdio",
      "command": ["npx", "-y", "tavily-mcp@0.2.3"]
    }
  }
}
```

## 配置文件格式

### JSON格式

```json
{
  "name": "database_query",
  "tool_type": "mcp",
  "description": "通过MCP服务器执行数据库查询",
  "enabled": true,
  "timeout": 30,
  "mcp_server_url": "http://localhost:8080/mcp",
  "dynamic_schema": true,
  "refresh_interval": 300,
  "parameters_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "SQL查询语句"
      },
      "database": {
        "type": "string",
        "description": "数据库名称",
        "default": "default"
      },
      "limit": {
        "type": "integer",
        "description": "返回结果的最大行数",
        "default": 100
      }
    },
    "required": ["query"]
  },
  "metadata": {
    "category": "database",
    "tags": ["database", "sql", "mcp"],
    "server_info": "本地MCP数据库服务器"
  }
}
```

### TOML格式

```toml
name = "database_query"
tool_type = "mcp"
description = "通过MCP服务器执行数据库查询"
enabled = true
timeout = 30
mcp_server_url = "http://localhost:8080/mcp"
dynamic_schema = true
refresh_interval = 300

[parameters_schema]
type = "object"

[parameters_schema.properties.query]
type = "string"
description = "SQL查询语句"

[parameters_schema.properties.database]
type = "string"
description = "数据库名称"
default = "default"

[parameters_schema.properties.limit]
type = "integer"
description = "返回结果的最大行数"
default = 100

[parameters_schema.required]
query = {}

[metadata]
category = "database"
tags = ["database", "sql", "mcp"]
server_info = "本地MCP数据库服务器"
```

## 配置管理

### 环境变量

使用环境变量管理敏感信息：

```yaml
mcp_server_url: "${MCP_SERVER_URL:http://localhost:8080/mcp}"
api_key: "${MCP_API_KEY}"
```

### 多环境配置

```yaml
# 开发环境
development:
  mcp_server_url: "http://localhost:8080/mcp"
  
# 生产环境
production:
  mcp_server_url: "https://mcp.example.com"
```

## 最佳实践

### 1. 安全性

- 使用环境变量存储敏感信息
- 验证MCP服务器证书
- 限制工具权限

### 2. 性能优化

- 合理设置超时时间
- 使用动态Schema减少配置更新频率
- 缓存常用工具信息

### 3. 错误处理

- 提供清晰的错误信息
- 实现重试机制
- 记录错误日志

### 4. 监控

- 监控工具调用性能
- 记录工具使用情况
- 设置告警机制

## 故障排除

### 常见问题

1. **连接失败**: 检查MCP服务器URL和网络连接
2. **认证错误**: 验证API密钥和认证配置
3. **超时**: 调整超时设置或优化工具性能
4. **Schema错误**: 检查参数Schema定义是否正确

### 调试步骤

1. 验证MCP服务器是否正常运行
2. 检查配置文件语法是否正确
3. 确认网络连接是否正常
4. 查看日志文件获取详细错误信息