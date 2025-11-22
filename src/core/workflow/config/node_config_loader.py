"""节点配置加载器

负责从配置文件中加载节点的默认配置，并提供配置合并功能。
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from ....interfaces.common import IConfigLoader
from ....services.container import get_global_container

logger = logging.getLogger(__name__)


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
        
        try:
            # 1. 加载节点组配置
            group_config = {}
            try:
                group_config = config_loader.load_config("nodes/_group.yaml") or {}
            except Exception as e:
                logger.warning(f"无法加载节点组配置: {e}")
            
            # 2. 加载各节点特定配置
            from pathlib import Path
            import os
            
            configs_dir = Path("configs/nodes")
            if not configs_dir.exists():
                # 尝试相对于项目根目录的路径
                project_root = Path(__file__).parent.parent.parent.parent
                configs_dir = project_root / "configs" / "nodes"
            
            if configs_dir.exists():
                for node_file in configs_dir.glob("*.yaml"):
                    if node_file.name != "_group.yaml":
                        try:
                            node_config = config_loader.load_config(f"nodes/{node_file.name}") or {}
                            node_type = node_file.stem
                            
                            # 3. 处理继承关系
                            if "inherits_from" in node_config:
                                base_path = node_config["inherits_from"]
                                base_config = self._resolve_inheritance(base_path, group_config)
                                # 合并基础配置和节点特定配置
                                merged_config = self._deep_merge(base_config, node_config)
                                self._node_configs[node_type] = merged_config
                            else:
                                self._node_configs[node_type] = node_config
                                
                            logger.debug(f"已加载节点配置: {node_type}")
                        except Exception as e:
                            logger.error(f"加载节点配置失败 {node_file.name}: {e}")
            else:
                logger.warning(f"节点配置目录不存在: {configs_dir}")
            
            self._loaded = True
            logger.info(f"节点配置加载完成，共加载 {len(self._node_configs)} 个节点配置")
            
        except Exception as e:
            logger.error(f"加载节点配置失败: {e}")
            # 使用空配置作为后备
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
    
    def _resolve_inheritance(self, inheritance_path: str, group_config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置继承路径
        
        Args:
            inheritance_path: 继承路径，格式为 "file.yaml#node_type"
            group_config: 组配置字典
            
        Returns:
            继承的基础配置
        """
        try:
            if "#" in inheritance_path:
                file_path, node_type = inheritance_path.split("#", 1)
                if file_path == "_group.yaml" and node_type in group_config:
                    return group_config[node_type]
            return {}
        except Exception as e:
            logger.warning(f"解析配置继承失败 {inheritance_path}: {e}")
            return {}
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典
        
        Args:
            base: 基础字典
            override: 覆盖字典
            
        Returns:
            合并后的字典
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


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