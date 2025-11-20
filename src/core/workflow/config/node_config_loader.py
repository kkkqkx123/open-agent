"""节点配置加载器

负责从配置文件中加载节点的默认配置，并提供配置合并功能。
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ...common.interfaces import IConfigLoader
from ....services.container import get_global_container


class NodeConfigLoader:
    """节点配置加载器"""
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None) -> None:
        """初始化节点配置加载器
        
        Args:
            config_loader: 配置加载器实例，如果为None则从容器获取
        """
        self._config_loader = config_loader
        self._node_configs: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    def _get_config_loader(self) -> IConfigLoader:
        """获取配置加载器实例"""
        if self._config_loader is None:
            container = get_global_container()
            self._config_loader = container.get(IConfigLoader)  # type: ignore
        return self._config_loader
    
    def load_configs(self) -> None:
        """加载所有节点配置"""
        if self._loaded:
            return
        
        config_loader = self._get_config_loader()
        # 这里应该从配置文件中加载节点配置
        # 暂时使用空配置
        self._node_configs = {}
        self._loaded = True
    
    def get_config(self, node_type: str) -> Dict[str, Any]:
        """获取指定节点类型的配置
        
        Args:
            node_type: 节点类型
            
        Returns:
            节点配置字典
        """
        if not self._loaded:
            self.load_configs()
        
        return self._node_configs.get(node_type, {})
    
    def merge_configs(self, node_type: str, runtime_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和运行时配置
        
        Args:
            node_type: 节点类型
            runtime_config: 运行时配置
            
        Returns:
            合并后的配置
        """
        default_config = self.get_config(node_type)
        merged_config = default_config.copy()
        merged_config.update(runtime_config)
        return merged_config
    
    def get_config_value(self, node_type: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            node_type: 节点类型
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_config(node_type)
        return config.get(key, default)


# 全局节点配置加载器实例
_node_config_loader: Optional[NodeConfigLoader] = None


def get_node_config_loader() -> NodeConfigLoader:
    """获取全局节点配置加载器实例
    
    Returns:
        节点配置加载器实例
    """
    global _node_config_loader
    if _node_config_loader is None:
        _node_config_loader = NodeConfigLoader()
    return _node_config_loader