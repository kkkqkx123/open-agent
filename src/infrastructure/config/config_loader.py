"""配置加载器实现"""

import os
import re
import yaml
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, TypeVar
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..exceptions import ConfigurationError
from ..infrastructure_types import CheckResult
from .config_inheritance import ConfigInheritanceHandler
from .config_interfaces import IConfigLoader
from ..container_interfaces import ILifecycleAware

# 定义类型变量
ConfigValue = TypeVar("ConfigValue", Dict[str, Any], List[Any], str, Any)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化处理器"""

    def __init__(self, config_loader: "YamlConfigLoader") -> None:
        self.config_loader = config_loader
        self._last_processed: Dict[str, float] = {}  # 用于去重处理
        self._debounce_time = 0.1  # 100ms防抖时间
        self._manual_trigger = False  # 标记是否是手动触发

    def on_modified(self, event: Any) -> None:
        """文件修改事件处理"""
        if (
            not event.is_directory
            and isinstance(event.src_path, str)
            and event.src_path.endswith((".yaml", ".yml"))
        ):
            import time

            current_time = time.time()
            file_path = event.src_path

            # 如果是手动触发，则跳过自动处理
            if self._manual_trigger:
                self._manual_trigger = False
                return

            # 检查是否在防抖时间内已经处理过此文件
            if file_path in self._last_processed:
                if current_time - self._last_processed[file_path] < self._debounce_time:
                    return  # 忽略过于频繁的事件

            # 更新最后处理时间
            self._last_processed[file_path] = current_time
            self.config_loader._handle_file_change(event.src_path)

    def trigger_manual(self, file_path: str) -> None:
        """手动触发文件变化处理"""
        self._manual_trigger = True
        self.config_loader._handle_file_change(file_path)


class YamlConfigLoader(IConfigLoader, ILifecycleAware):
    """YAML配置加载器实现"""

    def __init__(self, base_path: str = "configs", enable_inheritance: bool = True) -> None:
        self.base_path = Path(base_path)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._observers: List[Any] = []
        self._callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._lock = threading.RLock()
        self._env_var_pattern = re.compile(r"\$\{([^}]+)\}")
        self._env_var_default_pattern = re.compile(r"\$\{([^:]+):([^}]*)\}")
        self._inheritance_handler = ConfigInheritanceHandler(self) if enable_inheritance else None

    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with self._lock:
            # 检查缓存中是否已有配置
            if config_path in self._configs:
                return self._configs[config_path]

            # 构建完整路径
            full_path = self.base_path / config_path

            # 检查文件是否存在
            if not full_path.exists():
                raise ConfigurationError(f"Configuration file not found: {full_path}")

            try:
                # 读取YAML文件
                with open(full_path, "r", encoding="utf-8") as f:
                    config: Dict[str, Any] = yaml.safe_load(f) or {}

                # 处理配置继承（如果启用）
                if self._inheritance_handler:
                    config = self._inheritance_handler.resolve_inheritance(config, full_path.parent)

                # 解析环境变量
                resolved_config = self.resolve_env_vars(config)

                # 缓存配置
                self._configs[config_path] = resolved_config

                return resolved_config
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to load {config_path}: {e}")

    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置，如果不存在则返回None"""
        with self._lock:
            return self._configs.get(config_path)

    def reload(self) -> None:
        """重新加载所有配置"""
        with self._lock:
            # 重新加载所有缓存的配置
            for config_path in list(self._configs.keys()):
                try:
                    # 先从缓存中移除，这样load会重新读取文件
                    del self._configs[config_path]
                    # 重新加载
                    self.load(config_path)
                except ConfigurationError as e:
                    # 记录错误但继续加载其他配置
                    print(f"Warning: Failed to reload {config_path}: {e}")

    def watch_for_changes(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """监听配置变化"""
        with self._lock:
            self._callbacks.append(callback)

            # 如果还没有观察者，创建一个
            if not self._observers:
                observer = Observer()
                observer.schedule(
                    ConfigFileHandler(self), str(self.base_path), recursive=True
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

    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""

        def _resolve_recursive(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: _resolve_recursive(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_resolve_recursive(item) for item in value]
            elif isinstance(value, str):
                return self._resolve_env_var_string(value)
            else:
                return value

        result = _resolve_recursive(config)
        # 确保返回类型是 Dict[str, Any]
        assert isinstance(result, dict)
        return result

    def _resolve_env_var_string(self, text: str) -> str:
        """解析字符串中的环境变量"""
        import re
        from typing import Any

        # 使用单一正则表达式匹配所有环境变量（包括带默认值的）
        def replace_env_var(match: Any) -> str:
            var_expr = match.group(1)

            # 检查是否包含默认值
            if ":" in var_expr:
                var_name, default_value = var_expr.split(":", 1)
                return os.getenv(var_name, default_value)
            else:
                # 普通环境变量
                value = os.getenv(var_expr)
                if value is None:
                    raise ConfigurationError(
                        f"Environment variable not found: {var_expr}"
                    )
                return value

        # 使用单一模式匹配所有环境变量
        env_pattern = re.compile(r"\$\{([^}]+)\}")
        text = env_pattern.sub(replace_env_var, text)

        return text

    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件"""
        try:
            # 获取相对路径
            rel_path = Path(file_path).relative_to(self.base_path)
            config_path = str(rel_path).replace("\\", "/")

            # 重新加载配置
            # 先从缓存中移除，确保重新加载
            if config_path in self._configs:
                del self._configs[config_path]
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

    def validate_config_structure(
        self, config: Dict[str, Any], required_keys: List[str]
    ) -> CheckResult:
        """验证配置结构"""
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            return CheckResult(
                component="config_structure",
                status="ERROR",
                message=f"Missing required keys: {', '.join(missing_keys)}",
                details={"missing_keys": missing_keys},
            )

        return CheckResult(
            component="config_structure",
            status="PASS",
            message="Configuration structure is valid",
        )

    def initialize(self) -> None:
        """初始化配置加载器"""
        # 配置加载器在创建时已经初始化，这里可以添加额外的初始化逻辑
        pass
    
    def start(self) -> None:
        """启动配置加载器"""
        # 开始监听配置文件变化
        if not self._observers:
            self.watch_for_changes(lambda path, config: None)
    
    def stop(self) -> None:
        """停止配置加载器"""
        # 停止监听配置文件变化
        self.dispose()
    
    def dispose(self) -> None:
        """释放配置加载器资源"""
        # 停止监听并清理资源
        self.stop_watching()
        self.clear_cache()
    def __del__(self) -> None:
        """析构函数，确保停止文件监听"""
        self.dispose()
