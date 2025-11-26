"""主内容区组件

包含会话历史显示、流式输出渲染和工具调用结果展示
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import json

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.columns import Columns
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.spinner import Spinner

from ....interfaces.state.workflow import IWorkflowState as WorkflowState
from typing import Any as ToolResult
from ..config import TUIConfig


class ConversationHistory:
    """会话历史显示组件"""
    
    def __init__(self, max_messages: int = 50):
        """初始化会话历史组件
        
        Args:
            max_messages: 最大消息数量
        """
        self.max_messages = max_messages
        self.messages: List[Dict[str, Any]] = []
        self.show_timestamps = True
        self.show_thinking = False
    
    def add_message(
        self,
        content: str,
        message_type: str = "user",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加消息
        
        Args:
            content: 消息内容
            message_type: 消息类型 (user, assistant, system, tool)
            timestamp: 时间戳
            metadata: 元数据
        """
        message = {
            "content": content,
            "type": message_type,
            "timestamp": timestamp or datetime.now(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        
        # 限制消息数量
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_messages_from_state(self, state: WorkflowState) -> None:
        """从工作流状态添加消息
        
        Args:
            state: Agent状态
        """
        for msg in state.get('messages', []):
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
            
            # 添加到历史
            self.add_message(
                content=content,
                message_type=msg_type,
                metadata={"source": "state"}
            )
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.messages = []
    
    def render(self) -> Panel:
        """渲染会话历史
        
        Returns:
            Panel: 会话历史面板
        """
        if not self.messages:
            content = Text("暂无会话历史", style="dim")
            return Panel(content, title="💬 会话历史", border_style="blue")
        
        # 创建消息列表
        message_content = Table.grid(padding=(0, 1))
        message_content.add_column("时间", style="dim", width=8)
        message_content.add_column("角色", width=8)
        message_content.add_column("内容")
        
        # 渲染每条消息
        for message in self.messages:
            # 时间戳
            if self.show_timestamps:
                time_str = message["timestamp"].strftime("%H:%M:%S")
            else:
                time_str = ""
            
            # 角色和样式
            msg_type = message["type"]
            role_styles = {
                "user": ("👤 用户", "blue"),
                "assistant": ("🤖 助手", "green"),
                "system": ("⚙️ 系统", "yellow"),
                "tool": ("🔧 工具", "magenta")
            }
            role_text, role_style = role_styles.get(msg_type, ("❓ 未知", "white"))
            
            # 消息内容
            content = message["content"]
            if len(content) > 200:  # 限制显示长度
                content = content[:200] + "..."
            
            # 添加到表格
            message_content.add_row(
                time_str,
                Text(role_text, style=role_style),
                Text(content, style=role_style)
            )
        
        return Panel(
            message_content,
            title="💬 会话历史",
            border_style="blue"
        )


class StreamOutput:
    """流式输出渲染组件"""
    
    def __init__(self):
        """初始化流式输出组件"""
        self.current_content = ""
        self.is_streaming = False
        self.stream_start_time: Optional[datetime] = None
        self.tokens_per_second = 0.0
        self.total_tokens = 0
        self.show_thinking = False
        self.thinking_content = ""
    
    def start_stream(self) -> None:
        """开始流式输出"""
        self.current_content = ""
        self.is_streaming = True
        self.stream_start_time = datetime.now()
        self.tokens_per_second = 0.0
        self.total_tokens = 0
    
    def add_content(self, content: str) -> None:
        """添加流式内容
        
        Args:
            content: 新内容
        """
        self.current_content += content
        self.total_tokens += len(content.split())  # 简单的token计算
        
        # 计算速度
        if self.stream_start_time:
            duration = (datetime.now() - self.stream_start_time).total_seconds()
            if duration > 0:
                self.tokens_per_second = self.total_tokens / duration
    
    def add_thinking(self, content: str) -> None:
        """添加思考内容
        
        Args:
            content: 思考内容
        """
        self.thinking_content += content
    
    def end_stream(self) -> None:
        """结束流式输出"""
        self.is_streaming = False
    
    def clear(self) -> None:
        """清空内容"""
        self.current_content = ""
        self.thinking_content = ""
        self.is_streaming = False
        self.stream_start_time = None
        self.tokens_per_second = 0.0
        self.total_tokens = 0
    
    def render(self) -> Panel:
        """渲染流式输出
        
        Returns:
            Panel: 流式输出面板
        """
        if not self.current_content and not self.thinking_content:
            content = Text("等待输出...", style="dim")
            return Panel(content, title="📝 流式输出", border_style="green")
        
        # 创建内容表格
        content_table = Table.grid(padding=(0, 1))
        
        # 添加思考内容（如果有）
        if self.show_thinking and self.thinking_content:
            thinking_text = Text()
            thinking_text.append("🤔 思考过程:\n", style="bold cyan")
            thinking_text.append(self.thinking_content, style="cyan")
            content_table.add_row(thinking_text)
            content_table.add_row("")
        
        # 添加主要内容
        main_content = Text(self.current_content)
        
        # 如果正在流式输出，添加光标
        if self.is_streaming:
            main_content.append("|", style="bold green")
        
        content_table.add_row(main_content)
        
        # 添加统计信息
        if self.is_streaming or self.total_tokens > 0:
            stats_text = Text()
            stats_text.append(f"Tokens: {self.total_tokens}", style="dim")
            if self.is_streaming and self.tokens_per_second > 0:
                stats_text.append(f" | 速度: {self.tokens_per_second:.1f} tokens/s", style="dim")
            
            content_table.add_row("")
            content_table.add_row(stats_text)
        
        # 添加加载动画（如果正在流式输出）
        if self.is_streaming:
            spinner = Spinner("dots", text="生成中...")
            content_table.add_row("")
            content_table.add_row(spinner)
        
        return Panel(
            content_table,
            title="📝 流式输出",
            border_style="green"
        )


class ToolResults:
    """工具调用结果展示组件"""
    
    def __init__(self, max_results: int = 10):
        """初始化工具结果组件
        
        Args:
            max_results: 最大结果数量
        """
        self.max_results = max_results
        self.tool_results: List[ToolResult] = []
        self.show_details = True
        self.show_json = False
    
    def add_tool_result(self, result: ToolResult) -> None:
        """添加工具结果
        
        Args:
            result: 工具结果
        """
        self.tool_results.append(result)
        
        # 限制结果数量
        if len(self.tool_results) > self.max_results:
            self.tool_results = self.tool_results[-self.max_results:]
    
    def add_results_from_state(self, state: WorkflowState) -> None:
        """从工作流状态添加工具结果
        
        Args:
            state: Agent状态
        """
        for result in state.get('tool_results', []):
            self.add_tool_result(result)
    
    def clear_results(self) -> None:
        """清空结果"""
        self.tool_results = []
    
    def render(self) -> Panel:
        """渲染工具调用结果
        
        Returns:
            Panel: 工具调用结果面板
        """
        if not self.tool_results:
            content = Text("暂无工具调用结果", style="dim")
            return Panel(content, title="🔧 工具调用结果", border_style="magenta")
        
        # 创建结果列表
        results_content = Table.grid(padding=(0, 1))
        
        # 渲染每个工具结果
        for result in self.tool_results:
            # 工具名称和状态
            status_icon = "✅" if result.success else "❌"
            status_style = "green" if result.success else "red"
            
            tool_name_text = Text()
            tool_name_text.append(f"{status_icon} {result.tool_name}", style=f"bold {status_style}")
            
            results_content.add_row(tool_name_text)
            
            # 结果内容
            if result.success and result.result is not None:
                result_content = self._format_result_content(result.result)
                results_content.add_row(result_content)
            elif not result.success and result.error:
                error_text = Text(f"错误: {result.error}", style="red")
                results_content.add_row(error_text)
            
            # 添加分隔线
            results_content.add_row("")
        
        return Panel(
            results_content,
            title="🔧 工具调用结果",
            border_style="magenta"
        )
    
    def _format_result_content(self, result: Any) -> Union[Text, Table, Syntax]:
        """格式化结果内容
        
        Args:
            result: 结果内容
            
        Returns:
            Union[Text, Table, Syntax]: 格式化后的内容
        """
        # 如果是字符串
        if isinstance(result, str):
            # 尝试解析为JSON
            try:
                json_data = json.loads(result)
                formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                return Syntax(formatted_json, "json", theme="monokai", line_numbers=False)
            except (json.JSONDecodeError, TypeError):
                # 如果不是JSON，检查是否是代码
                if any(result.strip().startswith(prefix) for prefix in ["```", "def ", "class ", "import ", "from "]):
                    # 简单的代码检测
                    return Syntax(result, "python", theme="monokai", line_numbers=False)
                else:
                    # 普通文本
                    if len(result) > 300:
                        result = result[:300] + "..."
                    return Text(result, style="dim")
        
        # 如果是字典或列表
        elif isinstance(result, (dict, list)):
            try:
                formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
                if len(formatted_json) > 500:
                    formatted_json = formatted_json[:500] + "..."
                return Syntax(formatted_json, "json", theme="monokai", line_numbers=False)
            except (TypeError, ValueError):
                return Text(str(result), style="dim")
        
        # 其他类型
        else:
            result_str = str(result)
            if len(result_str) > 300:
                result_str = result_str[:300] + "..."
            return Text(result_str, style="dim")


class MainContentComponent:
    """主内容区组件
    
    包含会话历史显示、流式输出渲染和工具调用结果展示
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化主内容区组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.conversation_history = ConversationHistory()
        self.stream_output = StreamOutput()
        self.tool_results = ToolResults()
        
        # 显示模式
        self.display_mode = "split"  # split, tabs, single
        self.active_tab = "history"  # history, stream, tools
    
    def update_from_state(self, state: Optional[WorkflowState] = None) -> None:
        """从工作流状态更新组件
        
        Args:
            state: Agent状态
        """
        if state:
            # 更新会话历史
            self.conversation_history.add_messages_from_state(state)
            
            # 更新工具结果
            self.tool_results.add_results_from_state(state)
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息
        
        Args:
            content: 消息内容
        """
        self.conversation_history.add_message(content, "user")
    
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息
        
        Args:
            content: 消息内容
        """
        self.conversation_history.add_message(content, "assistant")
    
    def start_stream(self) -> None:
        """开始流式输出"""
        self.stream_output.start_stream()
    
    def add_stream_content(self, content: str) -> None:
        """添加流式内容
        
        Args:
            content: 内容
        """
        self.stream_output.add_content(content)
    
    def end_stream(self) -> None:
        """结束流式输出"""
        self.stream_output.end_stream()
    
    def add_tool_result(self, result: ToolResult) -> None:
        """添加工具结果
        
        Args:
            result: 工具结果
        """
        self.tool_results.add_tool_result(result)
    
    def clear_all(self) -> None:
        """清空所有内容"""
        self.conversation_history.clear_history()
        self.stream_output.clear()
        self.tool_results.clear_results()
    
    def render(self) -> Panel:
        """渲染主内容区
        
        Returns:
            Panel: 主内容区面板
        """
        if self.display_mode == "split":
            return self._render_split_mode()
        elif self.display_mode == "tabs":
            return self._render_tabs_mode()
        else:
            return self._render_single_mode()
    
    def _render_split_mode(self) -> Panel:
        """渲染分割模式
        
        Returns:
            Panel: 分割模式面板
        """
        # 创建三列布局
        history_panel = self.conversation_history.render()
        stream_panel = self.stream_output.render()
        tools_panel = self.tool_results.render()
        
        # 使用Columns创建水平布局
        columns = Columns([
            history_panel,
            stream_panel,
            tools_panel
        ], equal=True)
        
        return Panel(
            columns,
            title="📋 主内容区",
            border_style="white"
        )
    
    def _render_tabs_mode(self) -> Panel:
        """渲染标签页模式
        
        Returns:
            Panel: 标签页模式面板
        """
        # 根据活动标签显示不同内容
        if self.active_tab == "history":
            content = self.conversation_history.render()
        elif self.active_tab == "stream":
            content = self.stream_output.render()
        else:  # tools
            content = self.tool_results.render()
        
        return Panel(
            content,
            title=f"📋 主内容区 ({self.active_tab})",
            border_style="white"
        )
    
    def _render_single_mode(self) -> Panel:
        """渲染单一模式
        
        Returns:
            Panel: 单一模式面板
        """
        # 只显示流式输出
        content = self.stream_output.render()
        
        return Panel(
            content,
            title="📋 主内容区",
            border_style="white"
        )