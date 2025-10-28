"""优化的依赖注入容器

提供高性能的依赖注入和缓存功能。
"""

import time
import threading
import weakref
from typing import Type, TypeVar, Dict, Any, Optional, List, Set, Callable, Union, cast
from inspect import isclass, signature
from contextlib import contextmanager
from enum import Enum
from dataclasses import dataclass

from .types import ServiceRegistration, ServiceLifetime, T
from .exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)
from .container import IDependencyContainer, DependencyContainer


@dataclass
class ServiceCacheEntry:
    """服务缓存条目"""
    instance: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    size_bytes: int = 0
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.last_accessed = time.time()
        self.access_count += 1


class OptimizedDependencyContainer(DependencyContainer):
    """优化的依赖注入容器
    
    提供以下优化功能：
    1. 服务实例缓存
    2. 创建路径缓存
    3. 性能监控
    4. 内存优化
    """
    
    def __init__(
        self,
        enable_service_cache: bool = True,
        enable_path_cache: bool = True,
        max_cache_size: int = 1000,
        cache_ttl_seconds: int = 3600
    ):
        """初始化优化的依赖注入容器
        
        Args:
            enable_service_cache: 是否启用服务缓存
            enable_path_cache: 是否启用路径缓存
            max_cache_size: 最大缓存大小
            cache_ttl_seconds: 缓存过期时间
        """
        # 继承基础容器功能
        super().__init__()
        
        self._enable_service_cache = enable_service_cache
        self._enable_path_cache = enable_path_cache
        self._max_cache_size = max_cache_size
        self._cache_ttl_seconds = cache_ttl_seconds
        
        # 服务缓存
        self._service_cache: Dict[Type, ServiceCacheEntry] = {}
        self._cache_lock = threading.RLock()
        
        # 创建路径缓存
        self._creation_path_cache: Dict[Type, List[Type]] = {}
        self._path_cache_lock = threading.RLock()
        
        # 性能统计
        self._performance_stats = {
            "total_resolutions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "service_creations": 0,
            "total_creation_time": 0.0,
            "average_creation_time": 0.0,
            "memory_saved": 0
        }
    
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例（优化版本）
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        start_time = time.time()
        self._performance_stats["total_resolutions"] += 1
        
        try:
            # 检查服务缓存
            if self._enable_service_cache:
                cached_instance = self._get_from_cache(service_type)
                if cached_instance is not None:
                    self._performance_stats["cache_hits"] += 1
                    return cast(T, cached_instance)
                self._performance_stats["cache_misses"] += 1
            
            # 检查创建路径缓存
            if self._enable_path_cache:
                creation_path = self._get_creation_path(service_type)
            else:
                creation_path = None
            
            # 创建服务实例
            instance = self._create_service_optimized(service_type, creation_path)
            
            # 缓存服务实例
            if self._enable_service_cache:
                self._add_to_cache(service_type, instance)
            
            # 更新性能统计
            creation_time = time.time() - start_time
            self._performance_stats["total_creation_time"] += creation_time
            self._performance_stats["service_creations"] += 1
            self._performance_stats["average_creation_time"] = (
                self._performance_stats["total_creation_time"] / 
                self._performance_stats["service_creations"]
            )
            
            return cast(T, instance)
            
        except Exception as e:
            raise ServiceCreationError(f"Failed to get service {service_type.__name__}: {e}")
    
    def get_service_creation_path(self, service_type: Type) -> List[Type]:
        """获取服务创建路径
        
        Args:
            service_type: 服务类型
            
        Returns:
            创建路径
        """
        if self._enable_path_cache:
            return self._get_creation_path(service_type)
        else:
            return self._build_creation_path(service_type)
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        with self._cache_lock:
            self._service_cache.clear()
        
        with self._path_cache_lock:
            self._creation_path_cache.clear()
        
        # 重置性能统计
        self._performance_stats["cache_hits"] = 0
        self._performance_stats["cache_misses"] = 0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计信息
        """
        total_requests = self._performance_stats["total_resolutions"]
        cache_hit_rate = (
            self._performance_stats["cache_hits"] / total_requests * 100
        ) if total_requests > 0 else 0
        
        # 计算缓存内存使用
        cache_memory = sum(
            entry.size_bytes for entry in self._service_cache.values()
        )
        
        return {
            "resolution_stats": {
                "total_resolutions": total_requests,
                "cache_hits": self._performance_stats["cache_hits"],
                "cache_misses": self._performance_stats["cache_misses"],
                "cache_hit_rate": f"{cache_hit_rate:.2f}%"
            },
            "creation_stats": {
                "service_creations": self._performance_stats["service_creations"],
                "total_creation_time": self._performance_stats["total_creation_time"],
                "average_creation_time": self._performance_stats["average_creation_time"]
            },
            "cache_stats": {
                "service_cache_size": len(self._service_cache),
                "path_cache_size": len(self._creation_path_cache),
                "max_cache_size": self._max_cache_size,
                "cache_memory_bytes": cache_memory,
                "memory_saved_bytes": self._performance_stats["memory_saved"]
            }
        }
    
    def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存
        
        Returns:
            优化结果
        """
        with self._cache_lock:
            # 移除过期的缓存条目
            expired_keys = []
            current_time = time.time()
            
            for service_type, entry in self._service_cache.items():
                if current_time - entry.created_at > self._cache_ttl_seconds:
                    expired_keys.append(service_type)
            
            for key in expired_keys:
                del self._service_cache[key]
            
            # 如果缓存仍然过大，移除最少使用的条目
            remove_count = 0
            if len(self._service_cache) > self._max_cache_size:
                # 按访问次数排序
                sorted_items = sorted(
                    self._service_cache.items(),
                    key=lambda x: x[1].access_count
                )
                
                remove_count = len(self._service_cache) - self._max_cache_size
                for i in range(remove_count):
                    service_type = sorted_items[i][0]
                    del self._service_cache[service_type]
            
            return {
                "expired_removed": len(expired_keys),
                "lru_removed": remove_count,
                "final_cache_size": len(self._service_cache)
            }
    
    def _get_from_cache(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            缓存的服务实例，如果不存在则返回None
        """
        with self._cache_lock:
            if service_type in self._service_cache:
                entry = self._service_cache[service_type]
                
                # 检查是否过期
                if time.time() - entry.created_at > self._cache_ttl_seconds:
                    del self._service_cache[service_type]
                    return None
                
                # 更新访问信息
                entry.update_access()
                return entry.instance
            
            return None
    
    def _add_to_cache(self, service_type: Type, instance: Any) -> None:
        """添加服务实例到缓存
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        with self._cache_lock:
            # 检查缓存大小
            if len(self._service_cache) >= self._max_cache_size:
                self._evict_lru_service()
            
            # 估算实例大小
            size_bytes = self._estimate_instance_size(instance)
            
            # 创建缓存条目
            entry = ServiceCacheEntry(
                instance=instance,
                created_at=time.time(),
                access_count=1,
                last_accessed=time.time(),
                size_bytes=size_bytes
            )
            
            self._service_cache[service_type] = entry
    
    def _evict_lru_service(self) -> None:
        """淘汰最少使用的服务"""
        if not self._service_cache:
            return
        
        # 找到最少使用的服务
        lru_service_type = min(
            self._service_cache.items(),
            key=lambda x: x[1].access_count
        )[0]
        
        del self._service_cache[lru_service_type]
    
    def _get_creation_path(self, service_type: Type) -> List[Type]:
        """从缓存获取创建路径
        
        Args:
            service_type: 服务类型
            
        Returns:
            创建路径
        """
        with self._path_cache_lock:
            if service_type in self._creation_path_cache:
                return self._creation_path_cache[service_type].copy()
            
            # 构建创建路径并缓存
            path = self._build_creation_path(service_type)
            self._creation_path_cache[service_type] = path.copy()
            
            return path
    
    def _build_creation_path(self, service_type: Type) -> List[Type]:
        """构建服务创建路径
        
        Args:
            service_type: 服务类型
            
        Returns:
            创建路径
        """
        path = []
        visited = set()
        
        def build_path_recursive(current_type: Type) -> None:
            if current_type in visited:
                return
            
            visited.add(current_type)
            path.append(current_type)
            
            # 获取依赖
            registration = self._find_registration(current_type)
            if registration and registration.implementation != type(None):
                dependencies = self._get_dependencies(registration.implementation)
                for dep_type in dependencies:
                    build_path_recursive(dep_type)
        
        build_path_recursive(service_type)
        return path
    
    def _get_dependencies(self, implementation: Type) -> List[Type]:
        """获取实现的依赖类型
        
        Args:
            implementation: 实现类
            
        Returns:
            依赖类型列表
        """
        dependencies = []
        
        try:
            sig = signature(implementation.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param.annotation == param.empty:
                    continue
                
                dep_type = param.annotation
                if isinstance(dep_type, type) and self.has_service(dep_type):
                    dependencies.append(dep_type)
        except Exception:
            pass
        
        return dependencies
    
    def _create_service_optimized(
        self,
        service_type: Type,
        creation_path: Optional[List[Type]] = None
    ) -> Any:
        """优化的服务创建
        
        Args:
            service_type: 服务类型
            creation_path: 创建路径
            
        Returns:
            服务实例
        """
        # 使用父类的创建逻辑，但添加路径优化
        if creation_path:
            # 预先创建路径中的所有依赖
            for dep_type in creation_path:
                if dep_type != service_type and not self._is_cached(dep_type):
                    try:
                        self._create_service_optimized(dep_type)
                    except Exception:
                        pass
        
        # 调用父类的创建方法
        registration = self._find_registration(service_type)
        if registration is None:
            raise ServiceNotRegisteredError(f"Service {service_type} not registered")
        return super()._create_instance(service_type, registration)
    
    def _is_cached(self, service_type: Type) -> bool:
        """检查服务是否已缓存
        
        Args:
            service_type: 服务类型
            
        Returns:
            是否已缓存
        """
        return service_type in self._service_cache
    
    def _find_registration(self, service_type: Type) -> Optional[ServiceRegistration]:
        """查找服务注册"""
        # 首先查找当前环境的注册
        if service_type in self._environment_services:
            env_services = self._environment_services[service_type]
            if self._environment in env_services:
                return env_services[self._environment]
        
        # 查找默认注册
        if service_type in self._services:
            return self._services[service_type]
        
        # 查找其他环境的默认注册
        if service_type in self._environment_services:
            env_services = self._environment_services[service_type]
            if "default" in env_services:
                return env_services["default"]
            # 返回任意一个注册
            if env_services:
                return next(iter(env_services.values()))
        
        return None
    
    def _estimate_instance_size(self, instance: Any) -> int:
        """估算实例大小
        
        Args:
            instance: 实例对象
            
        Returns:
            估算的大小（字节）
        """
        try:
            import pickle
            serialized = pickle.dumps(instance)
            return len(serialized)
        except Exception:
            # 如果序列化失败，使用默认估算
            return 1024


def create_optimized_container(
    enable_service_cache: bool = True,
    enable_path_cache: bool = True,
    max_cache_size: int = 1000,
    cache_ttl_seconds: int = 3600
) -> OptimizedDependencyContainer:
    """创建优化的依赖注入容器
    
    Args:
        enable_service_cache: 是否启用服务缓存
        enable_path_cache: 是否启用路径缓存
        max_cache_size: 最大缓存大小
        cache_ttl_seconds: 缓存过期时间
        
    Returns:
        优化的依赖注入容器实例
    """
    return OptimizedDependencyContainer(
        enable_service_cache=enable_service_cache,
        enable_path_cache=enable_path_cache,
        max_cache_size=max_cache_size,
        cache_ttl_seconds=cache_ttl_seconds
    )