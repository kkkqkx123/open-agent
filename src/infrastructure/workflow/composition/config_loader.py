"""组合配置加载器实现

从文件系统加载配置，支持环境变量注入，配置热重载。
"""

import os
import re
import yaml
import json
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler
import threading
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class CompositionConfigLoader:
    """组合配置加载器
    
    负责从文件系统加载组合配置，支持环境变量注入和热重载。
    遵循Infrastructure层原则，只依赖Interfaces层。
    """
    
    def __init__(
        self,
        config_path: Union[str, Path] = "configs/workflow_compositions",
        enable_hot_reload: bool = False
    ):
        """初始化配置加载器
        
        Args:
            config_path: 配置文件路径
            enable_hot_reload: 是否启用热重载
        """
        self._config_path = Path(config_path) if isinstance(config_path, str) else config_path
        self._enable_hot_reload = enable_hot_reload
        self._logger = get_logger(f"{__name__}.CompositionConfigLoader")
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._registry_cache: Optional[Dict[str, Any]] = None
        
        # 热重载相关
        self._observer: Optional[BaseObserver] = None
        self._reload_callbacks: List[Callable[[str], None]] = []
        self._reload_lock = threading.Lock()
        
        # 环境变量模式
        self._env_pattern = re.compile(r'\$\{([^:}]+)(?::([^}]*))?\}')
        
        self._logger.info(f"组合配置加载器初始化完成，配置路径: {config_path}")
        
        # 启用热重载
        if self._enable_hot_reload:
            self._enable_hot_reload_feature()
    
    def load_composition_config(self, composition_name: str) -> Optional[Dict[str, Any]]:
        """加载组合配置
        
        Args:
            composition_name: 组合名称
            
        Returns:
            Dict[str, Any]: 组合配置，如果不存在则返回None
        """
        try:
            self._logger.debug(f"加载组合配置: {composition_name}")
            
            # 检查缓存
            if composition_name in self._config_cache:
                self._logger.debug(f"从缓存加载组合配置: {composition_name}")
                return self._config_cache[composition_name].copy()
            
            # 构建配置文件路径
            config_file = self._config_path / f"{composition_name}.yaml"
            
            if not config_file.exists():
                # 尝试JSON格式
                config_file = self._config_path / f"{composition_name}.json"
            
            if not config_file.exists():
                self._logger.warning(f"组合配置文件不存在: {composition_name}")
                return None
            
            # 加载配置
            config_data = self._load_config_file(config_file)
            
            if config_data:
                # 注入环境变量
                config_data = self._inject_environment_variables(config_data)
                
                # 缓存配置
                self._config_cache[composition_name] = config_data.copy()
                
                self._logger.info(f"组合配置加载成功: {composition_name}")
                return config_data
            
            return None
            
        except Exception as e:
            self._logger.error(f"加载组合配置失败: {composition_name}, 错误: {e}")
            return None
    
    def load_registry_config(self) -> Optional[Dict[str, Any]]:
        """加载注册表配置
        
        Returns:
            Dict[str, Any]: 注册表配置，如果不存在则返回None
        """
        try:
            self._logger.debug("加载注册表配置")
            
            # 检查缓存
            if self._registry_cache is not None:
                self._logger.debug("从缓存加载注册表配置")
                return self._registry_cache.copy()
            
            # 构建注册表文件路径
            registry_file = self._config_path / "__registry__.yaml"
            
            if not registry_file.exists():
                # 尝试JSON格式
                registry_file = self._config_path / "__registry__.json"
            
            if not registry_file.exists():
                self._logger.warning("注册表配置文件不存在")
                return None
            
            # 加载配置
            registry_data = self._load_config_file(registry_file)
            
            if registry_data:
                # 注入环境变量
                registry_data = self._inject_environment_variables(registry_data)
                
                # 缓存配置
                self._registry_cache = registry_data.copy()
                
                self._logger.info("注册表配置加载成功")
                return registry_data
            
            return None
            
        except Exception as e:
            self._logger.error(f"加载注册表配置失败: {e}")
            return None
    
    def list_available_compositions(self) -> List[str]:
        """列出可用的组合配置
        
        Returns:
            List[str]: 组合名称列表
        """
        try:
            self._logger.debug("列出可用的组合配置")
            
            compositions = []
            
            # 扫描配置文件
            for config_file in self._config_path.glob("*.yaml"):
                if config_file.name != "__registry__.yaml":
                    compositions.append(config_file.stem)
            
            for config_file in self._config_path.glob("*.json"):
                if config_file.name != "__registry__.json":
                    compositions.append(config_file.stem)
            
            # 去重并排序
            compositions = sorted(list(set(compositions)))
            
            self._logger.debug(f"列出可用组合配置完成，数量: {len(compositions)}")
            return compositions
            
        except Exception as e:
            self._logger.error(f"列出可用组合配置失败: {e}")
            return []
    
    def reload_config(self, composition_name: str) -> bool:
        """重新加载配置
        
        Args:
            composition_name: 组合名称
            
        Returns:
            bool: 是否重新加载成功
        """
        try:
            self._logger.debug(f"重新加载配置: {composition_name}")
            
            # 清除缓存
            if composition_name in self._config_cache:
                del self._config_cache[composition_name]
            
            # 重新加载
            config_data = self.load_composition_config(composition_name)
            
            if config_data:
                self._logger.info(f"配置重新加载成功: {composition_name}")
                return True
            else:
                self._logger.warning(f"配置重新加载失败: {composition_name}")
                return False
                
        except Exception as e:
            self._logger.error(f"重新加载配置失败: {composition_name}, 错误: {e}")
            return False
    
    def reload_registry(self) -> bool:
        """重新加载注册表
        
        Returns:
            bool: 是否重新加载成功
        """
        try:
            self._logger.debug("重新加载注册表")
            
            # 清除缓存
            self._registry_cache = None
            
            # 重新加载
            registry_data = self.load_registry_config()
            
            if registry_data:
                self._logger.info("注册表重新加载成功")
                return True
            else:
                self._logger.warning("注册表重新加载失败")
                return False
                
        except Exception as e:
            self._logger.error(f"重新加载注册表失败: {e}")
            return False
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        with self._reload_lock:
            self._config_cache.clear()
            self._registry_cache = None
            self._logger.info("配置缓存已清除")
    
    def add_reload_callback(self, callback: Callable[[str], None]) -> None:
        """添加重载回调
        
        Args:
            callback: 回调函数
        """
        self._reload_callbacks.append(callback)
        self._logger.debug("添加重载回调")
    
    def _load_config_file(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() == '.yaml':
                    return yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    self._logger.warning(f"不支持的配置文件格式: {config_file.suffix}")
                    return None
                    
        except Exception as e:
            self._logger.error(f"加载配置文件失败: {config_file}, 错误: {e}")
            return None
    
    def _inject_environment_variables(self, data: Any) -> Any:
        """注入环境变量
        
        Args:
            data: 原始数据
            
        Returns:
            Any: 注入环境变量后的数据
        """
        if isinstance(data, str):
            return self._replace_env_variables(data)
        elif isinstance(data, dict):
            return {key: self._inject_environment_variables(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._inject_environment_variables(item) for item in data]
        else:
            return data
    
    def _replace_env_variables(self, text: str) -> str:
        """替换字符串中的环境变量
        
        Args:
            text: 原始字符串
            
        Returns:
            str: 替换后的字符串
        """
        def replace_match(match: re.Match) -> str:
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.getenv(var_name, default_value)
        
        return self._env_pattern.sub(replace_match, text)
    
    def _enable_hot_reload_feature(self) -> None:
        """启用热重载功能"""
        try:
            self._observer = Observer()
            event_handler = ConfigFileEventHandler(self)
            
            # 监控配置目录
            if self._observer is not None:
                self._observer.schedule(event_handler, str(self._config_path), recursive=False)
                self._observer.start()
            
            self._logger.info("热重载功能已启用")
            
        except Exception as e:
            self._logger.error(f"启用热重载功能失败: {e}")
            self._enable_hot_reload = False
    
    def _disable_hot_reload_feature(self) -> None:
        """禁用热重载功能"""
        try:
            if self._observer:
                self._observer.stop()
                self._observer.join()
                self._observer = None
                
            self._logger.info("热重载功能已禁用")
            
        except Exception as e:
            self._logger.error(f"禁用热重载功能失败: {e}")
    
    def _notify_reload_callbacks(self, file_path: str) -> None:
        """通知重载回调
        
        Args:
            file_path: 变化的文件路径
        """
        for callback in self._reload_callbacks:
            try:
                callback(file_path)
            except Exception as e:
                self._logger.error(f"执行重载回调失败: {e}")
    
    def get_loader_stats(self) -> Dict[str, Any]:
        """获取加载器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "config_path": str(self._config_path),
            "cached_configs": len(self._config_cache),
            "registry_cached": self._registry_cache is not None,
            "hot_reload_enabled": self._enable_hot_reload,
            "reload_callbacks": len(self._reload_callbacks),
            "available_compositions": len(self.list_available_compositions()),
        }
    
    def __del__(self) -> None:
        """析构函数"""
        if self._enable_hot_reload:
            self._disable_hot_reload_feature()


class ConfigFileEventHandler(FileSystemEventHandler):
    """配置文件事件处理器"""
    
    def __init__(self, loader: CompositionConfigLoader):
        """初始化事件处理器
        
        Args:
            loader: 配置加载器
        """
        self._loader = loader
        self._logger = get_logger(f"{__name__}.ConfigFileEventHandler")
    
    def on_modified(self, event: Any) -> None:
        """文件修改事件处理
        
        Args:
            event: 文件事件
        """
        if not event.is_directory:
            src_path = event.src_path
            if isinstance(src_path, bytes):
                src_path = src_path.decode('utf-8')
            elif not isinstance(src_path, str):
                src_path = str(src_path)
            file_path = Path(src_path)
            
            # 只处理配置文件
            if file_path.suffix.lower() in ['.yaml', '.json']:
                self._logger.info(f"检测到配置文件变化: {file_path.name}")
                
                # 重新加载配置
                if file_path.name == "__registry__.yaml" or file_path.name == "__registry__.json":
                    self._loader.reload_registry()
                else:
                    composition_name = file_path.stem
                    self._loader.reload_config(composition_name)
                
                # 通知回调
                self._loader._notify_reload_callbacks(str(file_path))


# 便捷函数
def create_composition_config_loader(
    config_path: str = "configs/workflow_compositions",
    enable_hot_reload: bool = False
) -> CompositionConfigLoader:
    """创建组合配置加载器实例
    
    Args:
        config_path: 配置文件路径
        enable_hot_reload: 是否启用热重载
        
    Returns:
        CompositionConfigLoader: 配置加载器实例
    """
    return CompositionConfigLoader(
        config_path=config_path,
        enable_hot_reload=enable_hot_reload
    )


# 导出实现
__all__ = [
    "CompositionConfigLoader",
    "ConfigFileEventHandler",
    "create_composition_config_loader",
]