"""分析监控子界面"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn
from rich.columns import Columns
from rich.align import Align

from .base import BaseSubview
from ..config import TUIConfig


class AnalyticsSubview(BaseSubview):
    """分析监控子界面
    
    包含性能分析、详细指标统计、执行历史分析
    """
    
    def __init__(self, config: TUIConfig):
        """初始化分析监控子界面
        
        Args:
            config: TUI配置
        """
        super().__init__(config)
        
        # 性能数据
        self.performance_data = {
            "total_requests": 0,
            "avg_response_time": 0.0,
            "success_rate": 100.0,
            "error_count": 0,
            "tokens_used": 0,
            "cost_estimate": 0.0
        }
        
        # 执行历史
        self.execution_history: List[Dict[str, Any]] = []
        
        # 系统指标
        self.system_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_io": 0.0
        }
    
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        return "📊 分析监控"
    
    def render(self) -> Panel:
        """渲染分析监控子界面
        
        Returns:
            Panel: 子界面面板
        """
        # 创建主要内容
        content = self._create_main_content()
        
        # 创建面板
        panel = Panel(
            content,
            title=self.create_header(),
            border_style="green",
            subtitle=self.create_help_text()
        )
        
        return panel
    
    def _create_main_content(self) -> Columns:
        """创建主要内容区域
        
        Returns:
            Columns: 列布局
        """
        # 性能概览
        performance_panel = self._create_performance_panel()
        
        # 系统指标
        metrics_panel = self._create_metrics_panel()
        
        # 执行历史
        history_panel = self._create_history_panel()
        
        # 组合布局
        return Columns([
            performance_panel,
            metrics_panel,
            history_panel
        ], equal=True)
    
    def _create_performance_panel(self) -> Panel:
        """创建性能概览面板
        
        Returns:
            Panel: 性能面板
        """
        table = Table(title="性能概览", show_header=True, header_style="bold cyan")
        table.add_column("指标", style="bold")
        table.add_column("数值", justify="right")
        table.add_column("状态", justify="center")
        
        # 添加性能数据
        data = self.performance_data
        
        # 请求总数
        table.add_row(
            "请求总数",
            str(data["total_requests"]),
            self._get_status_indicator("normal")
        )
        
        # 平均响应时间
        avg_time = data["avg_response_time"]
        table.add_row(
            "平均响应时间",
            f"{avg_time:.2f}ms",
            self._get_response_time_status(avg_time)
        )
        
        # 成功率
        success_rate = data["success_rate"]
        table.add_row(
            "成功率",
            f"{success_rate:.1f}%",
            self._get_success_rate_status(success_rate)
        )
        
        # 错误计数
        table.add_row(
            "错误计数",
            str(data["error_count"]),
            self._get_error_count_status(data["error_count"])
        )
        
        # Token使用量
        table.add_row(
            "Token使用",
            str(data["tokens_used"]),
            self._get_status_indicator("normal")
        )
        
        # 成本估算
        table.add_row(
            "成本估算",
            f"${data['cost_estimate']:.4f}",
            self._get_status_indicator("normal")
        )
        
        return Panel(
            table,
            title="📈 性能概览",
            border_style="blue"
        )
    
    def _create_metrics_panel(self) -> Panel:
        """创建系统指标面板
        
        Returns:
            Panel: 指标面板
        """
        table = Table(title="系统指标", show_header=True, header_style="bold cyan")
        table.add_column("指标", style="bold")
        table.add_column("当前值", justify="right")
        table.add_column("进度条", justify="left")
        
        metrics = self.system_metrics
        
        # CPU使用率
        cpu_usage = metrics["cpu_usage"]
        table.add_row(
            "CPU使用率",
            f"{cpu_usage:.1f}%",
            self._create_progress_bar(cpu_usage, "cpu")
        )
        
        # 内存使用率
        memory_usage = metrics["memory_usage"]
        table.add_row(
            "内存使用率",
            f"{memory_usage:.1f}%",
            self._create_progress_bar(memory_usage, "memory")
        )
        
        # 磁盘使用率
        disk_usage = metrics["disk_usage"]
        table.add_row(
            "磁盘使用率",
            f"{disk_usage:.1f}%",
            self._create_progress_bar(disk_usage, "disk")
        )
        
        # 网络IO
        network_io = metrics["network_io"]
        table.add_row(
            "网络IO",
            f"{network_io:.1f}KB/s",
            self._create_progress_bar(min(network_io / 1000, 100), "network")
        )
        
        return Panel(
            table,
            title="🖥️ 系统指标",
            border_style="yellow"
        )
    
    def _create_history_panel(self) -> Panel:
        """创建执行历史面板
        
        Returns:
            Panel: 历史面板
        """
        if not self.execution_history:
            return Panel(
                Text("暂无执行历史", style="dim italic"),
                title="📜 执行历史",
                border_style="dim"
            )
        
        tree = Tree("执行历史", style="bold cyan")
        
        # 显示最近10条记录
        recent_history = self.execution_history[-10:]
        
        for record in reversed(recent_history):
            timestamp = record.get("timestamp", datetime.now())
            action = record.get("action", "未知操作")
            status = record.get("status", "unknown")
            duration = record.get("duration", 0)
            
            # 创建记录节点
            status_icon = self._get_status_icon(status)
            time_str = timestamp.strftime("%H:%M:%S")
            
            node_text = f"{status_icon} {time_str} - {action}"
            if duration > 0:
                node_text += f" ({duration:.2f}s)"
            
            node = tree.add(node_text, style=self._get_status_style(status))
            
            # 添加详细信息
            if "details" in record:
                details = record["details"]
                if isinstance(details, dict):
                    for key, value in details.items():
                        node.add(f"{key}: {value}", style="dim")
        
        return Panel(
            tree,
            title="📜 执行历史",
            border_style="magenta"
        )
    
    def _get_status_indicator(self, status: str) -> str:
        """获取状态指示器
        
        Args:
            status: 状态类型
            
        Returns:
            str: 状态指示器
        """
        indicators = {
            "normal": "✅",
            "warning": "⚠️",
            "error": "❌",
            "good": "🟢",
            "slow": "🟡",
            "fast": "🚀"
        }
        return indicators.get(status, "❓")
    
    def _get_response_time_status(self, response_time: float) -> str:
        """获取响应时间状态
        
        Args:
            response_time: 响应时间（毫秒）
            
        Returns:
            str: 状态指示器
        """
        if response_time < 100:
            return self._get_status_indicator("fast")
        elif response_time < 500:
            return self._get_status_indicator("good")
        elif response_time < 1000:
            return self._get_status_indicator("slow")
        else:
            return self._get_status_indicator("warning")
    
    def _get_success_rate_status(self, success_rate: float) -> str:
        """获取成功率状态
        
        Args:
            success_rate: 成功率（百分比）
            
        Returns:
            str: 状态指示器
        """
        if success_rate >= 95:
            return self._get_status_indicator("good")
        elif success_rate >= 90:
            return self._get_status_indicator("normal")
        elif success_rate >= 80:
            return self._get_status_indicator("warning")
        else:
            return self._get_status_indicator("error")
    
    def _get_error_count_status(self, error_count: int) -> str:
        """获取错误计数状态
        
        Args:
            error_count: 错误数量
            
        Returns:
            str: 状态指示器
        """
        if error_count == 0:
            return self._get_status_indicator("good")
        elif error_count < 5:
            return self._get_status_indicator("warning")
        else:
            return self._get_status_indicator("error")
    
    def _create_progress_bar(self, value: float, metric_type: str) -> str:
        """创建进度条
        
        Args:
            value: 进度值（0-100）
            metric_type: 指标类型
            
        Returns:
            str: 进度条字符串
        """
        # 根据指标类型选择颜色
        colors = {
            "cpu": "blue",
            "memory": "green",
            "disk": "yellow",
            "network": "magenta"
        }
        
        color = colors.get(metric_type, "white")
        
        # 创建进度条
        bar_length = 10
        filled_length = int(bar_length * value / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        return f"[{color}]{bar}[/{color}] {value:.1f}%"
    
    def _get_status_icon(self, status: str) -> str:
        """获取状态图标
        
        Args:
            status: 状态
            
        Returns:
            str: 状态图标
        """
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "pending": "⏳"
        }
        return icons.get(status, "❓")
    
    def _get_status_style(self, status: str) -> str:
        """获取状态样式
        
        Args:
            status: 状态
            
        Returns:
            str: 状态样式
        """
        styles = {
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
            "pending": "dim"
        }
        return styles.get(status, "white")
    
    def update_performance_data(self, data: Dict[str, Any]) -> None:
        """更新性能数据
        
        Args:
            data: 性能数据
        """
        self.performance_data.update(data)
    
    def update_system_metrics(self, metrics: Dict[str, Any]) -> None:
        """更新系统指标
        
        Args:
            metrics: 系统指标
        """
        self.system_metrics.update(metrics)
    
    def add_execution_record(self, record: Dict[str, Any]) -> None:
        """添加执行记录
        
        Args:
            record: 执行记录
        """
        # 确保记录有时间戳
        if "timestamp" not in record:
            record["timestamp"] = datetime.now()
        
        self.execution_history.append(record)
        
        # 限制历史记录数量
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def handle_key(self, key: str) -> bool:
        """处理键盘输入
        
        Args:
            key: 按键
            
        Returns:
            bool: True表示已处理，False表示需要传递到上层
        """
        if key == "escape":
            return True
        
        # 可以添加其他快捷键处理
        if key == "r":
            # 刷新数据
            self._refresh_data()
            return True
        
        return super().handle_key(key)
    
    def _refresh_data(self) -> None:
        """刷新数据"""
        # 这里可以添加数据刷新逻辑
        # 例如：重新获取性能数据、系统指标等
        pass