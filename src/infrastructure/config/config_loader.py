"""
配置加载器 - 统一配置加载功能
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable

from src.infrastructure.common.cache import config_cached
from src.infrastructure.common.exceptions.config import (
    ConfigNotFoundError,
    ConfigFormatError,
    ConfigError
)
from src.interfaces.config.interfaces import IConfigLoader
from src.interfaces.container import ILifecycleAware

class ConfigLoader(IConfigLoader, ILifecycleAware):
    """统一配置加载器，实现IConfigLoader接口"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """初始化加载器"""
        self._base_path = base_path or Path("configs")
        self._supported_formats = {'.yaml', '.yml', '.json'}
    
    @property
    def base_path(self) -> Path:
        """获取配置基础路径"""
        return self._base_path
    
    @config_cached(maxsize=256)
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        full_path = self._resolve_path(config_path)
        
        if not full_path.exists():
            raise ConfigNotFoundError(str(full_path))
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                if full_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif full_path.suffix == '.json':
                    return json.load(f)
                else:
                    raise ConfigFormatError(f"不支持的文件格式: {full_path.suffix}")
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigFormatError(f"配置文件格式错误: {e}", str(full_path))
        except Exception as e:
            raise ConfigError(f"加载配置失败: {e}", str(full_path))
    
    def exists(self, config_path: str) -> bool:
        """检查配置是否存在"""
        try:
            full_path = self._resolve_path(config_path)
            return full_path.exists()
        except Exception:
            return False
    
    def _resolve_path(self, config_path: str) -> Path:
        """解析配置路径"""
        path = Path(config_path)
        
        # 如果是绝对路径，直接使用
        if path.is_absolute():
            if not path.suffix:
                # 尝试添加支持的扩展名
                for ext in self._supported_formats:
                    test_path = path.with_suffix(ext)
                    if test_path.exists():
                        return test_path
                # 如果都没有找到，返回原始路径
                return path.with_suffix('.yaml')
            return path
        
        # 相对路径，在基础路径中查找
        if not path.suffix:
            # 尝试不同的扩展名
            for ext in self._supported_formats:
                test_path = self.base_path / path.with_suffix(ext)
                if test_path.exists():
                    return test_path
            # 默认使用yaml
            return self.base_path / path.with_suffix('.yaml')
        else:
            return self.base_path / path
    
    def get_config_files(self, directory: Optional[str] = None, recursive: bool = True) -> list:
        """获取配置文件列表"""
        search_path = self.base_path
        if directory:
            search_path = search_path / directory
        
        if not search_path.exists():
            return []
        
        config_files = []
        if recursive:
            for ext in self._supported_formats:
                config_files.extend(search_path.rglob(f'*{ext}'))
        else:
            for ext in self._supported_formats:
                config_files.extend(search_path.glob(f'*{ext}'))
        
        return [str(f.relative_to(self.base_path)) for f in config_files]
    
    
    def invalidate_cache(self, config_path: str) -> None:
        """清除指定配置的缓存"""
        # 通过清除全局缓存来实现
        from src.infrastructure.common.cache import clear_cache
        clear_cache("config_func")
    
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Returns:
            配置数据
        """
        return self.load(config_path)
    
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置数据或None
        """
        if self.exists(config_path):
            return self.load(config_path)
        return None
    
    def reload(self) -> None:
        """重新加载所有配置"""
        self.clear_cache()
    
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
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
    
    def save_config(self, config: Dict[str, Any], config_path: str, config_type: Optional[str] = None) -> None:
        """保存配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            config_type: 配置类型（可选）
        """
        import yaml
        full_path = self._base_path / config_path
        
        # 确保文件有.yaml扩展名
        if not full_path.suffix:
            full_path = full_path.with_suffix('.yaml')

        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False,
                         allow_unicode=True, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save {config_path}: {e}")
    
    def list_configs(self, config_type: Optional[str] = None) -> List[str]:
        """列出配置文件
        
        Args:
            config_type: 配置类型（可选）
            
        Returns:
            配置文件路径列表
        """
        return self.get_config_files()
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            路径是否有效
        """
        return self.exists(config_path)
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        from src.infrastructure.common.cache import clear_cache
        clear_cache("config_func")
    
    # ILifecycleAware 接口方法
    def initialize(self) -> None:
        """初始化配置加载器"""
        pass
    
    def start(self) -> None:
        """启动配置加载器"""
        pass
    
    def stop(self) -> None:
        """停止配置加载器"""
        pass
    
    def dispose(self) -> None:
        """释放配置加载器资源"""
        self.clear_cache()


# 工具函数
def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """直接加载配置文件"""
    loader = ConfigLoader()
    return loader.load(str(file_path))


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个配置"""
    from src.infrastructure.common.utils.dict_merger import DictMerger
    merger = DictMerger()
    result = {}
    for config in configs:
        if config:
            # 使用通用的字典合并器进行深度合并
            result = merger.deep_merge(result, config)
    return result