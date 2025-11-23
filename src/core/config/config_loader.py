"""
配置加载器 - 统一配置加载功能
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import re

from ..common.cache import config_cached
from ..common.exceptions.config import (
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
        
        # 配置类型推断的正则模式
        self._workflow_patterns = [
            r".*workflow.*\.ya?ml$",
            r".*react.*\.ya?ml$",
            r".*plan.*\.ya?ml$",
            r".*collaborative.*\.ya?ml$",
            r".*thinking.*\.ya?ml$",
            r".*deep.*\.ya?ml$",
            r".*ultra.*\.ya?ml$"
        ]
        
        self._tool_patterns = [
            r".*tool.*\.ya?ml$",
            r".*calculator.*\.ya?ml$",
            r".*fetch.*\.ya?ml$",
            r".*weather.*\.ya?ml$",
            r".*database.*\.ya?ml$",
            r".*search.*\.ya?ml$",
            r".*hash.*\.ya?ml$"
        ]
        
        self._state_machine_patterns = [
            r".*state.*machine.*\.ya?ml$",
            r".*thinking.*\.ya?ml$",
            r".*deep.*thinking.*\.ya?ml$",
            r".*ultra.*thinking.*\.ya?ml$"
        ]
        
        # 编译正则表达式
        self._compiled_workflow_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self._workflow_patterns]
        self._compiled_tool_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self._tool_patterns]
        self._compiled_state_machine_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self._state_machine_patterns]
    
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
    
    def infer_config_type(self, config_path: str) -> str:
        """推断配置类型
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            str: 配置类型 ("workflow", "tool", "state_machine", "unknown")
        """
        path_lower = config_path.lower()
        
        # 状态机配置优先级最高
        if "state_machine" in path_lower or any(pattern.search(config_path) for pattern in self._compiled_state_machine_patterns):
            return "state_machine"
        
        # 工作流配置
        if "workflow" in path_lower or any(pattern.search(config_path) for pattern in self._compiled_workflow_patterns):
            return "workflow"
        
        # 工具配置
        if "tool" in path_lower or any(pattern.search(config_path) for pattern in self._compiled_tool_patterns):
            return "tool"
        
        # 默认为未知
        return "unknown"
    
    def get_config_files_by_type(self, directory: Optional[str] = None, recursive: bool = True) -> Dict[str, List[str]]:
        """按类型获取配置文件列表
        
        Args:
            directory: 目录路径
            recursive: 是否递归搜索
            
        Returns:
            Dict[str, List[str]]: 按类型分组的配置文件列表
        """
        config_files = self.get_config_files(directory, recursive)
        
        result = {
            "workflow": [],
            "tool": [],
            "state_machine": [],
            "unknown": []
        }
        
        for file_path in config_files:
            config_type = self.infer_config_type(file_path)
            result[config_type].append(file_path)
        
        return result
    
    def invalidate_cache(self, config_path: str) -> None:
        """清除指定配置的缓存"""
        # 通过清除全局缓存来实现
        from ..common.cache import clear_cache
        clear_cache("config_func")
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        from ..common.cache import clear_cache
        clear_cache("config_func")


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