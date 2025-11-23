"""统一时间线输出组件

实现虚拟滚动和统一事件输出系统
"""

from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Console, ConsoleOptions, RenderResult
from rich.spinner import Spinner


@dataclass
class TimelineEvent:
    """时间线事件基类"""
    timestamp: datetime
    event_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    level: str = "info"  # info, warning, error, success
    
    def __post_init__(self) -> None:
        """后处理，确保event_type被正确设置"""
        if not hasattr(self, 'event_type') or not self.event_type:
            self.event_type = self.__class__.__name__.replace("Event", "").lower()


class UserMessageEvent(TimelineEvent):
    """用户消息事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "user_message", content, metadata or {}, level)


class AssistantMessageEvent(TimelineEvent):
    """助手消息事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "assistant_message", content, metadata or {}, level)


class ToolCallStartEvent(TimelineEvent):
    """工具调用开始事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "tool_call_start", content, metadata or {}, level)


class ToolCallEndEvent(TimelineEvent):
    """工具调用结束事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "tool_call_end", content, metadata or {}, level)


class NodeSwitchEvent(TimelineEvent):
    """节点切换事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "node_switch", content, metadata or {}, level)


class TriggerEvent(TimelineEvent):
    """触发器触发事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "trigger", content, metadata or {}, level)


class WorkflowEvent(TimelineEvent):
    """工作流事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "workflow", content, metadata or {}, level)


class StreamSegmentEvent(TimelineEvent):
    """流式输出分段事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "stream_segment", content, metadata or {}, level)


class SystemMessageEvent(TimelineEvent):
    """系统消息事件"""
    
    def __init__(self, timestamp: datetime, content: str, metadata: Optional[Dict[str, Any]] = None, level: str = "info"):
        super().__init__(timestamp, "system_message", content, metadata or {}, level)


class VirtualScrollManager:
    """虚拟滚动管理器"""
    
    def __init__(self, total_items: int, visible_height: int, item_height: int = 1):
        """初始化虚拟滚动管理器
        
        Args:
            total_items: 总项目数
            visible_height: 可见高度
            item_height: 项目高度
        """
        self.total_items = total_items
        self.visible_height = visible_height
        self.item_height = item_height
        self.scroll_offset = 0
        self.visible_start = 0
        self.visible_end = 0
        
    def update_visible_range(self) -> Tuple[int, int]:
        """更新可见范围
        
        Returns:
            Tuple[int, int]: 可见范围的开始和结束索引
        """
        max_visible_items = max(1, self.visible_height // self.item_height)
        self.visible_start = self.scroll_offset
        self.visible_end = min(self.visible_start + max_visible_items, self.total_items)
        return self.visible_start, self.visible_end
        
    def scroll_to(self, position: int) -> None:
        """滚动到指定位置
        
        Args:
            position: 目标位置
        """
        self.scroll_offset = max(0, min(position, self.total_items - 1))
        
    def scroll_by(self, delta: int) -> None:
        """相对滚动
        
        Args:
            delta: 滚动增量
        """
        self.scroll_to(self.scroll_offset + delta)
        
    def scroll_to_end(self) -> None:
        """滚动到末尾"""
        if self.total_items > 0:
            max_visible_items = max(1, self.visible_height // self.item_height)
            self.scroll_offset = max(0, self.total_items - max_visible_items)
        
    def can_scroll_up(self) -> bool:
        """检查是否可以向上滚动
        
        Returns:
            bool: 是否可以向上滚动
        """
        return self.scroll_offset > 0
        
    def can_scroll_down(self) -> bool:
        """检查是否可以向下滚动
        
        Returns:
            bool: 是否可以向下滚动
        """
        max_visible_items = max(1, self.visible_height // self.item_height)
        return self.scroll_offset + max_visible_items < self.total_items
        
    def update_total_items(self, total_items: int) -> None:
        """更新总项目数
        
        Args:
            total_items: 新的总项目数
        """
        self.total_items = total_items
        # 调整滚动偏移以确保不超出范围
        max_visible_items = max(1, self.visible_height // self.item_height)
        max_offset = max(0, self.total_items - max_visible_items)
        if self.scroll_offset > max_offset:
            self.scroll_offset = max_offset


class SegmentedStreamOutput:
    """分段流式输出管理器"""
    
    def __init__(self, segment_size: int = 200, timeline_component=None):
        """初始化分段流式输出管理器
        
        Args:
            segment_size: 分段大小
            timeline_component: 时间线组件引用
        """
        self.segment_size = segment_size
        self.current_segment = ""
        self.segments: List[str] = []
        self.is_streaming = False
        self.timeline_component = timeline_component
        self.stream_start_time: Optional[datetime] = None
        
    def add_content(self, content: str) -> None:
        """添加流式内容，按段分割
        
        Args:
            content: 新内容
        """
        self.current_segment += content
        
        # 当达到分段大小时，创建新事件
        while len(self.current_segment) >= self.segment_size:
            self._flush_segment()
            
    def _flush_segment(self) -> None:
        """刷新当前分段"""
        if self.current_segment:
            # 创建流式分段事件
            event = StreamSegmentEvent(
                timestamp=datetime.now(),
                content=self.current_segment[:self.segment_size],
                metadata={"segment_index": len(self.segments)}
            )
            
            # 添加到时间线
            if self.timeline_component:
                self.timeline_component.add_event(event)
            
            self.segments.append(self.current_segment[:self.segment_size])
            self.current_segment = self.current_segment[self.segment_size:]
            
    def start_stream(self) -> None:
        """开始流式输出"""
        self.current_segment = ""
        self.segments = []
        self.is_streaming = True
        self.stream_start_time = datetime.now()
        
    def end_stream(self) -> None:
        """结束流式输出，刷新剩余内容"""
        if self.current_segment:
            self._flush_segment()
        self.is_streaming = False
        
    def clear(self) -> None:
        """清空内容"""
        self.current_segment = ""
        self.segments = []
        self.is_streaming = False
        self.stream_start_time = None


class VirtualScrollRenderable:
    """虚拟滚动可渲染对象"""
    
    def __init__(self, timeline_component: 'UnifiedTimelineComponent'):
        """初始化虚拟滚动可渲染对象
        
        Args:
            timeline_component: 时间线组件引用
        """
        self.timeline = timeline_component
        self.scroll_manager = VirtualScrollManager(
            total_items=len(timeline_component.events),
            visible_height=30  # 默认可见高度
        )
        
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Rich渲染接口
        
        Args:
            console: Rich控制台
            options: 渲染选项
            
        Yields:
            RenderResult: 渲染结果
        """
        # 更新可见范围
        start, end = self.scroll_manager.update_visible_range()
        
        # 只渲染可见项
        visible_events = self.timeline.events[start:end]
        
        # 如果没有事件，返回空文本
        if not visible_events:
            from rich.text import Text
            yield Text("暂无事件", style="dim")
            return
        
        # 直接yield每个渲染的事件，确保每次都是独立的渲染
        for event in visible_events:
            yield self._render_event(event)
            
    def _render_event(self, event: TimelineEvent) -> Union[Text, Table]:
        """渲染单个事件
        
        Args:
            event: 事件对象
            
        Returns:
            Union[Text, Table]: 渲染结果
        """
        # 根据事件类型使用不同的样式
        event_styles = {
            "user_message": ("👤", "blue"),
            "assistant_message": ("🤖", "green"), 
            "tool_call_start": ("🔧", "magenta"),
            "tool_call_end": ("✅", "green"),
            "node_switch": ("🔄", "cyan"),
            "trigger": ("⚡", "yellow"),
            "workflow": ("📋", "white"),
            "stream_segment": ("📝", "dim"),
            "system_message": ("⚙️", "yellow")
        }
        
        icon, style = event_styles.get(event.event_type, ("❓", "white"))
        time_str = event.timestamp.strftime("%H:%M:%S")
        
        # 根据级别调整样式
        level_styles = {
            "error": "bold red",
            "warning": "bold yellow",
            "success": "bold green",
            "info": style
        }
        final_style = level_styles.get(event.level, style)
        
        content = Text()
        content.append(f"{time_str} {icon} ", style=final_style)
        content.append(event.content, style=final_style)
        
        return content
        
    def update_scroll_manager(self) -> None:
        """更新滚动管理器"""
        self.scroll_manager.update_total_items(len(self.timeline.events))
        
    def scroll_to_end(self) -> None:
        """滚动到末尾"""
        self.scroll_manager.scroll_to_end()


class UnifiedTimelineComponent:
    """统一时间线输出组件"""
    
    def __init__(self, max_events: int = 1000):
        """初始化统一时间线组件
        
        Args:
            max_events: 最大事件数量
        """
        self.max_events = max_events
        self.events: List[TimelineEvent] = []
        self.virtual_scroll_offset = 0
        self.visible_range = (0, 50)  # 虚拟滚动可见范围
        self.auto_scroll = True  # 自动滚动到最新事件
        
        # 初始化分段流式输出管理器
        self.stream_manager = SegmentedStreamOutput(timeline_component=self)
        
        # 初始化虚拟滚动渲染器
        self.virtual_renderable = VirtualScrollRenderable(self)
        
    def add_event(self, event: TimelineEvent) -> None:
        """添加事件到时间线
        
        Args:
            event: 事件对象
        """
        self.events.append(event)
        
        # 限制事件数量，支持虚拟滚动
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
            
        # 更新虚拟滚动管理器
        self.virtual_renderable.update_scroll_manager()
        
        # 自动滚动到最新事件
        if self.auto_scroll:
            self.virtual_renderable.scroll_to_end()
            
    def add_user_message(self, content: str) -> None:
        """添加用户消息
        
        Args:
            content: 消息内容
        """
        event = UserMessageEvent(
            timestamp=datetime.now(),
            content=content
        )
        self.add_event(event)
        
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息
        
        Args:
            content: 消息内容
        """
        event = AssistantMessageEvent(
            timestamp=datetime.now(),
            content=content
        )
        self.add_event(event)
        
    def add_system_message(self, content: str, level: str = "info") -> None:
        """添加系统消息
        
        Args:
            content: 消息内容
            level: 消息级别
        """
        event = SystemMessageEvent(
            timestamp=datetime.now(),
            content=content,
            level=level
        )
        self.add_event(event)
        
    def add_tool_call(self, tool_name: str, success: bool, result: Any = None, error: Optional[str] = None) -> None:
        """添加工具调用
        
        Args:
            tool_name: 工具名称
            success: 是否成功
            result: 结果
            error: 错误信息
        """
        # 开始事件
        start_event = ToolCallStartEvent(
            timestamp=datetime.now(),
            content=f"调用工具: {tool_name}"
        )
        self.add_event(start_event)
        
        # 结束事件
        if success:
            status = "成功"
            level = "success"
            content = f"工具调用{status}: {tool_name}"
            if result is not None:
                content += f" | 结果: {str(result)[:100]}..."
        else:
            status = "失败"
            level = "error"
            content = f"工具调用{status}: {tool_name}"
            if error:
                content += f" | 错误: {error}"
                
        end_event = ToolCallEndEvent(
            timestamp=datetime.now(),
            content=content,
            level=level
        )
        self.add_event(end_event)
        
    def add_node_switch(self, from_node: str, to_node: str) -> None:
        """添加节点切换事件
        
        Args:
            from_node: 源节点
            to_node: 目标节点
        """
        event = NodeSwitchEvent(
            timestamp=datetime.now(),
            content=f"节点切换: {from_node} → {to_node}"
        )
        self.add_event(event)
        
    def add_trigger_event(self, trigger_name: str, details: str = "") -> None:
        """添加触发器事件
        
        Args:
            trigger_name: 触发器名称
            details: 详细信息
        """
        content = f"触发器: {trigger_name}"
        if details:
            content += f" | {details}"
            
        event = TriggerEvent(
            timestamp=datetime.now(),
            content=content
        )
        self.add_event(event)
        
    def add_workflow_event(self, workflow_name: str, action: str, details: str = "") -> None:
        """添加工作流事件
        
        Args:
            workflow_name: 工作流名称
            action: 动作
            details: 详细信息
        """
        content = f"工作流[{workflow_name}]: {action}"
        if details:
            content += f" | {details}"
            
        event = WorkflowEvent(
            timestamp=datetime.now(),
            content=content
        )
        self.add_event(event)
        
    def start_stream(self) -> None:
        """开始流式输出"""
        self.stream_manager.start_stream()
        
    def add_stream_content(self, content: str) -> None:
        """添加流式内容
        
        Args:
            content: 内容
        """
        self.stream_manager.add_content(content)
        
    def end_stream(self) -> None:
        """结束流式输出"""
        self.stream_manager.end_stream()
        
    def clear_events(self) -> None:
        """清空所有事件"""
        self.events = []
        self.stream_manager.clear()
        self.virtual_renderable.update_scroll_manager()
        
    def set_auto_scroll(self, auto_scroll: bool) -> None:
        """设置自动滚动
        
        Args:
            auto_scroll: 是否自动滚动
        """
        self.auto_scroll = auto_scroll
        
    def scroll_up(self) -> None:
        """向上滚动"""
        self.virtual_renderable.scroll_manager.scroll_by(-5)
        self.auto_scroll = False  # 手动滚动时禁用自动滚动
        
    def scroll_down(self) -> None:
        """向下滚动"""
        self.virtual_renderable.scroll_manager.scroll_by(5)
        self.auto_scroll = False  # 手动滚动时禁用自动滚动
        
    def scroll_to_end(self) -> None:
        """滚动到末尾"""
        self.virtual_renderable.scroll_to_end()
        self.auto_scroll = True  # 滚动到末尾时启用自动滚动
        
    def render(self) -> Panel:
        """渲染统一时间线
        
        Returns:
            Panel: 时间线面板
        """
        if not self.events:
            content = Text("暂无事件", style="dim")
            return Panel(content, title="📋 执行时间线", border_style="white")
            
        # 创建滚动提示
        scroll_info = Text()
        if self.virtual_renderable.scroll_manager.can_scroll_up():
            scroll_info.append("↑ ", style="dim")
        if self.virtual_renderable.scroll_manager.can_scroll_down():
            scroll_info.append("↓ ", style="dim")
        scroll_info.append(f"事件: {len(self.events)}/{self.max_events}", style="dim")
        
        return Panel(
            self.virtual_renderable,
            title=f"📋 执行时间线 {scroll_info}",
            border_style="white"
        )