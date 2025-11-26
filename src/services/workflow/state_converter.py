"""工作流状态转换器

负责在工作流状态的不同表示形式之间进行转换：
- WorkflowState (图系统状态) <-> WorkflowStateAdapter (内部状态)
- 处理消息格式转换
- 向后兼容性支持
"""

import warnings
from typing import Dict, Any, Optional, List, cast
from dataclasses import dataclass, asdict, field
import logging

from src.core.state import WorkflowState
from src.core.state.implementations.workflow_state import BaseMessage
from core.llm.utils.message_converters import MessageConverter
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStateAdapter:
    """工作流状态适配器
    
    提供WorkflowState的结构化表示，便于状态操作和转换。
    """
    # 基本标识信息
    workflow_id: str = ""
    workflow_type: str = ""
    
    # 消息相关
    messages: List[BaseMessage] = field(default_factory=list)
    
    # 任务相关
    current_task: Optional[str] = None
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 工具执行结果
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # 控制信息
    current_step: str = ""
    max_iterations: int = 10
    iteration_count: int = 0
    
    # 时间信息
    start_time: Optional[str] = None
    last_update_time: Optional[str] = None
    
    # 错误和日志
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # 性能指标
    execution_metrics: Dict[str, Any] = field(default_factory=dict)

    # 自定义字段
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # 上下文信息
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __getattr__(self, name: str) -> Any:
        """提供向后兼容性支持
        
        Args:
            name: 属性名
            
        Returns:
            属性值
            
        Raises:
            AttributeError: 如果属性不存在且不在兼容列表中
        """
        # 向后兼容性映射
        compatibility_map = {
            'agent_id': 'workflow_id',
            'agent_type': 'workflow_type',
        }
        
        if name in compatibility_map:
            new_name = compatibility_map[name]
            warnings.warn(
                f"{name} is deprecated, use {new_name} instead",
                DeprecationWarning,
                stacklevel=2
            )
            return getattr(self, new_name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """提供向后兼容性支持
        
        Args:
            name: 属性名
            value: 属性值
        """
        # 向后兼容性映射
        compatibility_map = {
            'agent_id': 'workflow_id',
            'agent_type': 'workflow_type',
        }
        
        if name in compatibility_map:
            new_name = compatibility_map[name]
            warnings.warn(
                f"{name} is deprecated, use {new_name} instead",
                DeprecationWarning,
                stacklevel=2
            )
            super().__setattr__(new_name, value)
        else:
            super().__setattr__(name, value)


# 向后兼容性别名
GraphAgentState = WorkflowStateAdapter


class WorkflowStateConverter:
    """工作流状态转换器
    
    处理不同工作流状态表示形式之间的双向转换。
    """
    
    def __init__(self) -> None:
        """初始化状态转换器"""
        self.logger = logging.getLogger(__name__)
        self.message_converter = MessageConverter()
    
    def from_graph_state(self, graph_state: WorkflowState) -> WorkflowStateAdapter:
        """将图状态转换为适配器状态
        
        Args:
            graph_state: 图系统状态
            
        Returns:
            WorkflowStateAdapter: 适配器状态
        """
        try:
            # 处理字典格式的图状态
            if isinstance(graph_state, dict):
                return self._dict_to_adapter_state(graph_state)
            else:
                # 处理对象格式的图状态
                return self._object_to_adapter_state(graph_state)
        except Exception as e:
            self.logger.error(f"状态转换失败: {e}")
            # 返回默认状态
            return WorkflowStateAdapter()
    
    def to_graph_state(self, adapter_state: WorkflowStateAdapter) -> WorkflowState:
        """将适配器状态转换为图状态
        
        Args:
            adapter_state: 适配器状态
            
        Returns:
            WorkflowState: 图系统状态
        """
        try:
            # 将适配器状态转换为字典格式
            state_dict = asdict(adapter_state)
            
            # 确保消息列表格式正确
            if "messages" in state_dict:
                state_dict["messages"] = self._convert_messages_to_langchain(state_dict["messages"])

            return cast(WorkflowState, state_dict)
        except Exception as e:
            self.logger.error(f"状态转换失败: {e}")
            # 返回默认状态
            return cast(WorkflowState, {})
    
    def _dict_to_adapter_state(self, state_dict: Dict[str, Any]) -> WorkflowStateAdapter:
        """将字典转换为适配器状态"""
        return WorkflowStateAdapter(
            # 字段映射：agent_id → workflow_id, agent_type → workflow_type
            workflow_id=state_dict.get("agent_id", state_dict.get("workflow_id", "")),
            workflow_type=state_dict.get("agent_type", state_dict.get("workflow_type", "")),
            messages=self._convert_messages_from_langchain(state_dict.get("messages", [])),
            current_task=state_dict.get("current_task"),
            task_history=state_dict.get("task_history", []),
            tool_results=state_dict.get("tool_results", []),
            current_step=state_dict.get("current_step", ""),
            max_iterations=state_dict.get("max_iterations", 10),
            iteration_count=state_dict.get("iteration_count", 0),
            start_time=state_dict.get("start_time"),
            last_update_time=state_dict.get("last_update_time"),
            errors=state_dict.get("errors", []),
            logs=state_dict.get("logs", []),
            execution_metrics=state_dict.get("execution_metrics", {}),
            custom_fields=state_dict.get("custom_fields", {}),
            context=state_dict.get("context", {})
        )
    
    def _object_to_adapter_state(self, state_obj: Any) -> WorkflowStateAdapter:
        """将对象转换为适配器状态"""
        # 提取对象属性
        state_dict = {}
        if hasattr(state_obj, '__dict__'):
            state_dict = state_obj.__dict__
        else:
            # 尝试获取常见属性，支持新旧字段名
            for attr in ['workflow_id', 'agent_id', 'workflow_type', 'agent_type', 'messages', 'current_task', 'task_history',
                         'tool_results', 'current_step', 'max_iterations', 'iteration_count',
                         'start_time', 'last_update_time', 'errors', 'logs', 'execution_metrics',
                         'custom_fields', 'context']:
                if hasattr(state_obj, attr):
                    state_dict[attr] = getattr(state_obj, attr)
        
        return self._dict_to_adapter_state(state_dict)
    
    def _convert_messages_from_langchain(self, messages: List) -> List[BaseMessage]:
        """将LangChain消息转换为内部消息格式"""
        converted_messages = []
        
        for msg in messages:
            if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
                # 已经是LangChain消息格式，直接使用
                converted_messages.append(msg)
            elif isinstance(msg, dict):
                # 字典格式，转换为LangChain消息
                content = msg.get("content", "")
                role = msg.get("role", "human")
                
                if role == "human":
                    converted_messages.append(HumanMessage(content=content))
                elif role == "ai":
                    converted_messages.append(AIMessage(content=content))
                elif role == "system":
                    converted_messages.append(SystemMessage(content=content))
                elif role == "tool":
                    tool_call_id = msg.get("tool_call_id", "")
                    converted_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
                else:
                    # 默认为人类消息
                    converted_messages.append(HumanMessage(content=content))
            else:
                # 其他格式，尝试转换为LangChain消息
                try:
                    if hasattr(msg, 'content') and hasattr(msg, 'type'):
                        content = getattr(msg, 'content')
                        msg_type = getattr(msg, 'type')
                        
                        if msg_type == 'human':
                            converted_messages.append(HumanMessage(content=content))
                        elif msg_type == 'ai':
                            converted_messages.append(AIMessage(content=content))
                        elif msg_type == 'system':
                            converted_messages.append(SystemMessage(content=content))
                        elif msg_type == 'tool':
                            tool_call_id = getattr(msg, 'tool_call_id', "")
                            converted_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
                        else:
                            converted_messages.append(HumanMessage(content=content))
                    else:
                        # 默认处理
                        converted_messages.append(HumanMessage(content=str(msg)))
                except Exception as e:
                    self.logger.warning(f"消息转换失败: {e}")
                    converted_messages.append(HumanMessage(content=str(msg)))
        
        return converted_messages
    
    def _convert_messages_to_langchain(self, messages: List) -> List[BaseMessage]:
        """将内部消息格式转换为LangChain消息"""
        converted_messages = []
        
        for msg in messages:
            if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
                # 已经是LangChain消息格式，直接使用
                converted_messages.append(msg)
            elif isinstance(msg, dict):
                # 字典格式，转换为LangChain消息
                content = msg.get("content", "")
                role = msg.get("role", "human")
                
                if role == "human":
                    converted_messages.append(HumanMessage(content=content))
                elif role == "ai":
                    converted_messages.append(AIMessage(content=content))
                elif role == "system":
                    converted_messages.append(SystemMessage(content=content))
                elif role == "tool":
                    tool_call_id = msg.get("tool_call_id", "")
                    converted_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
                else:
                    # 默认为人类消息
                    converted_messages.append(HumanMessage(content=content))
            else:
                # 其他格式，尝试转换为LangChain消息
                try:
                    if hasattr(msg, 'content') and hasattr(msg, 'type'):
                        content = getattr(msg, 'content')
                        msg_type = getattr(msg, 'type')
                        
                        if msg_type == 'human':
                            converted_messages.append(HumanMessage(content=content))
                        elif msg_type == 'ai':
                            converted_messages.append(AIMessage(content=content))
                        elif msg_type == 'system':
                            converted_messages.append(SystemMessage(content=content))
                        elif msg_type == 'tool':
                            tool_call_id = getattr(msg, 'tool_call_id', "")
                            converted_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
                        else:
                            converted_messages.append(HumanMessage(content=content))
                    else:
                        # 默认处理
                        converted_messages.append(HumanMessage(content=str(msg)))
                except Exception as e:
                    self.logger.warning(f"消息转换失败: {e}")
                    converted_messages.append(HumanMessage(content=str(msg)))
        
        return converted_messages


# 全局状态转换器实例
_global_converter: Optional[WorkflowStateConverter] = None


def get_state_converter() -> WorkflowStateConverter:
    """获取全局状态转换器实例
    
    Returns:
        WorkflowStateConverter: 状态转换器实例
    """
    global _global_converter
    if _global_converter is None:
        _global_converter = WorkflowStateConverter()
    return _global_converter


# 向后兼容性别名
def get_state_adapter() -> WorkflowStateConverter:
    """获取全局状态转换器实例（旧名称，保留向后兼容性）
    
    .. deprecated::
        使用 get_state_converter() 替代
    
    Returns:
        WorkflowStateConverter: 状态转换器实例
    """
    warnings.warn(
        "get_state_adapter() is deprecated, use get_state_converter() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return get_state_converter()


# 向后兼容性别名
def get_graph_agent_state_adapter() -> WorkflowStateConverter:
    """获取全局状态转换器实例（已废弃）
    
    .. deprecated::
        使用 get_state_converter() 替代
    
    Returns:
        WorkflowStateConverter: 状态转换器实例
    """
    warnings.warn(
        "get_graph_agent_state_adapter() is deprecated, use get_state_converter() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return get_state_converter()
