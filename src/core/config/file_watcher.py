"""配置文件监听器

为配置系统提供文件变化监听功能，支持自动重载配置。
"""

import os
import time
import threading
from typing import Callable, Dict, List, Optional, Any, TYPE_CHECKING
from pathlib import Path

from src.interfaces.configuration import ConfigError

# 仅在类型检查时导入，避免循环导入
if TYPE_CHECKING:
    from .config_manager import ConfigManager


class ConfigFileWatcher:
    """配置文件监听器"""
    
    def __init__(
        self,
        config_manager: 'ConfigManager',
        watch_path: Optional[str] = None,
        patterns: Optional[List[str]] = None
    ):
        """初始化配置文件监听器
        
        Args:
            config_manager: 配置管理器实例
            watch_path: 监听路径，默认使用配置管理器的基础路径
            patterns: 文件模式列表，默认监听YAML文件
        """
        self.config_manager = config_manager
        self.watch_path = Path(watch_path or config_manager.base_path)
        self.patterns = patterns or ["*.yaml", "*.yml"]
        self.callbacks: Dict[str, List[Callable[[str, Dict[str, Any]], None]]] = {}
        self._lock = threading.RLock()
        self._is_watching = False
        
        # 使用通用文件监听器
        from src.core.common.utils.file_watcher import FileWatcher
        self._file_watcher = FileWatcher(str(self.watch_path), self.patterns)
        self._file_watcher.add_callback('*', self._handle_file_change)
        
    def start(self) -> None:
        """开始监听配置文件变化"""
        with self._lock:
            if self._is_watching:
                return  # 已经在监听
                
            if not self.watch_path.exists():
                raise ConfigError(f"监听路径不存在: {self.watch_path}")
            
            # 使用通用文件监听器
            self._file_watcher.start()
            self._is_watching = True
            
    def stop(self) -> None:
        """停止监听配置文件变化"""
        with self._lock:
            # 使用通用文件监听器
            self._file_watcher.stop()
            self._is_watching = False
            
    def add_callback(
        self, 
        pattern: str, 
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """添加配置变化回调
        
        Args:
            pattern: 文件模式（如 "*.yaml"）
            callback: 回调函数，接收文件路径和配置数据
        """
        with self._lock:
            if pattern not in self.callbacks:
                self.callbacks[pattern] = []
            self.callbacks[pattern].append(callback)
            
    def remove_callback(
        self, 
        pattern: str, 
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """移除配置变化回调
        
        Args:
            pattern: 文件模式
            callback: 回调函数
        """
        with self._lock:
            if pattern in self.callbacks and callback in self.callbacks[pattern]:
                self.callbacks[pattern].remove(callback)
                
    def is_watching(self) -> bool:
        """检查是否正在监听"""
        return self._is_watching
        
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件
        
        Args:
            file_path: 变化的文件路径
        """
        try:
            file_path_obj = Path(file_path)
            
            # 检查文件是否匹配监听模式
            matched_patterns = []
            
            for pattern in self.patterns:
                if file_path_obj.match(pattern):
                    matched_patterns.append(pattern)
                    
            if not matched_patterns:
                return
                
            # 获取相对路径
            try:
                rel_path = file_path_obj.relative_to(self.watch_path)
                config_path = str(rel_path).replace("\\", "/")
            except ValueError:
                # 文件不在监听路径下
                return
                
            # 尝试重新加载配置
            try:
                # 清除缓存
                self.config_manager.invalidate_cache(config_path)
                
                # 重新加载配置
                new_config = self.config_manager.load_config(config_path)
                
                # 调用匹配的回调
                for pattern in matched_patterns:
                    if pattern in self.callbacks:
                        for callback in self.callbacks[pattern]:
                            try:
                                callback(config_path, new_config)
                            except Exception as e:
                                print(f"配置变化回调执行失败: {e}")
                
                # 触发回调管理器
                if hasattr(self.config_manager, 'trigger_callbacks'):
                    # 获取旧配置（如果存在）
                    old_config = None
                    try:
                        old_config = self.config_manager._config_cache.get(config_path)
                    except Exception:
                        pass
                        
                    # 触发回调
                    self.config_manager.trigger_callbacks(
                        config_path, old_config, new_config, "file_watcher"
                    )
                            
            except Exception as e:
                print(f"重新加载配置失败 {config_path}: {e}")
                
        except Exception as e:
            print(f"处理配置文件变化失败 {file_path}: {e}")
            
    def __del__(self) -> None:
        """析构函数，确保停止监听"""
        self.stop()


# _ConfigFileHandler类已移除，因为使用通用文件监听器


# 便捷函数
def create_config_watcher(
    config_manager: 'ConfigManager',
    watch_path: Optional[str] = None,
    patterns: Optional[List[str]] = None
) -> 'ConfigFileWatcher':
    """创建配置文件监听器的便捷函数
    
    Args:
        config_manager: 配置管理器实例
        watch_path: 监听路径
        patterns: 文件模式列表
        
    Returns:
        配置文件监听器实例
    """
    return ConfigFileWatcher(config_manager, watch_path, patterns)