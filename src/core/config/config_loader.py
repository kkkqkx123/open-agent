"""
配置加载器 - 统一配置加载功能
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from functools import lru_cache

from .exceptions import (
    ConfigNotFoundError,
    ConfigFormatError,
    ConfigError
)


class ConfigLoader:
    """统一配置加载器"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """初始化加载器"""
        self.base_path = base_path or Path("configs")
        self._supported_formats = {'.yaml', '.yml', '.json'}
    
    @lru_cache(maxsize=128)
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置（带缓存）"""
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
        # lru_cache会自动管理，这里提供接口用于手动清除
        # 可以通过调用相同参数的load来刷新缓存
        pass


class CachedConfigLoader(ConfigLoader):
    """带缓存的配置加载器"""
    
    def __init__(self, base_path: Optional[Path] = None, cache_size: int = 128):
        super().__init__(base_path)
        self._cache = {}
        self._cache_size = cache_size
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置（带手动缓存）"""
        if config_path in self._cache:
            return self._cache[config_path]
        
        config = super().load(config_path)
        self._cache[config_path] = config
        
        # 简单的LRU缓存清理
        if len(self._cache) > self._cache_size:
            # 移除最旧的条目
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        return config
    
    def invalidate_cache(self, config_path: str) -> None:
        """清除指定配置的缓存"""
        if config_path in self._cache:
            del self._cache[config_path]


# 工具函数
def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """直接加载配置文件"""
    loader = ConfigLoader()
    return loader.load(str(file_path))


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """合并多个配置"""
    result = {}
    for config in configs:
        if config:
            # 深度合并
            result = _deep_merge(result, config)
    return result


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并字典"""
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result