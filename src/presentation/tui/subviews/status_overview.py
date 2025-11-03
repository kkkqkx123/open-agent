"""状态概览子界面"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich.console import Group

from .base import BaseSubview
from ..config import TUIConfig


class StatusOverviewSubview(BaseSubview):
    """状态概览子界面
    
    包含会话信息、Agent信息、工作流状态、核心指标等四栏信息布局
    """
    
    def __init__(self, config: TUIConfig):
        """初始化状态概览子界面
        
        Args:
            config: TUI配置
        """
        super().__init__(config)
        
        # 会话信息
        self.session_info = {
            "session_id": "",
            "workflow_name": "",
            "status": "未连接",
            "created_time": None,
            "message_count": 0,
            "token_count": 0
        }
        
        # Agent信息
        self.agent_info = {
            "name": "",
            "model": "",
            "status": "未运行",
            "tool_count": 0,
            "current_task": ""
        }
        
        # 工作流状态
        self.workflow_status = {
            "name": "",
            "status": "未启动",
            "progress": 0.0,
            "iteration_count": 0,
            "max_iterations": 10
        }
        
        # 核心指标
        self.core_metrics = {
            "message_count": 0,
            "token_count": 0,
            "cost_estimate": 0.0,
            "runtime": 0.0,
            "success_rate": 100.0,
            "error_count": 0
        }
        
        # 实时性能监控
        self.performance_monitoring = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "response_time": 0.0,
            "error_rate": 0.0,
            "network_io": 0.0,
            "disk_usage": 0.0
        }
    
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        return "📋 状态概览"
    
    def render(self) -> Panel:
        """渲染状态概览子界面
        
        Returns:
            Panel: 子界面面板
        """
        # 创建主要内容
        content = self._create_main_content()
        
        # 创建面板
        panel = Panel(
            content,
            title=self.create_header(),
            border_style="blue",
            subtitle=self.create_help_text()
        )
        
        return panel
    
    def _create_main_content(self) -> Group:
        """创建主要内容区域
        
        Returns:
            Columns: 列布局
        """
        # 会话信息面板
        session_panel = self._create_session_panel()
        
        # Agent信息面板
        agent_panel = self._create_agent_panel()
        
        # 工作流状态面板
        workflow_panel = self._create_workflow_panel()
        
        # 核心指标面板
        metrics_panel = self._create_metrics_panel()
        
        # 性能监控面板
        performance_panel = self._create_performance_panel()
        
        # 组合布局 - 四栏信息布局
        info_columns = Columns([
            session_panel,
            agent_panel,
            workflow_panel,
            metrics_panel
        ], equal=True, expand=True)
        
        # 组合整体布局
        return Group(info_columns, performance_panel)
    
    def _create_session_panel(self) -> Panel:
        """创建会话信息面板
        
        Returns:
            Panel: 会话信息面板
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        info = self.session_info
        
        # 会话ID
        session_id = info["session_id"]
        if session_id:
            table.add_row("会话ID", session_id[:8] + "..." if len(session_id) > 8 else session_id)
        else:
            table.add_row("会话ID", "未连接")
        
        # 工作流名称
        workflow_name = info["workflow_name"]
        table.add_row("工作流", workflow_name if workflow_name else "未指定")
        
        # 状态
        status = info["status"]
        status_style = self._get_status_style(status)
        table.add_row("状态", f"[{status_style}]{status}[/{status_style}]")
        
        # 创建时间
        created_time = info["created_time"]
        if created_time:
            table.add_row("创建时间", created_time.strftime("%H:%M:%S"))
        else:
            table.add_row("创建时间", "-")
        
        # 消息数
        table.add_row("消息数", str(info["message_count"]))
        
        # Token数
        table.add_row("Token数", f"{info['token_count']:,}")
        
        return Panel(
            table,
            title="💾 会话信息",
            border_style="green"
        )
    
    def _create_agent_panel(self) -> Panel:
        """创建Agent信息面板
        
        Returns:
            Panel: Agent信息面板
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        info = self.agent_info
        
        # 名称
        name = info["name"]
        table.add_row("名称", name if name else "未指定")
        
        # 模型
        model = info["model"]
        table.add_row("模型", model if model else "未指定")
        
        # 状态
        status = info["status"]
        status_style = self._get_status_style(status)
        table.add_row("状态", f"[{status_style}]{status}[/{status_style}]")
        
        # 工具数
        table.add_row("工具数", str(info["tool_count"]))
        
        # 当前任务
        current_task = info["current_task"]
        if current_task:
            table.add_row("当前任务", current_task[:20] + "..." if len(current_task) > 20 else current_task)
        else:
            table.add_row("当前任务", "-")
        
        return Panel(
            table,
            title="🤖 Agent信息",
            border_style="cyan"
        )
    
    def _create_workflow_panel(self) -> Panel:
        """创建工作流状态面板
        
        Returns:
            Panel: 工作流状态面板
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        status = self.workflow_status
        
        # 名称
        name = status["name"]
        table.add_row("名称", name if name else "未指定")
        
        # 状态
        workflow_status = status["status"]
        status_style = self._get_status_style(workflow_status)
        table.add_row("状态", f"[{status_style}]{workflow_status}[/{status_style}]")
        
        # 进度
        progress = status["progress"]
        progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
        table.add_row("进度", f"{progress_bar} {progress:.0%}")
        
        # 迭代次数
        iteration = status["iteration_count"]
        max_iterations = status["max_iterations"]
        table.add_row("迭代次数", f"{iteration}/{max_iterations}")
        
        return Panel(
            table,
            title="🔄 工作流状态",
            border_style="yellow"
        )
    
    def _create_metrics_panel(self) -> Panel:
        """创建核心指标面板
        
        Returns:
            Panel: 核心指标面板
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        metrics = self.core_metrics
        
        # 消息数
        table.add_row("消息数", str(metrics["message_count"]))
        
        # Token数
        table.add_row("Token数", f"{metrics['token_count']:,}")
        
        # 成本估算
        table.add_row("成本", f"${metrics['cost_estimate']:.4f}")
        
        # 运行时长
        runtime = metrics["runtime"]
        table.add_row("运行时长", f"{runtime:.1f}s")
        
        # 成功率
        success_rate = metrics["success_rate"]
        table.add_row("成功率", f"{success_rate:.1f}%")
        
        # 错误数
        table.add_row("错误数", str(metrics["error_count"]))
        
        return Panel(
            table,
            title="📊 核心指标",
            border_style="magenta"
        )
    
    def _create_performance_panel(self) -> Panel:
        """创建实时性能监控面板
        
        Returns:
            Panel: 性能监控面板
        """
        table = Table(title="实时性能监控", show_header=True, header_style="bold cyan")
        table.add_column("指标", style="bold")
        table.add_column("当前值", justify="right")
        table.add_column("进度条", justify="left")
        
        perf = self.performance_monitoring
        
        # CPU使用率
        cpu_usage = perf["cpu_usage"]
        table.add_row(
            "CPU使用率",
            f"{cpu_usage:.1f}%",
            self._create_progress_bar(cpu_usage, 100, "blue")
        )
        
        # 内存使用率
        memory_usage = perf["memory_usage"]
        table.add_row(
            "内存使用",
            f"{memory_usage:.1f}MB",
            self._create_progress_bar(memory_usage, 512, "green")  # 假设512MB为最大值
        )
        
        # 响应时间
        response_time = perf["response_time"]
        table.add_row(
            "响应时间",
            f"{response_time:.0f}ms",
            self._create_progress_bar(response_time, 1000, "yellow")  # 假设1000ms为最大值
        )
        
        # 错误率
        error_rate = perf["error_rate"]
        table.add_row(
            "错误率",
            f"{error_rate:.2f}%",
            self._create_progress_bar(error_rate, 10, "red")  # 假设10%为最大值
        )
        
        # 网络IO
        network_io = perf["network_io"]
        table.add_row(
            "网络IO",
            f"{network_io:.1f}MB/s",
            self._create_progress_bar(network_io, 10, "magenta")  # 假设10MB/s为最大值
        )
        
        # 磁盘使用率
        disk_usage = perf["disk_usage"]
        table.add_row(
            "磁盘使用",
            f"{disk_usage:.1f}%",
            self._create_progress_bar(disk_usage, 100, "white")
        )
        
        return Panel(
            table,
            border_style="dim"
        )
    
    def _create_progress_bar(self, value: float, max_value: float, color: str) -> str:
        """创建进度条
        
        Args:
            value: 当前值
            max_value: 最大值
            color: 颜色
            
        Returns:
            str: 进度条字符串
        """
        if max_value == 0:
            percentage = 0
        else:
            percentage = min(100, max(0, (value / max_value) * 100))
        
        bar_length = 10
        filled_length = int(bar_length * percentage / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        return f"[{color}]{bar}[/{color}] {percentage:.1f}%"
    
    def _get_status_style(self, status: str) -> str:
        """获取状态样式
        
        Args:
            status: 状态
            
        Returns:
            str: 状态样式
        """
        styles = {
            "运行中": "green",
            "已连接": "green",
            "进行中": "yellow",
            "未运行": "red",
            "未连接": "red",
            "未启动": "red",
            "已完成": "green",
            "已失败": "red"
        }
        return styles.get(status, "white")
    
    def update_session_info(self, info: Dict[str, Any]) -> None:
        """更新会话信息
        
        Args:
            info: 会话信息
        """
        self.session_info.update(info)
    
    def update_agent_info(self, info: Dict[str, Any]) -> None:
        """更新Agent信息
        
        Args:
            info: Agent信息
        """
        self.agent_info.update(info)
    
    def update_workflow_status(self, status: Dict[str, Any]) -> None:
        """更新工作流状态
        
        Args:
            status: 工作流状态
        """
        self.workflow_status.update(status)
    
    def update_core_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新核心指标
        
        Args:
            metrics: 核心指标
        """
        self.core_metrics.update(metrics)
    
    def update_performance_monitoring(self, perf: Dict[str, Any]) -> None:
        """更新性能监控数据
        
        Args:
            perf: 性能监控数据
        """
        self.performance_monitoring.update(perf)