"""统一主内容区组件

使用统一时间线显示所有事件，支持虚拟滚动和分段输出
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Console, ConsoleOptions, RenderResult

from ....interfaces.state.workflow import IWorkflowState as WorkflowState
from src.presentation.tui.config import TUIConfig
from .unified_timeline import (
    UnifiedTimelineComponent,
    UserMessageEvent,
    AssistantMessageEvent,
    SystemMessageEvent,
    ToolCallStartEvent,
    ToolCallEndEvent,
    NodeSwitchEvent,
    TriggerEvent,
    WorkflowEvent
)


class ToolResult:
    """工具结果类（兼容性）"""
    
    def __init__(self, tool_name: str, success: bool, result: Any = None, error: Optional[str] = None):
        """初始化工具结果
        
        Args:
            tool_name: 工具名称
            success: 是否成功
            result: 结果
            error: 错误信息
        """
        self.tool_name = tool_name
        self.success = success
        self.result = result
        self.error = error


class UnifiedMainContentComponent:
    """统一主内容区组件
    
    使用统一时间线显示所有事件，替代原有的分割显示模式
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化统一主内容区组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        
        # 初始化统一时间线组件
        self.timeline = UnifiedTimelineComponent(max_events=1000)
        
        # 显示模式（保持兼容性）
        self.display_mode = "unified"  # unified, split, tabs, single
        self.active_tab = "timeline"  # timeline, history, stream, tools
        
        # 统计信息
        self.stats = {
            "total_events": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "tool_calls": 0,
            "system_messages": 0,
            "errors": 0
        }
        
    def update_from_state(self, state: Optional[WorkflowState] = None) -> None:
        """从工作流状态更新组件
        
        Args:
            state: Agent状态
        """
        if state:
            # 添加消息到时间线
            messages = state.get('messages', [])
            for msg in messages:
                self._add_message_from_state(msg)
                
            # 添加工具结果到时间线
            tool_results = state.get('tool_results', [])
            for result in tool_results:
                self._add_tool_result_from_state(result)
                
    def _add_message_from_state(self, msg: Any) -> None:
        """从状态添加消息
        
        Args:
            msg: 消息对象
        """
        # 确定消息类型
        msg_type = "user"
        if hasattr(msg, 'type'):
            msg_type_value = getattr(msg, 'type', None)
            if msg_type_value:
                if msg_type_value == "human":
                    msg_type = "user"
                elif msg_type_value == "system":
                    msg_type = "system"
                elif msg_type_value == "ai":
                    msg_type = "assistant"
                else:
                    msg_type = msg_type_value
        elif hasattr(msg, '__class__'):
            class_name = msg.__class__.__name__
            if "Human" in class_name:
                msg_type = "user"
            elif "System" in class_name:
                msg_type = "system"
            elif "AI" in class_name or "Assistant" in class_name:
                msg_type = "assistant"
        
        # 获取消息内容
        content = getattr(msg, 'content', str(msg))
        
        # 添加到时间线
        if msg_type == "user":
            self.add_user_message(content)
        elif msg_type == "assistant":
            self.add_assistant_message(content)
        elif msg_type == "system":
            self.add_system_message(content)
            
    def _add_tool_result_from_state(self, result: Any) -> None:
        """从状态添加工具结果
        
        Args:
            result: 工具结果
        """
        if hasattr(result, 'tool_name'):
            tool_name = result.tool_name
            success = getattr(result, 'success', True)
            result_data = getattr(result, 'result', None)
            error = getattr(result, 'error', None)
            
            self.add_tool_call(tool_name, success, result_data, error)
            
    def add_user_message(self, content: str) -> None:
        """添加用户消息
        
        Args:
            content: 消息内容
        """
        self.timeline.add_user_message(content)
        self.stats["user_messages"] += 1
        self.stats["total_events"] += 1
        
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息
        
        Args:
            content: 消息内容
        """
        self.timeline.add_assistant_message(content)
        self.stats["assistant_messages"] += 1
        self.stats["total_events"] += 1
        
    def add_system_message(self, content: str, level: str = "info") -> None:
        """添加系统消息
        
        Args:
            content: 消息内容
            level: 消息级别
        """
        self.timeline.add_system_message(content, level)
        self.stats["system_messages"] += 1
        self.stats["total_events"] += 1
        
        if level == "error":
            self.stats["errors"] += 1
            
    def start_stream(self) -> None:
        """开始流式输出"""
        self.timeline.start_stream()
        
    def add_stream_content(self, content: str) -> None:
        """添加流式内容
        
        Args:
            content: 内容
        """
        self.timeline.add_stream_content(content)
        
    def end_stream(self) -> None:
        """结束流式输出"""
        self.timeline.end_stream()
        
    def add_tool_result(self, result: ToolResult) -> None:
        """添加工具结果（兼容性方法）
        
        Args:
            result: 工具结果
        """
        self.add_tool_call(
            result.tool_name,
            result.success,
            result.result,
            result.error
        )
        
    def add_tool_call(self, tool_name: str, success: bool, result: Any = None, error: Optional[str] = None) -> None:
        """添加工具调用
        
        Args:
            tool_name: 工具名称
            success: 是否成功
            result: 结果
            error: 错误信息
        """
        self.timeline.add_tool_call(tool_name, success, result, error)
        self.stats["tool_calls"] += 1
        self.stats["total_events"] += 1
        
        if not success:
            self.stats["errors"] += 1
            
    def add_node_switch(self, from_node: str, to_node: str) -> None:
        """添加节点切换事件
        
        Args:
            from_node: 源节点
            to_node: 目标节点
        """
        self.timeline.add_node_switch(from_node, to_node)
        self.stats["total_events"] += 1
        
    def add_trigger_event(self, trigger_name: str, details: str = "") -> None:
        """添加触发器事件
        
        Args:
            trigger_name: 触发器名称
            details: 详细信息
        """
        self.timeline.add_trigger_event(trigger_name, details)
        self.stats["total_events"] += 1
        
    def add_workflow_event(self, workflow_name: str, action: str, details: str = "") -> None:
        """添加工作流事件
        
        Args:
            workflow_name: 工作流名称
            action: 动作
            details: 详细信息
        """
        self.timeline.add_workflow_event(workflow_name, action, details)
        self.stats["total_events"] += 1
        
    def clear_all(self) -> None:
        """清空所有内容"""
        self.timeline.clear_events()
        self.stats = {
            "total_events": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "tool_calls": 0,
            "system_messages": 0,
            "errors": 0
        }
        
    def scroll_up(self) -> None:
        """向上滚动"""
        self.timeline.scroll_up()
        
    def scroll_down(self) -> None:
        """向下滚动"""
        self.timeline.scroll_down()
        
    def scroll_to_end(self) -> None:
        """滚动到末尾"""
        self.timeline.scroll_to_end()
        
    def set_auto_scroll(self, auto_scroll: bool) -> None:
        """设置自动滚动
        
        Args:
            auto_scroll: 是否自动滚动
        """
        self.timeline.set_auto_scroll(auto_scroll)
        
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息
        
        Returns:
            Dict[str, int]: 统计信息
        """
        return self.stats.copy()
        
    def render(self) -> Panel:
        """渲染主内容区
        
        Returns:
            Panel: 主内容区面板
        """
        if self.display_mode == "unified":
            return self._render_unified_mode()
        elif self.display_mode == "split":
            return self._render_split_mode()
        elif self.display_mode == "tabs":
            return self._render_tabs_mode()
        else:
            return self._render_single_mode()
            
    def _render_unified_mode(self) -> Panel:
        """渲染统一模式
        
        Returns:
            Panel: 统一模式面板
        """
        # 渲染时间线
        timeline_panel = self.timeline.render()
        
        # 添加统计信息到标题
        stats_text = Text()
        stats_text.append(f"事件: {self.stats['total_events']} ", style="dim")
        stats_text.append(f"用户: {self.stats['user_messages']} ", style="blue")
        stats_text.append(f"助手: {self.stats['assistant_messages']} ", style="green")
        stats_text.append(f"工具: {self.stats['tool_calls']} ", style="magenta")
        if self.stats['errors'] > 0:
            stats_text.append(f"错误: {self.stats['errors']} ", style="red")
            
        # 创建新的面板，包含统计信息
        return Panel(
            timeline_panel.renderable,
            title=f"📋 执行时间线 {stats_text}",
            border_style="white"
        )
        
    def _render_split_mode(self) -> Panel:
        """渲染分割模式（兼容性）
        
        Returns:
            Panel: 分割模式面板
        """
        # 在分割模式下，仍然使用统一时间线，但添加说明
        timeline_panel = self.timeline.render()
        
        # 添加模式说明
        content = Table.grid(padding=(0, 1))
        content.add_row(Text("分割模式已统一为时间线显示", style="yellow"))
        content.add_row("")
        content.add_row(timeline_panel.renderable)
        
        return Panel(
            content,
            title="📋 主内容区 (分割模式)",
            border_style="white"
        )
        
    def _render_tabs_mode(self) -> Panel:
        """渲染标签页模式（兼容性）
        
        Returns:
            Panel: 标签页模式面板
        """
        # 在标签页模式下，根据活动标签显示不同内容
        if self.active_tab == "timeline":
            content: Any = self.timeline.render()
            title = "📋 主内容区 (时间线)"
        else:
            # 其他标签页显示说明
            content = Text(f"标签页 '{self.active_tab}' 已统一到时间线显示", style="yellow")
            title = f"📋 主内容区 ({self.active_tab})"
            
        return Panel(
            content,
            title=title,
            border_style="white"
        )
        
    def _render_single_mode(self) -> Panel:
        """渲染单一模式（兼容性）
        
        Returns:
            Panel: 单一模式面板
        """
        # 在单一模式下，仍然使用统一时间线
        return self._render_unified_mode()
        
    def handle_key(self, key: str) -> bool:
        """处理按键事件
        
        Args:
            key: 按键字符串
            
        Returns:
            bool: 是否处理了该按键
        """
        if key == "key_ppage":
            self.scroll_up()
            return True
        elif key == "key_npage":
            self.scroll_down()
            return True
        elif key == "key_home":
            self.timeline.virtual_renderable.scroll_manager.scroll_to(0)
            return True
        elif key == "key_end":
            self.scroll_to_end()
            return True
        elif key == "a":
            # 切换自动滚动
            current_auto = self.timeline.auto_scroll
            self.set_auto_scroll(not current_auto)
            self.add_system_message(
                f"自动滚动: {'开启' if not current_auto else '关闭'}",
                "info"
            )
            return True
            
        return False
        
    def get_help_text(self) -> str:
        """获取帮助文本
        
        Returns:
            str: 帮助文本
        """
        return """
统一时间线快捷键:
  PageUp/PageDown - 上下滚动
  Home/End - 跳到开始/末尾
  A - 切换自动滚动
        """.strip()