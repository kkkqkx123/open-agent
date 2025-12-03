# 基础设施层消息系统架构设计

## 1. 架构概述

### 1.1 设计目标
- 完全替代 `langchain_core.messages` 依赖
- 保持与现有代码的兼容性
- 提供高性能、可扩展的消息系统
- 支持项目的三层架构原则

### 1.2 架构原则
- **依赖方向**: 应用层 → 领域层 → 基础设施层
- **接口驱动**: 通过抽象接口解耦具体实现
- **单一职责**: 每个组件只负责一个明确的功能
- **开闭原则**: 对扩展开放，对修改封闭

## 2. 层次结构设计

### 2.1 整体架构
```
src/
├── interfaces/           # 接口层（现有）
│   ├── messages.py      # 消息系统接口定义
│   └── ...
├── infrastructure/      # 基础设施层（新增）
│   └── messages/        # 消息系统实现
│       ├── __init__.py
│       ├── base.py      # BaseMessage 实现
│       ├── types.py     # 具体消息类型
│       ├── converters.py # 消息转换器
│       ├── utils.py     # 工具函数
│       └── adapters.py  # 兼容性适配器
├── core/               # 核心层（现有）
│   └── llm/
│       └── models.py   # 更新为使用新消息系统
├── services/           # 服务层（现有）
│   └── llm/
│       └── utils/
│           └── message_converters.py  # 更新转换逻辑
└── adapters/           # 适配器层（现有）
    └── ...
```

### 2.2 依赖关系
```
应用层 (Services)
    ↓ 依赖
领域层 (Core)
    ↓ 依赖  
基础设施层 (Infrastructure)
    ↓ 实现
接口层 (Interfaces)
```

## 3. 接口设计

### 3.1 消息系统接口 (src/interfaces/messages.py)

```python
"""消息系统接口定义

定义消息系统的核心抽象，遵循领域层接口设计原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

class IBaseMessage(ABC):
    """基础消息接口
    
    定义所有消息类型的核心契约，这是领域层的核心抽象。
    """
    
    @property
    @abstractmethod
    def content(self) -> Union[str, List[Union[str, Dict[str, Any]]]]:
        """获取消息内容"""
        pass
    
    @property
    @abstractmethod
    def type(self) -> str:
        """获取消息类型"""
        pass
    
    @property
    @abstractmethod
    def additional_kwargs(self) -> Dict[str, Any]:
        """获取额外参数"""
        pass
    
    @property
    @abstractmethod
    def response_metadata(self) -> Dict[str, Any]:
        """获取响应元数据"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> Optional[str]:
        """获取消息名称"""
        pass
    
    @property
    @abstractmethod
    def id(self) -> Optional[str]:
        """获取消息ID"""
        pass

class IMessageConverter(ABC):
    """消息转换器接口
    
    定义不同消息格式之间的转换契约。
    """
    
    @abstractmethod
    def to_base_message(self, message: Any) -> IBaseMessage:
        """转换为标准消息格式"""
        pass
    
    @abstractmethod
    def from_base_message(self, message: IBaseMessage) -> Any:
        """从标准消息格式转换"""
        pass

class IMessageFactory(ABC):
    """消息工厂接口
    
    定义消息创建的契约。
    """
    
    @abstractmethod
    def create_human_message(self, content: str, **kwargs) -> IBaseMessage:
        """创建人类消息"""
        pass
    
    @abstractmethod
    def create_ai_message(self, content: str, **kwargs) -> IBaseMessage:
        """创建AI消息"""
        pass
    
    @abstractmethod
    def create_system_message(self, content: str, **kwargs) -> IBaseMessage:
        """创建系统消息"""
        pass
    
    @abstractmethod
    def create_tool_message(self, content: str, tool_call_id: str, **kwargs) -> IBaseMessage:
        """创建工具消息"""
        pass
```

## 4. 实现设计

### 4.1 基础消息类 (src/infrastructure/messages/base.py)

```python
"""基础消息实现

实现 BaseMessage 类，提供消息的核心功能。
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field

from ...interfaces.messages import IBaseMessage

@dataclass
class BaseMessage(IBaseMessage):
    """基础消息实现
    
    提供消息的核心功能，支持序列化和反序列化。
    """
    
    content: Union[str, List[Union[str, Dict[str, Any]]]]
    additional_kwargs: Dict[str, Any] = field(default_factory=dict)
    response_metadata: Dict[str, Any] = field(default_factory=dict)
    type: str = field(init=False)
    name: Optional[str] = None
    id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "content": self.content,
            "type": self.type,
            "additional_kwargs": self.additional_kwargs,
            "response_metadata": self.response_metadata,
            "name": self.name,
            "id": self.id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMessage":
        """从字典创建实例"""
        # 子类需要实现具体的 from_dict 逻辑
        raise NotImplementedError("Subclasses must implement from_dict")
```

### 4.2 具体消息类型 (src/infrastructure/messages/types.py)

```python
"""具体消息类型实现

实现 HumanMessage, AIMessage, SystemMessage, ToolMessage 等具体类型。
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from .base import BaseMessage

@dataclass
class HumanMessage(BaseMessage):
    """人类消息
    
    表示来自用户的消息。
    """
    
    type: str = "human"
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs):
        super().__init__(content=content, **kwargs)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanMessage":
        """从字典创建实例"""
        return cls(
            content=data["content"],
            additional_kwargs=data.get("additional_kwargs", {}),
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id")
        )

@dataclass
class AIMessage(BaseMessage):
    """AI消息
    
    表示来自AI助手的消息。
    """
    
    type: str = "ai"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs):
        super().__init__(content=content, **kwargs)
        self.tool_calls = kwargs.get("tool_calls")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIMessage":
        """从字典创建实例"""
        return cls(
            content=data["content"],
            additional_kwargs=data.get("additional_kwargs", {}),
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id"),
            tool_calls=data.get("tool_calls")
        )

@dataclass
class SystemMessage(BaseMessage):
    """系统消息
    
    表示系统级别的消息，通常用于设置AI行为。
    """
    
    type: str = "system"
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs):
        super().__init__(content=content, **kwargs)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemMessage":
        """从字典创建实例"""
        return cls(
            content=data["content"],
            additional_kwargs=data.get("additional_kwargs", {}),
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id")
        )

@dataclass
class ToolMessage(BaseMessage):
    """工具消息
    
    表示工具执行结果的消息。
    """
    
    type: str = "tool"
    tool_call_id: str
    
    def __init__(self, content: Union[str, List[Union[str, Dict[str, Any]]]], tool_call_id: str, **kwargs):
        super().__init__(content=content, **kwargs)
        self.tool_call_id = tool_call_id
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolMessage":
        """从字典创建实例"""
        return cls(
            content=data["content"],
            tool_call_id=data["tool_call_id"],
            additional_kwargs=data.get("additional_kwargs", {}),
            response_metadata=data.get("response_metadata", {}),
            name=data.get("name"),
            id=data.get("id")
        )
```

### 4.3 消息转换器 (src/infrastructure/messages/converters.py)

```python
"""消息转换器实现

提供不同消息格式之间的转换功能。
"""

from typing import Dict, Any, List, Optional, Union
from ...interfaces.messages import IMessageConverter, IBaseMessage
from ...core.llm.models import LLMMessage, MessageRole
from .types import HumanMessage, AIMessage, SystemMessage, ToolMessage

class MessageConverter(IMessageConverter):
    """消息转换器实现
    
    提供内部消息格式与外部格式之间的转换。
    """
    
    def to_base_message(self, message: Any) -> IBaseMessage:
        """转换为标准消息格式"""
        if isinstance(message, IBaseMessage):
            return message
        elif isinstance(message, LLMMessage):
            return self._from_llm_message(message)
        elif isinstance(message, dict):
            return self._from_dict(message)
        else:
            # 默认转换为人类消息
            return HumanMessage(content=str(message))
    
    def from_base_message(self, message: IBaseMessage) -> Any:
        """从标准消息格式转换"""
        if isinstance(message, LLMMessage):
            return message
        else:
            return self._to_llm_message(message)
    
    def _from_llm_message(self, llm_message: LLMMessage) -> IBaseMessage:
        """从LLMMessage转换"""
        if llm_message.role == MessageRole.USER:
            return HumanMessage(content=llm_message.content)
        elif llm_message.role == MessageRole.ASSISTANT:
            return AIMessage(
                content=llm_message.content,
                tool_calls=llm_message.tool_calls
            )
        elif llm_message.role == MessageRole.SYSTEM:
            return SystemMessage(content=llm_message.content)
        elif llm_message.role == MessageRole.TOOL:
            tool_call_id = llm_message.metadata.get("tool_call_id", "")
            return ToolMessage(content=llm_message.content, tool_call_id=tool_call_id)
        else:
            return HumanMessage(content=llm_message.content)
    
    def _to_llm_message(self, base_message: IBaseMessage) -> LLMMessage:
        """转换为LLMMessage"""
        if isinstance(base_message, HumanMessage):
            role = MessageRole.USER
        elif isinstance(base_message, AIMessage):
            role = MessageRole.ASSISTANT
        elif isinstance(base_message, SystemMessage):
            role = MessageRole.SYSTEM
        elif isinstance(base_message, ToolMessage):
            role = MessageRole.TOOL
        else:
            role = MessageRole.USER
        
        metadata = base_message.additional_kwargs.copy()
        if isinstance(base_message, ToolMessage):
            metadata["tool_call_id"] = base_message.tool_call_id
        elif isinstance(base_message, AIMessage) and base_message.tool_calls:
            metadata["tool_calls"] = base_message.tool_calls
        
        return LLMMessage(
            role=role,
            content=base_message.content if isinstance(base_message.content, str) else str(base_message.content),
            metadata=metadata
        )
    
    def _from_dict(self, message_dict: Dict[str, Any]) -> IBaseMessage:
        """从字典转换"""
        content = message_dict.get("content", "")
        message_type = message_dict.get("type", "human")
        
        if message_type == "human":
            return HumanMessage(content=content, **message_dict)
        elif message_type == "ai":
            return AIMessage(content=content, **message_dict)
        elif message_type == "system":
            return SystemMessage(content=content, **message_dict)
        elif message_type == "tool":
            tool_call_id = message_dict.get("tool_call_id", "")
            return ToolMessage(content=content, tool_call_id=tool_call_id, **message_dict)
        else:
            return HumanMessage(content=content)
```

### 4.4 兼容性适配器 (src/infrastructure/messages/adapters.py)

```python
"""兼容性适配器

提供与 LangChain 消息系统的兼容性支持。
"""

from typing import Dict, Any, List, Optional, Union
from .types import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

class LangChainCompatibilityAdapter:
    """LangChain兼容性适配器
    
    提供与LangChain消息系统的兼容性，确保现有代码无缝迁移。
    """
    
    @staticmethod
    def create_human_message(content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs) -> HumanMessage:
        """创建人类消息（兼容LangChain接口）"""
        return HumanMessage(content=content, **kwargs)
    
    @staticmethod
    def create_ai_message(content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs) -> AIMessage:
        """创建AI消息（兼容LangChain接口）"""
        return AIMessage(content=content, **kwargs)
    
    @staticmethod
    def create_system_message(content: Union[str, List[Union[str, Dict[str, Any]]]], **kwargs) -> SystemMessage:
        """创建系统消息（兼容LangChain接口）"""
        return SystemMessage(content=content, **kwargs)
    
    @staticmethod
    def create_tool_message(content: Union[str, List[Union[str, Dict[str, Any]]]], tool_call_id: str, **kwargs) -> ToolMessage:
        """创建工具消息（兼容LangChain接口）"""
        return ToolMessage(content=content, tool_call_id=tool_call_id, **kwargs)
    
    @staticmethod
    def convert_from_langchain(langchain_message: Any) -> BaseMessage:
        """从LangChain消息转换"""
        # 这里需要处理实际的LangChain消息对象
        # 在迁移过程中，这个方法会逐步替换现有的转换逻辑
        pass
    
    @staticmethod
    def convert_to_langchain(base_message: BaseMessage) -> Any:
        """转换为LangChain消息"""
        # 在迁移过程中，这个方法会逐步替换现有的转换逻辑
        pass
```

## 5. 迁移策略

### 5.1 阶段性迁移
1. **第一阶段**: 创建基础设施层和核心消息类
2. **第二阶段**: 更新核心模块中的消息引用
3. **第三阶段**: 更新服务层中的消息引用
4. **第四阶段**: 更新适配器层中的消息引用
5. **第五阶段**: 移除LangChain依赖

### 5.2 兼容性保证
- 保持现有API接口不变
- 提供适配器层确保平滑过渡
- 渐进式替换，避免破坏性变更

### 5.3 测试策略
- 单元测试覆盖所有消息类型
- 集成测试验证转换逻辑
- 性能测试确保无性能回归

## 6. 性能优化

### 6.1 内存优化
- 使用__slots__减少内存占用
- 实现消息池复用机制
- 延迟加载非必要属性

### 6.2 序列化优化
- 高效的序列化/反序列化
- 支持流式处理
- 压缩大型消息内容

### 6.3 缓存策略
- 消息转换结果缓存
- 常用消息类型缓存
- 智能缓存失效机制

## 7. 扩展性设计

### 7.1 插件化架构
- 支持自定义消息类型
- 可插拔的转换器
- 扩展点设计

### 7.2 版本兼容
- 消息格式版本控制
- 向后兼容性保证
- 平滑升级路径

### 7.3 多协议支持
- 支持不同LLM提供商的消息格式
- 协议适配器机制
- 统一的消息抽象层