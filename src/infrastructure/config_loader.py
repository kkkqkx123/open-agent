"""配置加载器实现"""

import os
import re
import yaml  # type: ignore
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .exceptions import ConfigurationError
from .types import CheckResult


class IConfigLoader(ABC):
    """配置加载器接口"""
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载所有配置"""
        pass
    
    @abstractmethod
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听配置变化"""
        pass
    
    @abstractmethod
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass
    
    @abstractmethod
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件"""
        pass


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化处理器"""
    
    def __init__(self, config_loader: 'YamlConfigLoader') -> None:
        self.config_loader = config_loader
    
    def on_modified(self, event) -> None:
        """文件修改事件处理"""
        if not event.is_directory and isinstance(event.src_path, str) and event.src_path.endswith(('.yaml', '.yml')):
            self.config_loader._handle_file_change(event.src_path)


class YamlConfigLoader(IConfigLoader):
    """YAML配置加载器实现"""
    
    def __init__(self, base_path: str = "configs") -> None:
        self.base_path = Path(base_path)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._observers: List[Any] = []
        self._callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._lock = threading.RLock()
        self._env_var_pattern = re.compile(r'\$\{([^}]+)\}')
        self._env_var_default_pattern = re.compile(r'\$\{([^:]+):([^}]*)\}')
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with self._lock:
            # 构建完整路径
            full_path = self.base_path / config_path
            
            # 检查文件是否存在
            if not full_path.exists():
                raise ConfigurationError(f"Configuration file not found: {full_path}")
            
            try:
                # 读取YAML文件
                with open(full_path, 'r', encoding='utf-8') as f:
                    config: Dict[str, Any] = yaml.safe_load(f) or {}
                
                # 解析环境变量
                resolved_config = self.resolve_env_vars(config)
                
                # 缓存配置
                self._configs[config_path] = resolved_config
                
                return resolved_config
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to load {config_path}: {e}")
    
    def reload(self) -> None:
        """重新加载所有配置"""
        with self._lock:
            # 重新加载所有缓存的配置
            for config_path in list(self._configs.keys()):
                try:
                    self.load(config_path)
                except ConfigurationError as e:
                    # 记录错误但继续加载其他配置
                    print(f"Warning: Failed to reload {config_path}: {e}")
    
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听配置变化"""
        with self._lock:
            self._callbacks.append(callback)
            
            # 如果还没有观察者，创建一个
            if not self._observers:
                observer = Observer()
                observer.schedule(
                    ConfigFileHandler(self),
                    str(self.base_path),
                    recursive=True
                )
                observer.start()
                self._observers.append(observer)
    
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        with self._lock:
            for observer in self._observers:
                observer.stop()
                observer.join()
            self._observers.clear()
            self._callbacks.clear()
    
    def resolve_env_vars(self, config: Any) -> Any:
        """解析环境变量"""
        if isinstance(config, dict):
            return {k: self.resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self.resolve_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._resolve_env_var_string(config)
        else:
            return config
    
    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量"""
        # 首先处理带默认值的环境变量 ${VAR:default}
        def replace_with_default(match: Any) -> str:
            var_name = match.group(1)
            default_value = match.group(2)
            return os.getenv(var_name, default_value)
        
        text = self._env_var_default_pattern.sub(replace_with_default, text)
        
        # 然后处理普通环境变量 ${VAR}
        def replace_simple(match: Any) -> str:
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value is None:
                raise ConfigurationError(f"Environment variable not found: {var_name}")
            return value
        
        return self._env_var_pattern.sub(replace_simple, text)
    
    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件"""
        try:
            # 获取相对路径
            rel_path = Path(file_path).relative_to(self.base_path)
            config_path = str(rel_path).replace('\\', '/')
            
            # 重新加载配置
            new_config = self.load(config_path)
            
            # 通知回调
            for callback in self._callbacks:
                try:
                    callback(config_path, new_config)
                except Exception as e:
                    print(f"Warning: Config change callback failed: {e}")
        
        except Exception as e:
            print(f"Warning: Failed to handle file change {file_path}: {e}")
    
    def get_cached_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存的配置"""
        with self._lock:
            return self._configs.get(config_path)
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        with self._lock:
            self._configs.clear()
    
    def validate_config_structure(self, config: Dict[str, Any], required_keys: List[str]) -> CheckResult:
        """验证配置结构"""
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            return CheckResult(
                component="config_structure",
                status="ERROR",
                message=f"Missing required keys: {', '.join(missing_keys)}",
                details={"missing_keys": missing_keys}
            )
        
        return CheckResult(
            component="config_structure",
            status="PASS",
            message="Configuration structure is valid"
        )
    
    def __del__(self) -> None:
        """析构函数，确保停止文件监听"""
        self.stop_watching()