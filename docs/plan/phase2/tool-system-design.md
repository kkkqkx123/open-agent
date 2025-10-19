# 工具系统模块详细设计

## 模块概述

**模块名称**：工具系统  
**开发周期**：5天  
**依赖模块**：配置系统、模型集成、基础架构  
**目标**：实现工具的统一管理，支持多类型工具（原生、MCP、内置），提供灵活的输出格式化策略

## 1. 架构设计

### 1.1 模块结构
```
src/tools/
├── __init__.py
├── interfaces.py          # 核心接口定义
├── base.py               # BaseTool抽象类
├── manager.py            # ToolManager实现
├── formatter.py          # ToolFormatter实现
├── executor.py           # ToolExecutor实现
├── types/                # 工具类型实现
│   ├── __init__.py
│   ├── native_tool.py    # 原生能力工具
│   ├── mcp_tool.py       # MCP工具
│   └── builtin_tool.py   # 内置工具
├── config.py             # 工具配置模型
└── utils/                # 工具类
    ├── __init__.py
    ├── schema_generator.py
    └── validator.py
```

### 1.2 核心接口定义

#### IToolManager
```python
class IToolManager(ABC):
    """工具管理器接口"""
    
    @abstractmethod
    def load_tools(self) -> list[BaseTool]:
        """加载所有可用工具"""
        pass
        
    @abstractmethod
    def get_tool(self, name: str) -> BaseTool:
        """根据名称获取工具"""
        pass
        
    @abstractmethod
    def get_tool_set(self, name: str) -> list[BaseTool]:
        """获取工具集"""
        pass
        
    @abstractmethod
    def register_tool(self, tool: BaseTool) -> None:
        """注册新工具"""
        pass
```

#### IToolFormatter
```python
class IToolFormatter(ABC):
    """工具格式化器接口"""
    
    @abstractmethod
    def format_for_llm(self, tools: list[BaseTool]) -> dict:
        """将工具格式化为LLM可识别的格式"""
        pass
        
    @abstractmethod
    def detect_strategy(self, llm_client: ILLMClient) -> str:
        """检测模型支持的输出策略"""
        pass
        
    @abstractmethod
    def parse_llm_response(self, response: BaseMessage) -> ToolCall:
        """解析LLM的工具调用响应"""
        pass
```

#### IToolExecutor
```python
class IToolExecutor(ABC):
    """工具执行器接口"""
    
    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass
        
    @abstractmethod
    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用"""
        pass
        
    @abstractmethod
    def execute_parallel(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """并行执行多个工具调用"""
        pass
```

## 2. 工具类型实现

### 2.1 BaseTool抽象类
```python
class BaseTool(ABC):
    """工具基类"""
    
    name: str
    description: str
    parameters_schema: dict
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass
        
    @abstractmethod
    async def execute_async(self, **kwargs) -> Any:
        """异步执行工具"""
        pass
        
    def get_schema(self) -> dict:
        """获取工具Schema"""
        return self.parameters_schema
```

### 2.2 NativeTool（原生能力工具）
```python
class NativeTool(BaseTool):
    """原生能力工具，调用外部API"""
    
    def __init__(self, config: NativeToolConfig):
        self.config = config
        self.http_client = AsyncHTTPClient()
        
    async def execute_async(self, **kwargs) -> Any:
        # 验证参数
        self._validate_parameters(kwargs)
        
        # 构建HTTP请求
        headers = self._build_headers()
        data = self._build_request_data(kwargs)
        
        # 发送请求
        response = await self.http_client.request(
            method=self.config.method,
            url=self.config.api_url,
            headers=headers,
            data=data,
            timeout=self.config.timeout
        )
        
        return self._parse_response(response)
```

### 2.3 MCPTool（MCP工具）
```python
class MCPTool(BaseTool):
    """MCP服务器提供的工具"""
    
    def __init__(self, config: MCPToolConfig):
        self.config = config
        self.mcp_client = MCPClient(config.mcp_server_url)
        
    async def execute_async(self, **kwargs) -> Any:
        # 获取工具Schema
        schema = await self.mcp_client.get_tool_schema(self.name)
        
        # 执行工具
        result = await self.mcp_client.execute_tool(
            tool_name=self.name,
            arguments=kwargs
        )
        
        return result
```

### 2.4 BuiltinTool（内置工具）
```python
class BuiltinTool(BaseTool):
    """项目内部Python函数工具"""
    
    def __init__(self, func: Callable, config: BuiltinToolConfig):
        self.func = func
        self.config = config
        
    def execute(self, **kwargs) -> Any:
        # 同步执行Python函数
        return self.func(**kwargs)
        
    async def execute_async(self, **kwargs) -> Any:
        # 异步执行Python函数
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            # 在线程池中执行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.func, **kwargs)
```

## 3. 工具管理器实现

### 3.1 ToolManager核心逻辑
```python
class ToolManager(IToolManager):
    """工具管理器实现"""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self._tools: dict[str, BaseTool] = {}
        self._tool_sets: dict[str, list[str]] = {}
        
    def load_tools(self) -> list[BaseTool]:
        """加载所有工具"""
        # 1. 加载工具配置
        tool_configs = self.config_loader.load_tool_configs()
        
        # 2. 创建工具实例
        for config in tool_configs:
            tool = self._create_tool(config)
            if tool.name not in self._tools:
                self._tools[tool.name] = tool
            else:
                # 重复工具警告
                logger.warning(f"工具名称重复: {tool.name}")
                
        # 3. 加载工具集配置
        self._load_tool_sets()
        
        return list(self._tools.values())
        
    def _create_tool(self, config: ToolConfig) -> BaseTool:
        """根据配置创建工具实例"""
        if config.tool_type == "native":
            return NativeTool(config)
        elif config.tool_type == "mcp":
            return MCPTool(config)
        elif config.tool_type == "builtin":
            return BuiltinTool(config)
        else:
            raise ValueError(f"未知的工具类型: {config.tool_type}")
```

## 4. 输出格式化策略

### 4.1 Function Calling策略
```python
class FunctionCallingFormatter(IToolFormatter):
    """Function Calling格式化策略"""
    
    def format_for_llm(self, tools: list[BaseTool]) -> dict:
        """生成Function Calling格式"""
        functions = []
        for tool in tools:
            function = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_schema()
            }
            functions.append(function)
            
        return {"functions": functions}
        
    def parse_llm_response(self, response: BaseMessage) -> ToolCall:
        """解析Function Calling响应"""
        if hasattr(response, "function_call"):
            return ToolCall(
                name=response.function_call.name,
                arguments=json.loads(response.function_call.arguments)
            )
        else:
            raise ValueError("LLM响应不包含Function Calling")
```

### 4.2 结构化输出策略
```python
class StructuredOutputFormatter(IToolFormatter):
    """结构化输出格式化策略"""
    
    def format_for_llm(self, tools: list[BaseTool]) -> dict:
        """生成结构化输出提示词"""
        tool_descriptions = []
        for tool in tools:
            desc = f"- {tool.name}: {tool.description}"
            tool_descriptions.append(desc)
            
        prompt = f"""
请按以下JSON格式调用工具：
{{
    "name": "工具名称",
    "parameters": {{
        "参数1": "值1",
        "参数2": "值2"
    }}
}}

可用工具：
{"\n".join(tool_descriptions)}
"""
        return {"prompt": prompt}
```

## 5. 工具执行器

### 5.1 核心执行逻辑
```python
class ToolExecutor(IToolExecutor):
    """工具执行器实现"""
    
    def __init__(self, tool_manager: IToolManager):
        self.tool_manager = tool_manager
        self.timeout = 30  # 默认超时时间
        
    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用"""
        try:
            # 获取工具实例
            tool = self.tool_manager.get_tool(tool_call.name)
            
            # 设置超时
            async with asyncio.timeout(self.timeout):
                # 执行工具
                result = await tool.execute_async(**tool_call.arguments)
                
                return ToolResult(
                    success=True,
                    output=result,
                    tool_name=tool_call.name
                )
                
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="工具调用超时",
                tool_name=tool_call.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=tool_call.name
            )
```

## 6. 配置管理

### 6.1 工具配置模型
```python
@dataclass
class ToolConfig:
    """工具配置基类"""
    name: str
    tool_type: str  # "native", "mcp", "builtin"
    description: str
    enabled: bool = True
    
@dataclass
class NativeToolConfig(ToolConfig):
    """原生工具配置"""
    api_url: str
    method: str = "POST"
    headers: dict = field(default_factory=dict)
    timeout: int = 30
    auth_method: str = "api_key"  # "api_key", "oauth", "none"
```

### 6.2 工具集配置
```yaml
# configs/tool-sets/data-analysis.yaml
name: data_analysis_set
description: 数据分析工具集
tools:
  - sql_query_tool
  - excel_analysis_tool
  - chart_generation_tool
```

## 7. 测试策略

### 7.1 单元测试
```python
class TestToolManager:
    def test_tool_loading(self):
        """测试工具加载"""
        manager = ToolManager(mock_config_loader)
        tools = manager.load_tools()
        assert len(tools) > 0
        
    def test_tool_duplication(self):
        """测试工具去重"""
        # 测试重复工具名称的处理
        pass

class TestToolExecutor:
    def test_tool_execution(self):
        """测试工具执行"""
        executor = ToolExecutor(mock_tool_manager)
        result = executor.execute(tool_call)
        assert result.success
```

### 7.2 集成测试
```python
class TestToolSystemIntegration:
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 加载工具 → 格式化 → LLM调用 → 执行 → 结果处理
        pass
        
    def test_parallel_execution(self):
        """测试并行工具执行"""
        pass
```

## 8. 实施计划

### 第1天：基础架构
- 定义核心接口和抽象类
- 实现BaseTool和工具类型基类
- 创建配置模型

### 第2天：工具实现
- 实现NativeTool、MCPTool、BuiltinTool
- 开发工具管理器
- 实现工具加载和注册逻辑

### 第3天：格式化策略
- 实现Function Calling格式化
- 实现结构化输出格式化
- 开发策略检测机制

### 第4天：执行器与安全
- 实现工具执行器
- 添加参数校验和超时控制
- 实现并行执行功能

### 第5天：集成测试
- 编写单元测试和集成测试
- 创建示例工具和配置
- 性能测试和优化

## 9. 关键依赖

### 9.1 内部依赖
- **配置系统**：加载工具配置
- **模型集成**：检测模型能力
- **日志系统**：记录工具调用日志

### 9.2 外部依赖
- **requests/aiohttp**：HTTP客户端
- **pydantic**：数据验证
- **langchain**：工具基础类

---
*文档版本：V1.0*
*创建日期：2025-10-19*