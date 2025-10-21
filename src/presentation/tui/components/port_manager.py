"""端口配置管理组件

包含端口分配、冲突检测和自动管理功能
"""

from typing import Optional, Dict, Any, List, Tuple, Callable
from datetime import datetime
import socket
import json
from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree

from ..config import TUIConfig


class PortInfo:
    """端口信息"""
    
    def __init__(
        self,
        port: int,
        service: str,
        session_id: Optional[str] = None,
        status: str = "free",
        allocated_time: Optional[datetime] = None
    ):
        self.port = port
        self.service = service
        self.session_id = session_id
        self.status = status  # free, used, reserved
        self.allocated_time = allocated_time or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 端口信息字典
        """
        return {
            "port": self.port,
            "service": self.service,
            "session_id": self.session_id,
            "status": self.status,
            "allocated_time": self.allocated_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortInfo":
        """从字典创建端口信息
        
        Args:
            data: 端口信息字典
            
        Returns:
            PortInfo: 端口信息对象
        """
        allocated_time = None
        if data.get("allocated_time"):
            try:
                allocated_time = datetime.fromisoformat(data["allocated_time"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            port=data["port"],
            service=data["service"],
            session_id=data.get("session_id"),
            status=data.get("status", "free"),
            allocated_time=allocated_time
        )


class PortManager:
    """端口管理器"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("./port_config.json")
        self.ports: Dict[int, PortInfo] = {}
        self.port_ranges = {
            "studio": (8123, 8223),
            "api": (8224, 8324),
            "debug": (8325, 8425)
        }
        self.default_ports = {
            "studio": 8123,
            "api": 8224,
            "debug": 8325
        }
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> None:
        """加载端口配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.ports = {}
                for port_data in data.get("ports", []):
                    port_info = PortInfo.from_dict(port_data)
                    self.ports[port_info.port] = port_info
                
                # 加载端口范围配置
                if "port_ranges" in data:
                    self.port_ranges.update(data["port_ranges"])
                
                # 加载默认端口配置
                if "default_ports" in data:
                    self.default_ports.update(data["default_ports"])
                    
            except Exception as e:
                print(f"加载端口配置失败: {e}")
    
    def save_config(self) -> None:
        """保存端口配置"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "ports": [port_info.to_dict() for port_info in self.ports.values()],
                "port_ranges": self.port_ranges,
                "default_ports": self.default_ports,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存端口配置失败: {e}")
    
    def is_port_available(self, port: int) -> bool:
        """检查端口是否可用
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否可用
        """
        # 检查端口是否在管理范围内
        if not self._is_port_in_range(port):
            return False
        
        # 检查端口是否已被分配
        if port in self.ports and self.ports[port].status == "used":
            return False
        
        # 检查端口是否被系统占用
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                return result != 0
        except Exception:
            return False
    
    def _is_port_in_range(self, port: int) -> bool:
        """检查端口是否在管理范围内
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否在范围内
        """
        for start_port, end_port in self.port_ranges.values():
            if start_port <= port <= end_port:
                return True
        return False
    
    def allocate_port(
        self,
        service: str,
        session_id: Optional[str] = None,
        preferred_port: Optional[int] = None
    ) -> Optional[int]:
        """分配端口
        
        Args:
            service: 服务名称
            session_id: 会话ID
            preferred_port: 首选端口
            
        Returns:
            Optional[int]: 分配的端口号
        """
        # 如果指定了首选端口，尝试分配
        if preferred_port:
            if self.is_port_available(preferred_port):
                self._mark_port_used(preferred_port, service, session_id)
                return preferred_port
        
        # 获取服务的端口范围
        port_range = self.port_ranges.get(service)
        if not port_range:
            return None
        
        start_port, end_port = port_range
        
        # 在范围内查找可用端口
        for port in range(start_port, end_port + 1):
            if self.is_port_available(port):
                self._mark_port_used(port, service, session_id)
                return port
        
        return None
    
    def _mark_port_used(self, port: int, service: str, session_id: Optional[str] = None) -> None:
        """标记端口为已使用
        
        Args:
            port: 端口号
            service: 服务名称
            session_id: 会话ID
        """
        port_info = PortInfo(
            port=port,
            service=service,
            session_id=session_id,
            status="used"
        )
        self.ports[port] = port_info
        self.save_config()
    
    def release_port(self, port: int) -> bool:
        """释放端口
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否成功释放
        """
        if port in self.ports:
            self.ports[port].status = "free"
            self.ports[port].session_id = None
            self.save_config()
            return True
        return False
    
    def release_session_ports(self, session_id: str) -> List[int]:
        """释放会话的所有端口
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[int]: 释放的端口列表
        """
        released_ports = []
        for port_info in self.ports.values():
            if port_info.session_id == session_id and port_info.status == "used":
                port_info.status = "free"
                port_info.session_id = None
                released_ports.append(port_info.port)
        
        if released_ports:
            self.save_config()
        
        return released_ports
    
    def get_port_info(self, port: int) -> Optional[PortInfo]:
        """获取端口信息
        
        Args:
            port: 端口号
            
        Returns:
            Optional[PortInfo]: 端口信息
        """
        return self.ports.get(port)
    
    def get_service_ports(self, service: str) -> List[PortInfo]:
        """获取服务的所有端口
        
        Args:
            service: 服务名称
            
        Returns:
            List[PortInfo]: 端口信息列表
        """
        return [port_info for port_info in self.ports.values() if port_info.service == service]
    
    def get_session_ports(self, session_id: str) -> List[PortInfo]:
        """获取会话的所有端口
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[PortInfo]: 端口信息列表
        """
        return [port_info for port_info in self.ports.values() if port_info.session_id == session_id]
    
    def get_used_ports(self) -> List[PortInfo]:
        """获取所有已使用的端口
        
        Returns:
            List[PortInfo]: 端口信息列表
        """
        return [port_info for port_info in self.ports.values() if port_info.status == "used"]
    
    def get_available_ports(self, service: str) -> List[int]:
        """获取服务的可用端口列表
        
        Args:
            service: 服务名称
            
        Returns:
            List[int]: 可用端口列表
        """
        port_range = self.port_ranges.get(service)
        if not port_range:
            return []
        
        start_port, end_port = port_range
        available_ports = []
        
        for port in range(start_port, end_port + 1):
            if self.is_port_available(port):
                available_ports.append(port)
        
        return available_ports
    
    def cleanup_expired_ports(self, max_age_hours: int = 24) -> List[int]:
        """清理过期端口
        
        Args:
            max_age_hours: 最大年龄（小时）
            
        Returns:
            List[int]: 清理的端口列表
        """
        cleaned_ports = []
        current_time = datetime.now()
        
        for port_info in list(self.ports.values()):
            if (port_info.status == "used" and 
                port_info.session_id and
                (current_time - port_info.allocated_time).total_seconds() > max_age_hours * 3600):
                
                port_info.status = "free"
                port_info.session_id = None
                cleaned_ports.append(port_info.port)
        
        if cleaned_ports:
            self.save_config()
        
        return cleaned_ports
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取端口统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_ports = sum(end - start + 1 for start, end in self.port_ranges.values())
        used_ports = len(self.get_used_ports())
        free_ports = total_ports - used_ports
        
        service_stats = {}
        for service in self.port_ranges.keys():
            service_ports = self.get_service_ports(service)
            service_stats[service] = {
                "total": len(service_ports),
                "used": len([p for p in service_ports if p.status == "used"]),
                "free": len([p for p in service_ports if p.status == "free"])
            }
        
        return {
            "total_ports": total_ports,
            "used_ports": used_ports,
            "free_ports": free_ports,
            "usage_percentage": (used_ports / total_ports * 100) if total_ports > 0 else 0,
            "service_stats": service_stats
        }


class PortManagerPanel:
    """端口管理器面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.port_manager = PortManager()
        self.show_details = False
        self.selected_service = "studio"
        
        # 外部回调
        self.on_port_action: Optional[Callable[[str, Any], None]] = None
    
    def set_port_action_callback(self, callback: Callable[[str, Any], None]) -> None:
        """设置端口动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_port_action = callback
    
    def toggle_details(self) -> None:
        """切换详情显示"""
        self.show_details = not self.show_details
    
    def select_service(self, service: str) -> None:
        """选择服务
        
        Args:
            service: 服务名称
        """
        if service in self.port_manager.port_ranges:
            self.selected_service = service
    
    def allocate_port(self, session_id: Optional[str] = None) -> Optional[int]:
        """分配端口
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[int]: 分配的端口
        """
        port = self.port_manager.allocate_port(self.selected_service, session_id)
        if port and self.on_port_action:
            self.on_port_action("port_allocated", {
                "service": self.selected_service,
                "port": port,
                "session_id": session_id
            })
        return port
    
    def release_port(self, port: int) -> bool:
        """释放端口
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否成功释放
        """
        success = self.port_manager.release_port(port)
        if success and self.on_port_action:
            self.on_port_action("port_released", {"port": port})
        return success
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "a":
            port = self.allocate_port()
            if port:
                return f"PORT_ALLOCATED:{port}"
            else:
                return "PORT_ALLOCATION_FAILED"
        elif key == "c":
            self.port_manager.cleanup_expired_ports()
            return "PORTS_CLEANED"
        elif key == "d":
            self.toggle_details()
        elif key == "1":
            self.select_service("studio")
        elif key == "2":
            self.select_service("api")
        elif key == "3":
            self.select_service("debug")
        
        return None
    
    def render(self) -> Panel:
        """渲染端口管理面板
        
        Returns:
            Panel: 端口管理面板
        """
        # 获取统计信息
        stats = self.port_manager.get_statistics()
        
        # 创建统计信息
        stats_text = Text()
        stats_text.append("端口统计:\\n", style="bold")
        stats_text.append(f"总端口数: {stats['total_ports']}\\n")
        stats_text.append(f"已使用: {stats['used_ports']}\\n")
        stats_text.append(f"可用: {stats['free_ports']}\\n")
        stats_text.append(f"使用率: {stats['usage_percentage']:.1f}%\\n\\n")
        
        # 服务统计
        stats_text.append("服务统计:\\n", style="bold")
        for service, service_stats in stats["service_stats"].items():
            marker = "●" if service == self.selected_service else "○"
            stats_text.append(f"{marker} {service}: {service_stats['used']}/{service_stats['total']}\\n")
        
        # 操作说明
        stats_text.append("\\n可用操作:\\n")
        stats_text.append("  [A] 分配端口\\n")
        stats_text.append("  [C] 清理过期端口\\n")
        stats_text.append("  [D] 切换详情显示\\n")
        stats_text.append("  [1/2/3] 选择服务")
        
        if self.show_details:
            # 显示详细信息
            used_ports = self.port_manager.get_used_ports()
            if used_ports:
                details_table = Table(
                    title="已分配端口",
                    show_header=True,
                    header_style="bold cyan",
                    border_style="blue"
                )
                details_table.add_column("端口", style="bold")
                details_table.add_column("服务", style="green")
                details_table.add_column("会话ID", style="yellow")
                details_table.add_column("分配时间", style="white")
                
                for port_info in used_ports:
                    session_id = port_info.session_id[:8] + "..." if port_info.session_id else "无"
                    time_str = port_info.allocated_time.strftime("%m-%d %H:%M")
                    
                    details_table.add_row(
                        str(port_info.port),
                        port_info.service,
                        session_id,
                        time_str
                    )
                
                content = Table.grid()
                content.add_column()
                content.add_row(stats_text)
                content.add_row("")
                content.add_row(details_table)
            else:
                content = stats_text
        else:
            content = stats_text
        
        return Panel(
            content,
            title=f"端口管理器 - {self.selected_service}",
            border_style="green",
            padding=(1, 1)
        )