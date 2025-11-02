"""状态适配器

负责在域层状态和图系统状态之间进行转换。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

from ..state import WorkflowState, AgentState, LCBaseMessage
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

logger = logging.getLogger(__name__)


@dataclass
class GraphAgentState:
    """图系统Agent状态"""
    # 基本标识信息
    agent_id: str = ""
    agent_type: str = ""
    
    # 消息相关
    messages: List[LCBaseMessage] = None
    
    # 任务相关
    current_task: Optional[str] = None
    task_history: List[Dict[str, Any]] = None
    
    # 工具执行结果
    tool_results: List[Dict[str, Any]] = None
    
    # 控制信息
    current_step: str = ""
    max_iterations: int = 10
    iteration_count: int = 0
    
    # 时间信息
    start_time: Optional[str] = None
    last_update_time: Optional[str] = None
    
    # 错误和日志
    errors: List[Dict[str, Any]] = None
    logs: List[Dict[str, Any]] = None
    
    # 性能指标
    execution_metrics: Dict[str, Any] = None
    
    # 自定义字段
    custom_fields: Dict[str, Any] = None
    
    # 上下文信息
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.task_history is None:
            self.task_history = []
        if self.tool_results is None:
            self.tool_results = []
        if self.errors is None:
            self.errors = []
        if self.logs is None:
            self.logs = []
        if self.execution_metrics is None:
            self.execution_metrics = {}
        if self.custom_fields is None:
            self.custom_fields = {}
        if self.context is None:
            self.context = {}


class StateAdapter:
    """状态适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def from_graph_state(self, graph_state: WorkflowState) -> GraphAgentState:
        """将图状态转换为域状态
        
        Args:
            graph_state: 图系统状态
            
        Returns:
            GraphAgentState: 域状态
        """
        try:
            # 处理字典格式的图状态
            if isinstance(graph_state, dict):
                return self._dict_to_domain_state(graph_state)
            else:
                # 处理对象格式的图状态
                return self._object_to_domain_state(graph_state)
        except Exception as e:
            self.logger.error(f"状态转换失败: {e}")
            # 返回默认状态
            return GraphAgentState()
    
    def to_graph_state(self, domain_state: GraphAgentState) -> WorkflowState:
        """将域状态转换为图状态
        
        Args:
            domain_state: 域状态
            
        Returns:
            WorkflowState: 图系统状态
        """
        try:
            # 将域状态转换为字典格式
            state_dict = asdict(domain_state)
            
            # 确保消息列表格式正确
            if "messages" in state_dict:
                state_dict["messages"] = self._convert_messages_to_langchain(state_dict["messages"])
            
            return state_dict
        except Exception as e:
            self.logger.error(f"状态转换失败: {e}")
            # 返回默认状态
            return {}
    
    def _dict_to_domain_state(self, state_dict: Dict[str, Any]) -> GraphAgentState:
        """将字典转换为域状态"""
        return GraphAgentState(
            agent_id=state_dict.get("agent_id", ""),
            agent_type=state_dict.get("agent_type", ""),
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
    
    def _object_to_domain_state(self, state_obj: Any) -> GraphAgentState:
        """将对象转换为域状态"""
        # 提取对象属性
        state_dict = {}
        if hasattr(state_obj, '__dict__'):
            state_dict = state_obj.__dict__
        else:
            # 尝试获取常见属性
            for attr in ['agent_id', 'agent_type', 'messages', 'current_task', 'task_history', 
                         'tool_results', 'current_step', 'max_iterations', 'iteration_count',
                         'start_time', 'last_update_time', 'errors', 'logs', 'execution_metrics',
                         'custom_fields', 'context']:
                if hasattr(state_obj, attr):
                    state_dict[attr] = getattr(state_obj, attr)
        
        return self._dict_to_domain_state(state_dict)
    
    def _convert_messages_from_langchain(self, messages: List) -> List[LCBaseMessage]:
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
    
    def _convert_messages_to_langchain(self, messages: List) -> List[LCBaseMessage]:
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


# 全局状态适配器实例
_global_adapter: Optional[StateAdapter] = None


def get_state_adapter() -> StateAdapter:
    """获取全局状态适配器实例
    
    Returns:
        StateAdapter: 状态适配器实例
    """
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = StateAdapter()
    return _global_adapter