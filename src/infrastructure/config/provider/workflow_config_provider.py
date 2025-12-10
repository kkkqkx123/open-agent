"""Workflow配置提供者

提供Workflow模块的配置获取、缓存和管理功能。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
import logging
import time
from threading import RLock
from datetime import datetime

from .base_provider import BaseConfigProvider
from ..impl.workflow_config_impl import WorkflowConfigImpl
from ..impl.base_impl import IConfigImpl

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class WorkflowConfigProvider(BaseConfigProvider):
    """Workflow配置提供者
    
    提供Workflow模块的配置获取、缓存和管理功能。
    支持工作流配置、节点配置、边配置的获取和管理。
    """
    
    def __init__(self, config_impl: IConfigImpl):
        """初始化Workflow配置提供者
        
        Args:
            config_impl: Workflow配置实现
        """
        super().__init__("workflow", config_impl)
        
        # 确保配置实现是WorkflowConfigImpl
        if not isinstance(config_impl, WorkflowConfigImpl):
            raise TypeError("config_impl必须是WorkflowConfigImpl实例")
        
        self._workflow_impl: WorkflowConfigImpl = config_impl
        
        # 工作流配置缓存
        self._workflow_cache: Dict[str, Dict[str, Any]] = {}
        self._workflow_cache_timestamps: Dict[str, float] = {}
        self._workflow_cache_lock = RLock()
        
        # 节点配置缓存
        self._node_cache: Dict[str, Dict[str, Any]] = {}
        self._node_cache_timestamps: Dict[str, float] = {}
        self._node_cache_lock = RLock()
        
        # 边配置缓存
        self._edge_cache: Dict[str, Dict[str, Any]] = {}
        self._edge_cache_timestamps: Dict[str, float] = {}
        self._edge_cache_lock = RLock()
        
        logger.debug("Workflow配置提供者初始化完成")
    
    def get_workflow_config(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """获取工作流配置
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            工作流配置，如果不存在则返回None
        """
        with self._workflow_cache_lock:
            # 检查缓存
            if workflow_name in self._workflow_cache:
                # 检查缓存是否有效
                if self._is_cache_valid_for_workflow(workflow_name):
                    logger.debug(f"从缓存获取工作流配置: {workflow_name}")
                    return self._workflow_cache[workflow_name].copy()
                else:
                    # 缓存过期，清除
                    del self._workflow_cache[workflow_name]
                    del self._workflow_cache_timestamps[workflow_name]
            
            # 从配置实现获取
            workflow_config = self._workflow_impl.get_workflow_config(workflow_name)
            
            if workflow_config:
                # 缓存配置
                self._workflow_cache[workflow_name] = workflow_config.copy()
                self._workflow_cache_timestamps[workflow_name] = time.time()
                logger.debug(f"获取并缓存工作流配置: {workflow_name}")
            
            return workflow_config
    
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
            node_config = self._workflow_impl.get_node_config(node_name)
            
            if node_config:
                # 缓存配置
                self._node_cache[node_name] = node_config.copy()
                self._node_cache_timestamps[node_name] = time.time()
                logger.debug(f"获取并缓存节点配置: {node_name}")
            
            return node_config
    
    def get_edge_config(self, from_node: str, to_node: str) -> Optional[Dict[str, Any]]:
        """获取边配置
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            
        Returns:
            边配置，如果不存在则返回None
        """
        edge_key = f"{from_node}_to_{to_node}"
        
        with self._edge_cache_lock:
            # 检查缓存
            if edge_key in self._edge_cache:
                # 检查缓存是否有效
                if self._is_cache_valid_for_edge(edge_key):
                    logger.debug(f"从缓存获取边配置: {edge_key}")
                    return self._edge_cache[edge_key].copy()
                else:
                    # 缓存过期，清除
                    del self._edge_cache[edge_key]
                    del self._edge_cache_timestamps[edge_key]
            
            # 从配置实现获取
            edge_config = self._workflow_impl.get_edge_config(from_node, to_node)
            
            if edge_config:
                # 缓存配置
                self._edge_cache[edge_key] = edge_config.copy()
                self._edge_cache_timestamps[edge_key] = time.time()
                logger.debug(f"获取并缓存边配置: {edge_key}")
            
            return edge_config
    
    def get_state_schema(self) -> Dict[str, Any]:
        """获取状态模式
        
        Returns:
            状态模式配置
        """
        return self._workflow_impl.get_state_schema()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config("workflow")
        if key in config:
            return config[key]
        
        return default
    
    def list_nodes(self) -> List[str]:
        """列出所有节点
        
        Returns:
            节点名称列表
        """
        return self._workflow_impl.list_nodes()
    
    def list_edges(self) -> List[Dict[str, Any]]:
        """列出所有边
        
        Returns:
            边配置列表
        """
        return self._workflow_impl.list_edges()
    
    def validate_workflow_config(self) -> List[str]:
        """验证工作流配置
        
        Returns:
            验证错误列表
        """
        return self._workflow_impl.validate_workflow_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        return self._workflow_impl.get_config_summary()
    
    def clear_workflow_cache(self, workflow_name: Optional[str] = None):
        """清除工作流配置缓存
        
        Args:
            workflow_name: 工作流名称，如果为None则清除所有工作流缓存
        """
        with self._workflow_cache_lock:
            if workflow_name:
                if workflow_name in self._workflow_cache:
                    del self._workflow_cache[workflow_name]
                    del self._workflow_cache_timestamps[workflow_name]
                    logger.debug(f"清除工作流配置缓存: {workflow_name}")
            else:
                self._workflow_cache.clear()
                self._workflow_cache_timestamps.clear()
                logger.debug("清除所有工作流配置缓存")
    
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
    
    def clear_edge_cache(self, from_node: Optional[str] = None, to_node: Optional[str] = None):
        """清除边配置缓存
        
        Args:
            from_node: 起始节点，如果为None则清除所有边缓存
            to_node: 目标节点，如果为None则清除所有边缓存
        """
        with self._edge_cache_lock:
            if from_node and to_node:
                edge_key = f"{from_node}_to_{to_node}"
                if edge_key in self._edge_cache:
                    del self._edge_cache[edge_key]
                    del self._edge_cache_timestamps[edge_key]
                    logger.debug(f"清除边配置缓存: {edge_key}")
            else:
                self._edge_cache.clear()
                self._edge_cache_timestamps.clear()
                logger.debug("清除所有边配置缓存")
    
    def clear_cache(self, config_name: Optional[str] = None):
        """清除缓存
        
        Args:
            config_name: 配置名称，如果为None则清除所有缓存
        """
        if config_name is None:
            self.clear_workflow_cache()
            self.clear_node_cache()
            self.clear_edge_cache()
        else:
            # 尝试清除特定类型的缓存
            self.clear_workflow_cache(config_name)
            self.clear_node_cache(config_name)
            # 边缓存需要两个参数，这里不处理
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._workflow_cache_lock, self._node_cache_lock, self._edge_cache_lock:
            return {
                "workflow_cache_size": len(self._workflow_cache),
                "workflow_cache_keys": list(self._workflow_cache.keys()),
                "node_cache_size": len(self._node_cache),
                "node_cache_keys": list(self._node_cache.keys()),
                "edge_cache_size": len(self._edge_cache),
                "edge_cache_keys": list(self._edge_cache.keys()),
                "cache_ttl": self.cache_ttl,
                "cache_enabled": self.cache_enabled
            }
    
    def preload_common_configs(self):
        """预加载常用配置
        
        预加载常用的工作流、节点和边配置到缓存中。
        """
        logger.debug("开始预加载常用配置")
        
        # 预加载工作流配置
        workflow_config = self.get_config("workflow")
        workflow_name = workflow_config.get("workflow_name")
        if workflow_name:
            self.get_workflow_config(workflow_name)
        
        # 预加载节点配置
        nodes = self.list_nodes()
        for node_name in nodes[:5]:  # 预加载前5个节点
            self.get_node_config(node_name)
        
        # 预加载边配置
        edges = self.list_edges()
        for edge in edges[:5]:  # 预加载前5条边
            from_node = edge.get("from")
            to_node = edge.get("to")
            if from_node and to_node:
                self.get_edge_config(from_node, to_node)
        
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
            self.get_workflow_config(config_name)
            self.get_node_config(config_name)
        else:
            # 刷新所有配置
            self.get_config("workflow")
            self.preload_common_configs()
        
        logger.debug("配置刷新完成")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            提供者统计信息
        """
        # 获取基础缓存统计
        stats = self._get_cache_stats()
        
        # 添加Workflow特定的统计信息
        workflow_stats = {
            "total_nodes": len(self.list_nodes()),
            "total_edges": len(self.list_edges()),
            "workflow_name": self.get_config_value("workflow_name"),
            "workflow_type": self.get_config_value("workflow_type"),
            "cache_stats": self.get_cache_stats()
        }
        
        stats.update({"workflow_specific": workflow_stats})
        return stats
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        # 对于Workflow配置，直接返回配置数据
        # 在实际应用中，可以转换为Pydantic模型
        return config_data
    
    def _is_cache_valid_for_workflow(self, workflow_name: str) -> bool:
        """检查工作流缓存是否有效（内部使用的辅助方法）
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if workflow_name not in self._workflow_cache_timestamps:
            return False
        
        age = time.time() - self._workflow_cache_timestamps[workflow_name]
        return age < self.cache_ttl
    
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
    
    def _is_cache_valid_for_edge(self, edge_key: str) -> bool:
        """检查边缓存是否有效（内部使用的辅助方法）
        
        Args:
            edge_key: 边键
            
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if edge_key not in self._edge_cache_timestamps:
            return False
        
        age = time.time() - self._edge_cache_timestamps[edge_key]
        return age < self.cache_ttl