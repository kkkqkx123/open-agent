"""事件收集器模块

负责收集和管理工作流执行过程中的事件。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json


class EventType(Enum):
    """事件类型枚举"""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    NODE_START = "node_start"
    NODE_END = "node_end"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"


class IEventCollector(ABC):
    """事件收集器接口"""

    @abstractmethod
    def collect_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """收集事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        pass

    @abstractmethod
    def get_events(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取事件列表

        Args:
            session_id: 会话ID
            limit: 限制返回的事件数量

        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        pass

    @abstractmethod
    def clear_events(self, session_id: str) -> bool:
        """清除事件

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功清除
        """
        pass

    @abstractmethod
    def register_handler(self, event_type: EventType, handler: Callable[[Dict[str, Any]], None]) -> None:
        """注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        pass


class EventCollector(IEventCollector):
    """事件收集器实现"""

    def __init__(self) -> None:
        """初始化事件收集器"""
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._handlers: Dict[EventType, List[Callable[[Dict[str, Any]], None]]] = {}

    def collect_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """收集事件"""
        session_id = data.get("session_id", "default")
        
        # 创建事件对象
        event = {
            "id": self._generate_event_id(),
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # 存储事件
        if session_id not in self._events:
            self._events[session_id] = []
        self._events[session_id].append(event)
        
        # 调用注册的处理器
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception:
                    # 处理器异常不应该影响事件收集
                    pass

    def get_events(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取事件列表"""
        events = self._events.get(session_id, [])
        
        if limit is not None:
            events = events[-limit:]
            
        return events

    def clear_events(self, session_id: str) -> bool:
        """清除事件"""
        if session_id in self._events:
            self._events[session_id].clear()
            return True
        return False

    def register_handler(self, event_type: EventType, handler: Callable[[Dict[str, Any]], None]) -> None:
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def get_events_by_type(self, session_id: str, event_type: EventType) -> List[Dict[str, Any]]:
        """按类型获取事件

        Args:
            session_id: 会话ID
            event_type: 事件类型

        Returns:
            List[Dict[str, Any]]: 指定类型的事件列表
        """
        events = self.get_events(session_id)
        return [event for event in events if event["type"] == event_type.value]

    def get_events_by_time_range(
        self,
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """按时间范围获取事件

        Args:
            session_id: 会话ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[Dict[str, Any]]: 指定时间范围内的事件列表
        """
        events = self.get_events(session_id)
        filtered_events = []
        
        for event in events:
            event_time = datetime.fromisoformat(event["timestamp"])
            
            if start_time and event_time < start_time:
                continue
            if end_time and event_time > end_time:
                continue
                
            filtered_events.append(event)
            
        return filtered_events

    def export_events(self, session_id: str, format: str = "json") -> str:
        """导出事件

        Args:
            session_id: 会话ID
            format: 导出格式，支持 "json" 或 "csv"

        Returns:
            str: 导出的事件数据
        """
        events = self.get_events(session_id)
        
        if format == "json":
            return json.dumps(events, ensure_ascii=False, indent=2)
        elif format == "csv":
            # 简单的CSV导出
            if not events:
                return ""
                
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题行
            writer.writerow(["ID", "Type", "Timestamp", "Data"])
            
            # 写入事件行
            for event in events:
                writer.writerow([
                    event["id"],
                    event["type"],
                    event["timestamp"],
                    json.dumps(event["data"], ensure_ascii=False)
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def _generate_event_id(self) -> str:
        """生成事件ID"""
        import uuid
        return str(uuid.uuid4())


class WorkflowEventCollector:
    """工作流事件收集器装饰器"""

    def __init__(self, event_collector: IEventCollector, session_id: str) -> None:
        """初始化工作流事件收集器

        Args:
            event_collector: 事件收集器
            session_id: 会话ID
        """
        self.event_collector = event_collector
        self.session_id = session_id

    def collect_workflow_start(self, workflow_name: str, config: Dict[str, Any]) -> None:
        """收集工作流开始事件"""
        self.event_collector.collect_event(
            EventType.WORKFLOW_START,
            {
                "session_id": self.session_id,
                "workflow_name": workflow_name,
                "config": config
            }
        )

    def collect_workflow_end(self, workflow_name: str, result: Dict[str, Any]) -> None:
        """收集工作流结束事件"""
        self.event_collector.collect_event(
            EventType.WORKFLOW_END,
            {
                "session_id": self.session_id,
                "workflow_name": workflow_name,
                "result": result
            }
        )

    def collect_node_start(self, node_name: str, node_type: str, config: Dict[str, Any]) -> None:
        """收集节点开始事件"""
        self.event_collector.collect_event(
            EventType.NODE_START,
            {
                "session_id": self.session_id,
                "node_name": node_name,
                "node_type": node_type,
                "config": config
            }
        )

    def collect_node_end(self, node_name: str, result: Dict[str, Any]) -> None:
        """收集节点结束事件"""
        self.event_collector.collect_event(
            EventType.NODE_END,
            {
                "session_id": self.session_id,
                "node_name": node_name,
                "result": result
            }
        )

    def collect_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """收集错误事件"""
        self.event_collector.collect_event(
            EventType.ERROR,
            {
                "session_id": self.session_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
        )

    def collect_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """收集工具调用事件"""
        self.event_collector.collect_event(
            EventType.TOOL_CALL,
            {
                "session_id": self.session_id,
                "tool_name": tool_name,
                "arguments": arguments
            }
        )

    def collect_tool_result(self, tool_name: str, result: Any, success: bool) -> None:
        """收集工具结果事件"""
        self.event_collector.collect_event(
            EventType.TOOL_RESULT,
            {
                "session_id": self.session_id,
                "tool_name": tool_name,
                "result": result,
                "success": success
            }
        )

    def collect_llm_call(self, model: str, messages: List[Dict[str, Any]], parameters: Dict[str, Any]) -> None:
        """收集LLM调用事件"""
        self.event_collector.collect_event(
            EventType.LLM_CALL,
            {
                "session_id": self.session_id,
                "model": model,
                "messages": messages,
                "parameters": parameters
            }
        )

    def collect_llm_response(self, model: str, response: str, token_usage: Dict[str, Any]) -> None:
        """收集LLM响应事件"""
        self.event_collector.collect_event(
            EventType.LLM_RESPONSE,
            {
                "session_id": self.session_id,
                "model": model,
                "response": response,
                "token_usage": token_usage
            }
        )