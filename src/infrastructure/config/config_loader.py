"""
配置加载器 - 基础配置加载功能

只负责文件读取和格式解析，不包含高级功能。
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable

from src.interfaces.config import (
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationParseError as ConfigFormatError,
    ConfigError
)
from src.interfaces.config import IConfigLoader

class ConfigLoader(IConfigLoader):
    """基础配置加载器，只负责文件读取和格式解析"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """初始化加载器
        
        Args:
            base_path: 配置文件基础路径
        """
        self._base_path = base_path or Path("configs")
        self._supported_formats = {'.yaml', '.yml', '.json'}
    
    @property
    def base_path(self) -> Path:
        """获取配置基础路径"""
        return self._base_path
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置数据字典
            
        Raises:
            ConfigNotFoundError: 配置文件不存在
            ConfigFormatError: 配置文件格式错误
            ConfigError: 其他加载错误
        """
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
    
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Returns:
            配置数据字典
        """
        return self.load(config_path)
    
    def exists(self, config_path: str) -> bool:
        """检查配置文件是否存在
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            文件是否存在
        """
        try:
            full_path = self._resolve_path(config_path)
            return full_path.exists()
        except Exception:
            return False
    
    def _resolve_path(self, config_path: str) -> Path:
        """解析配置文件路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            解析后的完整路径
        """
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
        """获取配置文件列表
        
        Args:
            directory: 搜索目录（可选）
            recursive: 是否递归搜索
            
        Returns:
            配置文件路径列表
        """
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
    
    # 以下是 IConfigLoader 接口要求的方法，但不是基础设施层的职责
    # 这些方法抛出 NotImplementedError，提示使用更高层的实现
    
    def reload(self) -> None:
        """重新加载所有配置 - 非基础设施层职责
        
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "reload is not implemented in infrastructure layer. Use core or services layer."
        )
    
    def watch_for_changes(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """监听配置变化 - 非基础设施层职责
        
        Args:
            callback: 变化回调函数
            
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "watch_for_changes is not implemented in infrastructure layer. Use services layer."
        )
    
    def stop_watching(self) -> None:
        """停止监听配置变化 - 非基础设施层职责
        
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "stop_watching is not implemented in infrastructure layer. Use services layer."
        )
    
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量 - 非基础设施层职责
        
        Args:
            config: 配置字典
            
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "resolve_env_vars is not implemented in infrastructure layer. Use core layer."
        )
    
    def get_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的配置 - 非基础设施层职责
        
        Args:
            config_path: 配置文件路径
            
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "get_config is not implemented in infrastructure layer. Use services layer."
        )
    
    def save_config(self, config: Dict[str, Any], config_path: str, config_type: Optional[str] = None) -> None:
        """保存配置 - 非基础设施层职责
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
            config_type: 配置类型（可选）
            
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "save_config is not implemented in infrastructure layer. Use services layer."
        )
    
    def list_configs(self, config_type: Optional[str] = None) -> List[str]:
        """列出配置文件 - 非基础设施层职责
        
        Args:
            config_type: 配置类型（可选）
            
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "list_configs is not implemented in infrastructure layer. Use services layer."
        )
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置路径 - 非基础设施层职责
        
        Args:
            config_path: 配置文件路径
            
        Raises:
            NotImplementedError: 此方法应在更高层实现
        """
        raise NotImplementedError(
            "validate_config_path is not implemented in infrastructure layer. Use core layer."
        )


# 工具函数
def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """直接加载配置文件
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        配置数据字典
    """
    loader = ConfigLoader()
    return loader.load(str(file_path))