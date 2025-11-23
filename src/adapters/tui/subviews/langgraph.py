"""LangGraph调试子界面"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.tree import Tree
from rich.console import Group

from .base import BaseSubview
from ..config import TUIConfig


class LangGraphSubview(BaseSubview):
    """LangGraph调试子界面
    
    包含节点监控、执行路径追踪、状态快照显示等功能
    """
    
    def __init__(self, config: TUIConfig):
        """初始化LangGraph调试子界面
        
        Args:
            config: TUI配置
        """
        super().__init__(config)
        
        # 当前节点信息
        self.current_node = {
            "id": "",
            "name": "",
            "type": "",
            "status": "idle",
            "input": {},
            "output": None,
            "execution_time": 0.0,
            "start_time": None,
            "end_time": None
        }
        
        # 执行路径
        self.execution_path: List[Dict[str, Any]] = []
        
        # 状态快照
        self.state_snapshot = {
            "messages": [],
            "current_step": "",
            "iteration": 0,
            "max_iterations": 10,
            "timestamp": None,
            "variables": {}
        }
        
        # 节点监控数据
        self.node_monitoring = {
            "total_nodes": 0,
            "completed_nodes": 0,
            "failed_nodes": 0,
            "running_nodes": 0,
            "pending_nodes": 0
        }
    
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        return "🔗 LangGraph调试"
    
    def render(self) -> Panel:
        """渲染LangGraph调试子界面
        
        Returns:
            Panel: 子界面面板
        """
        # 创建主要内容
        content = self._create_main_content()
        
        # 创建面板
        panel = Panel(
            content,
            title=self.create_header(),
            border_style="cyan",
            subtitle=self.create_help_text()
        )
        
        return panel
    
    def _create_main_content(self) -> Group:
        """创建主要内容区域
        
        Returns:
            Columns: 列布局
        """
        # 当前节点面板
        current_node_panel = self._create_current_node_panel()
        
        # 执行路径面板
        execution_path_panel = self._create_execution_path_panel()
        
        # 状态快照面板
        state_snapshot_panel = self._create_state_snapshot_panel()
        
        # 节点监控面板
        node_monitoring_panel = self._create_node_monitoring_panel()
        
        # 组合布局 - 两行两列布局
        top_row = Columns([current_node_panel, execution_path_panel], equal=True, expand=True)
        bottom_row = Columns([state_snapshot_panel, node_monitoring_panel], equal=True, expand=True)

        return Group(top_row, bottom_row)
    
    def _create_current_node_panel(self) -> Panel:
        """创建当前节点面板
        
        Returns:
            Panel: 当前节点面板
        """
        node = self.current_node
        
        if not node["id"]:
            return Panel(
                Text("暂无当前节点信息", style="dim italic"),
                title="📍 当前节点",
                border_style="dim"
            )
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        # 节点ID
        table.add_row("节点ID", node["id"])
        
        # 节点名称
        if node["name"]:
            table.add_row("名称", node["name"])
        
        # 节点类型
        if node["type"]:
            table.add_row("类型", node["type"])
        
        # 状态
        status = node["status"]
        status_icon = self._get_status_icon(status)
        status_style = self._get_status_style(status)
        table.add_row("状态", f"{status_icon} [{status_style}]{status}[/{status_style}]")
        
        # 执行时间
        if node["execution_time"] > 0:
            table.add_row("执行时间", f"{node['execution_time']:.3f}s")
        
        # 输入数据
        if node["input"]:
            input_text = self._format_dict(node["input"], max_length=30)
            table.add_row("输入", input_text)
        
        # 输出数据
        if node["output"] is not None:
            output_text = self._format_value(node["output"], max_length=30)
            table.add_row("输出", output_text)
        
        return Panel(
            table,
            title="📍 当前节点",
            border_style="green"
        )
    
    def _create_execution_path_panel(self) -> Panel:
        """创建执行路径面板
        
        Returns:
            Panel: 执行路径面板
        """
        if not self.execution_path:
            return Panel(
                Text("暂无执行路径", style="dim italic"),
                title="🛤️ 执行路径",
                border_style="dim"
            )
        
        table = Table(title="执行路径", show_header=True, header_style="bold cyan")
        table.add_column("步骤", style="bold", justify="right")
        table.add_column("节点", style="bold")
        table.add_column("状态", justify="center")
        table.add_column("耗时", justify="right")
        
        # 显示最近15个步骤
        recent_path = self.execution_path[-15:]
        
        for i, step in enumerate(recent_path, len(self.execution_path) - len(recent_path) + 1):
            node_id = step.get("node_id", "unknown")
            status = step.get("status", "unknown")
            duration = step.get("duration", 0)
            
            # 状态图标
            status_icon = self._get_status_icon(status)
            
            # 耗时
            duration_str = f"{duration:.3f}s" if duration > 0 else "-"
            
            table.add_row(
                str(i),
                node_id,
                f"{status_icon} {status}",
                duration_str
            )
        
        return Panel(
            table,
            border_style="blue"
        )
    
    def _create_state_snapshot_panel(self) -> Panel:
        """创建状态快照面板
        
        Returns:
            Panel: 状态快照面板
        """
        snapshot = self.state_snapshot
        
        # 创建JSON格式的文本显示
        content = Text()
        
        # 添加基本信息
        content.append("{\n", style="dim")
        
        # 消息数量
        message_count = len(snapshot["messages"])
        content.append(f'  "messages": [ /* {message_count} 条消息 */ ],\n', style="dim")
        
        # 当前步骤
        content.append(f'  "current_step": "{snapshot["current_step"]}",\n', style="dim")
        
        # 迭代次数
        content.append(f'  "iteration": {snapshot["iteration"]},\n', style="dim")
        
        # 最大迭代次数
        content.append(f'  "max_iterations": {snapshot["max_iterations"]},\n', style="dim")
        
        # 时间戳
        if snapshot["timestamp"]:
            timestamp_str = snapshot["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            content.append(f'  "timestamp": "{timestamp_str}",\n', style="dim")
        
        # 变量数量
        var_count = len(snapshot["variables"])
        content.append(f'  "variables": {{ /* {var_count} 个变量 */ }}\n', style="dim")
        
        content.append("}", style="dim")
        
        return Panel(
            content,
            title="💾 状态快照",
            border_style="yellow"
        )
    
    def _create_node_monitoring_panel(self) -> Panel:
        """创建节点监控面板
        
        Returns:
            Panel: 节点监控面板
        """
        monitoring = self.node_monitoring
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("状态", style="bold")
        table.add_column("数量", style="dim", justify="right")
        
        # 总节点数
        table.add_row("总节点数", str(monitoring["total_nodes"]))
        
        # 运行中节点
        table.add_row("运行中", f"{monitoring['running_nodes']} 🟡")
        
        # 已完成节点
        table.add_row("已完成", f"{monitoring['completed_nodes']} ✅")
        
        # 失败节点
        table.add_row("已失败", f"{monitoring['failed_nodes']} ❌")
        
        # 待处理节点
        table.add_row("待处理", f"{monitoring['pending_nodes']} ⏳")
        
        # 计算完成率
        if monitoring["total_nodes"] > 0:
            completion_rate = (monitoring["completed_nodes"] / monitoring["total_nodes"]) * 100
            table.add_row("完成率", f"{completion_rate:.1f}%")
        
        return Panel(
            table,
            title="📊 节点监控",
            border_style="magenta"
        )
    
    def _get_status_icon(self, status: str) -> str:
        """获取状态图标
        
        Args:
            status: 状态
            
        Returns:
            str: 状态图标
        """
        icons = {
            "idle": "⚪",
            "running": "🟡",
            "completed": "✅",
            "failed": "❌",
            "pending": "⏳",
            "skipped": "⏭️"
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
            "idle": "dim",
            "running": "yellow",
            "completed": "green",
            "failed": "red",
            "pending": "blue",
            "skipped": "magenta"
        }
        return styles.get(status, "white")
    
    def _format_dict(self, data: Dict[str, Any], max_length: int = 50) -> str:
        """格式化字典数据
        
        Args:
            data: 字典数据
            max_length: 最大长度
            
        Returns:
            str: 格式化后的字符串
        """
        if not data:
            return "{}"
        
        # 简化显示
        items = []
        for key, value in list(data.items())[:2]:  # 只显示前2个键值对
            value_str = self._format_value(value, max_length=15)
            items.append(f"{key}: {value_str}")
        
        result = "{ " + ", ".join(items) + " }"
        
        # 如果数据太多，添加省略号
        if len(data) > 2:
            result += " ..."
        
        # 限制总长度
        if len(result) > max_length:
            result = result[:max_length-3] + "..."
        
        return result
    
    def _format_value(self, value: Any, max_length: int = 30) -> str:
        """格式化值
        
        Args:
            value: 值
            max_length: 最大长度
            
        Returns:
            str: 格式化后的字符串
        """
        if isinstance(value, str):
            if len(value) > max_length:
                return f'"{value[:max_length-3]}..."'
            else:
                return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, list):
            if len(value) > 3:
                return f"[{len(value)} items]"
            else:
                items = [self._format_value(item, 10) for item in value[:3]]
                return f"[{', '.join(items)}]"
        elif isinstance(value, dict):
            return self._format_dict(value, max_length)
        elif value is None:
            return "null"
        else:
            str_value = str(value)
            if len(str_value) > max_length:
                return str_value[:max_length-3] + "..."
            else:
                return str_value
    
    def update_current_node(self, node_info: Dict[str, Any]) -> None:
        """更新当前节点信息
        
        Args:
            node_info: 节点信息
        """
        self.current_node.update(node_info)
    
    def add_execution_step(self, step: Dict[str, Any]) -> None:
        """添加执行步骤
        
        Args:
            step: 执行步骤
        """
        # 确保步骤有时间戳
        if "timestamp" not in step:
            step["timestamp"] = datetime.now()
        
        self.execution_path.append(step)
        
        # 限制路径长度
        if len(self.execution_path) > 100:
            self.execution_path = self.execution_path[-100:]
    
    def update_state_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """更新状态快照
        
        Args:
            snapshot: 状态快照
        """
        self.state_snapshot.update(snapshot)
        # 确保时间戳更新
        if "timestamp" not in self.state_snapshot or not self.state_snapshot["timestamp"]:
            self.state_snapshot["timestamp"] = datetime.now()
    
    def update_node_monitoring(self, monitoring: Dict[str, Any]) -> None:
        """更新节点监控数据
        
        Args:
            monitoring: 节点监控数据
        """
        self.node_monitoring.update(monitoring)