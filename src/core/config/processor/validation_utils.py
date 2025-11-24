"""验证工具模块

提供通用的验证工具和实用功能。
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
import yaml
import json
import logging
from pathlib import Path


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标


class ValidationSeverity(Enum):
    """验证严重性级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCache:
    """验证缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存结果"""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl:
                return result
            else:
                del self._cache[key]  # 过期清理
        return None
    
    def set(self, key: str, result: Any) -> None:
        """设置缓存结果"""
        if len(self._cache) >= self.max_size:
            # LRU淘汰策略
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[key] = (result, datetime.now())


def load_config_file(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix.lower() == '.json':
            return json.load(f)
        else:
            # 尝试作为YAML加载
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError:
                raise ValueError(f"不支持的配置文件格式: {config_path}")


def generate_cache_key(config_path: str, levels: List[ValidationLevel]) -> str:
    """生成缓存键"""
    level_names = "_".join(level.value for level in sorted(levels, key=lambda x: x.value))
    return f"{config_path}_{level_names}"


logger = logging.getLogger(__name__)