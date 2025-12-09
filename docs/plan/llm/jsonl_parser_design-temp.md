# JSONL解析功能设计文档

## 概述

本文档描述了为不支持function calling的LLM API添加JSONL（JSON Lines）解析功能的设计方案。JSONL格式允许在不支持原生function calling的模型中实现工具调用功能。

## 背景与需求

### 当前问题
- 部分LLM API不支持原生的function calling功能
- 现有的工具调用解析器只支持单个工具调用
- 缺少批量工具调用处理能力
- 不支持流式工具调用解析

### JSONL格式优势
- **兼容性强**：几乎所有LLM都能生成JSON格式文本
- **批量处理**：支持一次调用多个工具
- **流式友好**：适合流式响应处理
- **错误恢复**：部分解析失败不影响其他调用

## 设计方案

### 1. JSONL格式规范

#### 标准JSONL格式
```json
{"name": "tool_name", "parameters": {"param1": "value1"}}
{"name": "tool_name2", "parameters": {"param2": "value2"}}
```

#### 扩展格式（支持call_id）
```json
{"name": "tool_name", "parameters": {"param1": "value1"}, "call_id": "call_123"}
{"name": "tool_name2", "parameters": {"param2": "value2"}, "call_id": "call_456"}
```

#### 错误处理格式
```json
{"name": "tool_name", "parameters": {"param1": "value1"}, "error": "参数验证失败"}
{"name": "tool_name2", "parameters": {"param2": "value2"}}
```

### 2. 架构设计

#### 核心组件
```
JSONLParser
├── JsonlLineParser      # 单行JSON解析
├── JsonlBatchParser     # 批量解析
├── JsonlStreamParser    # 流式解析
└── JsonlValidator       # 格式验证
```

#### 集成点
- `ToolCallParser` - 添加JSONL解析方法
- `StructuredOutputFormatter` - 增强JSONL提示词
- `LLM客户端` - 动态格式检测和适配

### 3. 实现细节

#### 3.1 JSONL解析器类

```python
class JsonlParser:
    """JSONL格式工具调用解析器"""
    
    @staticmethod
    def parse_jsonl_line(line: str) -> Optional[ToolCall]:
        """解析单行JSONL"""
        
    @staticmethod
    def parse_jsonl_batch(content: str) -> List[ToolCall]:
        """解析批量JSONL"""
        
    @staticmethod
    def parse_jsonl_stream(stream: AsyncGenerator[str, None]) -> AsyncGenerator[ToolCall, None]:
        """解析流式JSONL"""
        
    @staticmethod
    def validate_jsonl_format(content: str) -> List[str]:
        """验证JSONL格式"""
```

#### 3.2 JSONLStructuredOutputFormatter

```python
class JSONLStructuredOutputFormatter(IToolFormatter):
    """增强的结构化输出格式化器，支持JSONL"""
    
    def format_for_llm_jsonl(self, tools: Sequence[ITool]) -> Dict[str, Any]:
        """为不支持function calling的LLM生成JSONL格式提示词"""
        
    def parse_jsonl_response(self, response: IBaseMessage) -> List[ToolCall]:
        """解析JSONL格式的LLM响应"""
```

#### 3.3 提示词模板

##### JSONL格式提示词
```python
JSONL_PROMPT_TEMPLATE = """
请按以下JSON Lines格式调用工具（每行一个JSON对象）：

{"name": "工具名称", "parameters": {"参数1": "值1"}}
{"name": "工具名称", "parameters": {"参数2": "值2"}}

可用工具：
{tool_descriptions}

要求：
1. 每行必须是有效的JSON对象
2. 支持一次调用多个工具
3. 如果调用失败，请在JSON中添加"error"字段
4. 不要包含任何解释性文本

请严格按照JSON Lines格式返回结果。
"""
```

##### 单行JSON格式提示词（向后兼容）
```python
SINGLE_JSON_PROMPT_TEMPLATE = """
请按以下JSON格式调用工具：
{
    "name": "工具名称",
    "parameters": {
        "参数1": "值1",
        "参数2": "值2"
    }
}

可用工具：
{tool_descriptions}

请只返回JSON格式的工具调用，不要包含其他文本。
"""
```

### 4. LLM客户端集成

#### 4.1 格式检测逻辑

```python
def detect_tool_calling_support(llm_client: ILLMClient) -> str:
    """检测LLM客户端的工具调用支持能力"""
    if llm_client.supports_function_calling():
        return "function_calling"
    else:
        return "jsonl"
```

#### 4.2 动态提示词生成

```python
def generate_tool_prompt(tools: Sequence[ITool], format_type: str) -> str:
    """根据格式类型生成提示词"""
    if format_type == "function_calling":
        return generate_function_calling_prompt(tools)
    elif format_type == "jsonl":
        return generate_jsonl_prompt(tools)
    else:
        return generate_single_json_prompt(tools)
```

#### 4.3 响应解析适配

```python
def parse_tool_response(response: IBaseMessage, format_type: str) -> List[ToolCall]:
    """根据格式类型解析工具调用响应"""
    if format_type == "function_calling":
        return parse_function_calling_response(response)
    elif format_type == "jsonl":
        return parse_jsonl_response(response)
    else:
        return [parse_single_json_response(response)]
```

### 5. 错误处理机制

#### 5.1 解析错误处理
- 跳过格式错误的行
- 记录错误信息
- 继续处理其他有效行
- 提供详细的错误报告

#### 5.2 验证机制
- JSON格式验证
- 必需字段检查
- 参数类型验证
- 工具名称验证

### 6. 性能优化

#### 6.1 流式处理
- 逐行解析，减少内存占用
- 异步处理，提高响应速度
- 背压控制，防止内存溢出

#### 6.2 缓存机制
- 解析结果缓存
- 提示词模板缓存
- 格式检测结果缓存

## 实施计划

### 第一阶段：核心解析器实现
1. 实现`JsonlParser`类
2. 添加基本的JSONL解析功能
3. 编写单元测试

### 第二阶段：格式化器增强
1. 扩展`StructuredOutputFormatter`
2. 实现JSONL提示词生成
3. 添加响应解析功能

### 第三阶段：LLM客户端集成
1. 实现格式检测逻辑
2. 添加动态提示词生成
3. 集成响应解析适配

### 第四阶段：测试和优化
1. 编写集成测试
2. 性能测试和优化
3. 文档完善

## 兼容性考虑

### 向后兼容
- 保持现有API不变
- 默认行为不变
- 渐进式迁移

### 多格式支持
- Function Calling格式
- JSONL格式
- 单行JSON格式
- 自定义格式扩展

## 风险评估

### 技术风险
- **解析复杂性**：JSONL格式比单JSON更复杂
- **性能影响**：批量解析可能影响性能
- **错误处理**：需要robust的错误处理机制

### 缓解措施
- 充分的单元测试和集成测试
- 性能基准测试
- 详细的错误日志和监控

## 总结

JSONL解析功能将显著提升系统对不支持function calling的LLM API的兼容性，同时提供批量工具调用和流式处理能力。通过分阶段实施和充分的测试，可以确保功能的稳定性和可靠性。