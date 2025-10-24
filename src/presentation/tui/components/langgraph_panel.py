"""LangGraph状态面板组件

包含当前节点显示、执行路径追踪和状态快照查看
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, ConsoleOptions, RenderResult

from src.domain.prompts.agent_state import AgentState
from ..config import TUIConfig


class CurrentNodeDisplay:
    """当前节点显示组件"""
    
    def __init__(self):
        self.current_node = "未运行"
        self.node_status = "idle"
        self.node_start_time: Optional[datetime] = None
        self.node_duration = 0.0
        self.node_metadata: Dict[str, Any] = {}
    
    def update_current_node(
        self,
        node_name: str,
        status: str = "running",
        start_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """更新当前节点信息
        
        Args:
            node_name: 节点名称
            status: 节点状态
            start_time: 节点开始时间
            metadata: 节点元数据
        """
        self.current_node = node_name
        self.node_status = status
        self.node_start_time = start_time or datetime.now()
        self.node_metadata = metadata or {}
        
        # 计算节点运行时间
        if self.node_start_time:
            self.node_duration = (datetime.now() - self.node_start_time).total_seconds()
    
    def render(self) -> Panel:
        """渲染当前节点显示
        
        Returns:
            Panel: 当前节点面板
        """
        # 创建节点状态文本
        status_text = Text()
        status_text.append("当前节点: ", style="bold")
        
        # 根据状态设置样式
        status_styles = {
            "idle": "dim",
            "running": "green",
            "completed": "blue",
            "error": "red",
            "paused": "yellow"
        }
        node_style = status_styles.get(self.node_status, "white")
        status_text.append(self.current_node, style=f"bold {node_style}")
        
        # 添加状态指示器
        status_indicators = {
            "idle": "⏸️",
            "running": "▶️",
            "completed": "✅",
            "error": "❌",
            "paused": "⏸️"
        }
        indicator = status_indicators.get(self.node_status, "❓")
        status_text.append(f" {indicator}")
        
        # 添加运行时间
        if self.node_status == "running" and self.node_duration > 0:
            status_text.append(f" ({self.node_duration:.1f}s)", style="dim")
        
        # 创建进度条（仅在运行时显示）
        progress_content = None
        if self.node_status == "running":
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            )
            progress.add_task(f"执行 {self.current_node}...", total=None)
            progress_content = progress
        
        # 组合内容
        if progress_content:
            content = Columns([status_text, progress_content], equal=False)
        else:
            content = status_text
        
        # 添加元数据信息
        if self.node_metadata:
            metadata_text = Text()
            for key, value in self.node_metadata.items():
                metadata_text.append(f"{key}: {value}\n", style="dim")
            
            if progress_content:
                full_content = Table.grid()
                full_content.add_row(content)
                full_content.add_row("")
                full_content.add_row(metadata_text)
                content = full_content
            else:
                content = Table.grid()
                content.add_row(status_text)
                content.add_row("")
                content.add_row(metadata_text)
        
        return Panel(
            content,
            title="🎯 当前节点",
            border_style="cyan"
        )


class ExecutionPathTracker:
    """执行路径追踪组件"""
    
    def __init__(self):
        self.execution_path: List[Dict[str, Any]] = []
        self.max_path_length = 20
    
    def add_node_execution(
        self,
        node_name: str,
        status: str = "completed",
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加节点执行记录
        
        Args:
            node_name: 节点名称
            status: 执行状态
            duration: 执行时长
            metadata: 元数据
        """
        execution_record = {
            "node_name": node_name,
            "status": status,
            "duration": duration,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self.execution_path.append(execution_record)
        
        # 限制路径长度
        if len(self.execution_path) > self.max_path_length:
            self.execution_path = self.execution_path[-self.max_path_length:]
    
    def render(self) -> Panel:
        """渲染执行路径
        
        Returns:
            Panel: 执行路径面板
        """
        if not self.execution_path:
            content = Text("无执行历史", style="dim")
            return Panel(content, title="🛤️ 执行路径", border_style="yellow")
        
        # 创建路径树
        path_tree = Tree("执行历史", style="bold")
        
        # 显示最近的执行记录
        recent_path = self.execution_path[-10:]  # 显示最近10个
        for i, record in enumerate(recent_path):
            node_name = record["node_name"]
            status = record["status"]
            duration = record["duration"]
            
            # 状态图标
            status_icons = {
                "completed": "✅",
                "error": "❌",
                "running": "🔄",
                "skipped": "⏭️"
            }
            icon = status_icons.get(status, "❓")
            
            # 节点文本
            node_text = f"{icon} {node_name}"
            if duration > 0:
                node_text += f" ({duration:.2f}s)"
            
            # 根据状态设置样式
            status_styles = {
                "completed": "green",
                "error": "red",
                "running": "yellow",
                "skipped": "dim"
            }
            node_style = status_styles.get(status, "white")
            
            # 添加到树
            if i == len(recent_path) - 1:  # 最后一个节点（当前）
                path_tree.add(node_text, style=f"bold {node_style}")
            else:
                path_tree.add(node_text, style=node_style)
        
        # 添加统计信息
        if len(self.execution_path) > 0:
            stats_text = Text()
            completed_count = sum(1 for r in self.execution_path if r["status"] == "completed")
            error_count = sum(1 for r in self.execution_path if r["status"] == "error")
            total_duration = sum(r["duration"] for r in self.execution_path)
            
            stats_text.append(f"总计: {len(self.execution_path)} | ", style="dim")
            stats_text.append(f"完成: {completed_count} | ", style="green")
            stats_text.append(f"错误: {error_count} | ", style="red")
            stats_text.append(f"总时长: {total_duration:.2f}s", style="dim")
            
            path_tree.add("")
            path_tree.add(stats_text)
        
        return Panel(
            path_tree,
            title="🛤️ 执行路径",
            border_style="yellow"
        )


class StateSnapshotViewer:
    """状态快照查看组件"""
    
    def __init__(self):
        self.state_snapshots: List[Dict[str, Any]] = []
        self.current_snapshot: Optional[Dict[str, Any]] = None
        self.max_snapshots = 5
    
    def capture_snapshot(
        self,
        state: AgentState,
        node_name: str = "unknown",
        description: str = ""
    ) -> None:
        """捕获状态快照
        
        Args:
            state: Agent状态
            node_name: 节点名称
            description: 描述
        """
        snapshot = {
            "timestamp": datetime.now(),
            "node_name": node_name,
            "description": description,
            "message_count": len(state.messages),
            "tool_results_count": len(state.tool_results),
            "current_step": getattr(state, 'current_step', ''),
            "iteration_count": getattr(state, 'iteration_count', 0),
            "max_iterations": getattr(state, 'max_iterations', 10)
        }
        
        self.state_snapshots.append(snapshot)
        self.current_snapshot = snapshot
        
        # 限制快照数量
        if len(self.state_snapshots) > self.max_snapshots:
            self.state_snapshots = self.state_snapshots[-self.max_snapshots:]
    
    def render(self) -> Panel:
        """渲染状态快照
        
        Returns:
            Panel: 状态快照面板
        """
        if not self.current_snapshot:
            content = Text("无状态快照", style="dim")
            return Panel(content, title="📸 状态快照", border_style="magenta")
        
        # 创建快照表格
        snapshot_table = Table.grid(padding=(0, 1))
        snapshot_table.add_column("属性", style="bold cyan")
        snapshot_table.add_column("值")
        
        # 添加快照信息
        snapshot = self.current_snapshot
        snapshot_table.add_row("时间", snapshot["timestamp"].strftime("%H:%M:%S"))
        snapshot_table.add_row("节点", snapshot["node_name"])
        if snapshot["description"]:
            snapshot_table.add_row("描述", snapshot["description"])
        snapshot_table.add_row("消息数", str(snapshot["message_count"]))
        snapshot_table.add_row("工具结果", str(snapshot["tool_results_count"]))
        snapshot_table.add_row("当前步骤", snapshot["current_step"])
        
        # 添加迭代进度
        iteration_text = f"{snapshot['iteration_count']}/{snapshot['max_iterations']}"
        snapshot_table.add_row("迭代进度", iteration_text)
        
        # 添加进度条
        progress = Progress(
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        progress.add_task(
            "",
            completed=snapshot["iteration_count"],
            total=snapshot["max_iterations"]
        )
        
        # 组合内容
        content = Table.grid()
        content.add_row(snapshot_table)
        content.add_row("")
        content.add_row(progress)
        
        # 如果有多个快照，添加快照历史
        if len(self.state_snapshots) > 1:
            content.add_row("")
            history_text = Text("快照历史: ", style="bold")
            for i, snap in enumerate(self.state_snapshots[-3:]):  # 显示最近3个
                time_str = snap["timestamp"].strftime("%H:%M:%S")
                node_name = snap["node_name"]
                history_text.append(f"{time_str}@{node_name}", style="dim")
                if i < min(2, len(self.state_snapshots) - 1):
                    history_text.append(" → ", style="dim")
            content.add_row(history_text)
        
        return Panel(
            content,
            title="📸 状态快照",
            border_style="magenta"
        )


class LangGraphPanelComponent:
    """LangGraph状态面板组件
    
    包含当前节点显示、执行路径追踪和状态快照查看
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化LangGraph状态面板组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.current_node_display = CurrentNodeDisplay()
        self.execution_path_tracker = ExecutionPathTracker()
        self.state_snapshot_viewer = StateSnapshotViewer()
        
        # Studio集成信息
        self.studio_server_running = False
        self.studio_server_port = 8079
        self.studio_server_url = ""
    
    def update_from_state(
        self,
        state: Optional[AgentState] = None,
        current_node: str = "未运行",
        node_status: str = "idle"
    ) -> None:
        """从Agent状态更新组件
        
        Args:
            state: Agent状态
            current_node: 当前节点名称
            node_status: 节点状态
        """
        # 更新当前节点
        self.current_node_display.update_current_node(
            node_name=current_node,
            status=node_status,
            metadata={
                "消息数": len(state.messages) if state else 0,
                "工具调用": len(state.tool_results) if state else 0,
                "迭代": f"{getattr(state, 'iteration_count', 0)}/{getattr(state, 'max_iterations', 10)}" if state else "0/10"
            }
        )
        
        # 捕获状态快照
        if state:
            self.state_snapshot_viewer.capture_snapshot(
                state=state,
                node_name=current_node,
                description=f"节点状态: {node_status}"
            )
        
        # 更新执行路径（如果节点状态变化）
        if node_status in ["completed", "error"]:
            self.execution_path_tracker.add_node_execution(
                node_name=current_node,
                status=node_status,
                duration=self.current_node_display.node_duration
            )
    
    def set_studio_status(self, running: bool, port: int = 8079) -> None:
        """设置Studio服务器状态
        
        Args:
            running: 是否运行中
            port: 端口号
        """
        self.studio_server_running = running
        self.studio_server_port = port
        self.studio_server_url = f"http://localhost:{port}" if running else ""
    
    def render(self) -> Panel:
        """渲染LangGraph状态面板
        
        Returns:
            Panel: LangGraph状态面板
        """
        # 创建子组件
        current_node_panel = self.current_node_display.render()
        execution_path_panel = self.execution_path_tracker.render()
        state_snapshot_panel = self.state_snapshot_viewer.render()
        
        # 创建Studio链接信息
        studio_info = self._render_studio_info()
        
        # 组合所有内容
        content = Table.grid(padding=1)
        content.add_row(current_node_panel)
        content.add_row(execution_path_panel)
        content.add_row(state_snapshot_panel)
        content.add_row(studio_info)
        
        return Panel(
            content,
            title="🔄 LangGraph状态",
            border_style="blue" if self.config else "blue"
        )
    
    def _render_studio_info(self) -> Panel:
        """渲染Studio信息
        
        Returns:
            Panel: Studio信息面板
        """
        if self.studio_server_running:
            studio_text = Text()
            studio_text.append("Studio: ", style="bold")
            studio_text.append(self.studio_server_url, style="underline blue")
            studio_text.append(" ↩", style="bold green")
            
            return Panel(
                studio_text,
                title="🌐 Studio集成",
                border_style="green"
            )
        else:
            studio_text = Text("Studio服务器未启动", style="dim")
            return Panel(
                studio_text,
                title="🌐 Studio集成",
                border_style="dim"
            )