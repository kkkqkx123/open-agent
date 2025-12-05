"""配置热重载组件

包含配置文件监控、热重载和错误处理功能
"""

from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import asyncio
import yaml
import json
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree

from ..config import TUIConfig, ConfigManager


class ConfigFileWatcher:
    """TUI配置文件监控器（轮询方式）
    
    Note: 这是TUI特定的实现，使用轮询方式监控配置文件变化。
    通用的文件监听功能应使用 src.infrastructure.filesystem.file_watcher.FileWatcher
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.watched_files: Dict[str, float] = {}  # 文件路径 -> 最后修改时间
        self.is_watching = False
        self.watch_interval = 1.0  # 秒
        
        # 回调函数
        self.on_config_changed: Optional[Callable[[str], None]] = None
        self.on_watch_error: Optional[Callable[[str, Exception], None]] = None
    
    def set_config_changed_callback(self, callback: Callable[[str], None]) -> None:
        """设置配置变化回调
        
        Args:
            callback: 回调函数，参数为文件路径
        """
        self.on_config_changed = callback
    
    def set_watch_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """设置监控错误回调
        
        Args:
            callback: 回调函数，参数为文件路径和异常
        """
        self.on_watch_error = callback
    
    def add_watch_file(self, file_path: str) -> None:
        """添加监控文件
        
        Args:
            file_path: 文件路径
        """
        path = Path(file_path)
        if path.exists():
            self.watched_files[file_path] = path.stat().st_mtime
    
    def remove_watch_file(self, file_path: str) -> None:
        """移除监控文件
        
        Args:
            file_path: 文件路径
        """
        self.watched_files.pop(file_path, None)
    
    def start_watching(self) -> None:
        """开始监控"""
        self.is_watching = True
    
    def stop_watching(self) -> None:
        """停止监控"""
        self.is_watching = False
    
    def check_changes(self) -> List[str]:
        """检查文件变化
        
        Returns:
            List[str]: 发生变化的文件路径列表
        """
        changed_files = []
        
        for file_path, last_mtime in self.watched_files.items():
            try:
                path = Path(file_path)
                if path.exists():
                    current_mtime = path.stat().st_mtime
                    if current_mtime > last_mtime:
                        self.watched_files[file_path] = current_mtime
                        changed_files.append(file_path)
                else:
                    # 文件被删除
                    changed_files.append(file_path)
            except Exception as e:
                if self.on_watch_error:
                    self.on_watch_error(file_path, e)
        
        return changed_files
    
    async def watch_loop(self) -> None:
        """监控循环"""
        while self.is_watching:
            try:
                changed_files = self.check_changes()
                for file_path in changed_files:
                    if self.on_config_changed:
                        self.on_config_changed(file_path)
                
                await asyncio.sleep(self.watch_interval)
            except Exception as e:
                if self.on_watch_error:
                    self.on_watch_error("watch_loop", e)


class ConfigReloadManager:
    """配置重载管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.watcher = ConfigFileWatcher(config_manager)
        self.reload_history: List[Dict[str, Any]] = []
        self.max_history = 50
        
        # 设置监控回调
        self.watcher.set_config_changed_callback(self._on_config_changed)
        self.watcher.set_watch_error_callback(self._on_watch_error)
        
        # 外部回调
        self.on_config_reloaded: Optional[Callable[[str, TUIConfig], None]] = None
        self.on_reload_error: Optional[Callable[[str, Exception], None]] = None
    
    def set_config_reloaded_callback(self, callback: Callable[[str, TUIConfig], None]) -> None:
        """设置配置重载回调
        
        Args:
            callback: 回调函数，参数为文件路径和新配置
        """
        self.on_config_reloaded = callback
    
    def set_reload_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """设置重载错误回调
        
        Args:
            callback: 回调函数，参数为文件路径和异常
        """
        self.on_reload_error = callback
    
    def _on_config_changed(self, file_path: str) -> None:
        """配置变化处理
        
        Args:
            file_path: 文件路径
        """
        try:
            # 重新加载配置
            new_config = self.config_manager.load_config()
            
            # 记录重载历史
            self.reload_history.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "success": True,
                "error": None
            })
            
            # 限制历史记录数量
            if len(self.reload_history) > self.max_history:
                self.reload_history = self.reload_history[-self.max_history:]
            
            # 通知外部
            if self.on_config_reloaded:
                self.on_config_reloaded(file_path, new_config)
                
        except Exception as e:
            # 记录错误
            self.reload_history.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "success": False,
                "error": str(e)
            })
            
            # 通知外部
            if self.on_reload_error:
                self.on_reload_error(file_path, e)
    
    def _on_watch_error(self, file_path: str, error: Exception) -> None:
        """监控错误处理
        
        Args:
            file_path: 文件路径
            error: 异常
        """
        # 记录监控错误
        self.reload_history.append({
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "success": False,
            "error": f"监控错误: {str(error)}"
        })
    
    def start_monitoring(self, config_paths: List[str]) -> None:
        """开始监控配置文件
        
        Args:
            config_paths: 配置文件路径列表
        """
        # 添加监控文件
        for path in config_paths:
            self.watcher.add_watch_file(path)
        
        # 开始监控
        self.watcher.start_watching()
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self.watcher.stop_watching()
    
    def manual_reload(self) -> bool:
        """手动重载配置
        
        Returns:
            bool: 是否成功重载
        """
        try:
            old_config = self.config_manager.get_config()
            new_config = self.config_manager.load_config()
            
            # 记录手动重载
            self.reload_history.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": "手动重载",
                "success": True,
                "error": None
            })
            
            if self.on_config_reloaded:
                self.on_config_reloaded("手动重载", new_config)
            
            return True
        except Exception as e:
            # 记录错误
            self.reload_history.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": "手动重载",
                "success": False,
                "error": str(e)
            })
            
            if self.on_reload_error:
                self.on_reload_error("手动重载", e)
            
            return False
    
    def get_recent_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的重载历史
        
        Args:
            count: 返回数量
            
        Returns:
            List[Dict[str, Any]]: 历史记录列表
        """
        return self.reload_history[-count:] if self.reload_history else []
    
    def is_monitoring(self) -> bool:
        """检查是否正在监控
        
        Returns:
            bool: 是否正在监控
        """
        return self.watcher.is_watching
    
    def get_watched_files(self) -> List[str]:
        """获取监控的文件列表
        
        Returns:
            List[str]: 文件路径列表
        """
        return list(self.watcher.watched_files.keys())


class ConfigReloadPanel:
    """配置重载面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.config_manager = get_config_manager() if config else None
        self.reload_manager: Optional[ConfigReloadManager] = None
        self.show_history = False
        
        # 初始化重载管理器
        if self.config_manager:
            self.reload_manager = ConfigReloadManager(self.config_manager)
            self.reload_manager.set_config_reloaded_callback(self._on_config_reloaded)
            self.reload_manager.set_reload_error_callback(self._on_reload_error)
        
        # 外部回调
        self.on_config_updated: Optional[Callable[[TUIConfig], None]] = None
    
    def set_config_updated_callback(self, callback: Callable[[TUIConfig], None]) -> None:
        """设置配置更新回调
        
        Args:
            callback: 回调函数
        """
        self.on_config_updated = callback
    
    def _on_config_reloaded(self, file_path: str, new_config: TUIConfig) -> None:
        """配置重载处理
        
        Args:
            file_path: 文件路径
            new_config: 新配置
        """
        if self.on_config_updated:
            self.on_config_updated(new_config)
    
    def _on_reload_error(self, file_path: str, error: Exception) -> None:
        """重载错误处理
        
        Args:
            file_path: 文件路径
            error: 异常
        """
        # 可以添加错误处理逻辑
        pass
    
    def start_monitoring(self) -> None:
        """开始监控"""
        if self.reload_manager and self.config_manager:
            config_paths = [str(self.config_manager.config_path)]
            self.reload_manager.start_monitoring(config_paths)
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        if self.reload_manager:
            self.reload_manager.stop_monitoring()
    
    def manual_reload(self) -> bool:
        """手动重载
        
        Returns:
            bool: 是否成功重载
        """
        if self.reload_manager:
            return self.reload_manager.manual_reload()
        return False
    
    def toggle_history(self) -> None:
        """切换历史显示"""
        self.show_history = not self.show_history
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "r":
            if self.manual_reload():
                return "CONFIG_RELOADED"
            else:
                return "RELOAD_FAILED"
        elif key == "m":
            if self.reload_manager and self.reload_manager.is_monitoring():
                self.stop_monitoring()
                return "MONITORING_STOPPED"
            else:
                self.start_monitoring()
                return "MONITORING_STARTED"
        elif key == "h":
            self.toggle_history()
        
        return None
    
    def render(self) -> Panel:
        """渲染重载面板
        
        Returns:
            Panel: 重载面板
        """
        if self.show_history and self.reload_manager:
            # 显示历史记录
            history_table = self._render_history()
            return Panel(
                history_table,
                title="配置重载历史 (H=返回)",
                border_style="blue"
            )
        else:
            # 显示控制面板
            control_content = self._render_control_panel()
            return Panel(
                control_content,
                title="配置热重载 (R=重载, M=监控, H=历史)",
                border_style="green"
            )
    
    def _render_control_panel(self) -> Table:
        """渲染控制面板
        
        Returns:
            Table: 控制面板表格
        """
        table = Table.grid()
        table.add_column()
        
        # 监控状态
        if self.reload_manager:
            is_monitoring = self.reload_manager.is_monitoring()
            status_text = "监控中" if is_monitoring else "已停止"
            status_style = "green" if is_monitoring else "red"
            
            table.add_row(Text(f"监控状态: [{status_style}]{status_text}[/{status_style}]"))
            
            # 监控文件
            watched_files = self.reload_manager.get_watched_files()
            if watched_files:
                table.add_row("监控文件:")
                for file_path in watched_files:
                    table.add_row(f"  • {file_path}")
            else:
                table.add_row("无监控文件")
        
        table.add_row("")
        
        # 操作说明
        table.add_row("可用操作:")
        table.add_row("  [R] 手动重载配置")
        table.add_row("  [M] 开始/停止监控")
        table.add_row("  [H] 查看重载历史")
        
        return table
    
    def _render_history(self) -> Table:
        """渲染历史记录
        
        Returns:
            Table: 历史记录表格
        """
        table = Table(
            title="重载历史",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("时间", style="dim", width=8)
        table.add_column("文件", style="white")
        table.add_column("状态", style="bold", width=6)
        table.add_column("错误", style="red")
        
        if self.reload_manager:
            history = self.reload_manager.get_recent_history(20)
            for record in reversed(history):  # 最新的在前
                timestamp = record.get("timestamp", "")
                file_path = record.get("file_path", "")
                success = record.get("success", False)
                error = record.get("error", "")
                
                # 格式化时间
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except (ValueError, TypeError):
                    time_str = timestamp[:8] if timestamp else ""
                
                # 状态样式
                status_text = "成功" if success else "失败"
                status_style = "green" if success else "red"
                
                # 截断文件路径
                file_display = file_path.split('/')[-1] if '/' in file_path else file_path
                file_display = file_display[:20] + "..." if len(file_display) > 20 else file_display
                
                # 截断错误信息
                error_display = error[:30] + "..." if len(error) > 30 else error
                
                table.add_row(
                    time_str,
                    file_display,
                    f"[{status_style}]{status_text}[/{status_style}]",
                    error_display
                )
        
        return table


# 导入配置管理器函数
def get_config_manager() -> ConfigManager:
    """获取配置管理器实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    from ..config import get_config_manager as _get_config_manager
    return _get_config_manager()