"""工作流状态实现

简化的工作流状态实现，职责更加明确。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..base.state_base import BaseState
from ..base.message_base import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    MessageManager, MessageRole
)
from src.interfaces.state.workflow import IWorkflowState


class WorkflowState(BaseState, IWorkflowState):
    """工作流状态实现
    
    专注于工作流执行状态的管理。
    """
    
    def __init__(self) -> None:
        """初始化工作流状态"""
        super().__init__()
        self._message_manager = MessageManager()
        self._current_node: Optional[str] = None
        self._iteration_count: int = 0
        self._thread_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._execution_history: List[Dict[str, Any]] = []
        self._errors: List[str] = []
        self._max_iterations: int = 10
    
    # IWorkflowState interface implementation
    def get_messages(self) -> List[Union[BaseMessage, Any]]:
        """获取所有消息
        
        Returns:
            List[Union[BaseMessage, Any]]: 消息列表
        """
        return self._message_manager.get_messages()
    
    def add_message(self, message: Union[BaseMessage, Any]) -> None:
        """添加消息
        
        Args:
            message: 消息
        """
        self._message_manager.add_message(message)
        self._updated_at = datetime.now()
    
    def get_last_message(self) -> Union[BaseMessage, Any, None]:
        """获取最后一条消息
        
        Returns:
            Union[BaseMessage, Any, None]: 最后一条消息
        """
        return self._message_manager.get_last_message()
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取值
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            Any: 值
        """
        # 首先检查基础数据
        value = self.get_data(key, None)
        if value is not None:
            return value
        
        # 检查特殊字段
        if key == "current_node":
            return self._current_node
        elif key == "iteration_count":
            return self._iteration_count
        elif key == "thread_id":
            return self._thread_id
        elif key == "session_id":
            return self._session_id
        elif key == "messages":
            return self.get_messages()
        elif key == "errors":
            return self._errors
        elif key == "max_iterations":
            return self._max_iterations
        elif key == "execution_history":
            return self._execution_history
        
        return default
    
    def set_value(self, key: str, value: Any) -> None:
        """设置值
        
        Args:
            key: 键名
            value: 值
        """
        # 检查特殊字段
        if key == "current_node":
            self._current_node = value
        elif key == "iteration_count":
            self._iteration_count = value
        elif key == "thread_id":
            self._thread_id = value
        elif key == "session_id":
            self._session_id = value
        elif key == "errors":
            self._errors = value
        elif key == "max_iterations":
            self._max_iterations = value
        elif key == "execution_history":
            self._execution_history = value
        else:
            # 存储在基础数据中
            self.set_data(key, value)
        
        self._updated_at = datetime.now()
    
    def get_current_node(self) -> Optional[str]:
        """获取当前节点
        
        Returns:
            Optional[str]: 当前节点ID
        """
        return self._current_node
    
    def set_current_node(self, node: str) -> None:
        """设置当前节点
        
        Args:
            node: 节点ID
        """
        self._current_node = node
        self._updated_at = datetime.now()
    
    def get_iteration_count(self) -> int:
        """获取迭代计数
        
        Returns:
            int: 迭代计数
        """
        return self._iteration_count
    
    def increment_iteration(self) -> None:
        """增加迭代计数"""
        self._iteration_count += 1
        self._updated_at = datetime.now()
    
    def get_thread_id(self) -> Optional[str]:
        """获取线程ID
        
        Returns:
            Optional[str]: 线程ID
        """
        return self._thread_id
    
    def set_thread_id(self, thread_id: str) -> None:
        """设置线程ID
        
        Args:
            thread_id: 线程ID
        """
        self._thread_id = thread_id
        self._updated_at = datetime.now()
    
    def get_session_id(self) -> Optional[str]:
        """获取会话ID
        
        Returns:
            Optional[str]: 会话ID
        """
        return self._session_id
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID
        
        Args:
            session_id: 会话ID
        """
        self._session_id = session_id
        self._updated_at = datetime.now()
    
    # 工作流特定方法
    def add_error(self, error: str) -> None:
        """添加错误
        
        Args:
            error: 错误信息
        """
        self._errors.append(error)
        self._updated_at = datetime.now()
    
    def has_errors(self) -> bool:
        """检查是否有错误
        
        Returns:
            bool: 是否有错误
        """
        return len(self._errors) > 0
    
    def get_errors(self) -> List[str]:
        """获取所有错误
        
        Returns:
            List[str]: 错误列表
        """
        return self._errors.copy()
    
    def clear_errors(self) -> None:
        """清除所有错误"""
        self._errors.clear()
        self._updated_at = datetime.now()
    
    def is_max_iterations_reached(self) -> bool:
        """检查是否达到最大迭代次数
        
        Returns:
            bool: 是否达到最大迭代次数
        """
        return self._iteration_count >= self._max_iterations
    
    def add_execution_step(self, step: Dict[str, Any]) -> None:
        """添加执行步骤
        
        Args:
            step: 执行步骤
        """
        self._execution_history.append(step)
        self._updated_at = datetime.now()
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史
        
        Returns:
            List[Dict[str, Any]]: 执行历史
        """
        return self._execution_history.copy()
    
    def clear_execution_history(self) -> None:
        """清除执行历史"""
        self._execution_history.clear()
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        base_dict = super().to_dict()
        base_dict.update({
            "messages": self._message_manager.to_dict(),
            "current_node": self._current_node,
            "iteration_count": self._iteration_count,
            "thread_id": self._thread_id,
            "session_id": self._session_id,
            "execution_history": self._execution_history,
            "errors": self._errors,
            "max_iterations": self._max_iterations
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """从字典创建状态
        
        Args:
            data: 字典数据
            
        Returns:
            WorkflowState: 工作流状态实例
        """
        instance = cls()
        
        # 加载基础数据
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 加载时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        # 加载消息
        messages_data = data.get("messages", [])
        instance._message_manager.from_dict(messages_data)
        
        # 加载工作流特定字段
        instance._current_node = data.get("current_node")
        instance._iteration_count = data.get("iteration_count", 0)
        instance._thread_id = data.get("thread_id")
        instance._session_id = data.get("session_id")
        instance._execution_history = data.get("execution_history", [])
        instance._errors = data.get("errors", [])
        instance._max_iterations = data.get("max_iterations", 10)
        
        return instance
    
    def reset(self) -> None:
        """重置状态"""
        super().reset()
        self._message_manager.clear_messages()
        self._current_node = None
        self._iteration_count = 0
        self._thread_id = None
        self._session_id = None
        self._execution_history.clear()
        self._errors.clear()
    
    def clone(self) -> "WorkflowState":
        """克隆状态
        
        Returns:
            WorkflowState: 克隆的状态
        """
        return self.from_dict(self.to_dict())
    
    def merge(self, other: "WorkflowState") -> None:
        """合并另一个状态
        
        Args:
            other: 另一个状态
        """
        super().merge(other)
        
        # 合并消息
        for message in other.get_messages():
            self.add_message(message)
        
        # 合并执行历史
        self._execution_history.extend(other._execution_history)
        
        # 合并错误
        self._errors.extend(other._errors)
        
        # 更新非合并字段
        if other._current_node is not None:
            self._current_node = other._current_node
        if other._thread_id is not None:
            self._thread_id = other._thread_id
        if other._session_id is not None:
            self._session_id = other._session_id
        
        self._updated_at = datetime.now()