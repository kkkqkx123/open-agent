"""工作流状态实现

提供工作流状态的具体实现，继承自基础状态并实现工作流特定功能。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from src.interfaces.state.workflow import IWorkflowState
from src.interfaces.state.base import IState
from ..implementations.base_state import BaseStateImpl


logger = get_logger(__name__)


# 消息类型定义
class MessageRole:
    """消息角色常量"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
    UNKNOWN = "unknown"


class BaseMessage:
    """消息基类"""
    def __init__(self, content: str, role: str = MessageRole.UNKNOWN):
        self.content = content
        self.role = role
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "role": self.role
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseMessage':
        """从字典创建消息"""
        return cls(data["content"], data.get("role", MessageRole.UNKNOWN))


class HumanMessage(BaseMessage):
    """人类消息"""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.HUMAN)


class AIMessage(BaseMessage):
    """AI消息"""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.AI)


class SystemMessage(BaseMessage):
    """系统消息"""
    def __init__(self, content: str):
        super().__init__(content, MessageRole.SYSTEM)


class ToolMessage(BaseMessage):
    """工具消息"""
    def __init__(self, content: str, tool_call_id: str = ""):
        super().__init__(content, MessageRole.TOOL)
        self.tool_call_id = tool_call_id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "role": self.role,
            "tool_call_id": self.tool_call_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolMessage':
        """从字典创建消息"""
        return cls(data["content"], data.get("tool_call_id", ""))


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
    
    def clear_messages(self) -> None:
        """清除所有消息"""
        self._messages.clear()
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self._messages)
    
    def get_messages_by_role(self, role: str) -> List[Union[BaseMessage, Any]]:
        """根据角色获取消息"""
        return [msg for msg in self._messages 
                if hasattr(msg, 'role') and msg.role == role]
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        messages_data = []
        for msg in self._messages:
            if isinstance(msg, BaseMessage):
                messages_data.append(msg.to_dict())
            elif hasattr(msg, 'content'):
                messages_data.append({
                    "content": msg.content,
                    "role": getattr(msg, 'type', 'unknown')
                })
            else:
                messages_data.append({
                    "content": str(msg),
                    "role": "unknown"
                })
        return messages_data
    
    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> 'MessageManager':
        """从字典创建消息管理器"""
        manager = cls()
        for msg_data in data:
            role = msg_data.get('role', MessageRole.UNKNOWN)
            content = msg_data.get('content', '')
            
            if role == MessageRole.HUMAN:
                msg = HumanMessage(content)
            elif role == MessageRole.AI:
                msg = AIMessage(content)
            elif role == MessageRole.SYSTEM:
                msg = SystemMessage(content)
            elif role == MessageRole.TOOL:
                msg = ToolMessage(content, msg_data.get('tool_call_id', ''))
            else:
                msg = BaseMessage(content, role)
            
            manager.add_message(msg)
        
        return manager


class WorkflowState(BaseStateImpl, IWorkflowState, IState):
    """工作流状态实现
    
    继承自基础状态实现，添加工作流特定的功能。
    """
    
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
    
    # IWorkflowState 接口实现
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

    @property
    def iteration_count(self) -> int:
        """迭代计数"""
        return self._iteration_count
    
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
    
    def get_last_message(self) -> Union[BaseMessage, Any, None]:
        """获取最后一条消息"""
        return self._message_manager.get_last_message()
    
    def copy(self) -> 'IWorkflowState':
        """创建状态副本"""
        return self.from_dict(self.to_dict())
    
    def with_metadata(self, metadata: Dict[str, Any]) -> 'IWorkflowState':
        """创建包含新元数据的状态"""
        new_state = self.from_dict(self.to_dict())
        new_state._metadata = {**self._metadata, **metadata}
        return new_state
    
    # 字典式接口支持
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值（字典式访问）"""
        # 首先尝试从data中获取
        if key in self._data:
            return self._data[key]
        # 然后尝试从fields中获取
        field_value = self.get_field(key)
        if field_value is not None:
            return field_value
        return default
    
    def set_value(self, key: str, value: Any) -> None:
        """设置状态值"""
        self._data[key] = value
        self._updated_at = datetime.now()
    
    # 字典访问方法
    def __getitem__(self, key: str) -> Any:
        """字典式获取"""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found in state")
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """字典式设置"""
        self.set_value(key, value)
    
    def setdefault(self, key: str, default: Any = None) -> Any:
        """字典式setdefault"""
        if key not in self._data and self.get_field(key) is None:
            self.set_value(key, default)
            return default
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """字典式包含检查"""
        return key in self._data or self.get_field(key) is not None
    
    def keys(self):
        """获取所有键"""
        all_keys = set(self._data.keys())
        all_keys.update(self.fields.keys())
        return all_keys
    
    def items(self):
        """获取所有键值对"""
        result = {}
        result.update(self._data)
        result.update(self.fields)
        return result.items()
    
    # 工作流特定方法
    def add_error(self, error: str) -> None:
        """添加错误"""
        self._errors.append(error)
        self._updated_at = datetime.now()
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self._errors) > 0
    
    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self._errors.copy()
    
    def clear_errors(self) -> None:
        """清除错误"""
        self._errors.clear()
        self._updated_at = datetime.now()
    
    def is_max_iterations_reached(self) -> bool:
        """检查是否达到最大迭代次数"""
        return self._iteration_count >= self._max_iterations
    
    def add_execution_step(self, step: Dict[str, Any]) -> None:
        """添加执行步骤"""
        self._execution_history.append(step)
        self._updated_at = datetime.now()
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self._execution_history.copy()
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return self._message_manager.get_message_count()
    
    def get_messages_by_role(self, role: str) -> List[Union[BaseMessage, Any]]:
        """根据角色获取消息"""
        return self._message_manager.get_messages_by_role(role)
    
    def clear_messages(self) -> None:
        """清除所有消息"""
        self._message_manager.clear_messages()
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'messages': self._message_manager.to_dict(),
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
        instance._message_manager = MessageManager.from_dict(messages_data)
        
        return instance