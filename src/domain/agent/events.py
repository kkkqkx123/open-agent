"""Agent事件定义"""

from enum import Enum
from typing import Dict, Any, Callable, List


class AgentEvent(Enum):
    EXECUTION_STARTED = "execution_started"
    TOOL_CALL_REQUESTED = "tool_call_requested"
    DECISION_MADE = "decision_made"
    EXECUTION_COMPLETED = "execution_completed"
    ERROR_OCCURRED = "error_occurred"


class AgentEventManager:
    """Agent事件管理器实现"""

    def __init__(self) -> None:
        self._handlers: Dict[AgentEvent, List[Callable]] = {}
    
    def subscribe(self, event_type: AgentEvent, handler: Callable) -> None:
        """订阅Agent事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: AgentEvent, data: Dict[str, Any]) -> None:
        """发布Agent事件"""
        if event in self._handlers:
            for handler in self._handlers[event]:
                handler(data)