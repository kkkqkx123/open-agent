# 有状态工具架构实施方案

## 概述

本文档详细描述了有状态工具架构的具体实施方案，包括实现步骤、代码示例、配置文件和迁移指南。

## 实施步骤

### 第一阶段：基础设施实现

#### 1.1 状态管理器接口和实现

**文件结构**:
```
src/core/tools/state/
├── __init__.py
├── interfaces.py          # 状态管理器接口
├── memory_state_manager.py    # 内存状态管理器
├── persistent_state_manager.py # 持久化状态管理器
├── session_state_manager.py   # 会话状态管理器
└── redis_state_manager.py      # 分布式状态管理器
```

**核心接口实现** (`src/core/tools/state/interfaces.py`):

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import uuid

class StateType(Enum):
    """状态类型枚举"""
    CONNECTION = "connection"
    SESSION = "session"
    BUSINESS = "business"
    CACHE = "cache"

@dataclass
class StateEntry:
    """状态条目"""
    state_id: str
    context_id: str
    state_type: StateType
    data: Dict[str, Any]
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    version: int = 1
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

class IToolStateManager(ABC):
    """工具状态管理器接口"""
    
    @abstractmethod
    def create_context(self, context_id: str, tool_type: str) -> str:
        """创建工具上下文"""
        pass
    
    @abstractmethod
    def get_state(self, context_id: str, state_type: StateType) -> Optional[Dict[str, Any]]:
        """获取状态数据"""
        pass
    
    @abstractmethod
    def set_state(self, context_id: str, state_type: StateType, state_data: Dict[str, Any], 
                  ttl: Optional[int] = None) -> bool:
        """设置状态数据"""
        pass
    
    @abstractmethod
    def update_state(self, context_id: str, state_type: StateType, updates: Dict[str, Any]) -> bool:
        """更新状态数据"""
        pass
    
    @abstractmethod
    def delete_state(self, context_id: str, state_type: StateType) -> bool:
        """删除状态"""
        pass
    
    @abstractmethod
    def cleanup_context(self, context_id: str) -> bool:
        """清理上下文"""
        pass
    
    @abstractmethod
    def list_contexts(self, tool_type: Optional[str] = None) -> List[str]:
        """列出上下文"""
        pass
    
    @abstractmethod
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        pass
```

**内存状态管理器实现** (`src/core/tools/state/memory_state_manager.py`):

```python
import threading
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

from .interfaces import IToolStateManager, StateType, StateEntry

class MemoryStateManager(IToolStateManager):
    """内存状态管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存状态管理器"""
        self.config = config
        self._states: Dict[str, Dict[StateType, StateEntry]] = defaultdict(dict)
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # 启动清理线程
        if config.get('auto_cleanup', True):
            self._start_cleanup_thread()
    
    def create_context(self, context_id: str, tool_type: str) -> str:
        """创建工具上下文"""
        with self._lock:
            # 生成唯一的状态ID
            state_id = f"{context_id}_{uuid.uuid4().hex[:8]}"
            
            # 初始化上下文状态
            if context_id not in self._states:
                self._states[context_id] = {}
            
            return state_id
    
    def get_state(self, context_id: str, state_type: StateType) -> Optional[Dict[str, Any]]:
        """获取状态数据"""
        with self._lock:
            if context_id not in self._states:
                return None
            
            state_entry = self._states[context_id].get(state_type)
            if not state_entry:
                return None
            
            # 检查是否过期
            if state_entry.is_expired():
                del self._states[context_id][state_type]
                return None
            
            return state_entry.data.copy()
    
    def set_state(self, context_id: str, state_type: StateType, state_data: Dict[str, Any], 
                  ttl: Optional[int] = None) -> bool:
        """设置状态数据"""
        with self._lock:
            now = time.time()
            expires_at = now + ttl if ttl else None
            
            state_entry = StateEntry(
                state_id=f"{context_id}_{state_type.value}_{uuid.uuid4().hex[:8]}",
                context_id=context_id,
                state_type=state_type,
                data=state_data.copy(),
                created_at=now,
                updated_at=now,
                expires_at=expires_at
            )
            
            self._states[context_id][state_type] = state_entry
            return True
    
    def update_state(self, context_id: str, state_type: StateType, updates: Dict[str, Any]) -> bool:
        """更新状态数据"""
        with self._lock:
            if context_id not in self._states:
                return False
            
            state_entry = self._states[context_id].get(state_type)
            if not state_entry:
                return False
            
            # 检查是否过期
            if state_entry.is_expired():
                del self._states[context_id][state_type]
                return False
            
            # 更新数据
            state_entry.data.update(updates)
            state_entry.updated_at = time.time()
            state_entry.version += 1
            
            return True
    
    def delete_state(self, context_id: str, state_type: StateType) -> bool:
        """删除状态"""
        with self._lock:
            if context_id not in self._states:
                return False
            
            if state_type in self._states[context_id]:
                del self._states[context_id][state_type]
                return True
            
            return False
    
    def cleanup_context(self, context_id: str) -> bool:
        """清理上下文"""
        with self._lock:
            if context_id in self._states:
                del self._states[context_id]
                return True
            return False
    
    def list_contexts(self, tool_type: Optional[str] = None) -> List[str]:
        """列出上下文"""
        with self._lock:
            contexts = list(self._states.keys())
            
            if tool_type:
                # 过滤特定工具类型的上下文
                filtered_contexts = []
                for context_id in contexts:
                    if tool_type in context_id:
                        filtered_contexts.append(context_id)
                return filtered_contexts
            
            return contexts
    
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        with self._lock:
            if context_id not in self._states:
                return None
            
            states = self._states[context_id]
            info = {
                'context_id': context_id,
                'state_count': len(states),
                'states': {}
            }
            
            for state_type, state_entry in states.items():
                info['states'][state_type.value] = {
                    'state_id': state_entry.state_id,
                    'created_at': state_entry.created_at,
                    'updated_at': state_entry.updated_at,
                    'expires_at': state_entry.expires_at,
                    'version': state_entry.version,
                    'is_expired': state_entry.is_expired(),
                    'data_size': len(str(state_entry.data))
                }
            
            return info
    
    def _start_cleanup_thread(self) -> None:
        """启动清理线程"""
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """清理工作线程"""
        cleanup_interval = self.config.get('cleanup_interval', 300)
        
        while not self._stop_cleanup.wait(cleanup_interval):
            self._cleanup_expired_states()
    
    def _cleanup_expired_states(self) -> None:
        """清理过期状态"""
        with self._lock:
            now = time.time()
            expired_contexts = []
            
            for context_id, states in self._states.items():
                expired_states = []
                
                for state_type, state_entry in states.items():
                    if state_entry.is_expired():
                        expired_states.append(state_type)
                
                # 删除过期状态
                for state_type in expired_states:
                    del states[state_type]
                
                # 如果上下文没有状态了，标记为删除
                if not states:
                    expired_contexts.append(context_id)
            
            # 删除空的上下文
            for context_id in expired_contexts:
                del self._states[context_id]
    
    def __del__(self):
        """析构函数"""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
```

#### 1.2 有状态工具基类实现

**文件**: `src/core/tools/base_stateful.py`

```python
import time
import uuid
from typing import Any, Dict, Optional, Union
from abc import ABC, abstractmethod

from .base import BaseTool
from ..interfaces.tool.state_manager import IToolStateManager, StateType

class StatefulBaseTool(BaseTool, ABC):
    """状态感知工具基类"""
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any], 
                 state_manager: IToolStateManager, config: Any):
        """初始化状态感知工具"""
        super().__init__(name, description, parameters_schema)
        self.state_manager = state_manager
        self.config = config
        self._context_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._initialized = False
    
    def initialize_context(self, session_id: Optional[str] = None) -> str:
        """初始化工具上下文"""
        if self._initialized:
            return self._context_id
        
        # 生成或使用提供的会话ID
        self._session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        
        # 创建上下文ID
        self._context_id = f"{self._session_id}_{self.name}_{uuid.uuid4().hex[:8]}"
        
        # 在状态管理器中创建上下文
        self.state_manager.create_context(self._context_id, self.__class__.__name__)
        
        # 初始化各种状态
        self._initialize_connection_state()
        self._initialize_session_state()
        self._initialize_business_state()
        
        self._initialized = True
        return self._context_id
    
    def _initialize_connection_state(self) -> None:
        """初始化连接状态"""
        initial_state = {
            'active': False,
            'created_at': time.time(),
            'last_used': time.time(),
            'error_count': 0,
            'last_error': None
        }
        self.state_manager.set_state(self._context_id, StateType.CONNECTION, initial_state)
    
    def _initialize_session_state(self) -> None:
        """初始化会话状态"""
        initial_state = {
            'session_id': self._session_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'user_id': None,
            'permissions': [],
            'auth_token': None
        }
        self.state_manager.set_state(self._context_id, StateType.SESSION, initial_state)
    
    def _initialize_business_state(self) -> None:
        """初始化业务状态"""
        initial_state = {
            'created_at': time.time(),
            'version': 1,
            'data': {},
            'history': [],
            'metadata': {}
        }
        self.state_manager.set_state(self._context_id, StateType.BUSINESS, initial_state)
    
    def get_connection_state(self) -> Optional[Dict[str, Any]]:
        """获取连接状态"""
        if not self._context_id:
            return None
        return self.state_manager.get_state(self._context_id, StateType.CONNECTION)
    
    def get_session_state(self) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if not self._context_id:
            return None
        return self.state_manager.get_state(self._context_id, StateType.SESSION)
    
    def get_business_state(self) -> Optional[Dict[str, Any]]:
        """获取业务状态"""
        if not self._context_id:
            return None
        return self.state_manager.get_state(self._context_id, StateType.BUSINESS)
    
    def update_connection_state(self, updates: Dict[str, Any]) -> bool:
        """更新连接状态"""
        if not self._context_id:
            return False
        
        # 添加最后使用时间
        updates['last_used'] = time.time()
        return self.state_manager.update_state(self._context_id, StateType.CONNECTION, updates)
    
    def update_session_state(self, updates: Dict[str, Any]) -> bool:
        """更新会话状态"""
        if not self._context_id:
            return False
        
        # 添加最后活动时间
        updates['last_activity'] = time.time()
        return self.state_manager.update_state(self._context_id, StateType.SESSION, updates)
    
    def update_business_state(self, updates: Dict[str, Any]) -> bool:
        """更新业务状态"""
        if not self._context_id:
            return False
        
        # 获取当前状态
        current_state = self.get_business_state()
        if not current_state:
            return False
        
        # 更新数据和版本
        if 'data' in updates:
            current_state['data'].update(updates.pop('data'))
        
        # 添加到历史记录
        if current_state.get('history') is not None:
            current_state['history'].append({
                'timestamp': time.time(),
                'updates': updates,
                'version': current_state.get('version', 1)
            })
            
            # 限制历史记录大小
            max_history = self.config.get('business_config', {}).get('max_history_size', 1000)
            if len(current_state['history']) > max_history:
                current_state['history'] = current_state['history'][-max_history:]
        
        # 更新版本
        current_state['version'] = current_state.get('version', 1) + 1
        
        # 应用其他更新
        current_state.update(updates)
        
        return self.state_manager.set_state(self._context_id, StateType.BUSINESS, current_state)
    
    def add_to_history(self, event_type: str, data: Dict[str, Any]) -> bool:
        """添加事件到历史记录"""
        if not self._context_id:
            return False
        
        current_state = self.get_business_state()
        if not current_state or 'history' not in current_state:
            return False
        
        history_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'data': data,
            'version': current_state.get('version', 1)
        }
        
        current_state['history'].append(history_entry)
        
        # 限制历史记录大小
        max_history = self.config.get('business_config', {}).get('max_history_size', 1000)
        if len(current_state['history']) > max_history:
            current_state['history'] = current_state['history'][-max_history:]
        
        return self.state_manager.update_state(self._context_id, StateType.BUSINESS, {
            'history': current_state['history']
        })
    
    def get_context_info(self) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        if not self._context_id:
            return None
        return self.state_manager.get_context_info(self._context_id)
    
    def cleanup_context(self) -> bool:
        """清理上下文"""
        if not self._context_id:
            return False
        
        result = self.state_manager.cleanup_context(self._context_id)
        self._context_id = None
        self._session_id = None
        self._initialized = False
        return result
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    @property
    def context_id(self) -> Optional[str]:
        """获取上下文ID"""
        return self._context_id
    
    @property
    def session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self._session_id
    
    def __del__(self):
        """析构函数"""
        if self._initialized:
            self.cleanup_context()
```

### 第二阶段：Sequential Thinking工具重构

#### 2.1 重构后的Sequential Thinking工具

**文件**: `src/core/tools/types/native/sequentialthinking_stateful.py`

```python
"""
有状态Sequential Thinking Tool实现

使用新的状态感知工具架构重构，提供更好的状态管理和会话隔离。
"""

import json
import time
from typing import Dict, Any, List, Optional

from ..stateful_native_tool import StatefulNativeTool
from ...interfaces.tool.state_manager import StateType

class ThoughtData:
    """思考数据类"""
    
    def __init__(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool,
        is_revision: Optional[bool] = None,
        revises_thought: Optional[int] = None,
        branch_from_thought: Optional[int] = None,
        branch_id: Optional[str] = None,
        needs_more_thoughts: Optional[bool] = None,
        timestamp: Optional[float] = None
    ):
        self.thought = thought
        self.thought_number = thought_number
        self.total_thoughts = total_thoughts
        self.next_thought_needed = next_thought_needed
        self.is_revision = is_revision
        self.revises_thought = revises_thought
        self.branch_from_thought = branch_from_thought
        self.branch_id = branch_id
        self.needs_more_thoughts = needs_more_thoughts
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "thought": self.thought,
            "thoughtNumber": self.thought_number,
            "totalThoughts": self.total_thoughts,
            "nextThoughtNeeded": self.next_thought_needed,
            "isRevision": self.is_revision,
            "revisesThought": self.revises_thought,
            "branchFromThought": self.branch_from_thought,
            "branchId": self.branch_id,
            "needsMoreThoughts": self.needs_more_thoughts,
            "timestamp": self.timestamp
        }

def sequentialthinking_stateful(
    thought: str,
    nextThoughtNeeded: bool,
    thoughtNumber: int,
    totalThoughts: int,
    isRevision: Optional[bool] = None,
    revisesThought: Optional[int] = None,
    branchFromThought: Optional[int] = None,
    branchId: Optional[str] = None,
    needsMoreThoughts: Optional[bool] = None,
    state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """有状态顺序思考工具主函数"""
    # 初始化状态结构
    if state is None:
        state = {}
    
    # 确保状态结构存在
    if 'thought_history' not in state:
        state['thought_history'] = []
    if 'branches' not in state:
        state['branches'] = {}
    if 'current_session' not in state:
        state['current_session'] = {
            'started_at': time.time(),
            'last_activity': time.time(),
            'thought_count': 0
        }
    
    # 验证输入数据
    if not thought or not isinstance(thought, str):
        raise ValueError("Invalid thought: must be a string")
    
    if not isinstance(thoughtNumber, int) or thoughtNumber < 1:
        raise ValueError("Invalid thoughtNumber: must be a positive integer")
    
    if not isinstance(totalThoughts, int) or totalThoughts < 1:
        raise ValueError("Invalid totalThoughts: must be a positive integer")
    
    if not isinstance(nextThoughtNeeded, bool):
        raise ValueError("Invalid nextThoughtNeeded: must be a boolean")
    
    # 创建思考数据
    thought_data = ThoughtData(
        thought=thought,
        thought_number=thoughtNumber,
        total_thoughts=totalThoughts,
        next_thought_needed=nextThoughtNeeded,
        is_revision=isRevision,
        revises_thought=revisesThought,
        branch_from_thought=branchFromThought,
        branch_id=branchId,
        needs_more_thoughts=needsMoreThoughts
    )
    
    # 如果思考编号超过总思考数，自动调整总思考数
    if thought_data.thought_number > thought_data.total_thoughts:
        thought_data.total_thoughts = thought_data.thought_number
    
    # 添加到思考历史
    state['thought_history'].append(thought_data.to_dict())
    
    # 处理分支
    if thought_data.branch_from_thought and thought_data.branch_id:
        if thought_data.branch_id not in state['branches']:
            state['branches'][thought_data.branch_id] = []
        state['branches'][thought_data.branch_id].append(thought_data.to_dict())
    
    # 更新会话信息
    state['current_session']['last_activity'] = time.time()
    state['current_session']['thought_count'] += 1
    
    # 格式化思考输出（如果未禁用日志）
    disable_thought_logging = state.get('disable_thought_logging', False)
    formatted_thought = None
    if not disable_thought_logging:
        formatted_thought = _format_thought(thought_data)
        print(formatted_thought, flush=True)
    
    # 准备返回结果
    result = {
        "thoughtNumber": thought_data.thought_number,
        "totalThoughts": thought_data.total_thoughts,
        "nextThoughtNeeded": thought_data.next_thought_needed,
        "branches": list(state['branches'].keys()),
        "thoughtHistoryLength": len(state['thought_history']),
        "sessionInfo": {
            "thoughtCount": state['current_session']['thought_count'],
            "sessionDuration": time.time() - state['current_session']['started_at']
        }
    }
    
    # 返回结果和状态更新
    return {
        "result": result,
        "state": state,
        "formatted_output": formatted_thought
    }

def _format_thought(thought_data: ThoughtData) -> str:
    """格式化思考输出"""
    prefix = ""
    context = ""
    
    if thought_data.is_revision:
        prefix = "🔄 Revision"
        context = f" (revising thought {thought_data.revises_thought})" if thought_data.revises_thought is not None else ""
    elif thought_data.branch_from_thought:
        prefix = "🌿 Branch"
        context = f" (from thought {thought_data.branch_from_thought}, ID: {thought_data.branch_id})" if thought_data.branch_id is not None else ""
    else:
        prefix = "💭 Thought"
        context = ""
    
    header = f"{prefix} {thought_data.thought_number}/{thought_data.total_thoughts}{context}"
    border = "─" * (max(len(header), len(thought_data.thought)) + 4)
    
    return f"""
┌{border}┐
│ {header} │
├{border}┤
│ {thought_data.thought.ljust(len(border) - 2)} │
└{border}┘"""

class SequentialThinkingStatefulTool(StatefulNativeTool):
    """有状态顺序思考工具类"""
    
    def __init__(self, config: Any, state_manager):
        """初始化有状态顺序思考工具"""
        super().__init__(sequentialthinking_stateful, config, state_manager)
    
    def get_thought_history(self) -> List[Dict[str, Any]]:
        """获取思考历史"""
        business_state = self.get_business_state()
        if not business_state:
            return []
        return business_state.get('data', {}).get('thought_history', [])
    
    def get_branches(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取分支信息"""
        business_state = self.get_business_state()
        if not business_state:
            return {}
        return business_state.get('data', {}).get('branches', {})
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        business_state = self.get_business_state()
        if not business_state:
            return {}
        return business_state.get('data', {}).get('current_session', {})
    
    def clear_history(self) -> bool:
        """清空思考历史"""
        return self.update_business_state({
            'data': {
                'thought_history': [],
                'branches': {},
                'current_session': {
                    'started_at': time.time(),
                    'last_activity': time.time(),
                    'thought_count': 0
                }
            }
        })
    
    def disable_logging(self) -> bool:
        """禁用思考日志输出"""
        return self.update_business_state({
            'data': {'disable_thought_logging': True}
        })
    
    def enable_logging(self) -> bool:
        """启用思考日志输出"""
        return self.update_business_state({
            'data': {'disable_thought_logging': False}
        })
    
    def export_session(self) -> Dict[str, Any]:
        """导出会话数据"""
        business_state = self.get_business_state()
        if not business_state:
            return {}
        
        data = business_state.get('data', {})
        return {
            'session_info': data.get('current_session', {}),
            'thought_history': data.get('thought_history', []),
            'branches': data.get('branches', {}),
            'exported_at': time.time(),
            'context_id': self.context_id,
            'session_id': self.session_id
        }
    
    def import_session(self, session_data: Dict[str, Any]) -> bool:
        """导入会话数据"""
        if not session_data:
            return False
        
        # 验证会话数据格式
        required_keys = ['session_info', 'thought_history']
        if not all(key in session_data for key in required_keys):
            return False
        
        # 导入数据
        return self.update_business_state({
            'data': {
                'current_session': session_data['session_info'],
                'thought_history': session_data['thought_history'],
                'branches': session_data.get('branches', {}),
                'disable_thought_logging': session_data.get('disable_thought_logging', False)
            }
        })
```

#### 2.2 配置文件

**文件**: `configs/tools/native/sequentialthinking_stateful.yaml`

```yaml
name: sequentialthinking_stateful
tool_type: native_stateful
description: |
  有状态顺序思考工具，支持会话隔离和状态持久化。
  
  这是原sequentialthinking工具的有状态版本，提供以下增强功能：
  - 会话级别的状态隔离
  - 思考历史的持久化存储
  - 分支管理的状态跟踪
  - 会话导入/导出功能
  - 可配置的日志输出控制

function_path: src.core.tools.types.native.sequentialthinking_stateful:sequentialthinking_stateful
enabled: true
timeout: 30

# 状态管理配置
state_config:
  manager_type: "memory"  # 使用内存状态管理器
  ttl: 3600  # 状态1小时后过期
  auto_cleanup: true
  cleanup_interval: 300
  session_isolation: true
  max_states_per_session: 5

# 业务状态配置
business_config:
  max_history_size: 1000
  versioning: true
  max_versions: 10
  auto_save: true
  backup_enabled: false

# 函数配置
state_injection: true
state_parameter_name: "state"

parameters_schema:
  type: object
  properties:
    thought:
      type: string
      description: |
        当前思考步骤，可以包括：
        * 常规分析步骤
        * 对之前思考的修订
        * 对之前决策的疑问
        * 需要更多分析的认知
        * 方法上的改变
        * 假设生成
        * 假设验证
    nextThoughtNeeded:
      type: boolean
      description: 即使在看似结束时，是否需要另一个思考步骤
    thoughtNumber:
      type: integer
      description: 序列中的当前编号（如果需要可以超过初始总数）
      minimum: 1
    totalThoughts:
      type: integer
      description: 当前需要的思考估计数（可以向上/向下调整）
      minimum: 1
    isRevision:
      type: boolean
      description: 这是否修订了之前的思考
    revisesThought:
      type: integer
      description: 如果is_revision为true，正在重新考虑哪个思考编号
      minimum: 1
    branchFromThought:
      type: integer
      description: 如果分支，哪个思考编号是分支点
      minimum: 1
    branchId:
      type: string
      description: 当前分支的标识符（如果有）
    needsMoreThoughts:
      type: boolean
      description: 如果到达结尾但意识到需要更多思考
  required:
    - thought
    - nextThoughtNeeded
    - thoughtNumber
    - totalThoughts

metadata:
  category: "reasoning"
  tags: ["thinking", "reasoning", "problem-solving", "analysis", "planning", "stateful"]
  version: "2.0.0"
  documentation_url: "https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking"
  migration_guide: "从sequentialthinking迁移到sequentialthinking_stateful"

examples:
  - description: "基本思考序列"
    parameters:
      thought: "分析问题的核心需求"
      nextThoughtNeeded: true
      thoughtNumber: 1
      totalThoughts: 3
  - description: "修订之前的思考"
    parameters:
      thought: "重新评估问题的优先级，发现安全性比性能更重要"
      nextThoughtNeeded: true
      thoughtNumber: 2
      totalThoughts: 4
      isRevision: true
      revisesThought: 1
  - description: "创建分支思考"
    parameters:
      thought: "探索替代技术解决方案：使用微服务架构而不是单体应用"
      nextThoughtNeeded: true
      thoughtNumber: 3
      totalThoughts: 5
      branchFromThought: 2
      branchId: "alternative-architecture"
```

### 第三阶段：工具工厂和管理器更新

#### 3.1 有状态工具工厂

**文件**: `src/core/tools/factory_stateful.py`

```python
"""支持有状态工具的工具工厂实现"""

from typing import Dict, Any, List, Optional, Type, Union, TYPE_CHECKING
import logging
import inspect

from src.interfaces.tool.base import ITool, IToolFactory
from src.interfaces.tool.state_manager import IToolStateManager

class StatefulToolFactory(IToolFactory):
    """支持有状态工具的工具工厂"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化有状态工具工厂"""
        self.config = config or {}
        
        # 注册支持的工具类型
        self._tool_types: Dict[str, Type[ITool]] = {}
        self._stateful_tool_types: Dict[str, Type[ITool]] = {}
        
        # 状态管理器缓存
        self._state_managers: Dict[str, IToolStateManager] = {}
        
        # 工具实例缓存
        self._tool_cache: Dict[str, ITool] = {}
        
        # 初始化工具类型
        self._register_tool_types()
        
        logger.info("StatefulToolFactory初始化完成")
    
    def create_tool(self, tool_config: Union[Dict[str, Any], 'ToolConfig']) -> ITool:
        """创建工具实例（支持有状态工具）"""
        try:
            # 解析配置
            config = self._parse_config(tool_config)
            
            # 检查是否为有状态工具
            if self._is_stateful_tool(config.tool_type):
                return self._create_stateful_tool(config)
            else:
                return self._create_stateless_tool(config)
                
        except Exception as e:
            logger.error(f"创建工具失败: {e}")
            raise ValueError(f"创建工具失败: {e}")
    
    def create_stateful_tool_session(self, tool_name: str, session_id: str) -> Optional[ITool]:
        """创建有状态工具会话"""
        try:
            # 从缓存或配置中获取工具配置
            tool_config = self._get_tool_config(tool_name)
            if not tool_config:
                return None
            
            # 创建工具实例
            tool = self.create_tool(tool_config)
            
            # 如果是有状态工具，初始化上下文
            if hasattr(tool, 'initialize_context'):
                tool.initialize_context(session_id)
            
            return tool
            
        except Exception as e:
            logger.error(f"创建有状态工具会话失败: {tool_name}, 错误: {e}")
            return None
```

#### 3.2 有状态工具管理器

**文件**: `src/core/tools/manager_stateful.py`

```python
"""支持有状态工具的工具管理器"""

import asyncio
from typing import Dict, Any, List, Optional
import logging

from src.interfaces.tool.base import ITool, IToolManager
from .factory_stateful import StatefulToolFactory

class StatefulToolManager(IToolManager):
    """支持有状态工具的工具管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化有状态工具管理器"""
        self.config = config or {}
        self.factory = StatefulToolFactory(config)
        self._initialized = False
        self._active_sessions: Dict[str, Dict[str, ITool]] = {}  # session_id -> {tool_name: tool}
    
    async def initialize(self) -> None:
        """初始化工具管理器"""
        if self._initialized:
            return
        
        # 加载配置中的工具
        await self._load_tools_from_config()
        
        self._initialized = True
        logger.info("StatefulToolManager初始化完成")
    
    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行工具"""
        session_id = context.get('session_id') if context else None
        
        # 获取工具实例
        tool = await self.get_tool(name, session_id)
        if not tool:
            raise ValueError(f"工具不存在: {name}")
        
        # 执行工具
        try:
            if hasattr(tool, 'execute_async'):
                return await tool.execute_async(**arguments)
            else:
                return tool.execute(**arguments)
        except Exception as e:
            logger.error(f"执行工具失败: {name}, 错误: {e}")
            raise
    
    async def cleanup_session(self, session_id: str) -> None:
        """清理会话"""
        if session_id in self._active_sessions:
            session_tools = self._active_sessions[session_id]
            
            # 清理所有工具的上下文
            for tool in session_tools.values():
                if hasattr(tool, 'cleanup_context'):
                    tool.cleanup_context()
            
            # 删除会话
            del self._active_sessions[session_id]
            
            logger.info(f"清理会话: {session_id}")
```

### 第四阶段：配置系统更新

#### 4.1 配置模型

**文件**: `src/core/tools/config_stateful.py`

```python
"""支持有状态工具的配置模型"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, validator

# 导入基础配置
from .config import (
    ToolConfig, NativeToolConfig, RestToolConfig, MCPToolConfig,
    StateManagerConfig, ConnectionStateConfig, BusinessStateConfig
)

@dataclass(kw_only=True)
class StatefulNativeToolConfig(NativeToolConfig):
    """有状态原生工具配置"""
    
    # 状态管理配置
    state_config: StateManagerConfig = field(default_factory=StateManagerConfig)
    
    # 业务状态配置
    business_config: BusinessStateConfig = field(default_factory=BusinessStateConfig)
    
    # 函数配置
    function_path: Optional[str] = None  # 函数路径（用于动态加载）
    state_injection: bool = True  # 是否注入状态参数
    state_parameter_name: str = "state"  # 状态参数名称
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        self.tool_type = "native_stateful"
```

#### 4.2 配置加载器

**文件**: `src/core/tools/loaders_stateful.py`

```python
"""支持有状态工具的配置加载器"""

import yaml
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

from .config_stateful import (
    StatefulToolRegistryConfig, StatefulNativeToolConfig, 
    StatefulMCPToolConfig, StatefulRestToolConfig
)

class StatefulToolConfigLoader:
    """有状态工具配置加载器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置加载器"""
        self.config_dir = Path(config_dir) if config_dir else Path("configs/tools")
        self._loaded_configs: Dict[str, Any] = {}
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = self.config_dir / config_path
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_file.suffix}")
            
            # 处理配置继承
            config_data = self._process_inheritance(config_data, config_file.parent)
            
            # 处理环境变量
            config_data = self._process_environment_variables(config_data)
            
            # 验证配置
            self._validate_config(config_data)
            
            return config_data
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {config_path}, 错误: {e}")
            raise
```

## 使用示例

### 基本使用示例

```python
# 1. 创建状态管理器
from src.core.tools.state.memory_state_manager import MemoryStateManager

state_config = {
    'manager_type': 'memory',
    'ttl': 3600,
    'auto_cleanup': True
}
state_manager = MemoryStateManager(state_config)

# 2. 创建工具配置
from src.core.tools.config_stateful import StatefulNativeToolConfig

tool_config = StatefulNativeToolConfig(
    name='sequentialthinking_stateful',
    description='有状态顺序思考工具',
    parameters_schema={
        'type': 'object',
        'properties': {
            'thought': {'type': 'string'},
            'nextThoughtNeeded': {'type': 'boolean'},
            'thoughtNumber': {'type': 'integer'},
            'totalThoughts': {'type': 'integer'}
        },
        'required': ['thought', 'nextThoughtNeeded', 'thoughtNumber', 'totalThoughts']
    },
    function_path='src.core.tools.types.native.sequentialthinking_stateful:sequentialthinking_stateful',
    state_injection=True
)

# 3. 创建工具实例
from src.core.tools.types.native.sequentialthinking_stateful import SequentialThinkingStatefulTool

tool = SequentialThinkingStatefulTool(tool_config, state_manager)

# 4. 初始化会话
session_id = "user_session_123"
context_id = tool.initialize_context(session_id)

# 5. 执行思考步骤
result1 = tool.execute(
    thought="分析问题的核心需求",
    nextThoughtNeeded=True,
    thoughtNumber=1,
    totalThoughts=3
)

result2 = tool.execute(
    thought="确定解决方案的技术路径",
    nextThoughtNeeded=True,
    thoughtNumber=2,
    totalThoughts=3
)

# 6. 查看会话信息
history = tool.get_thought_history()
session_info = tool.get_session_info()
branches = tool.get_branches()

# 7. 导出会话数据
session_data = tool.export_session()

# 8. 清理会话
tool.cleanup_context()
```

### 工厂使用示例

```python
# 1. 创建工厂
from src.core.tools.factory_stateful import StatefulToolFactory

factory = StatefulToolFactory()

# 2. 创建工具
tool_config = {
    'name': 'sequentialthinking_stateful',
    'tool_type': 'native_stateful',
    'description': '有状态顺序思考工具',
    'function_path': 'src.core.tools.types.native.sequentialthinking_stateful:sequentialthinking_stateful',
    'state_config': {
        'manager_type': 'memory',
        'ttl': 3600
    },
    'parameters_schema': {
        'type': 'object',
        'properties': {
            'thought': {'type': 'string'},
            'nextThoughtNeeded': {'type': 'boolean'},
            'thoughtNumber': {'type': 'integer'},
            'totalThoughts': {'type': 'integer'}
        }
    }
}

tool = factory.create_tool(tool_config)

# 3. 创建会话
session_tool = factory.create_stateful_tool_session('sequentialthinking_stateful', 'session_123')
```

### 管理器使用示例

```python
# 1. 创建管理器
from src.core.tools.manager_stateful import StatefulToolManager

manager = StatefulToolManager()

# 2. 初始化
await manager.initialize()

# 3. 执行工具
result = await manager.execute_tool(
    name='sequentialthinking_stateful',
    arguments={
        'thought': '分析问题的核心需求',
        'nextThoughtNeeded': True,
        'thoughtNumber': 1,
        'totalThoughts': 3
    },
    context={'session_id': 'session_123'}
)

# 4. 获取会话信息
session_info = await manager.get_session_info('session_123')

# 5. 清理会话
await manager.cleanup_session('session_123')
```

## 测试策略

### 单元测试

```python
# tests/unit/core/tools/state/test_memory_state_manager.py

import pytest
import time
from src.core.tools.state.memory_state_manager import MemoryStateManager
from src.core.tools.state.interfaces import StateType

class TestMemoryStateManager:
    
    @pytest.fixture
    def state_manager(self):
        config = {
            'manager_type': 'memory',
            'ttl': 3600,
            'auto_cleanup': False  # 测试时禁用自动清理
        }
        return MemoryStateManager(config)
    
    def test_create_context(self, state_manager):
        context_id = state_manager.create_context("test_context", "TestTool")
        assert context_id is not None
        assert isinstance(context_id, str)
    
    def test_set_and_get_state(self, state_manager):
        context_id = state_manager.create_context("test_context", "TestTool")
        
        state_data = {"key": "value", "number": 42}
        result = state_manager.set_state(context_id, StateType.BUSINESS, state_data)
        assert result is True
        
        retrieved_state = state_manager.get_state(context_id, StateType.BUSINESS)
        assert retrieved_state == state_data
    
    def test_update_state(self, state_manager):
        context_id = state_manager.create_context("test_context", "TestTool")
        
        # 设置初始状态
        state_data = {"key": "value", "number": 42}
        state_manager.set_state(context_id, StateType.BUSINESS, state_data)
        
        # 更新状态
        updates = {"number": 100, "new_key": "new_value"}
        result = state_manager.update_state(context_id, StateType.BUSINESS, updates)
        assert result is True
        
        # 验证更新
        retrieved_state = state_manager.get_state(context_id, StateType.BUSINESS)
        assert retrieved_state["key"] == "value"
        assert retrieved_state["number"] == 100
        assert retrieved_state["new_key"] == "new_value"
    
    def test_delete_state(self, state_manager):
        context_id = state_manager.create_context("test_context", "TestTool")
        
        # 设置状态
        state_data = {"key": "value"}
        state_manager.set_state(context_id, StateType.BUSINESS, state_data)
        
        # 删除状态
        result = state_manager.delete_state(context_id, StateType.BUSINESS)
        assert result is True
        
        # 验证删除
        retrieved_state = state_manager.get_state(context_id, StateType.BUSINESS)
        assert retrieved_state is None
    
    def test_cleanup_context(self, state_manager):
        context_id = state_manager.create_context("test_context", "TestTool")
        
        # 设置多个状态
        state_manager.set_state(context_id, StateType.BUSINESS, {"data": "business"})
        state_manager.set_state(context_id, StateType.SESSION, {"data": "session"})
        
        # 清理上下文
        result = state_manager.cleanup_context(context_id)
        assert result is True
        
        # 验证清理
        assert state_manager.get_state(context_id, StateType.BUSINESS) is None
        assert state_manager.get_state(context_id, StateType.SESSION) is None
    
    def test_ttl_expiration(self, state_manager):
        context_id = state_manager.create_context("test_context", "TestTool")
        
        # 设置带TTL的状态
        state_data = {"key": "value"}
        result = state_manager.set_state(context_id, StateType.BUSINESS, state_data, ttl=1)
        assert result is True
        
        # 立即获取应该成功
        retrieved_state = state_manager.get_state(context_id, StateType.BUSINESS)
        assert retrieved_state == state_data
        
        # 等待过期
        time.sleep(2)
        
        # 过期后获取应该返回None
        retrieved_state = state_manager.get_state(context_id, StateType.BUSINESS)
        assert retrieved_state is None
```

### 集成测试

```python
# tests/integration/core/tools/test_stateful_tool_integration.py

import pytest
from src.core.tools.state.memory_state_manager import MemoryStateManager
from src.core.tools.types.native.sequentialthinking_stateful import SequentialThinkingStatefulTool
from src.core.tools.config_stateful import StatefulNativeToolConfig

class TestStatefulToolIntegration:
    
    @pytest.fixture
    def state_manager(self):
        config = {
            'manager_type': 'memory',
            'ttl': 3600,
            'auto_cleanup': False
        }
        return MemoryStateManager(config)
    
    @pytest.fixture
    def tool_config(self):
        return StatefulNativeToolConfig(
            name='sequentialthinking_stateful',
            description='有状态顺序思考工具',
            parameters_schema={
                'type': 'object',
                'properties': {
                    'thought': {'type': 'string'},
                    'nextThoughtNeeded': {'type': 'boolean'},
                    'thoughtNumber': {'type': 'integer'},
                    'totalThoughts': {'type': 'integer'}
                },
                'required': ['thought', 'nextThoughtNeeded', 'thoughtNumber', 'totalThoughts']
            },
            function_path='src.core.tools.types.native.sequentialthinking_stateful:sequentialthinking_stateful',
            state_injection=True
        )
    
    @pytest.fixture
    def tool(self, state_manager, tool_config):
        return SequentialThinkingStatefulTool(tool_config, state_manager)
    
    def test_full_session_lifecycle(self, tool):
        # 初始化会话
        session_id = "test_session_123"
        context_id = tool.initialize_context(session_id)
        
        assert tool.is_initialized
        assert tool.context_id == context_id
        assert tool.session_id == session_id
        
        # 执行多个思考步骤
        result1 = tool.execute(
            thought="分析问题的核心需求",
            nextThoughtNeeded=True,
            thoughtNumber=1,
            totalThoughts=3
        )
        
        result2 = tool.execute(
            thought="确定解决方案的技术路径",
            nextThoughtNeeded=True,
            thoughtNumber=2,
            totalThoughts=3
        )
        
        result3 = tool.execute(
            thought="制定实施计划",
            nextThoughtNeeded=False,
            thoughtNumber=3,
            totalThoughts=3
        )
        
        # 验证结果
        assert result1["result"]["thoughtNumber"] == 1
        assert result2["result"]["thoughtNumber"] == 2
        assert result3["result"]["thoughtNumber"] == 3
        
        # 验证状态
        history = tool.get_thought_history()
        assert len(history) == 3
        
        session_info = tool.get_session_info()
        assert session_info["thought_count"] == 3
        
        # 导出会话
        session_data = tool.export_session()
        assert "session_info" in session_data
        assert "thought_history" in session_data
        assert len(session_data["thought_history"]) == 3
        
        # 清理会话
        result = tool.cleanup_context()
        assert result is True
        assert not tool.is_initialized
    
    def test_session_isolation(self, state_manager, tool_config):
        # 创建两个工具实例
        tool1 = SequentialThinkingStatefulTool(tool_config, state_manager)
        tool2 = SequentialThinkingStatefulTool(tool_config, state_manager)
        
        # 初始化不同会话
        tool1.initialize_context("session_1")
        tool2.initialize_context("session_2")
        
        # 在不同会话中执行操作
        tool1.execute(
            thought="会话1的思考",
            nextThoughtNeeded=False,
            thoughtNumber=1,
            totalThoughts=1
        )
        
        tool2.execute(
            thought="会话2的思考",
            nextThoughtNeeded=False,
            thoughtNumber=1,
            totalThoughts=1
        )
        
        # 验证会话隔离
        history1 = tool1.get_thought_history()
        history2 = tool2.get_thought_history()
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0]["thought"] == "会话1的思考"
        assert history2[0]["thought"] == "会话2的思考"
        
        # 清理
        tool1.cleanup_context()
        tool2.cleanup_context()
```

## 部署和监控

### 部署配置

```yaml
# configs/tools/registry_stateful.yaml
# 有状态工具注册表配置

# 全局状态管理配置
global_state_config:
  manager_type: "memory"
  ttl: 3600
  auto_cleanup: true
  cleanup_interval: 300

# 默认配置
default_state_manager: "memory"
default_connection_pool_size: 10
default_session_timeout: 3600

# 工具列表
tools:
  - name: "sequentialthinking_stateful"
    tool_type: "native_stateful"
    description: "有状态顺序思考工具"
    function_path: "src.core.tools.types.native.sequentialthinking_stateful:sequentialthinking_stateful"
    enabled: true
    timeout: 30
    
    state_config:
      manager_type: "memory"
      ttl: 3600
      auto_cleanup: true
      session_isolation: true
      max_states_per_session: 5
    
    business_config:
      max_history_size: 1000
      versioning: true
      max_versions: 10
      auto_save: true
```

### 监控指标

```python
# src/core/tools/monitoring/stateful_metrics.py

from typing import Dict, Any
import time
import psutil
from src.interfaces.tool.state_manager import StateType

class StatefulToolMetrics:
    """有状态工具监控指标"""
    
    def __init__(self):
        self.metrics = {
            'active_sessions': 0,
            'total_states': 0,
            'memory_usage': 0,
            'state_operations': 0,
            'error_count': 0,
            'performance': {}
        }
    
    def collect_metrics(self, state_manager, active_sessions: Dict[str, Any]) -> Dict[str, Any]:
        """收集监控指标"""
        # 会话指标
        self.metrics['active_sessions'] = len(active_sessions)
        
        # 状态指标
        contexts = state_manager.list_contexts()
        self.metrics['total_states'] = len(contexts)
        
        # 内存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        self.metrics['memory_usage'] = memory_info.rss / 1024 / 1024  # MB
        
        # 性能指标
        self.metrics['performance'] = self._collect_performance_metrics(state_manager)
        
        return self.metrics.copy()
    
    def _collect_performance_metrics(self, state_manager) -> Dict[str, Any]:
        """收集性能指标"""
        start_time = time.time()
        
        # 测试状态操作性能
        test_context = "metrics_test_context"
        state_manager.create_context(test_context, "MetricsTest")
        
        # 测试写入性能
        write_start = time.time()
        state_manager.set_state(test_context, StateType.BUSINESS, {"test": "data"})
        write_time = time.time() - write_start
        
        # 测试读取性能
        read_start = time.time()
        state_manager.get_state(test_context, StateType.BUSINESS)
        read_time = time.time() - read_start
        
        # 清理
        state_manager.cleanup_context(test_context)
        
        total_time = time.time() - start_time
        
        return {
            'write_latency_ms': write_time * 1000,
            'read_latency_ms': read_time * 1000,
            'total_operation_time_ms': total_time * 1000
        }
```

## 总结

本实施方案提供了：

1. **完整的实现代码**: 从状态管理器到工具类的完整实现
2. **详细的配置示例**: 展示如何配置有状态工具
3. **丰富的使用示例**: 涵盖各种使用场景
4. **全面的测试策略**: 单元测试和集成测试
5. **部署和监控**: 生产环境的部署和监控方案

通过这个实施方案，开发者可以：
- 理解有状态工具架构的实现细节
- 按照步骤进行迁移和部署
- 根据实际需求进行定制和扩展
- 确保系统的稳定性和性能

这个方案为项目的有状态工具需求提供了完整、可行的解决方案。