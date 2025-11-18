"""YAML文件加载工具

提供通用的YAML文件加载和缓存功能，可以被多个模块使用。
"""

import os
import yaml
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.core.common.exceptions import ConfigurationError
from src.core.common.types import CheckResult


class YamlLoader:
    """YAML文件加载器 - 通用工具类
    
    提供线程安全的YAML文件加载和缓存功能。
    """

    def __init__(self, base_path: str = ".") -> None:
        """初始化YAML加载器
        
        Args:
            base_path: 文件基础路径
        """
        self._base_path = Path(base_path)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    @property
    def base_path(self) -> Path:
        """获取基础路径"""
        return self._base_path

    def load(self, file_path: str) -> Dict[str, Any]:
        """加载YAML文件
        
        Args:
            file_path: 文件路径（相对于base_path）
            
        Returns:
            解析后的YAML内容
            
        Raises:
            ConfigurationError: 文件不存在或格式错误
        """
        with self._lock:
            # 检查缓存
            if file_path in self._cache:
                return self._cache[file_path]

            # 构建完整路径
            full_path = self._base_path / file_path

            # 确保文件有.yaml扩展名
            if not full_path.suffix:
                full_path = full_path.with_suffix('.yaml')

            # 检查文件是否存在
            if not full_path.exists():
                raise ConfigurationError(f"YAML file not found: {full_path}")

            try:
                # 读取和解析YAML文件
                with open(full_path, "r", encoding="utf-8") as f:
                    content: Dict[str, Any] = yaml.safe_load(f) or {}

                # 缓存内容
                self._cache[file_path] = content

                return content
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in {file_path}: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to load {file_path}: {e}")

    def get_cached(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的内容，如果不存在则返回None
        
        Args:
            file_path: 文件路径
            
        Returns:
            缓存的内容或None
        """
        with self._lock:
            return self._cache.get(file_path)

    def reload(self, file_path: Optional[str] = None) -> None:
        """重新加载文件
        
        Args:
            file_path: 要重新加载的文件路径，如果为None则重新加载所有文件
        """
        with self._lock:
            if file_path:
                # 重新加载指定文件
                if file_path in self._cache:
                    del self._cache[file_path]
                    self.load(file_path)
            else:
                # 重新加载所有文件
                for path in list(self._cache.keys()):
                    try:
                        del self._cache[path]
                        self.load(path)
                    except ConfigurationError as e:
                        # 记录错误但继续加载其他文件
                        print(f"Warning: Failed to reload {path}: {e}")

    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            file_path: 要清除的文件路径，如果为None则清除所有缓存
        """
        with self._lock:
            if file_path:
                self._cache.pop(file_path, None)
            else:
                self._cache.clear()

    def list_files(self, pattern: str = "*.yaml") -> List[str]:
        """列出基础路径下的YAML文件
        
        Args:
            pattern: 文件匹配模式
            
        Returns:
            文件路径列表
        """
        try:
            return [str(p.relative_to(self._base_path)) 
                   for p in self._base_path.glob(pattern)]
        except Exception:
            return []

    def validate_structure(
        self, content: Dict[str, Any], required_keys: List[str]
    ) -> CheckResult:
        """验证内容结构
        
        Args:
            content: 要验证的内容
            required_keys: 必需的键列表
            
        Returns:
            验证结果
        """
        missing_keys = [key for key in required_keys if key not in content]

        if missing_keys:
            return CheckResult(
                component="yaml_structure",
                status="ERROR",
                message=f"Missing required keys: {', '.join(missing_keys)}",
                details={"missing_keys": missing_keys},
            )

        return CheckResult(
            component="yaml_structure",
            status="PASS",
            message="YAML structure is valid",
        )

    def save(self, content: Dict[str, Any], file_path: str) -> None:
        """保存内容到YAML文件
        
        Args:
            content: 要保存的内容
            file_path: 文件路径
        """
        full_path = self._base_path / file_path
        
        # 确保文件有.yaml扩展名
        if not full_path.suffix:
            full_path = full_path.with_suffix('.yaml')

        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                yaml.dump(content, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)

            # 更新缓存
            with self._lock:
                self._cache[file_path] = content
        except Exception as e:
            raise ConfigurationError(f"Failed to save {file_path}: {e}")

    def exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        full_path = self._base_path / file_path
        if not full_path.suffix:
            full_path = full_path.with_suffix('.yaml')
        return full_path.exists()