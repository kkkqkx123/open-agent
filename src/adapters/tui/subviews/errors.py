
"""错误反馈子界面"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.columns import Columns
from rich.align import Align
from rich.syntax import Syntax
from rich.markdown import Markdown

from .base import BaseSubview
from ..config import TUIConfig


class ErrorFeedbackSubview(BaseSubview):
    """错误反馈子界面
    
    包含错误信息查看和反馈
    """
    
    def __init__(self, config: TUIConfig):
        """初始化错误反馈子界面
        
        Args:
            config: TUI配置
        """
        super().__init__(config)
        
        # 错误列表
        self.error_list: List[Dict[str, Any]] = []
        
        # 错误分类
        self.error_categories = {
            "system": "系统错误",
            "workflow": "工作流错误",
            "agent": "Agent错误",
            "tool": "工具错误",
            "network": "网络错误",
            "user": "用户错误"
        }
        
        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "critical_errors": 0,
            "warning_errors": 0,
            "info_errors": 0,
            "resolved_errors": 0
        }
        
        # 反馈设置
        self.feedback_settings = {
            "auto_report": False,
            "include_stacktrace": True,
            "include_context": True,
            "report_anonymously": True
        }
        
        # 当前选中的错误
        self.selected_error: Optional[Dict[str, Any]] = None
    
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        return "🚨 错误反馈"
    
    def render(self) -> Panel:
        """渲染错误反馈子界面
        
        Returns:
            Panel: 子界面面板
        """
        # 创建主要内容
        content = self._create_main_content()
        
        # 创建面板
        panel = Panel(
            content,
            title=self.create_header(),
            border_style="red",
            subtitle=self.create_help_text()
        )
        
        return panel
    
    def _create_main_content(self) -> Columns:
        """创建主要内容区域
        
        Returns:
            Columns: 列布局
        """
        # 错误列表
        error_list_panel = self._create_error_list_panel()
        
        # 错误详情
        error_detail_panel = self._create_error_detail_panel()
        
        # 错误统计
        stats_panel = self._create_stats_panel()
        
        # 反馈设置
        feedback_panel = self._create_feedback_panel()
        
        # 组合布局
        return Columns([
            error_list_panel,
            Columns([error_detail_panel, stats_panel], equal=True),
            feedback_panel
        ], equal=True)
    
    def _create_error_list_panel(self) -> Panel:
        """创建错误列表面板
        
        Returns:
            Panel: 错误列表面板
        """
        if not self.error_list:
            return Panel(
                Text("暂无错误记录", style="dim italic"),
                title="📋 错误列表",
                border_style="dim"
            )
        
        # 创建错误列表表格
        table = Table(title="错误列表", show_header=True, header_style="bold cyan")
        table.add_column("时间", style="dim", width=8)
        table.add_column("级别", justify="center", width=6)
        table.add_column("类别", width=8)
        table.add_column("消息", style="bold")
        table.add_column("状态", justify="center", width=6)
        
        # 显示最近的错误（最多20条）
        recent_errors = self.error_list[-20:]
        
        for error in reversed(recent_errors):
            timestamp = error.get("timestamp", datetime.now())
            level = error.get("level", "error")
            category = error.get("category", "system")
            message = error.get("message", "未知错误")
            resolved = error.get("resolved", False)
            
            # 格式化时间
            time_str = timestamp.strftime("%H:%M:%S")
            
            # 级别图标
            level_icon = self._get_level_icon(level)
            
            # 状态图标
            status_icon = "✅" if resolved else "❌"
            
            # 截断消息
            if len(message) > 30:
                message = message[:27] + "..."
            
            table.add_row(
                time_str,
                level_icon,
                category,
                message,
                status_icon
            )
        
        return Panel(
            table,
            title="📋 错误列表",
            border_style="yellow"
        )
    
    def _create_error_detail_panel(self) -> Panel:
        """创建错误详情面板
        
        Returns:
            Panel: 错误详情面板
        """
        if not self.selected_error:
            return Panel(
                Text("请选择一个错误查看详情", style="dim italic"),
                title="🔍 错误详情",
                border_style="dim"
            )
        
        # 创建错误详情内容
        error = self.selected_error
        
        # 创建详情表格
        table = Table(title=f"错误详情: {error.get('id', 'Unknown')}", show_header=True, header_style="bold cyan")
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        # 基本信息
        table.add_row("错误ID", str(error.get("id", "Unknown")))
        table.add_row("时间", error.get("timestamp", datetime.now()).strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("级别", error.get("level", "error"))
        table.add_row("类别", error.get("category", "system"))
        table.add_row("状态", "已解决" if error.get("resolved", False) else "未解决")
        
        # 错误消息
        message = error.get("message", "无消息")
        if len(message) > 50:
            message = message[:47] + "..."
        table.add_row("消息", message)
        
        # 错误源
        source = error.get("source", "未知")
        table.add_row("错误源", source)
        
        return Panel(
            table,
            title="🔍 错误详情",
            border_style="red"
        )
    
    def _create_stats_panel(self) -> Panel:
        """创建错误统计面板
        
        Returns:
            Panel: 错误统计面板
        """
        # 创建统计表格
        table = Table(title="错误统计", show_header=True, header_style="bold cyan")
        table.add_column("指标", style="bold")
        table.add_column("数量", justify="right")
        table.add_column("占比", justify="right")
        
        stats = self.error_stats
        total = stats["total_errors"]
        
        if total == 0:
            table.add_row("总错误数", "0", "0%")
            table.add_row("严重错误", "0", "0%")
            table.add_row("警告错误", "0", "0%")
            table.add_row("信息错误", "0", "0%")
            table.add_row("已解决", "0", "0%")
        else:
            table.add_row("总错误数", str(total), "100%")
            
            critical = stats["critical_errors"]
            table.add_row(
                "严重错误",
                str(critical),
                f"{critical/total*100:.1f}%"
            )
            
            warning = stats["warning_errors"]
            table.add_row(
                "警告错误",
                str(warning),
                f"{warning/total*100:.1f}%"
            )
            
            info = stats["info_errors"]
            table.add_row(
                "信息错误",
                str(info),
                f"{info/total*100:.1f}%"
            )
            
            resolved = stats["resolved_errors"]
            table.add_row(
                "已解决",
                str(resolved),
                f"{resolved/total*100:.1f}%"
            )
        
        return Panel(
            table,
            title="📊 错误统计",
            border_style="magenta"
        )
    
    def _create_feedback_panel(self) -> Panel:
        """创建反馈设置面板
        
        Returns:
            Panel: 反馈设置面板
        """
        # 创建设置表格
        table = Table(title="反馈设置", show_header=True, header_style="bold cyan")
        table.add_column("设置", style="bold")
        table.add_column("状态", justify="center")
        table.add_column("操作", justify="center")
        
        settings = self.feedback_settings
        
        # 自动报告
        auto_report = "启用" if settings["auto_report"] else "禁用"
        auto_report_style = "green" if settings["auto_report"] else "red"
        table.add_row(
            "自动报告",
            Text(auto_report, style=auto_report_style),
            "切换"
        )
        
        # 包含堆栈跟踪
        include_stacktrace = "启用" if settings["include_stacktrace"] else "禁用"
        stacktrace_style = "green" if settings["include_stacktrace"] else "red"
        table.add_row(
            "包含堆栈跟踪",
            Text(include_stacktrace, style=stacktrace_style),
            "切换"
        )
        
        # 包含上下文
        include_context = "启用" if settings["include_context"] else "禁用"
        context_style = "green" if settings["include_context"] else "red"
        table.add_row(
            "包含上下文",
            Text(include_context, style=context_style),
            "切换"
        )
        
        # 匿名报告
        report_anonymously = "启用" if settings["report_anonymously"] else "禁用"
        anonymous_style = "green" if settings["report_anonymously"] else "red"
        table.add_row(
            "匿名报告",
            Text(report_anonymously, style=anonymous_style),
            "切换"
        )
        
        return Panel(
            table,
            title="⚙️ 反馈设置",
            border_style="blue"
        )
    
    def _get_level_icon(self, level: str) -> str:
        """获取错误级别图标
        
        Args:
            level: 错误级别
            
        Returns:
            str: 级别图标
        """
        icons = {
            "critical": "🔴",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        return icons.get(level, "❓")
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """添加错误
        
        Args:
            error: 错误信息
        """
        # 确保错误有必要的字段
        if "id" not in error:
            error["id"] = f"error_{len(self.error_list) + 1}"
        
        if "timestamp" not in error:
            error["timestamp"] = datetime.now()
        
        if "resolved" not in error:
            error["resolved"] = False
        
        # 添加到错误列表
        self.error_list.append(error)
        
        # 更新统计
        self._update_stats()
        
        # 限制错误列表数量
        if len(self.error_list) > 100:
            self.error_list = self.error_list[-100:]
    
    def select_error(self, error_id: str) -> bool:
        """选择错误
        
        Args:
            error_id: 错误ID
            
        Returns:
            bool: 是否成功选择
        """
        for error in self.error_list:
            if error.get("id") == error_id:
                self.selected_error = error
                return True
        return False
    
    def resolve_error(self, error_id: str) -> bool:
        """解决错误
        
        Args:
            error_id: 错误ID
            
        Returns:
            bool: 是否成功解决
        """
        for error in self.error_list:
            if error.get("id") == error_id:
                error["resolved"] = True
                self._update_stats()
                return True
        return False
    
    def _update_stats(self) -> None:
        """更新错误统计"""
        stats = {
            "total_errors": len(self.error_list),
            "critical_errors": 0,
            "warning_errors": 0,
            "info_errors": 0,
            "resolved_errors": 0
        }
        
        for error in self.error_list:
            level = error.get("level", "error")
            if level == "critical":
                stats["critical_errors"] += 1
            elif level == "warning":
                stats["warning_errors"] += 1
            elif level == "info":
                stats["info_errors"] += 1
            
            if error.get("resolved", False):
                stats["resolved_errors"] += 1
        
        self.error_stats = stats
    
    def toggle_auto_report(self) -> None:
        """切换自动报告"""
        self.feedback_settings["auto_report"] = not self.feedback_settings["auto_report"]
        
        # 触发回调
        self.trigger_callback("auto_report_toggled", self.feedback_settings["auto_report"])
    
    def toggle_include_stacktrace(self) -> None:
        """切换包含堆栈跟踪"""
        self.feedback_settings["include_stacktrace"] = not self.feedback_settings["include_stacktrace"]
    
    def toggle_include_context(self) -> None:
        """切换包含上下文"""
        self.feedback_settings["include_context"] = not self.feedback_settings["include_context"]
    
    def toggle_report_anonymously(self) -> None:
        """切换匿名报告"""
        self.feedback_settings["report_anonymously"] = not self.feedback_settings["report_anonymously"]
    
    def submit_feedback(self, error_id: str, feedback_text: str) -> bool:
        """提交错误反馈
        
        Args:
            error_id: 错误ID
            feedback_text: 反馈文本
            
        Returns:
            bool: 是否成功提交
        """
        # 这里可以添加实际的反馈提交逻辑
        # 例如：发送到错误收集服务
        
        # 触发回调
        self.trigger_callback("feedback_submitted", {
            "error_id": error_id,
            "feedback": feedback_text,
            "timestamp": datetime.now()
        })
        
        return True
    
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
            # 刷新错误列表
            self._refresh_errors()
            return True
        
        if key == "c":
            # 清除已解决的错误
            self._clear_resolved_errors()
            return True
        
        if key == "a":
            # 切换自动报告
            self.toggle_auto_report()
            return True
        
        return super().handle_key(key)
    
    def _refresh_errors(self) -> None:
        """刷新错误列表"""
        # 这里可以添加刷新逻辑
        # 例如：重新加载错误数据
        pass
    
    def _clear_resolved_errors(self) -> None:
        """清除已解决的错误"""
        self.error_list = [error for error in self.error_list if not error.get("resolved", False)]
        self._update_stats()