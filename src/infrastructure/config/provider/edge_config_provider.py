"""Edge配置提供者

提供Edge模块的配置获取、缓存和管理功能。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
import logging
import time
from threading import RLock
from datetime import datetime

from .base_provider import BaseConfigProvider
from ..impl.edge_config_impl import EdgeConfigImpl
from ..impl.base_impl import IConfigImpl

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EdgeConfigProvider(BaseConfigProvider):
    """Edge配置提供者
    
    提供Edge模块的配置获取、缓存和管理功能。
    专注于边的具体配置，包括类型、条件、路径映射等。
    """
    
    def __init__(self, config_impl: IConfigImpl):
        """初始化Edge配置提供者
        
        Args:
            config_impl: Edge配置实现
        """
        super().__init__("edge", config_impl)
        
        # 确保配置实现是EdgeConfigImpl
        if not isinstance(config_impl, EdgeConfigImpl):
            raise TypeError("config_impl必须是EdgeConfigImpl实例")
        
        self._edge_impl: EdgeConfigImpl = config_impl
        
        # 边配置缓存
        self._edge_cache: Dict[str, Dict[str, Any]] = {}
        self._edge_cache_timestamps: Dict[str, float] = {}
        self._edge_cache_lock = RLock()
        
        # 条件配置缓存
        self._condition_cache: Optional[Dict[str, Any]] = None
        self._condition_cache_timestamp: Optional[float] = None
        self._condition_cache_lock = RLock()
        
        # 转换配置缓存
        self._transformation_cache: Optional[Dict[str, Any]] = None
        self._transformation_cache_timestamp: Optional[float] = None
        self._transformation_cache_lock = RLock()
        
        # 节点引用缓存
        self._node_refs_cache: Optional[Dict[str, str]] = None
        self._node_refs_cache_timestamp: Optional[float] = None
        self._node_refs_cache_lock = RLock()
        
        logger.debug("Edge配置提供者初始化完成")
    
    def get_edge_config(self, edge_name: str) -> Optional[Dict[str, Any]]:
        """获取边配置
        
        Args:
            edge_name: 边名称
            
        Returns:
            边配置，如果不存在则返回None
        """
        with self._edge_cache_lock:
            # 检查缓存
            if edge_name in self._edge_cache:
                # 检查缓存是否有效
                if self._is_cache_valid_for_edge(edge_name):
                    logger.debug(f"从缓存获取边配置: {edge_name}")
                    return self._edge_cache[edge_name].copy()
                else:
                    # 缓存过期，清除
                    del self._edge_cache[edge_name]
                    del self._edge_cache_timestamps[edge_name]
            
            # 从配置实现获取
            edge_config = self._edge_impl.get_edge_config(edge_name)
            
            if edge_config:
                # 缓存配置
                self._edge_cache[edge_name] = edge_config.copy()
                self._edge_cache_timestamps[edge_name] = time.time()
                logger.debug(f"获取并缓存边配置: {edge_name}")
            
            return edge_config
    
    def get_condition_config(self) -> Dict[str, Any]:
        """获取条件配置
        
        Returns:
            条件配置
        """
        with self._condition_cache_lock:
            # 检查缓存
            if (self._condition_cache is not None and 
                self._condition_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_condition():
                    logger.debug("从缓存获取条件配置")
                    return self._condition_cache.copy()
                else:
                    # 缓存过期，清除
                    self._condition_cache = None
                    self._condition_cache_timestamp = None
            
            # 从配置实现获取
            condition_config = self._edge_impl.get_condition_config()
            
            # 缓存配置
            self._condition_cache = condition_config.copy()
            self._condition_cache_timestamp = time.time()
            logger.debug("获取并缓存条件配置")
            
            return condition_config
    
    def get_transformation_config(self) -> Dict[str, Any]:
        """获取数据转换配置
        
        Returns:
            数据转换配置
        """
        with self._transformation_cache_lock:
            # 检查缓存
            if (self._transformation_cache is not None and 
                self._transformation_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_transformation():
                    logger.debug("从缓存获取转换配置")
                    return self._transformation_cache.copy()
                else:
                    # 缓存过期，清除
                    self._transformation_cache = None
                    self._transformation_cache_timestamp = None
            
            # 从配置实现获取
            transformation_config = self._edge_impl.get_transformation_config()
            
            # 缓存配置
            self._transformation_cache = transformation_config.copy()
            self._transformation_cache_timestamp = time.time()
            logger.debug("获取并缓存转换配置")
            
            return transformation_config
    
    def get_node_references(self) -> Dict[str, str]:
        """获取节点引用
        
        Returns:
            节点引用字典
        """
        with self._node_refs_cache_lock:
            # 检查缓存
            if (self._node_refs_cache is not None and 
                self._node_refs_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_node_refs():
                    logger.debug("从缓存获取节点引用")
                    return self._node_refs_cache.copy()
                else:
                    # 缓存过期，清除
                    self._node_refs_cache = None
                    self._node_refs_cache_timestamp = None
            
            # 从配置实现获取
            node_refs = self._edge_impl.get_node_references()
            
            # 缓存配置
            self._node_refs_cache = node_refs.copy()
            self._node_refs_cache_timestamp = time.time()
            logger.debug("获取并缓存节点引用")
            
            return node_refs
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config("edge")
        if key in config:
            return config[key]
        
        return default
    
    def validate_edge_config(self) -> List[str]:
        """验证边配置
        
        Returns:
            验证错误列表
        """
        return self._edge_impl.validate_edge_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        return self._edge_impl.get_config_summary()
    
    def clear_edge_cache(self, edge_name: Optional[str] = None):
        """清除边配置缓存
        
        Args:
            edge_name: 边名称，如果为None则清除所有边缓存
        """
        with self._edge_cache_lock:
            if edge_name:
                if edge_name in self._edge_cache:
                    del self._edge_cache[edge_name]
                    del self._edge_cache_timestamps[edge_name]
                    logger.debug(f"清除边配置缓存: {edge_name}")
            else:
                self._edge_cache.clear()
                self._edge_cache_timestamps.clear()
                logger.debug("清除所有边配置缓存")
    
    def clear_condition_cache(self):
        """清除条件配置缓存"""
        with self._condition_cache_lock:
            self._condition_cache = None
            self._condition_cache_timestamp = None
            logger.debug("清除条件配置缓存")
    
    def clear_transformation_cache(self):
        """清除转换配置缓存"""
        with self._transformation_cache_lock:
            self._transformation_cache = None
            self._transformation_cache_timestamp = None
            logger.debug("清除转换配置缓存")
    
    def clear_node_refs_cache(self):
        """清除节点引用缓存"""
        with self._node_refs_cache_lock:
            self._node_refs_cache = None
            self._node_refs_cache_timestamp = None
            logger.debug("清除节点引用缓存")
    
    def clear_cache(self, config_name: Optional[str] = None):
        """清除缓存
        
        Args:
            config_name: 配置名称，如果为None则清除所有缓存
        """
        if config_name is None:
            self.clear_edge_cache()
            self.clear_condition_cache()
            self.clear_transformation_cache()
            self.clear_node_refs_cache()
        else:
            # 尝试清除特定边缓存
            self.clear_edge_cache(config_name)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._edge_cache_lock, self._condition_cache_lock, self._transformation_cache_lock, self._node_refs_cache_lock:
            return {
                "edge_cache_size": len(self._edge_cache),
                "edge_cache_keys": list(self._edge_cache.keys()),
                "condition_cached": self._condition_cache is not None,
                "condition_cache_timestamp": self._condition_cache_timestamp,
                "transformation_cached": self._transformation_cache is not None,
                "transformation_cache_timestamp": self._transformation_cache_timestamp,
                "node_refs_cached": self._node_refs_cache is not None,
                "node_refs_cache_timestamp": self._node_refs_cache_timestamp,
                "cache_ttl": self.cache_ttl,
                "cache_enabled": self.cache_enabled
            }
    
    def preload_common_configs(self):
        """预加载常用配置
        
        预加载常用的边配置、条件配置、转换配置和节点引用到缓存中。
        """
        logger.debug("开始预加载常用配置")
        
        # 预加载边配置
        edge_config = self.get_config("edge")
        edge_name = edge_config.get("name")
        if edge_name:
            self.get_edge_config(edge_name)
        
        # 预加载条件配置
        self.get_condition_config()
        
        # 预加载转换配置
        self.get_transformation_config()
        
        # 预加载节点引用
        self.get_node_references()
        
        logger.debug("常用配置预加载完成")
    
    def refresh_config(self, config_name: Optional[str] = None):
        """刷新配置
        
        Args:
            config_name: 配置名称，如果为None则刷新所有配置
        """
        logger.debug(f"刷新配置: {config_name or '全部'}")
        
        # 清除相关缓存
        self.clear_cache(config_name)
        
        # 重新加载配置
        if config_name:
            # 尝试刷新特定配置
            self.get_edge_config(config_name)
        else:
            # 刷新所有配置
            self.get_config("edge")
            self.preload_common_configs()
        
        logger.debug("配置刷新完成")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            提供者统计信息
        """
        # 获取基础缓存统计
        stats = self._get_cache_stats()
        
        # 添加Edge特定的统计信息
        edge_stats = {
            "edge_name": self.get_config_value("name"),
            "edge_type": self.get_config_value("type"),
            "from_node": self.get_config_value("from"),
            "to_node": self.get_config_value("to"),
            "timeout": self.get_config_value("timeout"),
            "retry_attempts": self.get_config_value("retry_attempts"),
            "enable_tracing": self.get_config_value("enable_tracing", False),
            "has_condition": self.get_config_value("has_condition", False),
            "has_path_map": self.get_config_value("has_path_map", False),
            "cache_stats": self.get_cache_stats()
        }
        
        stats.update({"edge_specific": edge_stats})
        return stats
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        # 对于Edge配置，直接返回配置数据
        # 在实际应用中，可以转换为Pydantic模型
        return config_data
    
    def _is_cache_valid_for_edge(self, edge_name: str) -> bool:
        """检查边缓存是否有效（内部使用的辅助方法）
        
        Args:
            edge_name: 边名称
            
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if edge_name not in self._edge_cache_timestamps:
            return False
        
        age = time.time() - self._edge_cache_timestamps[edge_name]
        return age < self.cache_ttl
    
    def _is_cache_valid_for_condition(self) -> bool:
        """检查条件缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._condition_cache_timestamp is None:
            return False
        
        age = time.time() - self._condition_cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_valid_for_transformation(self) -> bool:
        """检查转换缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._transformation_cache_timestamp is None:
            return False
        
        age = time.time() - self._transformation_cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_valid_for_node_refs(self) -> bool:
        """检查节点引用缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._node_refs_cache_timestamp is None:
            return False
        
        age = time.time() - self._node_refs_cache_timestamp
        return age < self.cache_ttl