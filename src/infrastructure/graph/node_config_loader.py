"""节点配置加载器

负责从配置文件中加载节点的默认配置，并提供配置合并功能。
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..config.loader.file_config_loader import IConfigLoader
from ..container import get_global_container


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
            self._config_loader = container.get(IConfigLoader)
        return self._config_loader
    
    def _load_configs(self) -> None:
        """加载节点配置"""
        if self._loaded:
            return
            
        try:
            # 首先尝试从配置加载器加载
            try:
                config_loader = self._get_config_loader()
                group_config = config_loader.load("nodes/_group.yaml")
                self._node_configs = group_config
                self._loaded = True
                return
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"从配置加载器加载节点配置失败: {e}")
            
            # 如果配置加载器失败，尝试直接加载文件
            try:
                import yaml
                from pathlib import Path
                
                config_path = Path("configs/nodes/_group.yaml")
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._node_configs = yaml.safe_load(f) or {}
                    self._loaded = True
                    return
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"直接加载节点配置文件失败: {e}")
            
            # 如果所有方法都失败，使用空配置
            self._node_configs = {}
            self._loaded = True
            
        except Exception:
            # 如果加载失败，使用空配置
            self._node_configs = {}
            self._loaded = True
    
    def get_node_config(self, node_type: str) -> Dict[str, Any]:
        """获取节点类型的默认配置
        
        Args:
            node_type: 节点类型
            
        Returns:
            节点默认配置字典
        """
        self._load_configs()
        return self._node_configs.get(node_type, {}).copy()
    
    def merge_configs(self, node_type: str, runtime_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并节点默认配置和运行时配置
        
        Args:
            node_type: 节点类型
            runtime_config: 运行时配置
            
        Returns:
            合并后的配置
        """
        default_config = self.get_node_config(node_type)
        merged_config = default_config.copy()
        merged_config.update(runtime_config)
        return merged_config
    
    def get_config_value(self, node_type: str, key: str, default: Any = None) -> Any:
        """获取节点配置中的特定值
        
        Args:
            node_type: 节点类型
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        node_config = self.get_node_config(node_type)
        return node_config.get(key, default)


# 全局节点配置加载器实例
_global_loader: Optional[NodeConfigLoader] = None


def get_node_config_loader() -> NodeConfigLoader:
    """获取全局节点配置加载器
    
    Returns:
        NodeConfigLoader: 全局节点配置加载器
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = NodeConfigLoader()
    return _global_loader