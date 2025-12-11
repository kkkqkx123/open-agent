"""统一的缓存配置体系
提供通用的缓存配置和配置系统专用缓存配置。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class BaseCacheConfig:
    """基础缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 3600
    max_size: int = 1000
    cache_type: str = "memory"
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    def is_enabled(self) -> bool:
        return self.enabled
    
    def get_ttl_seconds(self) -> int:
        return self.ttl_seconds
    
    def get_max_size(self) -> int:
        return self.max_size
    
    def get_provider_config(self) -> Dict[str, Any]:
        return self.provider_config.copy()


@dataclass
class CacheEntry:
    """缓存项"""
    
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        import time
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        import time
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def get_age_seconds(self) -> float:
        """获取缓存项年龄（秒）"""
        import time
        return time.time() - self.created_at
    
    def get_idle_seconds(self) -> Optional[float]:
        """获取空闲时间（秒）"""
        if self.last_accessed is None:
            return self.get_age_seconds()
        import time
        return time.time() - self.last_accessed


@dataclass
class ConfigCacheConfig(BaseCacheConfig):
    """配置缓存专用配置
    
    继承自BaseCacheConfig，添加配置系统特定的缓存参数。
    """
    
    # 配置缓存特定参数
    cache_key_prefix: str = "config:"
    enable_versioning: bool = True
    enable_dependency_tracking: bool = True
    max_config_size: int = 10 * 1024 * 1024  # 10MB
    
    # 缓存策略
    cache_strategy: str = "lru"  # lru, lfu, ttl
    enable_hierarchical_cache: bool = False
    
    # 依赖管理
    dependency_ttl: int = 3600  # 依赖缓存TTL
    
    # 配置特定参数
    enable_config_validation_cache: bool = True
    enable_schema_cache: bool = True
    config_reload_threshold: int = 5  # 配置重新加载阈值
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 验证缓存策略
        allowed_strategies = ["lru", "lfu", "ttl"]
        if self.cache_strategy not in allowed_strategies:
            raise ValueError(f"缓存策略必须是以下之一: {allowed_strategies}")
    
    def get_cache_key(self, config_path: str, module_type: Optional[str] = None) -> str:
        """生成配置缓存键
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
            
        Returns:
            缓存键
        """
        if module_type:
            return f"{self.cache_key_prefix}{module_type}:{config_path}"
        return f"{self.cache_key_prefix}{config_path}"
    
    def get_dependency_key(self, config_path: str) -> str:
        """生成依赖缓存键
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            依赖缓存键
        """
        return f"{self.cache_key_prefix}dep:{config_path}"
    
    def get_validation_cache_key(self, config_path: str, config_hash: str) -> str:
        """生成验证缓存键
        
        Args:
            config_path: 配置文件路径
            config_hash: 配置内容哈希
            
        Returns:
            验证缓存键
        """
        return f"{self.cache_key_prefix}val:{config_path}:{config_hash}"
    
    def get_schema_cache_key(self, schema_name: str, version: str) -> str:
        """生成模式缓存键
        
        Args:
            schema_name: 模式名称
            version: 模式版本
            
        Returns:
            模式缓存键
        """
        return f"{self.cache_key_prefix}schema:{schema_name}:{version}"
    
    def is_config_too_large(self, config_size: int) -> bool:
        """检查配置是否过大
        
        Args:
            config_size: 配置大小（字节）
            
        Returns:
            是否过大
        """
        return config_size > self.max_config_size
    
    def should_cache_validation(self) -> bool:
        """是否应该缓存验证结果"""
        return self.enable_config_validation_cache
    
    def should_cache_schema(self) -> bool:
        """是否应该缓存模式"""
        return self.enable_schema_cache


@dataclass
class ConfigCacheEntry:
    """配置缓存项
    
    包含配置数据及其元数据。
    """
    
    config_path: str
    module_type: Optional[str]
    config_data: Dict[str, Any]
    version: str
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: __import__('time').time())
    last_accessed: float = field(default_factory=lambda: __import__('time').time())
    access_count: int = 0
    config_hash: str = ""
    size_bytes: int = 0
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.config_hash:
            import hashlib
            import json
            # 生成配置内容哈希
            config_str = json.dumps(self.config_data, sort_keys=True)
            self.config_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        # 计算配置大小
        import sys
        self.size_bytes = sys.getsizeof(self.config_data)
    
    def is_expired(self, ttl: int) -> bool:
        """检查是否过期
        
        Args:
            ttl: 生存时间（秒）
            
        Returns:
            是否过期
        """
        import time
        return (time.time() - self.created_at) > ttl
    
    def access(self) -> Dict[str, Any]:
        """访问缓存项
        
        Returns:
            配置数据
        """
        import time
        self.access_count += 1
        self.last_accessed = time.time()
        return self.config_data
    
    def add_dependency(self, dependency_path: str) -> None:
        """添加依赖
        
        Args:
            dependency_path: 依赖配置路径
        """
        if dependency_path not in self.dependencies:
            self.dependencies.append(dependency_path)
    
    def remove_dependency(self, dependency_path: str) -> None:
        """移除依赖
        
        Args:
            dependency_path: 依赖配置路径
        """
        if dependency_path in self.dependencies:
            self.dependencies.remove(dependency_path)
    
    def has_dependency(self, dependency_path: str) -> bool:
        """检查是否有指定依赖
        
        Args:
            dependency_path: 依赖配置路径
            
        Returns:
            是否有依赖
        """
        return dependency_path in self.dependencies
    
    def get_age_seconds(self) -> float:
        """获取缓存项年龄（秒）
        
        Returns:
            年龄（秒）
        """
        import time
        return time.time() - self.created_at
    
    def get_idle_seconds(self) -> float:
        """获取空闲时间（秒）
        
        Returns:
            空闲时间（秒）
        """
        import time
        return time.time() - self.last_accessed
    
    def get_access_rate(self) -> float:
        """获取访问率（次/秒）
        
        Returns:
            访问率
        """
        age = self.get_age_seconds()
        if age == 0:
            return 0.0
        return self.access_count / age
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            "config_path": self.config_path,
            "module_type": self.module_type,
            "config_data": self.config_data,
            "version": self.version,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "config_hash": self.config_hash,
            "size_bytes": self.size_bytes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigCacheEntry":
        """从字典创建缓存项
        
        Args:
            data: 字典数据
            
        Returns:
            配置缓存项
        """
        return cls(**data)


@dataclass
class ConfigDependencyEntry:
    """配置依赖项
    
    记录配置之间的依赖关系。
    """
    
    config_path: str
    dependent_paths: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: __import__('time').time())
    last_updated: float = field(default_factory=lambda: __import__('time').time())
    
    def add_dependent(self, dependent_path: str) -> None:
        """添加依赖者
        
        Args:
            dependent_path: 依赖者配置路径
        """
        if dependent_path not in self.dependent_paths:
            self.dependent_paths.append(dependent_path)
            self._update_timestamp()
    
    def remove_dependent(self, dependent_path: str) -> None:
        """移除依赖者
        
        Args:
            dependent_path: 依赖者配置路径
        """
        if dependent_path in self.dependent_paths:
            self.dependent_paths.remove(dependent_path)
            self._update_timestamp()
    
    def has_dependent(self, dependent_path: str) -> bool:
        """检查是否有指定依赖者
        
        Args:
            dependent_path: 依赖者配置路径
            
        Returns:
            是否有依赖者
        """
        return dependent_path in self.dependent_paths
    
    def get_dependent_count(self) -> int:
        """获取依赖者数量
        
        Returns:
            依赖者数量
        """
        return len(self.dependent_paths)
    
    def _update_timestamp(self) -> None:
        """更新时间戳"""
        import time
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            "config_path": self.config_path,
            "dependent_paths": self.dependent_paths,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigDependencyEntry":
        """从字典创建依赖项
        
        Args:
            data: 字典数据
            
        Returns:
            配置依赖项
        """
        return cls(**data)


# 导出所有缓存配置相关的类
__all__ = [
    "BaseCacheConfig",
    "CacheEntry",
    "ConfigCacheConfig",
    "ConfigCacheEntry",
    "ConfigDependencyEntry"
]
