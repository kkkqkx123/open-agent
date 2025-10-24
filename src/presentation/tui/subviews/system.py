"""系统管理子界面"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.columns import Columns
from rich.align import Align

from .base import BaseSubview
from ..config import TUIConfig


class SystemSubview(BaseSubview):
    """系统管理子界面
    
    包含Studio服务器管理、端口配置、配置重载
    """
    
    def __init__(self, config: TUIConfig):
        """初始化系统管理子界面
        
        Args:
            config: TUI配置
        """
        super().__init__(config)
        
        # Studio服务器状态
        self.studio_status = {
            "running": False,
            "port": 8079,
            "url": "",
            "start_time": None,
            "version": "1.0.0",
            "connected_clients": 0
        }
        
        # 端口配置
        self.port_config = {
            "studio_port": 8079,
            "api_port": 8000,
            "websocket_port": 8001,
            "debug_port": 5678
        }
        
        # 配置管理
        self.config_management = {
            "current_config": {},
            "last_reload": None,
            "auto_reload": False,
            "config_file": "",
            "validation_errors": []
        }
        
        # 系统信息
        self.system_info = {
            "python_version": "",
            "framework_version": "",
            "uptime": "",
            "memory_usage": 0,
            "cpu_usage": 0
        }
    
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        return "⚙️ 系统管理"
    
    def render(self) -> Panel:
        """渲染系统管理子界面
        
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
    
    def _create_main_content(self) -> Columns:
        """创建主要内容区域
        
        Returns:
            Columns: 列布局
        """
        # Studio管理
        studio_panel = self._create_studio_panel()
        
        # 端口配置
        port_panel = self._create_port_panel()
        
        # 配置管理
        config_panel = self._create_config_panel()
        
        # 系统信息
        info_panel = self._create_system_info_panel()
        
        # 组合布局
        # 创建垂直布局用于config_panel和info_panel
        from rich.layout import Layout
        
        vertical_layout = Layout()
        vertical_layout.split_column(
            Layout(config_panel),
            Layout(info_panel)
        )
        
        return Columns([
            studio_panel,
            port_panel,
            vertical_layout
        ], equal=True)
    
    def _create_studio_panel(self) -> Panel:
        """创建Studio管理面板
        
        Returns:
            Panel: Studio面板
        """
        # 创建Studio状态表格
        table = Table(title="LangGraph Studio", show_header=True, header_style="bold cyan")
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        table.add_column("操作", justify="center")
        
        status = self.studio_status
        
        # 运行状态
        status_text = "运行中" if status["running"] else "已停止"
        status_style = "green" if status["running"] else "red"
        table.add_row(
            "状态",
            Text(status_text, style=status_style),
            self._get_studio_action_button()
        )
        
        # 端口
        table.add_row(
            "端口",
            str(status["port"]),
            ""
        )
        
        # URL
        url = status["url"] or "未启动"
        table.add_row(
            "URL",
            url,
            ""
        )
        
        # 版本
        table.add_row(
            "版本",
            status["version"],
            ""
        )
        
        # 连接客户端数
        table.add_row(
            "连接客户端",
            str(status["connected_clients"]),
            ""
        )
        
        # 运行时间
        if status["start_time"] and status["running"]:
            uptime = self._calculate_uptime(status["start_time"])
            table.add_row(
                "运行时间",
                uptime,
                ""
            )
        else:
            table.add_row(
                "运行时间",
                "-",
                ""
            )
        
        return Panel(
            table,
            title="🎬 Studio管理",
            border_style="green"
        )
    
    def _create_port_panel(self) -> Panel:
        """创建端口配置面板
        
        Returns:
            Panel: 端口面板
        """
        # 创建端口配置表格
        table = Table(title="端口配置", show_header=True, header_style="bold cyan")
        table.add_column("服务", style="bold")
        table.add_column("端口", justify="right")
        table.add_column("状态", justify="center")
        table.add_column("操作", justify="center")
        
        ports = self.port_config
        
        # Studio端口
        table.add_row(
            "Studio",
            str(ports["studio_port"]),
            self._get_port_status(ports["studio_port"]),
            "修改"
        )
        
        # API端口
        table.add_row(
            "API",
            str(ports["api_port"]),
            self._get_port_status(ports["api_port"]),
            "修改"
        )
        
        # WebSocket端口
        table.add_row(
            "WebSocket",
            str(ports["websocket_port"]),
            self._get_port_status(ports["websocket_port"]),
            "修改"
        )
        
        # 调试端口
        table.add_row(
            "调试",
            str(ports["debug_port"]),
            self._get_port_status(ports["debug_port"]),
            "修改"
        )
        
        return Panel(
            table,
            title="🔌 端口配置",
            border_style="yellow"
        )
    
    def _create_config_panel(self) -> Panel:
        """创建配置管理面板
        
        Returns:
            Panel: 配置面板
        """
        # 创建配置管理表格
        table = Table(title="配置管理", show_header=True, header_style="bold cyan")
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        table.add_column("操作", justify="center")
        
        config = self.config_management
        
        # 配置文件
        config_file = config["config_file"] or "未加载"
        table.add_row(
            "配置文件",
            config_file,
            "浏览"
        )
        
        # 最后重载时间
        last_reload = config["last_reload"]
        if last_reload:
            reload_time = last_reload.strftime("%Y-%m-%d %H:%M:%S")
        else:
            reload_time = "未重载"
        
        table.add_row(
            "最后重载",
            reload_time,
            "重载"
        )
        
        # 自动重载
        auto_reload = "启用" if config["auto_reload"] else "禁用"
        auto_reload_style = "green" if config["auto_reload"] else "red"
        
        table.add_row(
            "自动重载",
            Text(auto_reload, style=auto_reload_style),
            "切换"
        )
        
        # 验证错误
        errors = config["validation_errors"]
        if errors:
            error_count = len(errors)
            error_text = f"{error_count} 个错误"
            error_style = "red"
        else:
            error_text = "无错误"
            error_style = "green"
        
        table.add_row(
            "验证错误",
            Text(error_text, style=error_style),
            "查看"
        )
        
        return Panel(
            table,
            title="📄 配置管理",
            border_style="magenta"
        )
    
    def _create_system_info_panel(self) -> Panel:
        """创建系统信息面板
        
        Returns:
            Panel: 系统信息面板
        """
        # 创建系统信息表格
        table = Table(title="系统信息", show_header=True, header_style="bold cyan")
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        info = self.system_info
        
        # Python版本
        table.add_row(
            "Python版本",
            info["python_version"] or "未知"
        )
        
        # 框架版本
        table.add_row(
            "框架版本",
            info["framework_version"] or "未知"
        )
        
        # 运行时间
        table.add_row(
            "运行时间",
            info["uptime"] or "未知"
        )
        
        # 内存使用
        memory_mb = info["memory_usage"]
        if memory_mb > 0:
            memory_text = f"{memory_mb:.1f} MB"
        else:
            memory_text = "未知"
        
        table.add_row(
            "内存使用",
            memory_text
        )
        
        # CPU使用
        cpu_percent = info["cpu_usage"]
        if cpu_percent > 0:
            cpu_text = f"{cpu_percent:.1f}%"
        else:
            cpu_text = "未知"
        
        table.add_row(
            "CPU使用",
            cpu_text
        )
        
        return Panel(
            table,
            title="💻 系统信息",
            border_style="blue"
        )
    
    def _get_studio_action_button(self) -> str:
        """获取Studio操作按钮
        
        Returns:
            str: 操作按钮文本
        """
        if self.studio_status["running"]:
            return "停止"
        else:
            return "启动"
    
    def _get_port_status(self, port: int) -> str:
        """获取端口状态
        
        Args:
            port: 端口号
            
        Returns:
            str: 端口状态
        """
        # 这里可以添加实际的端口检查逻辑
        # 暂时返回模拟状态
        return "✅ 可用"
    
    def _calculate_uptime(self, start_time: datetime) -> str:
        """计算运行时间
        
        Args:
            start_time: 开始时间
            
        Returns:
            str: 运行时间字符串
        """
        now = datetime.now()
        delta = now - start_time
        
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def update_studio_status(self, status: Dict[str, Any]) -> None:
        """更新Studio状态
        
        Args:
            status: Studio状态数据
        """
        self.studio_status.update(status)
    
    def update_port_config(self, config: Dict[str, Any]) -> None:
        """更新端口配置
        
        Args:
            config: 端口配置数据
        """
        self.port_config.update(config)
    
    def update_config_management(self, config: Dict[str, Any]) -> None:
        """更新配置管理
        
        Args:
            config: 配置管理数据
        """
        self.config_management.update(config)
    
    def update_system_info(self, info: Dict[str, Any]) -> None:
        """更新系统信息
        
        Args:
            info: 系统信息数据
        """
        self.system_info.update(info)
    
    def start_studio(self) -> bool:
        """启动Studio服务器
        
        Returns:
            bool: 是否成功启动
        """
        # 这里可以添加实际的Studio启动逻辑
        self.studio_status["running"] = True
        self.studio_status["start_time"] = datetime.now()
        self.studio_status["url"] = f"http://localhost:{self.studio_status['port']}"
        
        # 触发回调
        self.trigger_callback("studio_started", self.studio_status)
        
        return True
    
    def stop_studio(self) -> bool:
        """停止Studio服务器
        
        Returns:
            bool: 是否成功停止
        """
        # 这里可以添加实际的Studio停止逻辑
        self.studio_status["running"] = False
        self.studio_status["url"] = ""
        self.studio_status["connected_clients"] = 0
        
        # 触发回调
        self.trigger_callback("studio_stopped", self.studio_status)
        
        return True
    
    def reload_config(self) -> bool:
        """重载配置
        
        Returns:
            bool: 是否成功重载
        """
        # 这里可以添加实际的配置重载逻辑
        self.config_management["last_reload"] = datetime.now()
        self.config_management["validation_errors"] = []
        
        # 触发回调
        self.trigger_callback("config_reloaded", self.config_management)
        
        return True
    
    def toggle_auto_reload(self) -> None:
        """切换自动重载"""
        self.config_management["auto_reload"] = not self.config_management["auto_reload"]
        
        # 触发回调
        self.trigger_callback("auto_reload_toggled", self.config_management["auto_reload"])
    
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
        if key == "s":
            # 启动/停止Studio
            if self.studio_status["running"]:
                self.stop_studio()
            else:
                self.start_studio()
            return True
        
        if key == "r":
            # 重载配置
            self.reload_config()
            return True
        
        if key == "a":
            # 切换自动重载
            self.toggle_auto_reload()
            return True
        
        return super().handle_key(key)