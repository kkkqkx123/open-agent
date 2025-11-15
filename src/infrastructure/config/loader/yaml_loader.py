"""配置加载器实现"""

import os
import yaml
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, TypeVar
from pathlib import Path

from ...exceptions import ConfigurationError
from ...infrastructure_types import CheckResult
from ..interfaces import IConfigLoader
from ...container_interfaces import ILifecycleAware

# 定义类型变量
ConfigValue = TypeVar("ConfigValue", Dict[str, Any], List[Any], str, Any)


class YamlConfigLoader(IConfigLoader, ILifecycleAware):
    """YAML配置加载器实现 - 专注于文件加载和缓存"""

    def __init__(self, base_path: str = "configs") -> None:
        """初始化YAML配置加载器
        
        Args:
            base_path: 配置文件基础路径
        """
        self._base_path = Path(base_path)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    @property
    def base_path(self) -> Path:
        """获取配置基础路径"""
        return self._base_path

    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            ConfigurationError: 配置文件不存在或格式错误
        """
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

                # 缓存配置
                self._configs[config_path] = config

                return config
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to load {config_path}: {e}")

    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置，如果不存在则返回None
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典或None
        """
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
        """监听配置变化 - 已弃用，请使用FileWatcher
        
        Args:
            callback: 变化回调函数
            
        Raises:
            NotImplementedError: 此方法已弃用
        """
        raise NotImplementedError(
            "watch_for_changes is deprecated. Please use FileWatcher instead."
        )

    def stop_watching(self) -> None:
        """停止监听配置变化 - 已弃用，请使用FileWatcher
        
        Raises:
            NotImplementedError: 此方法已弃用
        """
        raise NotImplementedError(
            "stop_watching is deprecated. Please use FileWatcher instead."
        )

    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量 - 已弃用，请使用EnvResolver
        
        Args:
            config: 配置字典
            
        Raises:
            NotImplementedError: 此方法已弃用
        """
        raise NotImplementedError(
            "resolve_env_vars is deprecated. Please use EnvResolver instead."
        )

    def _handle_file_change(self, file_path: str) -> None:
        """处理文件变化事件 - 已弃用，请使用FileWatcher
        
        Args:
            file_path: 文件路径
            
        Raises:
            NotImplementedError: 此方法已弃用
        """
        raise NotImplementedError(
            "_handle_file_change is deprecated. Please use FileWatcher instead."
        )

    def get_cached_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存的配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典或None
        """
        with self._lock:
            return self._configs.get(config_path)

    def clear_cache(self) -> None:
        """清除配置缓存"""
        with self._lock:
            self._configs.clear()

    def validate_config_structure(
        self, config: Dict[str, Any], required_keys: List[str]
    ) -> CheckResult:
        """验证配置结构
        
        Args:
            config: 配置字典
            required_keys: 必需的键列表
            
        Returns:
            验证结果
        """
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
        # YamlConfigLoader 不需要启动逻辑
        pass
    
    def stop(self) -> None:
        """停止配置加载器"""
        # YamlConfigLoader 不需要停止逻辑
        pass
    
    def dispose(self) -> None:
        """释放配置加载器资源"""
        # 清理缓存
        self.clear_cache()
        
    def __del__(self) -> None:
        """析构函数，确保清理资源"""
        self.dispose()