# 完全集中化状态管理架构设计文档

## 1. 架构概述

### 1.1 设计目标

- **统一状态管理**：将所有状态管理功能集中到 `src/core/state/` 目录
- **消除代码重复**：通过统一实现消除重复代码
- **标准化API**：提供一致的接口和实现
- **提升可维护性**：单一实现点，降低维护成本
- **保持功能完整性**：确保所有原有功能得到保留和优化

### 1.2 核心设计原则

1. **单一职责**：每个组件只负责特定的状态管理功能
2. **开闭原则**：对扩展开放，对修改封闭
3. **依赖倒置**：高层模块不依赖低层模块
4. **接口隔离**：提供细粒度的接口
5. **可配置性**：通过配置支持不同使用场景

## 2. 目录结构设计

```
src/core/state/
├── __init__.py                 # 统一导出
├── interfaces/                 # 接口定义
│   ├── __init__.py
│   ├── base.py                # 基础状态接口
│   ├── workflow.py            # 工作流状态接口
│   ├── tools.py               # 工具状态接口
│   ├── sessions.py            # 会话状态接口
│   ├── threads.py             # 线程状态接口
│   └── checkpoints.py         # 检查点接口
├── core/                      # 核心实现
│   ├── __init__.py
│   ├── base.py                # 基础状态管理器
│   ├── state_manager.py       # 统一状态管理器
│   ├── serializer.py          # 统一序列化器
│   ├── validator.py           # 统一验证器
│   ├── lifecycle.py           # 生命周期管理
│   └── cache.py               # 统一缓存管理
├── implementations/           # 具体实现
│   ├── __init__.py
│   ├── base_state.py          # 基础状态实现
│   ├── workflow_state.py      # 工作流状态实现
│   ├── tool_state.py          # 工具状态实现
│   ├── session_state.py       # 会话状态实现
│   ├── thread_state.py        # 线程状态实现
│   └── checkpoint_state.py    # 检查点状态实现
├── factories/                 # 工厂模式
│   ├── __init__.py
│   ├── state_factory.py       # 状态工厂
│   ├── manager_factory.py     # 管理器工厂
│   └── builder_factory.py     # 构建器工厂
├── builders/                  # 构建器模式
│   ├── __init__.py
│   ├── workflow_builder.py    # 工作流状态构建器
│   ├── tool_builder.py        # 工具状态构建器
│   ├── session_builder.py     # 会话状态构建器
│   └── base_builder.py        # 基础构建器
├── storage/                   # 存储适配器
│   ├── __init__.py
│   ├── base_adapter.py        # 基础存储适配器
│   ├── memory_adapter.py      # 内存存储适配器
│   ├── sqlite_adapter.py      # SQLite存储适配器
│   ├── file_adapter.py        # 文件存储适配器
│   └── adapter_factory.py     # 存储适配器工厂
├── history/                   # 历史管理
│   ├── __init__.py
│   ├── history_manager.py     # 历史管理器
│   ├── history_entry.py       # 历史记录实体
│   └── history_analyzer.py    # 历史分析器
├── snapshots/                 # 快照管理
│   ├── __init__.py
│   ├── snapshot_manager.py    # 快照管理器
│   ├── snapshot_entity.py     # 快照实体
│   └── snapshot_service.py    # 快照服务
├── utils/                     # 工具类
│   ├── __init__.py
│   ├── converters.py          # 状态转换工具
│   ├── helpers.py             # 辅助工具
│   ├── constants.py           # 常量定义
│   └── validators.py          # 验证工具
└── config/                    # 配置管理
    ├── __init__.py
    ├── settings.py            # 配置设置
    └── defaults.py            # 默认配置
```

## 3. 核心组件设计

### 3.1 统一状态接口

```python
# src/core/state/interfaces/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

class IState(ABC):
    """统一状态接口"""
    
    # 基础状态操作
    @abstractmethod
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        pass
    
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """设置状态数据"""
        pass
    
    @abstractmethod
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        pass
    
    # 生命周期管理
    @abstractmethod
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        pass
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """检查是否完成"""
        pass
    
    @abstractmethod
    def mark_complete(self) -> None:
        """标记为完成"""
        pass
    
    # 序列化支持
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IState':
        """从字典创建状态"""
        pass

class IStateManager(ABC):
    """统一状态管理器接口"""
    
    @abstractmethod
    def create_state(self, state_type: str, **kwargs) -> IState:
        """创建状态"""
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态"""
        pass
    
    @abstractmethod
    def save_state(self, state: IState) -> bool:
        """保存状态"""
        pass
    
    @abstractmethod
    def delete_state(self, state_id: str) -> bool:
        """删除状态"""
        pass
    
    @abstractmethod
    def list_states(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """列出状态ID"""
        pass
```

### 3.2 工作流状态特化接口

```python
# src/core/state/interfaces/workflow.py
from .base import IState
from typing import Any, Dict, List, Optional

class IWorkflowState(IState):
    """工作流状态接口"""
    
    # 工作流特定属性
    @property
    @abstractmethod
    def messages(self) -> List[Any]:
        """消息列表"""
        pass
    
    @property
    @abstractmethod
    def fields(self) -> Dict[str, Any]:
        """工作流字段"""
        pass
    
    @property
    @abstractmethod
    def values(self) -> Dict[str, Any]:
        """所有状态值"""
        pass
    
    # 工作流特定方法
    @abstractmethod
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        pass
    
    @abstractmethod
    def set_field(self, key: str, value: Any) -> 'IWorkflowState':
        """设置字段值"""
        pass
    
    @abstractmethod
    def add_message(self, message: Any) -> None:
        """添加消息"""
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Any]:
        """获取消息列表"""
        pass
    
    @abstractmethod
    def with_messages(self, messages: List[Any]) -> 'IWorkflowState':
        """创建包含新消息的状态"""
        pass
    
    @abstractmethod
    def get_current_node(self) -> Optional[str]:
        """获取当前节点"""
        pass
    
    @abstractmethod
    def set_current_node(self, node: str) -> None:
        """设置当前节点"""
        pass
    
    @abstractmethod
    def get_iteration_count(self) -> int:
        """获取迭代计数"""
        pass
    
    @abstractmethod
    def increment_iteration(self) -> None:
        """增加迭代计数"""
        pass
    
    @abstractmethod
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID"""
        pass
    
    @abstractmethod
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID"""
        pass
    
    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        pass
    
    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        pass
```

### 3.3 工具状态特化接口

```python
# src/core/state/interfaces/tools.py
from .base import IState
from typing import Any, Dict, List, Optional
from enum import Enum

class StateType(Enum):
    """状态类型枚举"""
    CONNECTION = "connection"
    SESSION = "session"
    BUSINESS = "business"
    CACHE = "cache"

class IToolState(IState):
    """工具状态接口"""
    
    @abstractmethod
    def get_context_id(self) -> str:
        """获取上下文ID"""
        pass
    
    @abstractmethod
    def get_state_type(self) -> StateType:
        """获取状态类型"""
        pass
    
    @abstractmethod
    def is_expired(self) -> bool:
        """检查是否过期"""
        pass
    
    @abstractmethod
    def set_ttl(self, ttl: int) -> None:
        """设置TTL"""
        pass
    
    @abstractmethod
    def get_tool_type(self) -> str:
        """获取工具类型"""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> None:
        """清理过期状态"""
        pass
```

### 3.4 统一状态管理器实现

```python
# src/core/state/core/state_manager.py
from typing import Any, Dict, List, Optional, Type, Callable
from datetime import datetime
import threading
import uuid
from ..interfaces.base import IState, IStateManager
from ..interfaces.workflow import IWorkflowState
from ..interfaces.tools import IToolState
from ..core.serializer import StateSerializer
from ..core.validator import StateValidator
from ..core.lifecycle import StateLifecycleManager
from ..core.cache import StateCache
from ..storage.memory_adapter import MemoryStateAdapter
from ..implementations.workflow_state import WorkflowState
from ..implementations.tool_state import ToolState
from ..implementations.session_state import SessionState
from ..implementations.thread_state import ThreadState
from ..implementations.checkpoint_state import CheckpointState

class StateManager(IStateManager):
    """统一状态管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化状态管理器"""
        self.config = config
        self._serializer = StateSerializer(config.get('serializer', {}))
        self._validator = StateValidator(config.get('validation', {}))
        self._lifecycle = StateLifecycleManager(config.get('lifecycle', {}))
        self._cache = StateCache(config.get('cache', {}))
        self._storage = self._create_storage_adapter(config.get('storage', {}))
        self._lock = threading.RLock()
        
        # 状态类型注册表
        self._state_types: Dict[str, Type[IState]] = {}
        self._register_default_state_types()
    
    def _create_storage_adapter(self, storage_config: Dict[str, Any]):
        """创建存储适配器"""
        adapter_type = storage_config.get('type', 'memory')
        if adapter_type == 'memory':
            from ..storage.memory_adapter import MemoryStateAdapter
            return MemoryStateAdapter(storage_config)
        elif adapter_type == 'sqlite':
            from ..storage.sqlite_adapter import SQLiteStateAdapter
            return SQLiteStateAdapter(storage_config)
        elif adapter_type == 'file':
            from ..storage.file_adapter import FileStateAdapter
            return FileStateAdapter(storage_config)
        else:
            raise ValueError(f"不支持的存储类型: {adapter_type}")
    
    def _register_default_state_types(self):
        """注册默认状态类型"""
        self.register_state_type('workflow', WorkflowState)
        self.register_state_type('tool', ToolState)
        self.register_state_type('session', SessionState)
        self.register_state_type('thread', ThreadState)
        self.register_state_type('checkpoint', CheckpointState)
    
    def register_state_type(self, state_type: str, state_class: Type[IState]):
        """注册状态类型"""
        with self._lock:
            self._state_types[state_type] = state_class
    
    def create_state(self, state_type: str, **kwargs) -> IState:
        """创建状态"""
        with self._lock:
            if state_type not in self._state_types:
                raise ValueError(f"未知状态类型: {state_type}")
            
            state_class = self._state_types[state_type]
            state = state_class(**kwargs)
            
            # 验证状态
            self._validator.validate_state(state)
            
            # 注册生命周期管理
            self._lifecycle.register_state(state)
            
            # 保存到存储
            self.save_state(state)
            
            return state
    
    def get_state(self, state_id: str) -> Optional[IState]:
        """获取状态"""
        with self._lock:
            # 先从缓存获取
            cached_state = self._cache.get(state_id)
            if cached_state:
                return cached_state
            
            # 从存储获取
            state_data = self._storage.get(state_id)
            if not state_data:
                return None
            
            # 反序列化
            state = self._serializer.deserialize(state_data)
            
            # 缓存状态
            self._cache.put(state_id, state)
            
            return state
    
    def save_state(self, state: IState) -> bool:
        """保存状态"""
        with self._lock:
            try:
                # 验证状态
                self._validator.validate_state(state)
                
                # 序列化状态
                serialized_data = self._serializer.serialize(state)
                
                # 保存到存储
                success = self._storage.save(state.get_id(), serialized_data)
                
                if success:
                    # 更新缓存
                    self._cache.put(state.get_id(), state)
                    
                    # 触发生命周期事件
                    self._lifecycle.on_state_saved(state)
                
                return success
            except Exception as e:
                self._lifecycle.on_state_error(state, e)
                raise
    
    def delete_state(self, state_id: str) -> bool:
        """删除状态"""
        with self._lock:
            # 从存储删除
            success = self._storage.delete(state_id)
            
            if success:
                # 从缓存删除
                self._cache.delete(state_id)
                
                # 触发生命周期事件
                self._lifecycle.on_state_deleted(state_id)
            
            return success
    
    def list_states(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """列出状态ID"""
        with self._lock:
            return self._storage.list(filters)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                'total_states': len(self._cache.get_all_keys()),
                'cache_size': self._cache.size(),
                'storage_stats': self._storage.get_statistics(),
                'lifecycle_stats': self._lifecycle.get_statistics()
            }
```

### 3.5 工作流状态实现

```python
# src/core/state/implementations/workflow_state.py
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from ..interfaces.workflow import IWorkflowState
from ..interfaces.base import IState
from ..implementations.base_state import BaseState

# 消息类型定义
class MessageRole:
    """消息角色常量"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
    UNKNOWN = "unknown"

@dataclass
class BaseMessage:
    """消息基类"""
    content: str
    role: str = MessageRole.UNKNOWN

@dataclass
class HumanMessage(BaseMessage):
    """人类消息"""
    role: str = MessageRole.HUMAN

@dataclass
class AIMessage(BaseMessage):
    """AI消息"""
    role: str = MessageRole.AI

class MessageManager:
    """消息管理器"""
    def __init__(self) -> None:
        self._messages: List[Union[BaseMessage, Any]] = []
    
    def add_message(self, message: Union[BaseMessage, Any]) -> None:
        """添加消息"""
        self._messages.append(message)
    
    def get_messages(self) -> List[Union[BaseMessage, Any]]:
        """获取所有消息"""
        return self._messages.copy()
    
    def get_last_message(self) -> Union[BaseMessage, Any, None]:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None

class WorkflowState(BaseState, IWorkflowState):
    """工作流状态实现"""
    
    def __init__(self, **kwargs):
        """初始化工作流状态"""
        super().__init__(**kwargs)
        
        # 工作流特定字段
        self._messages: List[Union[BaseMessage, Any]] = kwargs.get('messages', [])
        self._current_node: Optional[str] = kwargs.get('current_node')
        self._iteration_count: int = kwargs.get('iteration_count', 0)
        self._thread_id: Optional[str] = kwargs.get('thread_id')
        self._session_id: Optional[str] = kwargs.get('session_id')
        self._execution_history: List[Dict[str, Any]] = kwargs.get('execution_history', [])
        self._errors: List[str] = kwargs.get('errors', [])
        self._max_iterations: int = kwargs.get('max_iterations', 10)
        
        # 初始化消息管理器
        self._message_manager = MessageManager()
        for msg in self._messages:
            self._message_manager.add_message(msg)
    
    @property
    def messages(self) -> List[Union[BaseMessage, Any]]:
        """消息列表"""
        return self._message_manager.get_messages()
    
    @property
    def fields(self) -> Dict[str, Any]:
        """工作流字段"""
        return {
            'current_node': self._current_node,
            'iteration_count': self._iteration_count,
            'thread_id': self._thread_id,
            'session_id': self._session_id,
            'execution_history': self._execution_history,
            'errors': self._errors,
            'max_iterations': self._max_iterations
        }
    
    @property
    def values(self) -> Dict[str, Any]:
        """所有状态值"""
        return {**self._data, **self.fields}
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        if key == "current_node":
            return self._current_node
        elif key == "iteration_count":
            return self._iteration_count
        elif key == "thread_id":
            return self._thread_id
        elif key == "session_id":
            return self._session_id
        elif key == "execution_history":
            return self._execution_history
        elif key == "errors":
            return self._errors
        elif key == "max_iterations":
            return self._max_iterations
        else:
            return default
    
    def set_field(self, key: str, value: Any) -> 'IWorkflowState':
        """设置字段值"""
        if key == "current_node":
            self._current_node = value
        elif key == "iteration_count":
            self._iteration_count = value
        elif key == "thread_id":
            self._thread_id = value
        elif key == "session_id":
            self._session_id = value
        elif key == "execution_history":
            self._execution_history = value
        elif key == "errors":
            self._errors = value
        elif key == "max_iterations":
            self._max_iterations = value
        
        self._updated_at = datetime.now()
        return self
    
    def add_message(self, message: Union[BaseMessage, Any]) -> None:
        """添加消息"""
        self._message_manager.add_message(message)
        self._updated_at = datetime.now()
    
    def get_messages(self) -> List[Union[BaseMessage, Any]]:
        """获取消息列表"""
        return self._message_manager.get_messages()
    
    def with_messages(self, messages: List[Union[BaseMessage, Any]]) -> 'IWorkflowState':
        """创建包含新消息的状态"""
        new_state = self.from_dict(self.to_dict())
        new_state._message_manager = MessageManager()
        for msg in messages:
            new_state._message_manager.add_message(msg)
        return new_state
    
    def get_current_node(self) -> Optional[str]:
        """获取当前节点"""
        return self._current_node
    
    def set_current_node(self, node: str) -> None:
        """设置当前节点"""
        self._current_node = node
        self._updated_at = datetime.now()
    
    def get_iteration_count(self) -> int:
        """获取迭代计数"""
        return self._iteration_count
    
    def increment_iteration(self) -> None:
        """增加迭代计数"""
        self._iteration_count += 1
        self._updated_at = datetime.now()
    
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID"""
        return self._thread_id
    
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID"""
        self._thread_id = thread_id
        self._updated_at = datetime.now()
    
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self._session_id
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        self._session_id = session_id
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'messages': [
                {
                    'content': msg.content if hasattr(msg, 'content') else str(msg),
                    'role': msg.role if hasattr(msg, 'role') else MessageRole.UNKNOWN
                }
                for msg in self._message_manager.get_messages()
            ],
            'current_node': self._current_node,
            'iteration_count': self._iteration_count,
            'thread_id': self._thread_id,
            'session_id': self._session_id,
            'execution_history': self._execution_history,
            'errors': self._errors,
            'max_iterations': self._max_iterations
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._current_node = data.get("current_node")
        instance._iteration_count = data.get("iteration_count", 0)
        instance._thread_id = data.get("thread_id")
        instance._session_id = data.get("session_id")
        instance._execution_history = data.get("execution_history", [])
        instance._errors = data.get("errors", [])
        instance._max_iterations = data.get("max_iterations", 10)
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 处理时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        # 处理消息
        messages_data = data.get("messages", [])
        instance._message_manager = MessageManager()
        for msg_data in messages_data:
            role = msg_data.get('role', MessageRole.UNKNOWN)
            content = msg_data.get('content', '')
            if role == MessageRole.HUMAN:
                msg = HumanMessage(content=content)
            elif role == MessageRole.AI:
                msg = AIMessage(content=content)
            else:
                msg = BaseMessage(content=content, role=role)
            instance._message_manager.add_message(msg)
        
        return instance
```

### 3.6 工具状态实现

```python
# src/core/state/implementations/tool_state.py
from typing import Any, Dict, Optional
from datetime import datetime
import time
from enum import Enum
from ..interfaces.tools import IToolState, StateType
from ..implementations.base_state import BaseState

class ToolState(BaseState, IToolState):
    """工具状态实现"""
    
    def __init__(self, **kwargs):
        """初始化工具状态"""
        super().__init__(**kwargs)
        
        # 工具特定字段
        self._context_id: str = kwargs.get('context_id', '')
        self._state_type: StateType = kwargs.get('state_type', StateType.BUSINESS)
        self._tool_type: str = kwargs.get('tool_type', '')
        self._expires_at: Optional[float] = kwargs.get('expires_at')
        self._version: int = kwargs.get('version', 1)
    
    def get_context_id(self) -> str:
        """获取上下文ID"""
        return self._context_id
    
    def get_state_type(self) -> StateType:
        """获取状态类型"""
        return self._state_type
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self._expires_at is None:
            return False
        return time.time() > self._expires_at
    
    def set_ttl(self, ttl: int) -> None:
        """设置TTL"""
        self._expires_at = time.time() + ttl
        self._updated_at = datetime.now()
    
    def get_tool_type(self) -> str:
        """获取工具类型"""
        return self._tool_type
    
    def cleanup_expired(self) -> None:
        """清理过期状态"""
        if self.is_expired():
            self._data.clear()
            self._metadata.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'context_id': self._context_id,
            'state_type': self._state_type.value,
            'tool_type': self._tool_type,
            'expires_at': self._expires_at,
            'version': self._version
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._context_id = data.get("context_id", "")
        instance._state_type = StateType(data.get("state_type", StateType.BUSINESS.value))
        instance._tool_type = data.get("tool_type", "")
        instance._expires_at = data.get("expires_at")
        instance._version = data.get("version", 1)
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 处理时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        return instance
```

### 3.7 状态构建器

```python
# src/core/state/builders/workflow_builder.py
from typing import Any, Dict, List, Optional, Union
from ..interfaces.workflow import IWorkflowState
from ..implementations.workflow_state import WorkflowState, BaseMessage, HumanMessage, AIMessage

class WorkflowStateBuilder:
    """工作流状态构建器"""
    
    def __init__(self) -> None:
        """初始化构建器"""
        self._state_data: Dict[str, Any] = {}
        self._messages: List[Union[BaseMessage, Any]] = []
    
    def with_id(self, state_id: str) -> 'WorkflowStateBuilder':
        """设置状态ID"""
        self._state_data['id'] = state_id
        return self
    
    def with_data(self, data: Dict[str, Any]) -> 'WorkflowStateBuilder':
        """设置状态数据"""
        self._state_data.update(data)
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'WorkflowStateBuilder':
        """设置元数据"""
        self._state_data['metadata'] = metadata
        return self
    
    def with_current_node(self, node: str) -> 'WorkflowStateBuilder':
        """设置当前节点"""
        self._state_data['current_node'] = node
        return self
    
    def with_thread_id(self, thread_id: str) -> 'WorkflowStateBuilder':
        """设置线程ID"""
        self._state_data['thread_id'] = thread_id
        return self
    
    def with_session_id(self, session_id: str) -> 'WorkflowStateBuilder':
        """设置会话ID"""
        self._state_data['session_id'] = session_id
        return self
    
    def with_max_iterations(self, max_iterations: int) -> 'WorkflowStateBuilder':
        """设置最大迭代次数"""
        self._state_data['max_iterations'] = max_iterations
        return self
    
    def add_message(self, message: Union[BaseMessage, str]) -> 'WorkflowStateBuilder':
        """添加消息"""
        if isinstance(message, str):
            msg = HumanMessage(content=message)
        else:
            msg = message
        self._messages.append(msg)
        return self
    
    def with_messages(self, messages: List[Union[BaseMessage, str]]) -> 'WorkflowStateBuilder':
        """设置消息列表"""
        for msg in messages:
            self.add_message(msg)
        return self
    
    def with_human_message(self, content: str) -> 'WorkflowStateBuilder':
        """添加人类消息"""
        self._messages.append(HumanMessage(content=content))
        return self
    
    def with_ai_message(self, content: str) -> 'WorkflowStateBuilder':
        """添加AI消息"""
        self._messages.append(AIMessage(content=content))
        return self
    
    def build(self) -> IWorkflowState:
        """构建工作流状态"""
        self._state_data['messages'] = self._messages
        return WorkflowState(**self._state_data)
```

## 4. 配置管理

### 4.1 统一配置结构

```yaml
# configs/state_management.yaml
state_management:
 # 核心配置
  core:
    default_ttl: 3600
    max_states: 10000
    cleanup_interval: 300
  
  # 序列化配置
  serializer:
    format: "json"  # json, pickle, msgpack
    compression: true
    compression_threshold: 1024
  
  # 缓存配置
 cache:
    enabled: true
    max_size: 1000
    ttl: 300
    eviction_policy: "lru"  # lru, lfu, fifo
  
  # 存储配置
 storage:
    default_type: "memory"
    memory:
      max_size: 10000
    sqlite:
      database_path: "data/states.db"
      connection_pool_size: 10
    file:
      base_path: "data/states"
      format: "json"
  
  # 验证配置
  validation:
    enabled: true
    strict_mode: false
    custom_validators: []
  
  # 生命周期配置
  lifecycle:
    auto_cleanup: true
    cleanup_interval: 300
    event_handlers: []
  
  # 特化配置
 specialized:
    workflow:
      max_iterations: 100
      message_history_limit: 1000
      auto_save: true
    
    tools:
      context_isolation: true
      auto_expiration: true
      default_ttl: 1800
    
    sessions:
      auto_cleanup: true
      max_inactive_duration: 3600
    
    threads:
      auto_cleanup: true
      max_inactive_duration: 7200
```

## 5. 迁移策略

### 5.1 迁移步骤

#### 第一阶段：基础设施准备（2周）
1. 创建新的 `src/core/state/` 目录结构
2. 实现统一接口和基础组件
3. 实现存储适配器
4. 实现序列化和验证组件

#### 第二阶段：核心功能实现（2周）
1. 实现各种状态类型的具体实现
2. 实现构建器和工厂模式
3. 实现历史和快照管理
4. 实现配置管理

#### 第三阶段：迁移工具状态（1周）
1. 将 `src/core/tools/state/` 迁移到新架构
2. 更新相关依赖
3. 测试功能完整性

#### 第四阶段：迁移工作流状态（1周）
1. 将 `src/core/workflow/states/` 迁移到新架构
2. 更新相关依赖
3. 测试功能完整性

#### 第五阶段：迁移服务层（2周）
1. 将 `src/services/state/`, `src/services/checkpoint/`, `src/services/sessions/`, `src/services/threads/` 迁移到新架构
2. 更新相关依赖
3. 测试功能完整性

#### 第六阶段：集成测试和优化（1周）
1. 进行全面的集成测试
2. 性能优化
3. 文档更新

### 5.2 风险缓解策略

1. **并行开发**：新旧系统并行运行一段时间
2. **逐步迁移**：按模块逐步迁移，避免一次性大规模变更
3. **回滚机制**：准备快速回滚方案
4. **充分测试**：每个迁移步骤都进行充分的单元和集成测试
5. **监控告警**：实施过程中密切监控系统状态

## 6. 性能优化设计

### 6.1 缓存策略

```python
# src/core/state/core/cache.py
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import threading
from collections import OrderedDict
import time

class StateCache:
    """状态缓存管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化缓存"""
        self.max_size = config.get('max_size', 1000)
        self.ttl = config.get('ttl', 300)
        self.eviction_policy = config.get('eviction_policy', 'lru')
        
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # 检查TTL
            if self._is_expired(entry):
                del self._cache[key]
                return None
            
            # 更新访问时间（LRU）
            if self.eviction_policy == 'lru':
                self._cache.move_to_end(key)
            
            entry['access_count'] = entry.get('access_count', 1) + 1
            return entry['value']
    
    def put(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            # 检查容量
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict()
            
            entry = {
                'value': value,
                'created_at': time.time(),
                'access_count': 1
            }
            
            self._cache[key] = entry
            
            # 移动到末尾（最新）
            self._cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def get_all_keys(self) -> List[str]:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:
            return False
        
        age = time.time() - entry['created_at']
        return age > self.ttl
    
    def _evict(self) -> None:
        """驱逐缓存项"""
        if not self._cache:
            return
        
        if self.eviction_policy == 'lru':
            # 删除最久未访问的项
            self._cache.popitem(last=False)
        elif self.eviction_policy == 'lfu':
            # 删除访问次数最少的项
            min_key = min(self._cache.keys(), 
                         key=lambda k: self._cache[k]['access_count'])
            del self._cache[min_key]
        elif self.eviction_policy == 'fifo':
            # 删除最早插入的项
            self._cache.popitem(last=False)
```

### 6.2 存储优化

```python
# src/core/state/storage/sqlite_adapter.py
import sqlite3
import json
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime
import zlib
from ..interfaces.base import IState

class SQLiteStateAdapter:
    """SQLite状态存储适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化适配器"""
        self.db_path = config.get('database_path', 'states.db')
        self.connection_pool_size = config.get('connection_pool_size', 10)
        self.compression = config.get('compression', True)
        
        self._lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    data BLOB NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    compressed INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_type ON states(type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON states(expires_at)
            """)
    
    def save(self, state_id: str, state_data: Any) -> bool:
        """保存状态"""
        try:
            # 序列化数据
            data_str = json.dumps(state_data, ensure_ascii=False)
            
            # 压缩数据（如果需要）
            if self.compression and len(data_str) > 1024:  # 大于1KB才压缩
                compressed_data = zlib.compress(data_str.encode('utf-8'))
                data_for_db = compressed_data
                is_compressed = 1
            else:
                data_for_db = data_str.encode('utf-8')
                is_compressed = 0
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO states 
                    (id, type, data, metadata, updated_at, compressed)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    state_id,
                    type(state_data).__name__,
                    data_for_db,
                    json.dumps({}, ensure_ascii=False),
                    is_compressed
                ))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False
    
    def get(self, state_id: str) -> Optional[Any]:
        """获取状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM states WHERE id = ?", (state_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # 解压数据（如果需要）
                if row['compressed']:
                    data_bytes = zlib.decompress(row['data'])
                    data_str = data_bytes.decode('utf-8')
                else:
                    data_str = row['data'].decode('utf-8')
                
                return json.loads(data_str)
        except Exception as e:
            print(f"获取状态失败: {e}")
            return None
    
    def delete(self, state_id: str) -> bool:
        """删除状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM states WHERE id = ?", (state_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除状态失败: {e}")
            return False
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """列出状态ID"""
        try:
            query = "SELECT id FROM states WHERE 1=1"
            params = []
            
            if filters:
                if 'type' in filters:
                    query += " AND type = ?"
                    params.append(filters['type'])
                if 'expires_after' in filters:
                    query += " AND (expires_at IS NULL OR expires_at > ?)"
                    params.append(filters['expires_after'])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"列出状态失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM states")
                total_count = cursor.fetchone()['count']
                
                cursor = conn.execute("SELECT SUM(LENGTH(data)) as size FROM states")
                total_size = cursor.fetchone()['size'] or 0
                
                return {
                    'total_states': total_count,
                    'total_size_bytes': total_size,
                    'database_path': self.db_path
                }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}
```

## 7. 总结

完全集中化状态管理架构设计通过以下方式解决了原架构的问题：

1. **消除代码重复**：通过统一的基础设施实现，消除了各模块间的重复代码
2. **标准化API**：提供一致的接口和实现，降低学习和维护成本
3. **提升可维护性**：单一实现点，便于统一维护和优化
4. **保持功能完整性**：确保所有原有功能得到保留和优化
5. **性能优化**：通过统一的缓存和存储策略，提升整体性能
6. **扩展性强**：通过接口和工厂模式，便于添加新的状态类型

该架构设计为项目提供了一个统一、高效、可维护的状态管理解决方案。

---

**文档版本**：1.0  
**创建日期**：2025-01-24  
**作者**：架构设计团队  
**审核状态**：待审核