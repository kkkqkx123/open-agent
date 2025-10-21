"""精简侧边栏组件

包含Agent基本信息、当前状态和核心指标
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align

from src.prompts.agent_state import AgentState
from ..config import TUIConfig


class AgentInfo:
    """Agent信息类"""
    
    def __init__(self):
        self.name = "默认Agent"
        self.model = "gpt-3.5-turbo"
        self.status = "就绪"
        self.tools = []
    
    def update_agent_info(self, name: str, model: str, tools: Optional[List[str]] = None, status: str = "就绪") -> None:
        """更新Agent信息
        
        Args:
            name: Agent名称
            model: 模型名称
            tools: 工具列表
            status: Agent状态
        """
        self.name = name
        self.model = model
        self.status = status
        if tools is not None:
            self.tools = tools
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return getattr(self, key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典式设置"""
        setattr(self, key, value)




class SidebarComponent:
    """精简侧边栏组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化精简侧边栏组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        
        # Agent基本信息
        self.agent_info = AgentInfo()
        
        # 工作流状态
        self.workflow_status = {
            "name": "未加载",
            "state": "停止",
            "progress": 0
        }
        
        # 核心指标
        self.core_metrics = {
            "messages": 0,
            "tokens": 0,
            "cost": 0.0,
            "duration": "0:00"
        }
    
    def update_from_state(self, state: Optional[AgentState]) -> None:
        """从Agent状态更新组件
        
        Args:
            state: Agent状态
        """
        if not state:
            return
        
        # 更新工作流状态
        if hasattr(state, 'workflow_name'):
            self.workflow_status["name"] = state.workflow_name
        
        if hasattr(state, 'iteration_count') and hasattr(state, 'max_iterations'):
            current = state.iteration_count
            maximum = state.max_iterations
            if maximum > 0:
                self.workflow_status["progress"] = int((current / maximum) * 100)
            
            if current >= maximum:
                self.workflow_status["state"] = "完成"
            elif current > 0:
                self.workflow_status["state"] = "运行中"
        
        # 更新核心指标
        if hasattr(state, 'messages'):
            self.core_metrics["messages"] = len(state.messages)
        
        # 计算运行时间
        if hasattr(state, 'start_time'):
            start_time = state.start_time
            if start_time:
                duration = datetime.now() - start_time
                minutes, seconds = divmod(duration.seconds, 60)
                self.core_metrics["duration"] = f"{minutes}:{seconds:02d}"
    
    def update_agent_info(self, name: str, model: str, status: str = "就绪") -> None:
        """更新Agent信息
        
        Args:
            name: Agent名称
            model: 模型名称
            status: Agent状态
        """
        self.agent_info["name"] = name
        self.agent_info["model"] = model
        self.agent_info["status"] = status
    
    def update_workflow_status(self, name: str, state: str, progress: int = 0) -> None:
        """更新工作流状态
        
        Args:
            name: 工作流名称
            state: 工作流状态
            progress: 进度百分比
        """
        self.workflow_status["name"] = name
        self.workflow_status["state"] = state
        self.workflow_status["progress"] = progress
    
    def update_core_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新核心指标
        
        Args:
            metrics: 指标数据
        """
        self.core_metrics.update(metrics)
    
    def render(self) -> Panel:
        """渲染精简侧边栏
        
        Returns:
            Panel: 侧边栏面板
        """
        # 创建主要内容
        content = self._create_content()
        
        return Panel(
            content,
            title="📊 状态概览",
            border_style="green"
        )
    
    def _create_content(self) -> Table:
        """创建内容表格
        
        Returns:
            Table: 内容表格
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold", width=12)
        table.add_column("值", style="dim")
        
        # Agent基本信息
        table.add_row("", "", style="bold cyan")  # 分隔线
        table.add_row("🤖 Agent", self.agent_info["name"], style="bold cyan")
        table.add_row("模型", self.agent_info["model"])
        table.add_row("状态", self._get_status_text(self.agent_info["status"]))
        
        # 工作流状态
        table.add_row("", "", style="bold yellow")  # 分隔线
        table.add_row("🔄 工作流", self.workflow_status["name"], style="bold yellow")
        table.add_row("状态", self._get_workflow_state_text(self.workflow_status["state"]))
        
        # 进度条
        if self.workflow_status["progress"] > 0:
            progress_bar = self._create_progress_bar(self.workflow_status["progress"])
            table.add_row("进度", progress_bar)
        
        # 核心指标
        table.add_row("", "", style="bold magenta")  # 分隔线
        table.add_row("📈 指标", "", style="bold magenta")
        table.add_row("消息", str(self.core_metrics["messages"]))
        table.add_row("Token", str(self.core_metrics["tokens"]))
        table.add_row("成本", f"${self.core_metrics['cost']:.4f}")
        table.add_row("时长", self.core_metrics["duration"])
        
        return table
    
    def _get_status_text(self, status: str) -> Text:
        """获取状态文本
        
        Args:
            status: 状态
            
        Returns:
            Text: 状态文本
        """
        status_colors = {
            "就绪": "green",
            "运行中": "yellow",
            "忙碌": "orange",
            "错误": "red",
            "离线": "dim"
        }
        
        color = status_colors.get(status, "white")
        return Text(status, style=color)
    
    def _get_workflow_state_text(self, state: str) -> Text:
        """获取工作流状态文本
        
        Args:
            state: 工作流状态
            
        Returns:
            Text: 状态文本
        """
        state_colors = {
            "停止": "dim",
            "运行中": "yellow",
            "完成": "green",
            "错误": "red",
            "暂停": "orange"
        }
        
        state_icons = {
            "停止": "⏹️",
            "运行中": "▶️",
            "完成": "✅",
            "错误": "❌",
            "暂停": "⏸️"
        }
        
        color = state_colors.get(state, "white")
        icon = state_icons.get(state, "❓")
        
        return Text(f"{icon} {state}", style=color)
    
    def _create_progress_bar(self, progress: int) -> str:
        """创建进度条
        
        Args:
            progress: 进度百分比
            
        Returns:
            str: 进度条字符串
        """
        bar_length = 10
        filled_length = int(bar_length * progress / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        return f"[green]{bar}[/green] {progress}%"