"""Node配置提供者

提供Node模块的配置获取、缓存和管理功能。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
import logging
import time
from threading import RLock
from datetime import datetime

from .base_provider import BaseConfigProvider
from ..impl.node_config_impl import NodeConfigImpl
from ..impl.base_impl import IConfigImpl

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class NodeConfigProvider(BaseConfigProvider):
    """Node配置提供者
    
    提供Node模块的配置获取、缓存和管理功能。
    专注于节点的具体配置，包括函数、类型、参数等。
    """
    
    def __init__(self, config_impl: IConfigImpl):
        """初始化Node配置提供者
        
        Args:
            config_impl: Node配置实现
        """
        super().__init__("node", config_impl)
        
        # 确保配置实现是NodeConfigImpl
        if not isinstance(config_impl, NodeConfigImpl):
            raise TypeError("config_impl必须是NodeConfigImpl实例")
        
        self._node_impl: NodeConfigImpl = config_impl
        
        # 节点配置缓存
        self._node_cache: Dict[str, Dict[str, Any]] = {}
        self._node_cache_timestamps: Dict[str, float] = {}
        self._node_cache_lock = RLock()
        
        # 函数配置缓存
        self._function_cache: Optional[Dict[str, Any]] = None
        self._function_cache_timestamp: Optional[float] = None
        self._function_cache_lock = RLock()
        
        # 输入参数缓存
        self._input_params_cache: Optional[Dict[str, Any]] = None
        self._input_params_cache_timestamp: Optional[float] = None
        self._input_params_cache_lock = RLock()
        
        # 输出参数缓存
        self._output_params_cache: Optional[Dict[str, Any]] = None
        self._output_params_cache_timestamp: Optional[float] = None
        self._output_params_cache_lock = RLock()
        
        # IO映射缓存
        self._io_mapping_cache: Optional[Dict[str, Any]] = None
        self._io_mapping_cache_timestamp: Optional[float] = None
        self._io_mapping_cache_lock = RLock()
        
        logger.debug("Node配置提供者初始化完成")
    
    def get_node_config(self, node_name: str) -> Optional[Dict[str, Any]]:
        """获取节点配置
        
        Args:
            node_name: 节点名称
            
        Returns:
            节点配置，如果不存在则返回None
        """
        with self._node_cache_lock:
            # 检查缓存
            if node_name in self._node_cache:
                # 检查缓存是否有效
                if self._is_cache_valid_for_node(node_name):
                    logger.debug(f"从缓存获取节点配置: {node_name}")
                    return self._node_cache[node_name].copy()
                else:
                    # 缓存过期，清除
                    del self._node_cache[node_name]
                    del self._node_cache_timestamps[node_name]
            
            # 从配置实现获取
            node_config = self._node_impl.get_node_config(node_name)
            
            if node_config:
                # 缓存配置
                self._node_cache[node_name] = node_config.copy()
                self._node_cache_timestamps[node_name] = time.time()
                logger.debug(f"获取并缓存节点配置: {node_name}")
            
            return node_config
    
    def get_function_config(self) -> Dict[str, Any]:
        """获取函数配置
        
        Returns:
            函数配置
        """
        with self._function_cache_lock:
            # 检查缓存
            if (self._function_cache is not None and 
                self._function_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_function():
                    logger.debug("从缓存获取函数配置")
                    return self._function_cache.copy()
                else:
                    # 缓存过期，清除
                    self._function_cache = None
                    self._function_cache_timestamp = None
            
            # 从配置实现获取
            function_config = self._node_impl.get_function_config()
            
            # 缓存配置
            self._function_cache = function_config.copy()
            self._function_cache_timestamp = time.time()
            logger.debug("获取并缓存函数配置")
            
            return function_config
    
    def get_input_parameters(self) -> Dict[str, Any]:
        """获取输入参数
        
        Returns:
            输入参数配置
        """
        with self._input_params_cache_lock:
            # 检查缓存
            if (self._input_params_cache is not None and 
                self._input_params_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_input_params():
                    logger.debug("从缓存获取输入参数")
                    return self._input_params_cache.copy()
                else:
                    # 缓存过期，清除
                    self._input_params_cache = None
                    self._input_params_cache_timestamp = None
            
            # 从配置实现获取
            input_params = self._node_impl.get_input_parameters()
            
            # 缓存配置
            self._input_params_cache = input_params.copy()
            self._input_params_cache_timestamp = time.time()
            logger.debug("获取并缓存输入参数")
            
            return input_params
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数
        
        Returns:
            输出参数配置
        """
        with self._output_params_cache_lock:
            # 检查缓存
            if (self._output_params_cache is not None and 
                self._output_params_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_output_params():
                    logger.debug("从缓存获取输出参数")
                    return self._output_params_cache.copy()
                else:
                    # 缓存过期，清除
                    self._output_params_cache = None
                    self._output_params_cache_timestamp = None
            
            # 从配置实现获取
            output_params = self._node_impl.get_output_parameters()
            
            # 缓存配置
            self._output_params_cache = output_params.copy()
            self._output_params_cache_timestamp = time.time()
            logger.debug("获取并缓存输出参数")
            
            return output_params
    
    def get_io_mapping(self) -> Dict[str, Any]:
        """获取输入输出映射
        
        Returns:
            输入输出映射配置
        """
        with self._io_mapping_cache_lock:
            # 检查缓存
            if (self._io_mapping_cache is not None and 
                self._io_mapping_cache_timestamp is not None):
                # 检查缓存是否有效
                if self._is_cache_valid_for_io_mapping():
                    logger.debug("从缓存获取IO映射")
                    return self._io_mapping_cache.copy()
                else:
                    # 缓存过期，清除
                    self._io_mapping_cache = None
                    self._io_mapping_cache_timestamp = None
            
            # 从配置实现获取
            io_mapping = self._node_impl.get_io_mapping()
            
            # 缓存配置
            self._io_mapping_cache = io_mapping.copy()
            self._io_mapping_cache_timestamp = time.time()
            logger.debug("获取并缓存IO映射")
            
            return io_mapping
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config("node")
        if key in config:
            return config[key]
        
        return default
    
    def validate_node_config(self) -> List[str]:
        """验证节点配置
        
        Returns:
            验证错误列表
        """
        return self._node_impl.validate_node_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        return self._node_impl.get_config_summary()
    
    def clear_node_cache(self, node_name: Optional[str] = None):
        """清除节点配置缓存
        
        Args:
            node_name: 节点名称，如果为None则清除所有节点缓存
        """
        with self._node_cache_lock:
            if node_name:
                if node_name in self._node_cache:
                    del self._node_cache[node_name]
                    del self._node_cache_timestamps[node_name]
                    logger.debug(f"清除节点配置缓存: {node_name}")
            else:
                self._node_cache.clear()
                self._node_cache_timestamps.clear()
                logger.debug("清除所有节点配置缓存")
    
    def clear_function_cache(self):
        """清除函数配置缓存"""
        with self._function_cache_lock:
            self._function_cache = None
            self._function_cache_timestamp = None
            logger.debug("清除函数配置缓存")
    
    def clear_input_params_cache(self):
        """清除输入参数缓存"""
        with self._input_params_cache_lock:
            self._input_params_cache = None
            self._input_params_cache_timestamp = None
            logger.debug("清除输入参数缓存")
    
    def clear_output_params_cache(self):
        """清除输出参数缓存"""
        with self._output_params_cache_lock:
            self._output_params_cache = None
            self._output_params_cache_timestamp = None
            logger.debug("清除输出参数缓存")
    
    def clear_io_mapping_cache(self):
        """清除IO映射缓存"""
        with self._io_mapping_cache_lock:
            self._io_mapping_cache = None
            self._io_mapping_cache_timestamp = None
            logger.debug("清除IO映射缓存")
    
    def clear_cache(self, config_name: Optional[str] = None):
        """清除缓存
        
        Args:
            config_name: 配置名称，如果为None则清除所有缓存
        """
        if config_name is None:
            self.clear_node_cache()
            self.clear_function_cache()
            self.clear_input_params_cache()
            self.clear_output_params_cache()
            self.clear_io_mapping_cache()
        else:
            # 尝试清除特定节点缓存
            self.clear_node_cache(config_name)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._node_cache_lock, self._function_cache_lock, self._input_params_cache_lock, self._output_params_cache_lock, self._io_mapping_cache_lock:
            return {
                "node_cache_size": len(self._node_cache),
                "node_cache_keys": list(self._node_cache.keys()),
                "function_cached": self._function_cache is not None,
                "function_cache_timestamp": self._function_cache_timestamp,
                "input_params_cached": self._input_params_cache is not None,
                "input_params_cache_timestamp": self._input_params_cache_timestamp,
                "output_params_cached": self._output_params_cache is not None,
                "output_params_cache_timestamp": self._output_params_cache_timestamp,
                "io_mapping_cached": self._io_mapping_cache is not None,
                "io_mapping_cache_timestamp": self._io_mapping_cache_timestamp,
                "cache_ttl": self.cache_ttl,
                "cache_enabled": self.cache_enabled
            }
    
    def preload_common_configs(self):
        """预加载常用配置
        
        预加载常用的节点配置、函数配置、参数配置和IO映射到缓存中。
        """
        logger.debug("开始预加载常用配置")
        
        # 预加载节点配置
        node_config = self.get_config("node")
        node_name = node_config.get("name")
        if node_name:
            self.get_node_config(node_name)
        
        # 预加载函数配置
        self.get_function_config()
        
        # 预加载输入参数
        self.get_input_parameters()
        
        # 预加载输出参数
        self.get_output_parameters()
        
        # 预加载IO映射
        self.get_io_mapping()
        
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
            self.get_node_config(config_name)
        else:
            # 刷新所有配置
            self.get_config("node")
            self.preload_common_configs()
        
        logger.debug("配置刷新完成")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            提供者统计信息
        """
        # 获取基础缓存统计
        stats = self._get_cache_stats()
        
        # 添加Node特定的统计信息
        node_stats = {
            "node_name": self.get_config_value("name"),
            "node_type": self.get_config_value("type"),
            "function_name": self.get_config_value("function_name"),
            "timeout": self.get_config_value("timeout"),
            "retry_attempts": self.get_config_value("retry_attempts"),
            "enable_tracing": self.get_config_value("enable_tracing", False),
            "cache_stats": self.get_cache_stats()
        }
        
        stats.update({"node_specific": node_stats})
        return stats
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        # 对于Node配置，直接返回配置数据
        # 在实际应用中，可以转换为Pydantic模型
        return config_data
    
    def _is_cache_valid_for_node(self, node_name: str) -> bool:
        """检查节点缓存是否有效（内部使用的辅助方法）
        
        Args:
            node_name: 节点名称
            
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if node_name not in self._node_cache_timestamps:
            return False
        
        age = time.time() - self._node_cache_timestamps[node_name]
        return age < self.cache_ttl
    
    def _is_cache_valid_for_function(self) -> bool:
        """检查函数缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._function_cache_timestamp is None:
            return False
        
        age = time.time() - self._function_cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_valid_for_input_params(self) -> bool:
        """检查输入参数缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._input_params_cache_timestamp is None:
            return False
        
        age = time.time() - self._input_params_cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_valid_for_output_params(self) -> bool:
        """检查输出参数缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._output_params_cache_timestamp is None:
            return False
        
        age = time.time() - self._output_params_cache_timestamp
        return age < self.cache_ttl
    
    def _is_cache_valid_for_io_mapping(self) -> bool:
        """检查IO映射缓存是否有效（内部使用的辅助方法）
        
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if self._io_mapping_cache_timestamp is None:
            return False
        
        age = time.time() - self._io_mapping_cache_timestamp
        return age < self.cache_ttl