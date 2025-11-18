"""节点配置加载器

负责从配置文件中加载节点的默认配置，并提供配置合并功能。
"""

from typing import Dict, Any, Optional
from pathlib import Path

from src.core.config.loader.file_config_loader import IConfigLoader
from src.services.container import get_global_container


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