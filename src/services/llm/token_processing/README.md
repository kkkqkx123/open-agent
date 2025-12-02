# Token处理模块文档

## 概述

Token处理模块提供统一的Token计算和解析功能，支持多种LLM提供商，具备完整的降级策略、缓存机制和对话跟踪功能。

## 架构设计

### 核心设计原则

1. **统一tiktoken依赖**：所有处理器完全依赖tiktoken，移除了除4等不准确的估算方法
2. **组合模式**：HybridTokenProcessor可以组合使用具体处理器的专门能力
3. **降级策略**：API → 缓存 → 本地计算的完整降级链
4. **类型安全**：严格的类型注解和mypy检查

### 模块结构

```
token_processing/
├── __init__.py                 # 模块导出
├── README.md                   # 本文档
├── token_types.py              # 数据类型定义
├── base_processor.py           # 基础接口和抽象类
├── local_calculator.py         # 本地Token计算器
├── openai_processor.py         # OpenAI专用处理器
├── anthropic_processor.py      # Anthropic专用处理器
├── gemini_processor.py         # Gemini专用处理器
├── hybrid_processor.py         # 混合处理器（功能最完整）
├── conversation_tracker.py     # 对话跟踪器
└── issue.md                    # 已知问题和解决方案
```

## 文件详细说明

### 1. `token_types.py` - 数据类型定义

**作用**：定义Token处理相关的核心数据结构

**主要组件**：
- `TokenUsage`：Token使用情况的数据类
  - 包含prompt_tokens、completion_tokens、total_tokens
  - 支持来源标识（local/api）
  - 提供数据合并、复制、序列化等功能

**使用场景**：
```python
# 创建Token使用记录
usage = TokenUsage(
    prompt_tokens=10,
    completion_tokens=5,
    total_tokens=15,
    source="api"
)

# 合并多个使用记录
total_usage = usage1.add(usage2)
```

### 2. `base_processor.py` - 基础接口和抽象类

**作用**：定义Token处理器的统一接口和基础实现

**主要组件**：
- `ITokenProcessor`：Token处理器接口
  - 定义了count_tokens、parse_response等核心方法
  - 包含缓存、降级、统计等扩展接口

- `BaseTokenProcessor`：基础实现类
  - 提供缓存机制（FIFO策略）
  - 实现降级策略框架
  - 统计信息收集
  - 对话跟踪支持

**关键特性**：
- 统一的tiktoken编码器加载
- 完整的缓存机制（默认1000条目）
- 降级策略支持
- 详细的统计信息

### 3. `local_calculator.py` - 本地Token计算器

**作用**：提供纯本地的Token计算能力

**主要特性**：
- 完全基于tiktoken的准确计算
- 支持模型特定的编码器选择
- 消息格式的Token计算（包含格式开销）
- 无API依赖的本地计算

**使用场景**：
```python
calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
token_count = calculator.count_tokens("Hello, world!")
```

### 4. `openai_processor.py` - OpenAI专用处理器

**作用**：专门处理OpenAI模型的Token计算和API响应解析

**主要特性**：
- 模型特定的tiktoken编码器
- OpenAI API响应格式解析
- 消息格式的精确Token计算
- 模型定价信息支持

**API响应格式**：
```python
{
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
}
```

### 5. `anthropic_processor.py` - Anthropic专用处理器

**作用**：专门处理Anthropic Claude模型的Token计算和API响应解析

**主要特性**：
- 使用cl100k_base编码器（最接近Claude的公开编码器）
- Anthropic API响应格式解析
- 缓存相关Token支持
- 模型定价信息

**API响应格式**：
```python
{
    "usage": {
        "input_tokens": 10,
        "output_tokens": 5
    }
}
```

### 6. `gemini_processor.py` - Gemini专用处理器

**作用**：专门处理Google Gemini模型的Token计算和API响应解析

**主要特性**：
- 使用cl100k_base编码器（最接近Gemini的公开编码器）
- Gemini API响应格式解析
- 思考Token和缓存Token支持
- 模型定价信息

**API响应格式**：
```python
{
    "usageMetadata": {
        "promptTokenCount": 10,
        "candidatesTokenCount": 5,
        "totalTokenCount": 15
    }
}
```

### 7. `hybrid_processor.py` - 混合处理器

**作用**：提供功能最完整的Token处理解决方案

**主要特性**：
- **完整的降级策略**：API → 缓存 → 本地计算
- **组合模式支持**：可以组合使用具体处理器的API解析能力
- **灵活配置**：支持优先API、降级开关、缓存大小等配置
- **对话跟踪**：内置对话历史和统计功能
- **性能优化**：智能缓存和统计收集

**使用场景**：
```python
# 独立使用
processor = HybridTokenProcessor(
    model_name="gpt-3.5-turbo",
    provider="openai",
    prefer_api=True,
    enable_degradation=True
)

# 组合使用具体处理器
anthropic_processor = AnthropicTokenProcessor("claude-3-sonnet-20240229")
hybrid_processor = HybridTokenProcessor(
    specific_processor=anthropic_processor
)
```

**降级策略流程**：
1. 优先使用API响应中的Token数量
2. 检查缓存中是否有计算结果
3. 使用本地计算器进行计算
4. 根据降级阈值决定是否使用本地结果

### 8. `conversation_tracker.py` - 对话跟踪器

**作用**：跟踪和管理对话历史，提供详细的Token使用统计

**主要特性**：
- **会话管理**：支持多会话跟踪
- **消息记录**：详细的消息历史和Token使用
- **统计分析**：丰富的统计信息和指标
- **数据导出**：支持JSON、TXT、CSV格式导出
- **历史清理**：灵活的历史记录管理

**使用场景**：
```python
tracker = ConversationTracker(max_history=1000)

# 开始会话
session_id = tracker.start_session("my_session")

# 添加消息
tracker.add_message(message, token_count=10)

# 获取统计
stats = tracker.get_stats()

# 导出数据
export_data = tracker.export_conversation("json")
```

### 9. `__init__.py` - 模块导出

**作用**：定义模块的公共接口

**导出内容**：
```python
__all__ = [
    "TokenUsage",              # 数据类型
    "ITokenProcessor",         # 接口
    "BaseTokenProcessor",      # 基础实现
    "OpenAITokenProcessor",    # OpenAI处理器
    "GeminiTokenProcessor",    # Gemini处理器
    "AnthropicTokenProcessor", # Anthropic处理器
    "HybridTokenProcessor",    # 混合处理器
    "ConversationTracker",     # 对话跟踪器
]
```

## 使用指南

### 基本使用

```python
from src.services.llm.token_processing import (
    HybridTokenProcessor, 
    OpenAITokenProcessor,
    AnthropicTokenProcessor
)

# 使用具体处理器
openai_processor = OpenAITokenProcessor("gpt-3.5-turbo")
tokens = openai_processor.count_tokens("Hello, world!")

# 使用混合处理器
hybrid_processor = HybridTokenProcessor(
    model_name="claude-3-sonnet-20240229",
    provider="anthropic",
    specific_processor=AnthropicTokenProcessor("claude-3-sonnet-20240229")
)
```

### 高级配置

```python
# 配置混合处理器
processor = HybridTokenProcessor(
    model_name="gpt-4",
    provider="openai",
    prefer_api=True,           # 优先使用API计算
    enable_degradation=True,   # 启用降级策略
    cache_size=2000,          # 缓存大小
    enable_conversation_tracking=True  # 启用对话跟踪
)

# 解析API响应
api_response = {
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
}
usage = processor.parse_response(api_response)
```

### 统计和监控

```python
# 获取处理器统计信息
stats = processor.get_stats()
print(f"成功率: {stats['success_rate_percent']}%")
print(f"缓存命中率: {stats['cache_hits']}")

# 获取对话统计
if processor.supports_conversation_tracking():
    conv_stats = processor.get_conversation_stats()
    print(f"总消息数: {conv_stats['total_messages']}")
    print(f"总Token数: {conv_stats['total_tokens']}")
```

## 最佳实践

### 1. 处理器选择

- **已知模型**：使用具体的处理器（OpenAITokenProcessor等）
- **未知模型**：使用HybridTokenProcessor作为兜底
- **生产环境**：推荐使用HybridTokenProcessor的完整功能

### 2. 性能优化

- 启用缓存机制减少重复计算
- 使用对话跟踪监控Token使用
- 合理设置缓存大小避免内存溢出

### 3. 错误处理

- 检查处理器的返回值是否为None
- 监控统计信息中的失败率
- 合理配置降级策略阈值

## 依赖关系

### 外部依赖
- `tiktoken`：Token编码和计算（必需）
- `langchain-core`：消息类型定义
- `pydantic`：数据验证（通过其他模块）

### 内部依赖
- `src.services.logger`：日志记录
- `src.interfaces.llm.encoding`：编码协议接口
- `src.services.llm.utils.encoding_protocol`：编码工具

## 扩展指南

### 添加新的处理器

1. 继承`BaseTokenProcessor`
2. 实现必要的抽象方法
3. 添加模型特定的API响应解析
4. 在`__init__.py`中导出新处理器

### 自定义降级策略

1. 重写`_should_degrade`方法
2. 实现自定义的降级逻辑
3. 添加相应的配置选项

## 故障排除

### 常见问题

1. **tiktoken导入失败**
   - 确保安装了tiktoken：`pip install tiktoken`
   - 检查Python环境和依赖版本

2. **Token计算不准确**
   - 确保使用了正确的编码器
   - 检查模型名称是否正确
   - 验证API响应格式

3. **性能问题**
   - 调整缓存大小
   - 启用降级策略
   - 监控统计信息

### 调试技巧

- 启用详细日志记录
- 使用统计信息监控系统状态
- 利用对话跟踪功能分析Token使用模式

## 版本历史

- **v1.0**：基础架构和核心功能
- **v1.1**：添加对话跟踪功能
- **v1.2**：统一tiktoken依赖，移除除4估算
- **v1.3**：重构HybridTokenProcessor，支持组合模式

## 贡献指南

1. 遵循现有的代码风格和类型注解
2. 添加适当的单元测试
3. 更新相关文档
4. 确保通过mypy类型检查