"""Studio服务器管理器组件

包含工作流Studio服务器启动、停止、监控和端口管理功能
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
import asyncio
import subprocess
import socket
import json
import requests
from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree

from ..config import TUIConfig


class ServerStatus(Enum):
    """服务器状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class StudioServerConfig:
    """Studio服务器配置"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        session_id: Optional[str] = None,
        auto_start: bool = False,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.session_id = session_id
        self.auto_start = auto_start
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "host": self.host,
            "port": self.port,
            "session_id": self.session_id,
            "auto_start": self.auto_start,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudioServerConfig":
        """从字典创建配置
        
        Args:
            data: 配置字典
            
        Returns:
            StudioServerConfig: 服务器配置
        """
        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 8123),
            session_id=data.get("session_id"),
            auto_start=data.get("auto_start", False),
            timeout=data.get("timeout", 30)
        )


class StudioServerManager:
    """Studio服务器管理器"""
    
    def __init__(self, config: Optional[StudioServerConfig] = None):
        self.config = config or StudioServerConfig()
        self.status = ServerStatus.STOPPED
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.error_message = ""
        self.session_isolation = {}  # session_id -> port
        
        # 回调函数
        self.on_status_changed: Optional[Callable[[ServerStatus], None]] = None
        self.on_session_isolated: Optional[Callable[[str, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def set_status_changed_callback(self, callback: Callable[[ServerStatus], None]) -> None:
        """设置状态变化回调
        
        Args:
            callback: 回调函数
        """
        self.on_status_changed = callback
    
    def set_session_isolated_callback(self, callback: Callable[[str, int], None]) -> None:
        """设置会话隔离回调
        
        Args:
            callback: 回调函数
        """
        self.on_session_isolated = callback
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """设置错误回调
        
        Args:
            callback: 回调函数
        """
        self.on_error = callback
    
    def _set_status(self, status: ServerStatus) -> None:
        """设置状态
        
        Args:
            status: 新状态
        """
        self.status = status
        if self.on_status_changed:
            self.on_status_changed(status)
    
    def _set_error(self, error_message: str) -> None:
        """设置错误
        
        Args:
            error_message: 错误消息
        """
        self.error_message = error_message
        self._set_status(ServerStatus.ERROR)
        if self.on_error:
            self.on_error(error_message)
    
    def is_port_available(self, port: int) -> bool:
        """检查端口是否可用
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否可用
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((self.config.host, port))
                return result != 0
        except Exception:
            return False
    
    def find_available_port(self, start_port: int = 8123, max_attempts: int = 100) -> int:
        """查找可用端口
        
        Args:
            start_port: 起始端口
            max_attempts: 最大尝试次数
            
        Returns:
            int: 可用端口
        """
        for port in range(start_port, start_port + max_attempts):
            if self.is_port_available(port):
                return port
        raise RuntimeError(f"无法在 {start_port}-{start_port + max_attempts} 范围内找到可用端口")
    
    async def start_server(self, session_id: Optional[str] = None) -> bool:
        """启动服务器
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功启动
        """
        if self.status != ServerStatus.STOPPED:
            return False
        
        try:
            self._set_status(ServerStatus.STARTING)
            
            # 如果指定了会话ID，启用会话隔离
            if session_id:
                isolated_port = self.find_available_port(self.config.port + 1)
                self.session_isolation[session_id] = isolated_port
                self.config.session_id = session_id
                self.config.port = isolated_port
                
                if self.on_session_isolated:
                    self.on_session_isolated(session_id, isolated_port)
            
            # 检查端口是否可用
            if not self.is_port_available(self.config.port):
                self._set_error(f"端口 {self.config.port} 已被占用")
                return False
            
            # 启动工作流Studio服务器
            cmd = [
                "python", "-m", "workflow.studio",
                "--host", self.config.host,
                "--port", str(self.config.port)
            ]
            
            if self.config.session_id:
                cmd.extend(["--session-id", self.config.session_id])
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务器启动
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < self.config.timeout:
                if self.process.poll() is not None:
                    # 进程已退出
                    stderr = self.process.stderr.read() if self.process.stderr else ""
                    self._set_error(f"服务器启动失败: {stderr}")
                    return False
                
                if self.is_port_available(self.config.port):
                    # 端口仍然可用，继续等待
                    await asyncio.sleep(0.5)
                    continue
                
                # 端口被占用，说明服务器已启动
                break
            else:
                self._set_error("服务器启动超时")
                return False
            
            self._set_status(ServerStatus.RUNNING)
            self.start_time = datetime.now()
            return True
            
        except Exception as e:
            self._set_error(f"启动服务器时发生错误: {str(e)}")
            return False
    
    async def stop_server(self) -> bool:
        """停止服务器
        
        Returns:
            bool: 是否成功停止
        """
        if self.status != ServerStatus.RUNNING:
            return False
        
        try:
            self._set_status(ServerStatus.STOPPING)
            
            if self.process:
                self.process.terminate()
                
                # 等待进程结束
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                
                self.process = None
            
            self._set_status(ServerStatus.STOPPED)
            self.start_time = None
            return True
            
        except Exception as e:
            self._set_error(f"停止服务器时发生错误: {str(e)}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息
        
        Returns:
            Dict[str, Any]: 服务器信息
        """
        info = {
            "status": self.status.value,
            "host": self.config.host,
            "port": self.config.port,
            "base_url": self.config.base_url,
            "session_id": self.config.session_id,
            "session_isolation": dict(self.session_isolation)
        }
        
        if self.start_time:
            info["uptime"] = (datetime.now() - self.start_time).total_seconds()
        
        if self.error_message:
            info["error"] = self.error_message
        
        return info
    
    async def check_server_health(self) -> bool:
        """检查服务器健康状态
        
        Returns:
            bool: 是否健康
        """
        if self.status != ServerStatus.RUNNING:
            return False
        
        try:
            # 尝试访问健康检查端点
            response = requests.get(
                f"{self.config.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False


class StudioManagerPanel:
    """Studio管理器面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.server_manager = StudioServerManager()
        self.show_details = False
        
        # 设置回调
        self.server_manager.set_status_changed_callback(self._on_status_changed)
        self.server_manager.set_session_isolated_callback(self._on_session_isolated)
        self.server_manager.set_error_callback(self._on_error)
        
        # 外部回调
        self.on_server_action: Optional[Callable[[str], None]] = None
    
    def set_server_action_callback(self, callback: Callable[[str], None]) -> None:
        """设置服务器动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_server_action = callback
    
    def _on_status_changed(self, status: ServerStatus) -> None:
        """状态变化处理
        
        Args:
            status: 新状态
        """
        if self.on_server_action:
            self.on_server_action(f"status_changed:{status.value}")
    
    def _on_session_isolated(self, session_id: str, port: int) -> None:
        """会话隔离处理
        
        Args:
            session_id: 会话ID
            port: 端口
        """
        if self.on_server_action:
            self.on_server_action(f"session_isolated:{session_id}:{port}")
    
    def _on_error(self, error_message: str) -> None:
        """错误处理
        
        Args:
            error_message: 错误消息
        """
        if self.on_server_action:
            self.on_server_action(f"error:{error_message}")
    
    async def start_server(self, session_id: Optional[str] = None) -> bool:
        """启动服务器
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功启动
        """
        return await self.server_manager.start_server(session_id)
    
    async def stop_server(self) -> bool:
        """停止服务器
        
        Returns:
            bool: 是否成功停止
        """
        return await self.server_manager.stop_server()
    
    def toggle_details(self) -> None:
        """切换详情显示"""
        self.show_details = not self.show_details
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "s":
            return "START_SERVER"
        elif key == "t":
            return "STOP_SERVER"
        elif key == "r":
            return "RESTART_SERVER"
        elif key == "d":
            self.toggle_details()
        elif key == "h":
            return "CHECK_HEALTH"
        
        return None
    
    def render(self) -> Panel:
        """渲染管理器面板
        
        Returns:
            Panel: 管理器面板
        """
        server_info = self.server_manager.get_server_info()
        
        # 创建状态信息
        status_text = Text()
        status_text.append("服务器状态: ", style="bold")
        
        status_styles = {
            ServerStatus.STOPPED.value: "red",
            ServerStatus.STARTING.value: "yellow",
            ServerStatus.RUNNING.value: "green",
            ServerStatus.STOPPING.value: "orange3",
            ServerStatus.ERROR.value: "red"
        }
        
        status_style = status_styles.get(server_info["status"], "white")
        status_text.append(server_info["status"].upper(), style=status_style)
        
        # 添加基本信息
        status_text.append(f"\\n主机: {server_info['host']}")
        status_text.append(f"\\n端口: {server_info['port']}")
        status_text.append(f"\\n地址: {server_info['base_url']}")
        
        if server_info.get("session_id"):
            status_text.append(f"\\n会话ID: {server_info['session_id'][:8]}...")
        
        if server_info.get("uptime"):
            uptime = server_info["uptime"]
            minutes, seconds = divmod(int(uptime), 60)
            status_text.append(f"\\n运行时间: {minutes}分{seconds}秒")
        
        # 添加错误信息
        if server_info.get("error"):
            status_text.append(f"\\n错误: {server_info['error']}", style="red")
        
        # 添加会话隔离信息
        if server_info.get("session_isolation"):
            status_text.append("\\n\\n会话隔离:")
            for session_id, port in server_info["session_isolation"].items():
                status_text.append(f"\\n  {session_id[:8]}... -> 端口 {port}")
        
        # 添加操作说明
        status_text.append("\\n\\n可用操作:")
        status_text.append("\\n  [S] 启动服务器")
        status_text.append("\\n  [T] 停止服务器")
        status_text.append("\\n  [R] 重启服务器")
        status_text.append("\\n  [H] 检查健康状态")
        status_text.append("\\n  [D] 切换详情显示")
        
        # 创建控制按钮表格
        if self.show_details:
            control_table = Table(
                title="详细配置",
                show_header=True,
                header_style="bold cyan",
                border_style="blue"
            )
            control_table.add_column("配置项", style="bold")
            control_table.add_column("值", style="white")
            
            config_dict = self.server_manager.config.to_dict()
            for key, value in config_dict.items():
                control_table.add_row(key, str(value))
            
            content = Table.grid()
            content.add_column()
            content.add_row(status_text)
            content.add_row("")
            content.add_row(control_table)
        else:
            content = status_text
        
        return Panel(
            content,
            title="工作流Studio管理器",
            border_style="cyan",
            padding=(1, 1)
        )