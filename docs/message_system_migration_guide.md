# 消息系统迁移指南

本指南帮助开发者从 LangChain 消息系统迁移到项目内部的消息系统实现。

## 1. 迁移概述

### 1.1 迁移目标
- 完全替代 `langchain_core.messages` 依赖
- 保持 API 兼容性
- 提供更好的性能和可扩展性
- 减少项目体积和依赖复杂度

### 1.2 迁移范围
- 52个文件引用了 `langchain_core.messages`
- 主要涉及核心层、服务层和适配器层
- 需要更新导入语句和部分使用方式

## 2. 新消息系统架构

### 2.1 目录结构
```
src/
├── interfaces/
│   └── messages.py              # 消息系统接口定义
├── infrastructure/
│   └── messages/
│       ├── __init__.py          # 模块导出
│       ├── base.py              # BaseMessage 基础实现
│       ├── types.py             # 具体消息类型
│       ├── converters.py        # 消息转换器
│       ├── factory.py           # 消息工厂
│       ├── adapters.py          # 兼容性适配器
│       └── utils.py             # 工具函数
```

### 2.2 核心组件
- **IBaseMessage**: 消息接口定义
- **BaseMessage**: 基础消息实现
- **HumanMessage/AIMessage/SystemMessage/ToolMessage**: 具体消息类型
- **MessageConverter**: 消息格式转换
- **MessageFactory**: 消息创建工厂
- **LangChainCompatibilityAdapter**: LangChain 兼容性适配器

## 3. 迁移步骤

### 3.1 第一阶段：更新导入语句

#### 旧代码
```python
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
```

#### 新代码
```python
from src.infrastructure.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
```

### 3.2 第二阶段：更新消息创建

#### 旧代码
```python
# 直接创建 LangChain 消息
message = HumanMessage(content="Hello")
```

#### 新代码（方式一：直接导入）
```python
from src.infrastructure.messages import HumanMessage
message = HumanMessage(content="Hello")
```

#### 新代码（方式二：使用工厂）
```python
from src.infrastructure.messages.factory import create_human_message
message = create_human_message("Hello")
```

### 3.3 第三阶段：更新消息转换

#### 旧代码
```python
from langchain_core.messages import BaseMessage
from src.core.llm.models import LLMMessage

# 手动转换
def convert_to_llm(message: BaseMessage) -> LLMMessage:
    # 复杂的转换逻辑...
    pass
```

#### 新代码
```python
from src.infrastructure.messages.converters import MessageConverter

# 使用转换器
converter = MessageConverter()
llm_message = converter.from_base_message(base_message)
```

### 3.4 第四阶段：更新类型注解

#### 旧代码
```python
from langchain_core.messages import BaseMessage

def process_message(message: BaseMessage) -> None:
    pass
```

#### 新代码
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

def process_message(message: "IBaseMessage") -> None:
    pass
```

## 4. 兼容性保证

### 4.1 兼容性适配器
提供 `LangChainCompatibilityAdapter` 确保与现有 LangChain 代码的兼容性：

```python
from src.infrastructure.messages.adapters import LangChainCompatibilityAdapter

# 自动检测和转换
message = LangChainCompatibilityAdapter.auto_convert(some_message)

# 批量转换
messages = LangChainCompatibilityAdapter.convert_list_from_langchain(langchain_messages)
```

### 4.2 渐进式迁移
支持新旧系统并存，允许渐进式迁移：

```python
try:
    # 尝试使用新系统
    from src.infrastructure.messages import HumanMessage
    message = HumanMessage(content="Hello")
except ImportError:
    # 回退到旧系统
    from langchain_core.messages import HumanMessage
    message = HumanMessage(content="Hello")
```

## 5. API 变更

### 5.1 保持不变的 API
- 消息的基本属性（content, type, name, id）
- 消息的创建方式
- 消息的序列化/反序列化

### 5.2 新增的 API
- `get_text_content()`: 获取纯文本内容
- `has_tool_calls()`: 检查是否包含工具调用
- `copy(**kwargs)`: 创建消息副本
- 消息工厂模式
- 丰富的工具函数

### 5.3 移除的 API
- LangChain 特有的方法和属性
- 不必要的复杂性

## 6. 性能优化

### 6.1 内存优化
- 使用 `__slots__` 减少内存占用
- 消息池复用机制
- 延迟加载非必要属性

### 6.2 转换优化
- 转换结果缓存
- 批量转换支持
- 智能类型检测

### 6.3 序列化优化
- 高效的序列化格式
- 压缩支持
- 流式处理

## 7. 测试策略

### 7.1 单元测试
```python
def test_message_creation():
    msg = HumanMessage(content="Hello")
    assert msg.content == "Hello"
    assert msg.type == "human"

def test_message_conversion():
    converter = MessageConverter()
    base_msg = converter.to_base_message({"content": "Hello", "type": "human"})
    assert isinstance(base_msg, HumanMessage)
```

### 7.2 集成测试
```python
def test_end_to_end_migration():
    # 测试完整的消息流程
    messages = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi there!")
    ]
    
    # 转换为 LLM 格式
    converter = MessageConverter()
    llm_messages = converter.convert_from_base_list(messages)
    
    # 验证结果
    assert len(llm_messages) == 2
    assert llm_messages[0].role == MessageRole.USER
    assert llm_messages[1].role == MessageRole.ASSISTANT
```

### 7.3 性能测试
```python
def test_performance():
    import time
    
    # 测试大量消息的创建和转换性能
    start_time = time.time()
    
    messages = [HumanMessage(content=f"Message {i}") for i in range(10000)]
    converter = MessageConverter()
    converted = converter.convert_message_list(messages)
    
    end_time = time.time()
    assert end_time - start_time < 1.0  # 应该在1秒内完成
```

## 8. 常见问题

### 8.1 导入错误
**问题**: `ImportError: No module named 'src.infrastructure.messages'`
**解决**: 确保 Python 路径包含项目根目录，或使用相对导入

### 8.2 类型不匹配
**问题**: 类型检查失败
**解决**: 使用 `TYPE_CHECKING` 进行类型注解，避免运行时循环依赖

### 8.3 性能回归
**问题**: 迁移后性能下降
**解决**: 检查是否正确使用了转换器缓存，避免重复转换

### 8.4 兼容性问题
**问题**: 与现有 LangChain 代码不兼容
**解决**: 使用兼容性适配器，或保持新旧系统并存

## 9. 最佳实践

### 9.1 代码风格
- 优先使用工厂方法创建消息
- 使用类型注解提高代码可读性
- 利用工具函数简化常见操作

### 9.2 性能优化
- 重用消息转换器实例
- 使用批量转换方法
- 合理使用缓存机制

### 9.3 错误处理
- 使用适配器处理兼容性问题
- 提供回退机制
- 记录迁移过程中的错误

## 10. 迁移检查清单

### 10.1 代码更新
- [ ] 更新所有导入语句
- [ ] 更新消息创建代码
- [ ] 更新消息转换代码
- [ ] 更新类型注解
- [ ] 添加错误处理

### 10.2 测试验证
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 运行性能测试
- [ ] 验证兼容性

### 10.3 文档更新
- [ ] 更新 API 文档
- [ ] 更新使用示例
- [ ] 更新迁移指南
- [ ] 更新变更日志

## 11. 回滚计划

如果迁移过程中遇到问题，可以按以下步骤回滚：

1. 恢复原始的 LangChain 导入
2. 移除新消息系统的引用
3. 恢复原有的消息处理逻辑
4. 运行测试确保功能正常

## 12. 后续优化

迁移完成后，可以考虑以下优化：

1. 移除 LangChain 依赖
2. 优化消息序列化格式
3. 添加更多消息类型支持
4. 实现消息持久化
5. 添加消息版本控制

---

**注意**: 本迁移指南会随着迁移进展持续更新。如有问题，请及时反馈。