"""配置加载器实现"""

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from src.core.common.exceptions import ConfigurationError
from src.core.common.types import CheckResult
from src.interfaces.common import IConfigLoader
from src.interfaces.container import ILifecycleAware
from src.core.config.yaml_loader import YamlLoader


class FileConfigLoader(IConfigLoader, ILifecycleAware):
    """YAML配置加载器实现 - 配置系统专用适配器
    
    使用通用的YamlLoader工具类提供配置系统特定的功能。
    """

    def __init__(self, base_path: str = "configs") -> None:
        """初始化YAML配置加载器
        
        Args:
            base_path: 配置文件基础路径
        """
        self._base_path = Path(base_path)
        self._yaml_loader = YamlLoader(base_path)

    @property
    def base_path(self) -> Path:
        """获取配置基础路径"""
        return self._base_path

    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选，为了兼容接口）
            
        Returns:
            配置字典
            
        Raises:
            ConfigurationError: 配置文件不存在或格式错误
        """
        return self._yaml_loader.load(config_path)

    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件（向后兼容方法）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        return self.load_config(config_path)

    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置，如果不存在则返回None
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典或None
        """
        return self._yaml_loader.get_cached(config_path)

    def reload(self) -> None:
        """重新加载所有配置"""
        self._yaml_loader.reload()

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
        return self._yaml_loader.get_cached(config_path)

    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._yaml_loader.clear_cache()

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
        return self._yaml_loader.validate_structure(config, required_keys)

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
    
    def save_config(self, config: Dict[str, Any], config_path: str, config_type: Optional[str] = None) -> None:
        """保存配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            config_type: 配置类型（可选，为了兼容接口）
        """
        self._yaml_loader.save(config, config_path)

    def list_configs(self, config_type: Optional[str] = None) -> List[str]:
        """列出配置文件
        
        Args:
            config_type: 配置类型（可选，为了兼容接口）
            
        Returns:
            配置文件路径列表
        """
        return self._yaml_loader.list_files()

    def validate_config_path(self, config_path: str) -> bool:
        """验证配置路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            路径是否有效
        """
        return self._yaml_loader.exists(config_path)

    def dispose(self) -> None:
        """释放配置加载器资源"""
        # 清理缓存
        self.clear_cache()
        
    def __del__(self) -> None:
        """析构函数，确保清理资源"""
        self.dispose()