"""会话播放器模块

提供会话回放和重放功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Iterator
from datetime import datetime
import json
import time

from .event_collector import IEventCollector, EventType


class IPlayer(ABC):
    """播放器接口"""

    @abstractmethod
    def replay_session(self, session_id: str, speed: float = 1.0) -> Iterator[Dict[str, Any]]:
        """回放会话

        Args:
            session_id: 会话ID
            speed: 播放速度，1.0为正常速度

        Yields:
            Dict[str, Any]: 事件数据
        """
        pass

    @abstractmethod
    def replay_from_timestamp(
        self,
        session_id: str,
        start_time: datetime,
        speed: float = 1.0
    ) -> Iterator[Dict[str, Any]]:
        """从指定时间点回放会话

        Args:
            session_id: 会话ID
            start_time: 开始时间
            speed: 播放速度

        Yields:
            Dict[str, Any]: 事件数据
        """
        pass

    @abstractmethod
    def replay_events(
        self,
        events: List[Dict[str, Any]],
        speed: float = 1.0
    ) -> Iterator[Dict[str, Any]]:
        """回放指定事件列表

        Args:
            events: 事件列表
            speed: 播放速度

        Yields:
            Dict[str, Any]: 事件数据
        """
        pass


class Player(IPlayer):
    """播放器实现"""

    def __init__(self, event_collector: IEventCollector) -> None:
        """初始化播放器

        Args:
            event_collector: 事件收集器
        """
        self.event_collector = event_collector

    def replay_session(self, session_id: str, speed: float = 1.0) -> Iterator[Dict[str, Any]]:
        """回放会话"""
        events = self.event_collector.get_events(session_id)
        yield from self._replay_events_with_timing(events, speed)

    def replay_from_timestamp(
        self,
        session_id: str,
        start_time: datetime,
        speed: float = 1.0
    ) -> Iterator[Dict[str, Any]]:
        """从指定时间点回放会话"""
        events = self.event_collector.get_events_by_time_range(session_id, start_time=start_time)
        yield from self._replay_events_with_timing(events, speed)

    def replay_events(
        self,
        events: List[Dict[str, Any]],
        speed: float = 1.0
    ) -> Iterator[Dict[str, Any]]:
        """回放指定事件列表"""
        yield from self._replay_events_with_timing(events, speed)

    def _replay_events_with_timing(
        self,
        events: List[Dict[str, Any]],
        speed: float
    ) -> Iterator[Dict[str, Any]]:
        """按时间顺序回放事件"""
        if not events:
            return

        # 按时间戳排序
        events = sorted(events, key=lambda e: e["timestamp"])

        # 计算时间间隔
        base_time = datetime.fromisoformat(events[0]["timestamp"])
        last_event_time = base_time

        for event in events:
            current_event_time = datetime.fromisoformat(event["timestamp"])
            
            # 计算与上一个事件的时间间隔
            time_diff = (current_event_time - last_event_time).total_seconds()
            
            # 根据播放速度调整等待时间
            if time_diff > 0 and speed > 0:
                time.sleep(time_diff / speed)
            
            last_event_time = current_event_time
            
            yield event

    def replay_session_interactive(
        self,
        session_id: str,
        event_handlers: Optional[Dict[EventType, Callable[[Dict[str, Any]], None]]] = None
    ) -> None:
        """交互式回放会话

        Args:
            session_id: 会话ID
            event_handlers: 事件处理器映射
        """
        events = self.event_collector.get_events(session_id)
        
        if not events:
            print(f"会话 {session_id} 没有事件记录")
            return

        print(f"开始回放会话 {session_id}，共 {len(events)} 个事件")
        print("按 Enter 播放下一个事件，输入 'q' 退出，输入 's' 跳过到下一个事件")

        for i, event in enumerate(events):
            print(f"\n事件 {i + 1}/{len(events)}: {event['type']} - {event['timestamp']}")
            
            # 显示事件数据摘要
            self._print_event_summary(event)
            
            # 等待用户输入
            while True:
                user_input = input("> ").strip().lower()
                
                if user_input == "" or user_input == "n":
                    # 播放事件
                    if event_handlers and event['type'] in event_handlers:
                        try:
                            event_handlers[event['type']](event)
                        except Exception as e:
                            print(f"处理事件时出错: {e}")
                    break
                elif user_input == "q":
                    print("回放结束")
                    return
                elif user_input == "s":
                    # 跳过事件
                    break
                else:
                    print("无效输入，请使用 Enter/n(下一个), q(退出), s(跳过)")

        print("回放完成")

    def _print_event_summary(self, event: Dict[str, Any]) -> None:
        """打印事件摘要"""
        data = event.get("data", {})
        
        if event["type"] == EventType.WORKFLOW_START.value:
            print(f"  工作流开始: {data.get('workflow_name', 'Unknown')}")
        elif event["type"] == EventType.WORKFLOW_END.value:
            print(f"  工作流结束: {data.get('workflow_name', 'Unknown')}")
        elif event["type"] == EventType.NODE_START.value:
            print(f"  节点开始: {data.get('node_name', 'Unknown')} ({data.get('node_type', 'Unknown')})")
        elif event["type"] == EventType.NODE_END.value:
            print(f"  节点结束: {data.get('node_name', 'Unknown')}")
        elif event["type"] == EventType.TOOL_CALL.value:
            print(f"  工具调用: {data.get('tool_name', 'Unknown')}")
        elif event["type"] == EventType.TOOL_RESULT.value:
            success = data.get('success', False)
            print(f"  工具结果: {data.get('tool_name', 'Unknown')} - {'成功' if success else '失败'}")
        elif event["type"] == EventType.LLM_CALL.value:
            print(f"  LLM调用: {data.get('model', 'Unknown')}")
        elif event["type"] == EventType.LLM_RESPONSE.value:
            print(f"  LLM响应: {data.get('model', 'Unknown')}")
        elif event["type"] == EventType.ERROR.value:
            print(f"  错误: {data.get('error_type', 'Unknown')} - {data.get('error_message', '')}")
        else:
            print(f"  数据: {json.dumps(data, ensure_ascii=False)[:100]}...")

    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """分析会话

        Args:
            session_id: 会话ID

        Returns:
            Dict[str, Any]: 分析结果
        """
        events = self.event_collector.get_events(session_id)
        
        if not events:
            return {"error": "会话没有事件记录"}

        # 基本统计
        analysis = {
            "session_id": session_id,
            "total_events": len(events),
            "event_types": {},
            "workflow_info": {},
            "node_info": {},
            "tool_info": {},
            "error_info": {},
            "timeline": []
        }

        # 统计事件类型
        for event in events:
            event_type = event["type"]
            if event_type not in analysis["event_types"]:
                analysis["event_types"][event_type] = 0
            analysis["event_types"][event_type] += 1

        # 分析工作流信息
        workflow_start_events = [e for e in events if e["type"] == EventType.WORKFLOW_START.value]
        workflow_end_events = [e for e in events if e["type"] == EventType.WORKFLOW_END.value]
        
        if workflow_start_events:
            analysis["workflow_info"]["start_time"] = workflow_start_events[0]["timestamp"]
            analysis["workflow_info"]["workflow_name"] = workflow_start_events[0]["data"].get("workflow_name")
        
        if workflow_end_events:
            analysis["workflow_info"]["end_time"] = workflow_end_events[-1]["timestamp"]
            
            # 计算执行时间
            if workflow_start_events:
                start_time = datetime.fromisoformat(workflow_start_events[0]["timestamp"])
                end_time = datetime.fromisoformat(workflow_end_events[-1]["timestamp"])
                analysis["workflow_info"]["duration_seconds"] = (end_time - start_time).total_seconds()

        # 分析节点信息
        node_start_events = [e for e in events if e["type"] == EventType.NODE_START.value]
        node_end_events = [e for e in events if e["type"] == EventType.NODE_END.value]
        
        analysis["node_info"]["total_nodes"] = len(set(e["data"].get("node_name") for e in node_start_events))
        analysis["node_info"]["executed_nodes"] = len(node_start_events)
        
        # 计算节点执行时间
        node_times = {}
        for start_event in node_start_events:
            node_name = start_event["data"].get("node_name")
            start_time = datetime.fromisoformat(start_event["timestamp"])
            
            # 查找对应的结束事件
            end_events = [e for e in node_end_events if e["data"].get("node_name") == node_name]
            if end_events:
                end_time = datetime.fromisoformat(end_events[0]["timestamp"])
                duration = (end_time - start_time).total_seconds()
                
                if node_name not in node_times:
                    node_times[node_name] = []
                node_times[node_name].append(duration)
        
        # 计算平均执行时间
        node_avg_times = {}
        for node_name, times in node_times.items():
            node_avg_times[node_name] = sum(times) / len(times)
        
        analysis["node_info"]["average_execution_times"] = node_avg_times

        # 分析工具信息
        tool_call_events = [e for e in events if e["type"] == EventType.TOOL_CALL.value]
        tool_result_events = [e for e in events if e["type"] == EventType.TOOL_RESULT.value]
        
        analysis["tool_info"]["total_calls"] = len(tool_call_events)
        analysis["tool_info"]["successful_calls"] = sum(1 for e in tool_result_events if e["data"].get("success", False))
        analysis["tool_info"]["failed_calls"] = sum(1 for e in tool_result_events if not e["data"].get("success", False))

        # 分析错误信息
        error_events = [e for e in events if e["type"] == EventType.ERROR.value]
        analysis["error_info"]["total_errors"] = len(error_events)
        analysis["error_info"]["error_types"] = {}
        
        for error_event in error_events:
            error_type = error_event["data"].get("error_type", "Unknown")
            if error_type not in analysis["error_info"]["error_types"]:
                analysis["error_info"]["error_types"][error_type] = 0
            analysis["error_info"]["error_types"][error_type] += 1

        # 生成时间线
        for event in events[:10]:  # 只取前10个事件
            analysis["timeline"].append({
                "timestamp": event["timestamp"],
                "type": event["type"],
                "summary": self._get_event_summary(event)
            })

        return analysis

    def _get_event_summary(self, event: Dict[str, Any]) -> str:
        """获取事件摘要"""
        data = event.get("data", {})
        
        if event["type"] == EventType.WORKFLOW_START.value:
            return f"工作流开始: {data.get('workflow_name', 'Unknown')}"
        elif event["type"] == EventType.NODE_START.value:
            return f"节点开始: {data.get('node_name', 'Unknown')}"
        elif event["type"] == EventType.TOOL_CALL.value:
            return f"工具调用: {data.get('tool_name', 'Unknown')}"
        elif event["type"] == EventType.ERROR.value:
            return f"错误: {data.get('error_type', 'Unknown')}"
        else:
            return f"事件: {event['type']}"