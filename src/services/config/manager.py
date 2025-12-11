"""配置管理服务 - 使用现有缓存基础设施

提供配置系统的高级管理功能，集成缓存、验证、依赖管理等。
"""

from typing import Dict, Any, Optional, List
import logging
import hashlib
import json

from src.interfaces.config import (
    IConfigLoader, IConfigProcessor, IConfigValidator,
    IConfigChangeListener, ConfigChangeEvent
)
from src.interfaces.common_domain import ValidationResult
from src.infrastructure.cache.core.cache_manager import CacheManager
from src.infrastructure.cache.config.cache_config import (
    ConfigCacheConfig, ConfigCacheEntry, ConfigDependencyEntry
)
from src.interfaces.config.exceptions import ConfigValidationError

logger = logging.getLogger(__name__)


class ConfigManagerService:
    """配置管理服务 - 使用现有缓存基础设施"""
    
    def __init__(self, 
                 config_loader: IConfigLoader,
                 config_processor: IConfigProcessor,
                 config_validator: IConfigValidator,
                 cache_config: Optional[ConfigCacheConfig] = None):
        """初始化配置管理服务
        
        Args:
            config_loader: 配置加载器（来自Infrastructure层）
            config_processor: 配置处理器（来自Infrastructure层）
            config_validator: 配置验证器（来自Infrastructure层）
            cache_config: 配置缓存配置（可选）
        """
        self.config_loader = config_loader
        self.config_processor = config_processor
        self.config_validator = config_validator
        
        # 使用现有的缓存管理器
        self.cache_config = cache_config or ConfigCacheConfig()
        self.cache_manager = CacheManager(self.cache_config)
        
        # 配置变更监听器
        self._change_listeners: List[IConfigChangeListener] = []
        
        # 依赖管理
        self._dependencies: Dict[str, ConfigDependencyEntry] = {}
        
        # 统计信息
        self._stats = {
            "loads": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "validations": 0,
            "errors": 0
        }
        
        logger.info("配置管理服务初始化完成")
    
    def load_config(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置 - 使用缓存
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
            
        Returns:
            配置数据
        """
        try:
            self._stats["loads"] += 1
            logger.debug(f"加载配置: {config_path} (模块: {module_type})")
            
            # 生成缓存键
            cache_key = self.cache_config.get_cache_key(config_path, module_type)
            
            # 尝试从缓存获取
            cached_entry = self.cache_manager.get(cache_key)
            if cached_entry is not None:
                self._stats["cache_hits"] += 1
                logger.debug(f"配置缓存命中: {config_path}")
                
                # 访问缓存项
                if isinstance(cached_entry, ConfigCacheEntry):
                    return cached_entry.access()
                else:
                    # 兼容旧的缓存格式
                    return cached_entry
            
            self._stats["cache_misses"] += 1
            logger.debug(f"配置缓存未命中: {config_path}")
            
            # 缓存未命中，加载配置
            raw_config = self.config_loader.load(config_path)
            processed_config = self.config_processor.process(raw_config, config_path)
            
            # 验证配置
            validation_result = self.validate_config(processed_config)
            if not validation_result.is_valid:
                error_msg = f"配置验证失败 {config_path}: " + "; ".join(validation_result.errors)
                logger.error(error_msg)
                self._stats["errors"] += 1
                raise ConfigValidationError(error_msg)
            
            # 创建缓存项
            config_hash = self._generate_config_hash(processed_config)
            cache_entry = ConfigCacheEntry(
                config_path=config_path,
                module_type=module_type,
                config_data=processed_config,
                version="1.0",  # 简化版本管理
                config_hash=config_hash
            )
            
            # 检查配置大小
            if not self.cache_config.is_config_too_large(cache_entry.size_bytes):
                # 缓存配置
                self.cache_manager.set(cache_key, cache_entry, self.cache_config.ttl_seconds)
                logger.debug(f"配置已缓存: {config_path}")
            else:
                logger.warning(f"配置过大，跳过缓存: {config_path} ({cache_entry.size_bytes} bytes)")
            
            # 处理依赖关系
            if self.cache_config.enable_dependency_tracking:
                self._track_dependencies(config_path, processed_config)
            
            return processed_config
            
        except Exception as e:
            logger.error(f"加载配置失败: {config_path}, 错误: {e}")
            self._stats["errors"] += 1
            raise
    
    def save_config(self, config: Dict[str, Any], config_path: str) -> None:
        """保存配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
        """
        try:
            logger.debug(f"保存配置: {config_path}")
            
            # 这里应该调用配置保存器，但当前Infrastructure层可能没有实现
            # 暂时抛出NotImplementedError
            raise NotImplementedError("配置保存功能尚未实现")
            
        except Exception as e:
            logger.error(f"保存配置失败: {config_path}, 错误: {e}")
            self._stats["errors"] += 1
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        try:
            self._stats["validations"] += 1
            
            # 如果启用了验证缓存，先检查缓存
            if self.cache_config.should_cache_validation():
                config_hash = self._generate_config_hash(config)
                validation_cache_key = f"val:{config_hash}"
                
                cached_result = self.cache_manager.get(validation_cache_key)
                if cached_result is not None:
                    logger.debug("验证结果缓存命中")
                    return cached_result
            
            # 执行验证
            result = self.config_validator.validate(config)
            
            # 缓存验证结果
            if self.cache_config.should_cache_validation() and result.is_valid:
                config_hash = self._generate_config_hash(config)
                validation_cache_key = f"val:{config_hash}"
                self.cache_manager.set(validation_cache_key, result, self.cache_config.dependency_ttl)
            
            return result
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            self._stats["errors"] += 1
            return ValidationResult(is_valid=False, errors=[str(e)], warnings=[])
    
    def reload_config(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
            
        Returns:
            重新加载的配置数据
        """
        try:
            logger.debug(f"重新加载配置: {config_path}")
            
            # 清除缓存
            self.invalidate_cache(config_path, module_type)
            
            # 重新加载
            return self.load_config(config_path, module_type)
            
        except Exception as e:
            logger.error(f"重新加载配置失败: {config_path}, 错误: {e}")
            self._stats["errors"] += 1
            raise
    
    def invalidate_cache(self, config_path: str, module_type: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
        """
        try:
            # 清除特定配置的缓存
            cache_key = self.cache_config.get_cache_key(config_path, module_type)
            self.cache_manager.delete(cache_key)
            
            # 清除验证缓存
            # 由于我们不知道配置哈希，这里简化处理
            # 实际实现中可以维护一个路径到哈希的映射
            
            # 清除依赖缓存
            if self.cache_config.enable_dependency_tracking:
                self._invalidate_dependent_cache(config_path)
            
            logger.debug(f"缓存已清除: {config_path}")
            
        except Exception as e:
            logger.error(f"清除缓存失败: {config_path}, 错误: {e}")
    
    def invalidate_all_cache(self) -> None:
        """清除所有配置缓存"""
        try:
            self.cache_manager.clear()
            self._dependencies.clear()
            logger.info("所有配置缓存已清除")
            
        except Exception as e:
            logger.error(f"清除所有缓存失败: {e}")
    
    def add_change_listener(self, listener: IConfigChangeListener) -> None:
        """添加配置变更监听器
        
        Args:
            listener: 配置变更监听器
        """
        self._change_listeners.append(listener)
        logger.info("已添加配置变更监听器")
    
    def remove_change_listener(self, listener: IConfigChangeListener) -> None:
        """移除配置变更监听器
        
        Args:
            listener: 配置变更监听器
        """
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
            logger.info("已移除配置变更监听器")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        cache_stats = self.cache_manager.get_stats()
        service_stats = self._stats.copy()
        
        # 计算缓存命中率
        total_requests = service_stats["cache_hits"] + service_stats["cache_misses"]
        hit_rate = service_stats["cache_hits"] / total_requests if total_requests > 0 else 0.0
        service_stats["cache_hit_rate"] = hit_rate
        
        return {
            "service_stats": service_stats,
            "cache_stats": cache_stats
        }
    
    def get_dependency_info(self, config_path: str) -> Optional[ConfigDependencyEntry]:
        """获取配置依赖信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            依赖信息，如果不存在则返回None
        """
        return self._dependencies.get(config_path)
    
    def _generate_config_hash(self, config: Dict[str, Any]) -> str:
        """生成配置内容哈希
        
        Args:
            config: 配置数据
            
        Returns:
            配置哈希
        """
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _track_dependencies(self, config_path: str, config: Dict[str, Any]) -> None:
        """跟踪配置依赖关系
        
        Args:
            config_path: 配置文件路径
            config: 配置数据
        """
        # 简化实现，实际应该解析配置中的引用
        # 这里假设配置中可能有 ${ref:other_config} 格式的引用
        
        import re
        pattern = r'\$\{ref:([^}]+)\}'
        
        dependencies = []
        for match in re.finditer(pattern, json.dumps(config)):
            ref_path = match.group(1)
            dependencies.append(ref_path)
        
        if dependencies:
            dependency_entry = ConfigDependencyEntry(
                config_path=config_path,
                dependent_paths=dependencies
            )
            self._dependencies[config_path] = dependency_entry
            
            # 反向依赖关系
            for dep_path in dependencies:
                if dep_path not in self._dependencies:
                    self._dependencies[dep_path] = ConfigDependencyEntry(
                        config_path=dep_path
                    )
                self._dependencies[dep_path].add_dependent(config_path)
    
    def _invalidate_dependent_cache(self, config_path: str) -> None:
        """清除依赖配置的缓存
        
        Args:
            config_path: 配置文件路径
        """
        dependency_entry = self._dependencies.get(config_path)
        if dependency_entry:
            for dependent_path in dependency_entry.dependent_paths:
                cache_key = self.cache_config.get_cache_key(dependent_path)
                self.cache_manager.delete(cache_key)
                logger.debug(f"已清除依赖配置缓存: {dependent_path}")
    
    def _notify_config_changed(self, event: ConfigChangeEvent) -> None:
        """通知配置变更
        
        Args:
            event: 配置变更事件
        """
        for listener in self._change_listeners:
            try:
                listener.on_config_changed(event)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败: {e}")


# 导出配置管理服务
__all__ = [
    "ConfigManagerService"
]