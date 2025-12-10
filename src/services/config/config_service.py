"""配置服务

提供高级配置管理功能，包括配置缓存、变更通知、错误恢复等。
"""

import logging
import threading
from typing import Dict, Any, Optional, List, Callable, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from src.interfaces.configuration import IConfigManager, IConfigValidator, ConfigError
from src.interfaces.common_domain import ValidationResult
from src.core.config.config_manager import ConfigManager, get_default_manager


class ConfigChangeType(Enum):
    """配置变更类型"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RELOADED = "reloaded"


@dataclass
class ConfigChangeEvent:
    """配置变更事件"""
    config_path: str
    change_type: ConfigChangeType
    key_path: Optional[str] = None  # 变更的键路径，如 "database.host"
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigService:
    """高级配置管理服务
    
    提供配置缓存、变更通知、错误恢复等高级功能。
    """
    
    def __init__(self, config_manager: Optional[IConfigManager] = None):
        """初始化配置服务
        
        Args:
            config_manager: 配置管理器实例，如果为None则使用默认的ConfigManager
        """
        self.config_manager = config_manager or get_default_manager()
        self.logger = logging.getLogger(__name__)
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_lock = threading.RLock()
        
        # 变更回调
        self._change_callbacks: List[Callable[..., None]] = []
        self._callback_lock = threading.RLock()
        
        # 错误恢复
        self._error_recovery_enabled = True
        self._backup_configs: Dict[str, List[Dict[str, Any]]] = {}
        self._max_backups = 5
        
        # 监控配置
        self._watched_paths: Set[str] = set()
        self._watch_interval = 60  # 秒
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_stop_event = threading.Event()
    
    def load_config(self, config_path: str, use_cache: bool = True, force_reload: bool = False) -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            use_cache: 是否使用缓存
            force_reload: 是否强制重新加载
            
        Returns:
            配置字典
            
        Raises:
            ConfigError: 配置加载失败
        """
        config_path = str(Path(config_path).resolve())
        
        # 检查缓存
        if use_cache and not force_reload:
            with self._cache_lock:
                if config_path in self._config_cache:
                    self.logger.debug(f"从缓存加载配置: {config_path}")
                    return self._config_cache[config_path].copy()
        
        try:
            # 加载配置
            config = self.config_manager.load_config(config_path)
            
            # 创建备份
            if self._error_recovery_enabled:
                self._create_backup(config_path, config)
            
            # 更新缓存
            with self._cache_lock:
                self._config_cache[config_path] = config.copy()
                self._cache_timestamps[config_path] = datetime.now()
            
            # 触发变更事件
            if force_reload or config_path not in self._config_cache:
                self._notify_change(ConfigChangeEvent(
                    config_path=config_path,
                    change_type=ConfigChangeType.RELOADED,
                    new_value=config
                ))
            
            self.logger.info(f"配置加载成功: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"配置加载失败: {config_path}, 错误: {e}")
            
            # 尝试错误恢复
            if self._error_recovery_enabled:
                backup_config = self._get_backup_config(config_path)
                if backup_config:
                    self.logger.warning(f"使用备份配置: {config_path}")
                    return backup_config
            
            raise ConfigError(f"配置加载失败: {config_path}") from e
    
    def save_config(self, config_path: str, config: Dict[str, Any], create_backup: bool = True) -> None:
        """保存配置
        
        Args:
            config_path: 配置文件路径
            config: 配置字典
            create_backup: 是否创建备份
            
        Raises:
            ConfigError: 配置保存失败
        """
        config_path = str(Path(config_path).resolve())
        
        try:
            # 获取旧配置用于比较
            old_config = None
            if config_path in self._config_cache:
                old_config = self._config_cache[config_path]
            
            # 创建备份
            if create_backup and self._error_recovery_enabled:
                self._create_backup(config_path, config)
            
            # 保存配置
            self.config_manager.save_config(config, config_path)
            
            # 更新缓存
            with self._cache_lock:
                self._config_cache[config_path] = config.copy()
                self._cache_timestamps[config_path] = datetime.now()
            
            # 触发变更事件
            if old_config:
                self._detect_and_notify_changes(config_path, old_config, config)
            else:
                self._notify_change(ConfigChangeEvent(
                    config_path=config_path,
                    change_type=ConfigChangeType.ADDED,
                    new_value=config
                ))
            
            self.logger.info(f"配置保存成功: {config_path}")
            
        except Exception as e:
            self.logger.error(f"配置保存失败: {config_path}, 错误: {e}")
            raise ConfigError(f"配置保存失败: {config_path}") from e
    
    def validate_config(self, config: Dict[str, Any], validator: Optional[IConfigValidator] = None) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            validator: 验证器，如果为None则使用默认验证器
            
        Returns:
            验证结果
        """
        if validator:
            return validator.validate(config)
        else:
            # 使用默认验证器
            from src.infrastructure.config.validation import BaseConfigValidator
            default_validator = BaseConfigValidator()
            return default_validator.validate(config)
    
    def get_config_value(self, config_path: str, key_path: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            config_path: 配置文件路径
            key_path: 键路径，如 "database.host"
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.load_config(config_path)
        
        # 解析键路径
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config_value(self, config_path: str, key_path: str, value: Any, save: bool = True) -> None:
        """设置配置值
        
        Args:
            config_path: 配置文件路径
            key_path: 键路径，如 "database.host"
            value: 配置值
            save: 是否保存到文件
        """
        config = self.load_config(config_path)
        
        # 解析键路径
        keys = key_path.split('.')
        current = config
        
        # 导航到父级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置值
        old_value = current.get(keys[-1])
        current[keys[-1]] = value
        
        # 保存配置
        if save:
            self.save_config(config_path, config)
        else:
            # 只更新缓存
            with self._cache_lock:
                self._config_cache[config_path] = config.copy()
                self._cache_timestamps[config_path] = datetime.now()
            
            # 触发变更事件
            self._notify_change(ConfigChangeEvent(
                config_path=config_path,
                change_type=ConfigChangeType.MODIFIED,
                key_path=key_path,
                old_value=old_value,
                new_value=value
            ))
    
    def add_change_callback(self, callback: Callable[..., None]) -> None:
        """添加配置变更回调
        
        Args:
            callback: 回调函数
        """
        with self._callback_lock:
            self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[..., None]) -> None:
        """移除配置变更回调
        
        Args:
            callback: 回调函数
        """
        with self._callback_lock:
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)
    
    def clear_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有缓存
        """
        with self._cache_lock:
            if config_path:
                self._config_cache.pop(config_path, None)
                self._cache_timestamps.pop(config_path, None)
            else:
                self._config_cache.clear()
                self._cache_timestamps.clear()
    
    def enable_error_recovery(self, enabled: bool = True) -> None:
        """启用/禁用错误恢复
        
        Args:
            enabled: 是否启用
        """
        self._error_recovery_enabled = enabled
    
    def start_watching(self, config_path: str) -> None:
        """开始监控配置文件变更
        
        Args:
            config_path: 配置文件路径
        """
        config_path = str(Path(config_path).resolve())
        self._watched_paths.add(config_path)
        
        # 启动监控线程
        if not self._watch_thread or not self._watch_thread.is_alive():
            self._watch_stop_event.clear()
            self._watch_thread = threading.Thread(target=self._watch_configs, daemon=True)
            self._watch_thread.start()
    
    def stop_watching(self, config_path: Optional[str] = None) -> None:
        """停止监控配置文件变更
        
        Args:
            config_path: 配置文件路径，如果为None则停止所有监控
        """
        if config_path:
            self._watched_paths.discard(config_path)
        else:
            self._watched_paths.clear()
        
        # 停止监控线程
        if not self._watched_paths:
            self._watch_stop_event.set()
    
    def _create_backup(self, config_path: str, config: Dict[str, Any]) -> None:
        """创建配置备份
        
        Args:
            config_path: 配置文件路径
            config: 配置字典
        """
        if config_path not in self._backup_configs:
            self._backup_configs[config_path] = []
        
        backups = self._backup_configs[config_path]
        backups.append({
            'config': config.copy(),
            'timestamp': datetime.now()
        })
        
        # 限制备份数量
        if len(backups) > self._max_backups:
            backups.pop(0)
    
    def _get_backup_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取备份配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            备份配置字典，如果没有备份则返回None
        """
        backups = self._backup_configs.get(config_path, [])
        if backups:
            # 返回最新的备份
            return backups[-1]['config'].copy()
        return None
    
    def _notify_change(self, event: Any) -> None:
        """通知配置变更
        
        Args:
            event: 变更事件
        """
        with self._callback_lock:
            for callback in self._change_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"配置变更回调执行失败: {e}")
    
    def _detect_and_notify_changes(self, config_path: str, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """检测并通知配置变更
        
        Args:
            config_path: 配置文件路径
            old_config: 旧配置
            new_config: 新配置
        """
        # 简单的变更检测，可以优化为更精确的算法
        all_keys = set(self._flatten_dict(old_config).keys()) | set(self._flatten_dict(new_config).keys())
        
        for key in all_keys:
            old_value = self._get_nested_value(old_config, key)
            new_value = self._get_nested_value(new_config, key)
            
            if old_value != new_value:
                if old_value is None:
                    change_type = ConfigChangeType.ADDED
                elif new_value is None:
                    change_type = ConfigChangeType.DELETED
                else:
                    change_type = ConfigChangeType.MODIFIED
                
                self._notify_change(ConfigChangeEvent(
                    config_path=config_path,
                    change_type=change_type,
                    key_path=key,
                    old_value=old_value,
                    new_value=new_value
                ))
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """扁平化字典
        
        Args:
            d: 字典
            parent_key: 父键
            sep: 分隔符
            
        Returns:
            扁平化后的字典
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _get_nested_value(self, d: Dict[str, Any], key_path: str, sep: str = '.') -> Any:
        """获取嵌套值
        
        Args:
            d: 字典
            key_path: 键路径
            sep: 分隔符
            
        Returns:
            嵌套值
        """
        keys = key_path.split(sep)
        value = d
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    def _watch_configs(self) -> None:
        """监控配置文件变更"""
        while not self._watch_stop_event.is_set():
            try:
                for config_path in list(self._watched_paths):
                    if not self._watch_stop_event.is_set():
                        # 检查文件修改时间
                        path = Path(config_path)
                        if path.exists():
                            current_mtime = path.stat().st_mtime
                            cached_time = self._cache_timestamps.get(config_path)
                            
                            if not cached_time or current_mtime > cached_time.timestamp():
                                # 文件已修改，重新加载
                                try:
                                    self.load_config(config_path, force_reload=True)
                                except Exception as e:
                                    self.logger.error(f"监控重新加载配置失败: {config_path}, 错误: {e}")
                
                # 等待下次检查
                self._watch_stop_event.wait(self._watch_interval)
                
            except Exception as e:
                self.logger.error(f"配置监控线程异常: {e}")
                self._watch_stop_event.wait(self._watch_interval)