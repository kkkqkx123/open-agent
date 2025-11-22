# 提示词工作流重构指南

## 概述

本文档提供了提示词注入工作流系统的全面重构指南，旨在解决当前实现中的类型安全、状态管理、错误处理等问题，并提供一个更加健壮、可扩展和高性能的架构。

## 重构目标

1. **类型安全**：消除类型转换，确保编译时类型检查
2. **状态管理**：实现不可变状态模式，提供状态验证和快照
3. **错误处理**：分层错误处理，提供详细的错误信息和恢复策略
4. **架构优化**：消除职责重叠，降低耦合度，提高可测试性
5. **扩展性**：插件化提示词类型，支持动态扩展
6. **性能优化**：缓存机制，异步加载，批量操作
7. **可维护性**：清晰的接口分离，完善的文档和测试

## 重构步骤

### 第一阶段：状态接口重构

#### 1.1 定义状态接口

创建真正的 `IWorkflowState` 接口，替代当前的字典假设：

```python
# src/interfaces/state/workflow.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime

class IWorkflowState(Protocol):
    """工作流状态接口"""
    
    @property
    def messages(self) -> List[Any]: ...
    
    @property
    def metadata(self) -> Dict[str, Any]: ...
    
    @property
    def created_at(self) -> datetime: ...
    
    @property
    def updated_at(self) -> datetime: ...
    
    def with_messages(self, messages: List[Any]) -> 'IWorkflowState': ...
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IWorkflowState': ...
    
    def get_field(self, key: str, default: Any = None) -> Any: ...
    
    def set_field(self, key: str, value: Any) -> 'IWorkflowState': ...
```

#### 1.2 实现状态类

```python
# src/core/state/workflow_state.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...interfaces.state.workflow import IWorkflowState

@dataclass(frozen=True)
class WorkflowState(IWorkflowState):
    """工作流状态实现"""
    
    messages: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def with_messages(self, messages: List[Any]) -> 'WorkflowState':
        """创建包含新消息的状态"""
        return WorkflowState(
            messages=messages,
            metadata=self.metadata,
            fields=self.fields,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'WorkflowState':
        """创建包含新元数据的状态"""
        return WorkflowState(
            messages=self.messages,
            metadata=metadata,
            fields=self.fields,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        return self.fields.get(key, default)
    
    def set_field(self, key: str, value: Any) -> 'WorkflowState':
        """创建包含新字段值的状态"""
        new_fields = self.fields.copy()
        new_fields[key] = value
        return WorkflowState(
            messages=self.messages,
            metadata=self.metadata,
            fields=new_fields,
            created_at=self.created_at,
            updated_at=datetime.now()
        )
```

#### 1.3 创建状态构建器

```python
# src/core/state/state_builder.py
from typing import Dict, Any, List, Optional
from ...interfaces.state.workflow import IWorkflowState
from .workflow_state import WorkflowState

class StateBuilder:
    """状态构建器"""
    
    def __init__(self, initial_state: Optional[IWorkflowState] = None):
        self._messages = list(initial_state.messages) if initial_state else []
        self._metadata = dict(initial_state.metadata) if initial_state else {}
        self._fields = dict(initial_state.fields) if initial_state else {}
    
    def add_message(self, message: Any) -> 'StateBuilder':
        """添加消息"""
        self._messages.append(message)
        return self
    
    def add_messages(self, messages: List[Any]) -> 'StateBuilder':
        """添加多个消息"""
        self._messages.extend(messages)
        return self
    
    def set_metadata(self, key: str, value: Any) -> 'StateBuilder':
        """设置元数据"""
        self._metadata[key] = value
        return self
    
    def set_field(self, key: str, value: Any) -> 'StateBuilder':
        """设置字段"""
        self._fields[key] = value
        return self
    
    def build(self) -> IWorkflowState:
        """构建状态"""
        return WorkflowState(
            messages=self._messages,
            metadata=self._metadata,
            fields=self._fields
        )
```

### 第二阶段：提示词注入器重构

#### 2.1 重构提示词注入器接口

```python
# src/interfaces/prompts.py
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from .state.workflow import IWorkflowState

if TYPE_CHECKING:
    from .prompts import PromptConfig

class IPromptInjector(ABC):
    """提示词注入器接口"""
    
    @abstractmethod
    async def inject_prompts(
        self,
        state: IWorkflowState,
        config: "PromptConfig"
    ) -> IWorkflowState:
        """异步注入提示词到工作流状态"""
        pass
    
    @abstractmethod
    def inject_system_prompt(
        self,
        state: IWorkflowState,
        prompt_name: str
    ) -> IWorkflowState:
        """注入系统提示词"""
        pass
    
    @abstractmethod
    def inject_rule_prompts(
        self,
        state: IWorkflowState,
        rule_names: List[str]
    ) -> IWorkflowState:
        """注入规则提示词"""
        pass
    
    @abstractmethod
    def inject_user_command(
        self,
        state: IWorkflowState,
        command_name: str
    ) -> IWorkflowState:
        """注入用户指令"""
        pass
```

#### 2.2 重构提示词注入器实现

```python
# src/services/prompts/injector.py
from typing import List, TYPE_CHECKING
from ...interfaces.prompts import IPromptInjector, IPromptLoader, IPromptCache, PromptConfig
from ...interfaces.state.workflow import IWorkflowState
from ...core.state.state_builder import StateBuilder
from ...core.common.exceptions import PromptInjectionError

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

class PromptInjector(IPromptInjector):
    """提示词注入器实现"""
    
    def __init__(
        self,
        loader: IPromptLoader,
        cache: Optional[IPromptCache] = None
    ):
        self.loader = loader
        self.cache = cache
    
    async def inject_prompts(
        self,
        state: IWorkflowState,
        config: PromptConfig
    ) -> IWorkflowState:
        """异步注入提示词到工作流状态"""
        try:
            builder = StateBuilder(state)
            
            # 注入系统提示词
            if config.system_prompt:
                await self._inject_system_prompt_async(builder, config.system_prompt)
            
            # 注入规则提示词
            if config.rules:
                await self._inject_rule_prompts_async(builder, config.rules)
            
            # 注入用户指令
            if config.user_command:
                await self._inject_user_command_async(builder, config.user_command)
            
            return builder.build()
        except Exception as e:
            raise PromptInjectionError(f"注入提示词失败: {e}") from e
    
    async def _inject_system_prompt_async(
        self,
        builder: StateBuilder,
        prompt_name: str
    ) -> None:
        """异步注入系统提示词"""
        content = await self._load_prompt_cached("system", prompt_name)
        message = self._create_system_message(content)
        builder.add_message(message)
    
    async def _inject_rule_prompts_async(
        self,
        builder: StateBuilder,
        rule_names: List[str]
    ) -> None:
        """异步注入规则提示词"""
        for rule_name in rule_names:
            content = await self._load_prompt_cached("rules", rule_name)
            message = self._create_system_message(content)
            builder.add_message(message)
    
    async def _inject_user_command_async(
        self,
        builder: StateBuilder,
        command_name: str
    ) -> None:
        """异步注入用户指令"""
        content = await self._load_prompt_cached("user_commands", command_name)
        message = self._create_human_message(content)
        builder.add_message(message)
    
    async def _load_prompt_cached(self, category: str, name: str) -> str:
        """带缓存的提示词加载"""
        cache_key = f"{category}:{name}"
        
        if self.cache:
            cached_content = await self.cache.get(cache_key)
            if cached_content:
                return cached_content
        
        content = await self.loader.load_prompt_async(category, name)
        
        if self.cache:
            await self.cache.set(cache_key, content)
        
        return content
    
    def _create_system_message(self, content: str) -> "BaseMessage":
        """创建系统消息"""
        from langchain_core.messages import SystemMessage
        return SystemMessage(content=content)
    
    def _create_human_message(self, content: str) -> "BaseMessage":
        """创建人类消息"""
        from langchain_core.messages import HumanMessage
        return HumanMessage(content=content)
```

### 第三阶段：提示词类型系统重构

#### 3.1 定义提示词类型接口

```python
# src/interfaces/prompts/types.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

class PromptType(Enum):
    """提示词类型枚举"""
    SYSTEM = "system"
    RULES = "rules"
    USER_COMMAND = "user_commands"
    CONTEXT = "context"
    EXAMPLES = "examples"
    CONSTRAINTS = "constraints"
    FORMAT = "format"
    CUSTOM = "custom"

class IPromptType(ABC):
    """提示词类型接口"""
    
    @property
    @abstractmethod
    def type_name(self) -> str:
        """类型名称"""
        pass
    
    @property
    @abstractmethod
    def injection_order(self) -> int:
        """注入顺序（数字越小越先注入）"""
        pass
    
    @abstractmethod
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理提示词内容"""
        pass
    
    @abstractmethod
    def create_message(self, content: str) -> Any:
        """创建消息对象"""
        pass
```

#### 3.2 实现核心提示词类型

```python
# src/core/prompts/types/system_prompt.py
from typing import Dict, Any
from ....interfaces.prompts.types import IPromptType, PromptType
from langchain_core.messages import SystemMessage

class SystemPromptType(IPromptType):
    """系统提示词类型"""
    
    @property
    def type_name(self) -> str:
        return PromptType.SYSTEM.value
    
    @property
    def injection_order(self) -> int:
        return 10  # 最先注入
    
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理系统提示词"""
        # 可以在这里添加变量替换等处理逻辑
        return content
    
    def create_message(self, content: str) -> SystemMessage:
        """创建系统消息"""
        return SystemMessage(content=content)
```

#### 3.3 实现提示词类型注册表

```python
# src/core/prompts/type_registry.py
from typing import Dict, List, Optional
from ....interfaces.prompts.types import IPromptType, PromptType

class PromptTypeRegistry:
    """提示词类型注册表"""
    
    def __init__(self):
        self._types: Dict[str, IPromptType] = {}
        self._register_core_types()
    
    def _register_core_types(self):
        """注册核心提示词类型"""
        from .types.system_prompt import SystemPromptType
        from .types.rules_prompt import RulesPromptType
        from .types.user_command_prompt import UserCommandPromptType
        
        self.register(SystemPromptType())
        self.register(RulesPromptType())
        self.register(UserCommandPromptType())
    
    def register(self, prompt_type: IPromptType):
        """注册提示词类型"""
        self._types[prompt_type.type_name] = prompt_type
    
    def get(self, type_name: str) -> Optional[IPromptType]:
        """获取提示词类型"""
        return self._types.get(type_name)
    
    def get_all(self) -> List[IPromptType]:
        """获取所有提示词类型"""
        return list(self._types.values())
    
    def get_sorted_by_injection_order(self) -> List[IPromptType]:
        """按注入顺序排序获取所有类型"""
        return sorted(self._types.values(), key=lambda t: t.injection_order)
```

### 第四阶段：缓存系统重构

#### 4.1 定义缓存接口

```python
# src/interfaces/prompts/cache.py
from abc import ABC, abstractmethod
from typing import Optional, Any

class IPromptCache(ABC):
    """提示词缓存接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """获取缓存内容"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """设置缓存内容"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存内容"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass
```

#### 4.2 实现内存缓存

```python
# src/services/prompts/cache/memory_cache.py
import time
from typing import Dict, Optional
from ....interfaces.prompts.cache import IPromptCache

class MemoryPromptCache(IPromptCache):
    """内存提示词缓存实现"""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, tuple] = {}  # key: (value, expiry_time)
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[str]:
        """获取缓存内容"""
        if key not in self._cache:
            return None
        
        value, expiry_time = self._cache[key]
        if expiry_time and time.time() > expiry_time:
            del self._cache[key]
            return None
        
        return value
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """设置缓存内容"""
        expiry_time = None
        if ttl:
            expiry_time = time.time() + ttl
        elif self.default_ttl:
            expiry_time = time.time() + self.default_ttl
        
        self._cache[key] = (value, expiry_time)
    
    async def delete(self, key: str) -> None:
        """删除缓存内容"""
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self.get(key) is not None
```

### 第五阶段：错误处理重构

#### 5.1 定义错误类型

```python
# src/core/common/exceptions/prompts.py
from typing import Optional, List, Any

class PromptError(Exception):
    """提示词基础错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = self.__class__.__name__

class PromptLoadError(PromptError):
    """提示词加载错误"""
    pass

class PromptInjectionError(PromptError):
    """提示词注入错误"""
    pass

class PromptValidationError(PromptError):
    """提示词验证错误"""
    
    def __init__(self, message: str, validation_errors: List[str] = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []

class PromptCacheError(PromptError):
    """提示词缓存错误"""
    pass
```

#### 5.2 实现错误处理器

```python
# src/core/prompts/error_handler.py
import logging
from typing import Type, Dict, Callable, Optional
from ....core.common.exceptions.prompts import PromptError

logger = logging.getLogger(__name__)

class PromptErrorHandler:
    """提示词错误处理器"""
    
    def __init__(self):
        self._error_handlers: Dict[Type[PromptError], Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        self.register_handler(PromptLoadError, self._handle_load_error)
        self.register_handler(PromptInjectionError, self._handle_injection_error)
        self.register_handler(PromptValidationError, self._handle_validation_error)
        self.register_handler(PromptCacheError, self._handle_cache_error)
    
    def register_handler(
        self,
        error_type: Type[PromptError],
        handler: Callable
    ):
        """注册错误处理器"""
        self._error_handlers[error_type] = handler
    
    def handle_error(self, error: PromptError) -> Optional[Exception]:
        """处理错误"""
        error_type = type(error)
        handler = self._error_handlers.get(error_type)
        
        if handler:
            try:
                return handler(error)
            except Exception as e:
                logger.error(f"错误处理器失败: {e}")
        
        # 默认处理：记录并返回原错误
        logger.error(f"未处理的提示词错误: {error}")
        return error
    
    def _handle_load_error(self, error: PromptLoadError) -> Optional[Exception]:
        """处理加载错误"""
        logger.error(f"提示词加载失败: {error.message}")
        # 可以尝试从备用源加载
        return error
    
    def _handle_injection_error(self, error: PromptInjectionError) -> Optional[Exception]:
        """处理注入错误"""
        logger.error(f"提示词注入失败: {error.message}")
        # 可以尝试使用默认提示词
        return error
    
    def _handle_validation_error(self, error: PromptValidationError) -> Optional[Exception]:
        """处理验证错误"""
        logger.error(f"提示词验证失败: {error.message}")
        for validation_error in error.validation_errors:
            logger.error(f"  - {validation_error}")
        return error
    
    def _handle_cache_error(self, error: PromptCacheError) -> Optional[Exception]:
        """处理缓存错误"""
        logger.warning(f"提示词缓存错误: {error.message}")
        # 缓存错误通常不应该中断流程
        return None  # 返回None表示错误已处理，可以继续
```

## 最佳实践

### 1. 状态管理最佳实践

- **使用不可变状态**：始终创建新状态而不是修改现有状态
- **使用状态构建器**：通过构建器模式简化状态创建和修改
- **验证状态**：在状态创建后进行验证，确保状态一致性
- **状态快照**：在关键点创建状态快照，支持回滚和调试

### 2. 提示词注入最佳实践

- **异步操作**：所有I/O操作都应该是异步的
- **缓存策略**：合理使用缓存，避免重复加载
- **错误处理**：区分可恢复和不可恢复错误，提供适当的恢复策略
- **类型安全**：使用强类型接口，避免运行时类型错误

### 3. 扩展性最佳实践

- **插件化设计**：通过接口和注册表支持动态扩展
- **配置驱动**：通过配置文件控制行为，避免硬编码
- **依赖注入**：使用依赖注入容器管理对象生命周期
- **接口隔离**：保持接口小而专注，提高可测试性

### 4. 性能优化最佳实践

- **批量操作**：尽可能批量处理，减少状态修改次数
- **预加载**：提前加载常用提示词，减少延迟
- **缓存策略**：实现多级缓存，提高命中率
- **异步并发**：利用异步并发提高吞吐量

## 测试策略

### 1. 单元测试

- **状态管理测试**：测试状态创建、修改和验证
- **提示词注入测试**：测试各种提示词类型的注入
- **缓存测试**：测试缓存的读写和失效
- **错误处理测试**：测试各种错误情况的处理

### 2. 集成测试

- **工作流集成测试**：测试提示词注入在完整工作流中的行为
- **配置集成测试**：测试配置文件加载和应用
- **性能测试**：测试系统在高负载下的性能

### 3. 端到端测试

- **场景测试**：测试真实使用场景
- **回归测试**：确保重构不破坏现有功能
- **兼容性测试**：确保向后兼容性

## 迁移指南

### 1. 渐进式迁移

- **阶段1**：重构状态接口，保持向后兼容
- **阶段2**：重构提示词注入器，提供适配器
- **阶段3**：重构提示词类型系统，逐步迁移
- **阶段4**：重构缓存和错误处理，完成迁移

### 2. 兼容性保证

- **适配器模式**：为旧接口提供适配器
- **版本控制**：使用版本控制管理API变更
- **废弃警告**：对废弃功能提供警告信息
- **迁移工具**：提供自动化迁移工具

### 3. 回滚策略

- **功能开关**：使用功能开关控制新旧实现
- **监控告警**：监控关键指标，及时发现问题
- **快速回滚**：准备快速回滚方案
- **数据备份**：备份关键数据，防止数据丢失

## 总结

本重构指南提供了一个全面的重构方案，旨在解决当前提示词注入工作流系统中的各种问题。通过分阶段实施，可以确保系统稳定性的同时，逐步提升系统的类型安全性、性能和可维护性。

重构后的系统将具有以下优势：

1. **类型安全**：通过强类型接口确保编译时类型检查
2. **高性能**：通过缓存和异步操作提高系统性能
3. **高可扩展性**：通过插件化设计支持动态扩展
4. **高可维护性**：通过清晰的架构和完善的文档提高可维护性
5. **高可靠性**：通过完善的错误处理和测试策略提高可靠性

建议按照本指南逐步实施重构，并在每个阶段进行充分的测试和验证，确保重构的成功。