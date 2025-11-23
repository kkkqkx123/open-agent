"""工作流状态实现

整合了状态管理和消息管理的简化实现。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Type

from src.interfaces.state.workflow import IWorkflowState

# Import LangChain message types
from langchain_core.messages import (
    BaseMessage as LCBaseMessage,
    HumanMessage as LCHumanMessage,
    AIMessage as LCAIMessage,
    SystemMessage as LCSystemMessage,
    ToolMessage as LCToolMessage,
)


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
    
    def to_langchain(self) -> LCBaseMessage:
        """转换为LangChain消息格式"""
        if self.role == MessageRole.HUMAN:
            return LCHumanMessage(content=self.content)
        elif self.role == MessageRole.AI:
            return LCAIMessage(content=self.content)
        elif self.role == MessageRole.SYSTEM:
            return LCSystemMessage(content=self.content)
        elif self.role == MessageRole.TOOL:
            return LCToolMessage(content=self.content, tool_call_id="")
        else:
            return LCBaseMessage(content=self.content)


@dataclass
class HumanMessage(BaseMessage):
    """人类消息"""
    role: str = MessageRole.HUMAN


@dataclass
class AIMessage(BaseMessage):
    """AI消息"""
    role: str = MessageRole.AI


@dataclass
class SystemMessage(BaseMessage):
    """系统消息"""
    role: str = MessageRole.SYSTEM


@dataclass
class ToolMessage(BaseMessage):
    """工具消息"""
    role: str = MessageRole.TOOL
    tool_call_id: str = ""
    
    def to_langchain(self) -> LCToolMessage:
        """转换为LangChain ToolMessage格式"""
        return LCToolMessage(content=self.content, tool_call_id=self.tool_call_id)


class MessageManager:
    """简化的消息管理器"""
    
    def __init__(self) -> None:
        self._messages: List[Union[BaseMessage, LCBaseMessage]] = []
    
    def add_message(self, message: Union[BaseMessage, LCBaseMessage]) -> None:
        """添加消息"""
        self._messages.append(message)
    
    def get_messages(self) -> List[Union[BaseMessage, LCBaseMessage]]:
        """获取所有消息"""
        return self._messages.copy()
    
    def get_last_message(self) -> Union[BaseMessage, LCBaseMessage, None]:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None
    
    def clear_messages(self) -> None:
        """清除所有消息"""
        self._messages.clear()
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        messages_data: List[Dict[str, Any]] = []
        for msg in self._messages:
            if isinstance(msg, BaseMessage):
                messages_data.append({
                    "content": msg.content,
                    "role": msg.role,
                    "tool_call_id": getattr(msg, 'tool_call_id', '')
                })
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


class WorkflowState(IWorkflowState):
    """工作流状态实现
    
    整合了状态管理和消息管理的完整实现。
    """
    
    def __init__(self) -> None:
        """初始化工作流状态"""
        # 基础状态数据
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = datetime.now()
        self._id: Optional[str] = None
        self._complete: bool = False
        
        # 消息管理
        self._message_manager = MessageManager()
        
        # 工作流特定字段
        self._current_node: Optional[str] = None
        self._iteration_count: int = 0
        self._thread_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._execution_history: List[Dict[str, Any]] = []
        self._errors: List[str] = []
        self._max_iterations: int = 10
    
    # IState 接口实现
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置状态数据"""
        self._data[key] = value
        self._updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
        self._updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._id
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._id = id
        self._updated_at = datetime.now()
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        return self._updated_at
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return self._complete
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._complete = True
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data": self._data,
            "metadata": self._metadata,
            "messages": self._message_manager.to_dict(),
            "current_node": self._current_node,
            "iteration_count": self._iteration_count,
            "thread_id": self._thread_id,
            "session_id": self._session_id,
            "execution_history": self._execution_history,
            "errors": self._errors,
            "max_iterations": self._max_iterations,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "id": self._id,
            "complete": self._complete
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
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
        
        return instance
    
    # IWorkflowState 接口实现
    @property
    def messages(self) -> List[Union[BaseMessage, LCBaseMessage]]:
        """获取消息列表"""
        return self._message_manager.get_messages()
    
    @property
    def fields(self) -> Dict[str, Any]:
        """获取工作流字段"""
        return {
            "current_node": self._current_node,
            "iteration_count": self._iteration_count,
            "thread_id": self._thread_id,
            "session_id": self._session_id,
            "execution_history": self._execution_history,
            "errors": self._errors,
            "max_iterations": self._max_iterations
        }
    
    @property
    def values(self) -> Dict[str, Any]:
        """获取所有状态值（包括data和fields）"""
        return {**self._data, **self.fields}
    
    def get_messages(self) -> List[Union[BaseMessage, Any]]:
        """获取所有消息"""
        return self._message_manager.get_messages()
    
    def add_message(self, message: Union[BaseMessage, Any]) -> None:
        """添加消息"""
        self._message_manager.add_message(message)
        self._updated_at = datetime.now()
    
    def get_last_message(self) -> Union[BaseMessage, Any, None]:
        """获取最后一条消息"""
        return self._message_manager.get_last_message()
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取工作流字段值"""
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
    
    def set_field(self, key: str, value: Any) -> "WorkflowState":
        """设置工作流字段值"""
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
    
    def with_messages(self, messages: List[Union[BaseMessage, Any]]) -> "WorkflowState":
        """创建包含新消息的状态副本"""
        new_state = self.from_dict(self.to_dict())
        new_state._message_manager = MessageManager()
        for msg in messages:
            new_state._message_manager.add_message(msg)
        return new_state
    
    def with_metadata(self, metadata: Dict[str, Any]) -> "WorkflowState":
        """创建包含新元数据的状态副本"""
        new_state = self.from_dict(self.to_dict())
        new_state._metadata = {**self._metadata, **metadata}
        return new_state
    
    def copy(self) -> "WorkflowState":
        """创建状态副本"""
        return self.from_dict(self.to_dict())
    
    # 工作流特定方法
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
    
    # 字典式接口实现
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值（字典式访问）
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            状态值
        """
        # 首先尝试从data中获取
        if key in self._data:
            return self._data[key]
        # 然后尝试从fields中获取
        if key in self.fields:
            return self.fields[key]
        return default
    
    def set_value(self, key: str, value: Any) -> None:
        """设置状态值
        
        Args:
            key: 键
            value: 值
        """
        self._data[key] = value
        self._updated_at = datetime.now()
    
    # 工厂方法 - 整合自 factory.py
    @classmethod
    def create_from_config(cls, workflow_id: str, workflow_name: str, input_text: str, 
                          workflow_config: Dict[str, Any] | None = None, 
                          max_iterations: int = 10) -> "WorkflowState":
        """从配置创建工作流状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            workflow_config: 工作流配置
            max_iterations: 最大迭代次数
            
        Returns:
            WorkflowState: 工作流状态实例
        """
        from .state_builder import builder
        
        return (builder()
                .with_id(workflow_id)
                .with_human_message(input_text)
                .with_max_iterations(max_iterations)
                .with_field("workflow_id", workflow_id)
                .with_field("workflow_name", workflow_name)
                .with_field("workflow_config", workflow_config or {})
                .build())

    @classmethod
    def create_state_class_from_config(cls, state_schema: Any) -> Type[Dict[str, Any]]:
        """从配置创建状态类
        
        Args:
            state_schema: 状态模式配置
            
        Returns:
            Type[Dict[str, Any]]: 状态类类型
        """
        # 创建基于配置的动态状态类
        fields: Dict[str, Any] = {}
        
        if hasattr(state_schema, 'fields'):
            for field_name, field_config in state_schema.fields.items():
                fields[field_name] = field_config
        
        # 返回可用作状态的动态类
        class DynamicState(dict):
            """从配置创建的动态状态类"""
            pass
        
        return DynamicState


# 向后兼容的工厂类
class WorkflowStateFactory:
    """工作流状态工厂 - 向后兼容
    
    提供创建工作流状态的静态方法。
    """
    
    @staticmethod
    def create_state_class_from_config(state_schema: Any) -> Type[Dict[str, Any]]:
        """从配置创建状态类
        
        Args:
            state_schema: 状态模式配置
            
        Returns:
            Type[Dict[str, Any]]: 状态类类型
        """
        return WorkflowState.create_state_class_from_config(state_schema)
    
    @staticmethod
    def create_workflow_state(
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        workflow_config: Dict[str, Any] | None = None,
        max_iterations: int = 10
    ) -> WorkflowState:
        """创建工作流状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            workflow_config: 工作流配置
            max_iterations: 最大迭代次数
            
        Returns:
            WorkflowState: 工作流状态实例
        """
        return WorkflowState.create_from_config(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            workflow_config=workflow_config,
            max_iterations=max_iterations
        )