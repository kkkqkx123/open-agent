"""Graph配置提供者

提供Graph模块的配置获取、缓存和管理功能。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
import logging
import time
from threading import RLock
from datetime import datetime

from .base_provider import BaseConfigProvider
from ..impl.graph_config_impl import GraphConfigImpl
from ..impl.base_impl import IConfigImpl

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class GraphConfigProvider(BaseConfigProvider):
    """Graph配置提供者
    
    提供Graph模块的配置获取、缓存和管理功能。
    专注于图的结构定义，包括节点引用、边引用和状态模式。
    """
    
    def __init__(self, config_impl: IConfigImpl):
        """初始化Graph配置提供者
        
        Args:
            config_impl: Graph配置实现
        """
        super().__init__("graph", config_impl)
        
        # 确保配置实现是GraphConfigImpl
        if not isinstance(config_impl, GraphConfigImpl):
            raise TypeError("config_impl必须是GraphConfigImpl实例")
        
        self._graph_impl: GraphConfigImpl = config_impl
        
        # 图配置缓存
        self._graph_cache: Dict[str, Dict[str, Any]] = {}
        self._graph_cache_timestamps: Dict[str, float] = {}
        self._graph_cache_lock = RLock()
        
        # 节点引用缓存
        self._node_refs_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._node_refs_cache_timestamp: Optional[float] = None
        self._node_refs_cache_lock = RLock()
        
        # 边引用缓存
        self._edge_refs_cache: Optional[List[Dict[str, Any]]] = None
        self._edge_refs_cache_timestamp: Optional[float] = None
        self._edge_refs_cache_lock = RLock()
        
        # 状态模式缓存
        self._state_schema_cache: Optional[Dict[str, Any]] = None
        self._state_schema_cache_timestamp: Optional[float] = None
        self._state_schema_cache_lock = RLock()
        
        logger.debug("Graph配置提供者初始化完成")
    
    def get_graph_config(self, graph_name: str) -> Optional[Dict[str, Any]]:
        """获取图配置
        
        Args:
            graph_name: 图名称
            
        Returns:
            图配置，如果不存在则返回None
        """
        with self._graph_cache_lock:
            # 检查缓存
            if graph_name in self._graph_cache:
                # 检查缓存是否有效
                if self._is_cache_valid_for_graph(graph_name):
                    logger.debug(f"从缓存获取图配置: {graph_name}")
                    return self._graph_cache[graph_name].copy()
                else:
                    # 缓存过期，清除
                    del self._graph_cache[graph_name]
                    del self._graph_cache_timestamps[graph_name]
            
            # 从配置实现获取
            graph_config = self._graph_impl.get_graph_config(graph_name)
            
            if graph_config:
                # 缓存配置
                self._graph_cache[graph_name] = graph_config.copy()
                self._graph_cache_timestamps[graph_name] = time.time()
                logger.debug(f"获取并缓存图配置: {graph_name}")
            
            return graph_config
    
    def get_node_references(self) -> Dict[str, Dict[str, Any]]:
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
            node_refs = self._graph_impl.get_node_references()
            
            # 缓存配置
            self._node_refs_cache = node_refs.copy()
            self._node_refs_cache_timestamp = time.time()
            logger.debug("获取并缓存节点引用")
            
            return node_refs
    
    def get_edge_references(self) -> List[Dict[str, Any]]:
        """获取边引用
        
        Returns:
            边引用列表
        """
        with self._edge_refs_cache_lock:
            # 检查缓存
            if (self._edge_refs_cache is not None and 
                self._edge_refs_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_edge_refs():
                    logger.debug("从缓存获取边引用")
                    return self._edge_refs_cache.copy()
                else:
                    # 缓存过期，清除
                    self._edge_refs_cache = None
                    self._edge_refs_cache_timestamp = None
            
            # 从配置实现获取
            edge_refs = self._graph_impl.get_edge_references()
            
            # 缓存配置
            self._edge_refs_cache = edge_refs.copy()
            self._edge_refs_cache_timestamp = time.time()
            logger.debug("获取并缓存边引用")
            
            return edge_refs
    
    def get_state_schema(self) -> Dict[str, Any]:
        """获取状态模式
        
        Returns:
            状态模式配置
        """
        with self._state_schema_cache_lock:
            # 检查缓存
            if (self._state_schema_cache is not None and 
                self._state_schema_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_state_schema():
                    logger.debug("从缓存获取状态模式")
                    return self._state_schema_cache.copy()
                else:
                    # 缓存过期，清除
                    self._state_schema_cache = None
                    self._state_schema_cache_timestamp = None
            
            # 从配置实现获取
            state_schema = self._graph_impl.get_state_schema()
            
            # 缓存配置
            self._state_schema_cache = state_schema.copy()
            self._state_schema_cache_timestamp = time.time()
            logger.debug("获取并缓存状态模式")
            
            return state_schema
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config("graph")
        if key in config:
            return config[key]
        
        return default
    
    def list_nodes(self) -> List[str]:
        """列出所有节点
        
        Returns:
            节点名称列表
        """
        return self._graph_impl.list_nodes()
    
    def list_edges(self) -> List[Dict[str, Any]]:
        """列出所有边
        
        Returns:
            边配置列表
        """
        return self._graph_impl.list_edges()
    
    def validate_graph_config(self) -> List[str]:
        """验证图配置
        
        Returns:
            验证错误列表
        """
        return self._graph_impl.validate_graph_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        return self._graph_impl.get_config_summary()
    
    def clear_graph_cache(self, graph_name: Optional[str] = None):
        """清除图配置缓存
        
        Args:
            graph_name: 图名称，如果为None则清除所有图缓存
        """
        with self._graph_cache_lock:
            if graph_name:
                if graph_name in self._graph_cache:
                    del self._graph_cache[graph_name]
                    del self._graph_cache_timestamps[graph_name]
                    logger.debug(f"清除图配置缓存: {graph_name}")
            else:
                self._graph_cache.clear()
                self._graph_cache_timestamps.clear()
                logger.debug("清除所有图配置缓存")
    
    def clear_node_refs_cache(self):
        """清除节点引用缓存"""
        with self._node_refs_cache_lock:
            self._node_refs_cache = None
            self._node_refs_cache_timestamp = None
            logger.debug("清除节点引用缓存")
    
    def clear_edge_refs_cache(self):
        """清除边引用缓存"""
        with self._edge_refs_cache_lock:
            self._edge_refs_cache = None
            self._edge_refs_cache_timestamp = None
            logger.debug("清除边引用缓存")
    
    def clear_state_schema_cache(self):
        """清除状态模式缓存"""
        with self._state_schema_cache_lock:
            self._state_schema_cache = None
            self._state_schema_cache_timestamp = None
            logger.debug("清除状态模式缓存")
    
    def clear_cache(self, config_name: Optional[str] = None):
        """清除缓存
        
        Args:
            config_name: 配置名称，如果为None则清除所有缓存
        """
        if config_name is None:
            self.clear_graph_cache()
            self.clear_node_refs_cache()
            self.clear_edge_refs_cache()
            self.clear_state_schema_cache()
        else:
            # 尝试清除特定图缓存
            self.clear_graph_cache(config_name)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._graph_cache_lock, self._node_refs_cache_lock, self._edge_refs_cache_lock, self._state_schema_cache_lock:
            return {
                "graph_cache_size": len(self._graph_cache),
                "graph_cache_keys": list(self._graph_cache.keys()),
                "node_refs_cached": self._node_refs_cache is not None,
                "node_refs_cache_timestamp": self._node_refs_cache_timestamp,
                "edge_refs_cached": self._edge_refs_cache is not None,
                "edge_refs_cache_timestamp": self._edge_refs_cache_timestamp,
                "state_schema_cached": self._state_schema_cache is not None,
                "state_schema_cache_timestamp": self._state_schema_cache_timestamp,
                "cache_ttl": self.cache_ttl,
                "cache_enabled": self.cache_enabled
            }
    
    def preload_common_configs(self):
        """预加载常用配置
        
        预加载常用的图配置、节点引用、边引用和状态模式到缓存中。
        """
        logger.debug("开始预加载常用配置")
        
        # 预加载图配置
        graph_config = self.get_config("graph")
        graph_name = graph_config.get("name")
        if graph_name:
            self.get_graph_config(graph_name)
        
        # 预加载节点引用
        self.get_node_references()
        
        # 预加载边引用
        self.get_edge_references()
        
        # 预加载状态模式
        self.get_state_schema()
        
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
            self.get_graph_config(config_name)
        else:
            # 刷新所有配置
            self.get_config("graph")
            self.preload_common_configs()
        
        logger.debug("配置刷新完成")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            提供者统计信息
        """
        # 获取基础缓存统计
        stats = self._get_cache_stats()
        
        # 添加Graph特定的统计信息
        graph_stats = {
            "total_nodes": len(self.list_nodes()),
            "total_edges": len(self.list_edges()),
            "graph_name": self.get_config_value("name"),
            "graph_id": self.get_config_value("id"),
            "enable_tracing": self.get_config_value("enable_tracing", False),
            "cache_stats": self.get_cache_stats()
        }
        
        stats.update({"graph_specific": graph_stats})
        return stats
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        # 对于Graph配置，直接返回配置数据
        # 在实际应用中，可以转换为Pydantic模型
        return config_data
    
    def _is_cache_valid_for_graph(self, graph_name: str) -> bool:
        """检查图缓存是否有效（内部使用的辅助方法）
        
        Args:
            graph_name: 图名称
            
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if graph_name not in self._graph_cache_timestamps:
            return False
        
        age = time.time() - self._graph_cache_timestamps[graph_name]
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
    
    def _is_cache_valid_for_edge_refs(self) -> bool:
        """检查边引用缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._edge_refs_cache_timestamp is None:
            return False
        
        age = time.time() - self._edge_refs_cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_valid_for_state_schema(self) -> bool:
        """检查状态模式缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._state_schema_cache_timestamp is None:
            return False
        
        age = time.time() - self._state_schema_cache_timestamp
        return age < self.cache_ttl