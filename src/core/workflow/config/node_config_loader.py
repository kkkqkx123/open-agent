"""节点配置加载器

负责从配置文件中加载节点的默认配置，并提供配置合并功能。
"""

from typing import Dict, Any, Optional
from pathlib import Path

from src.interfaces.common_infra import IConfigLoader


class NodeConfigLoader:
    """节点配置加载器"""
    
    def __init__(self, config_loader: IConfigLoader) -> None:
        """初始化节点配置加载器

        Args:
            config_loader: 配置加载器实例
        """
        self._config_loader = config_loader
        self._node_configs: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    def load_configs(self) -> None:
        """加载所有节点配置"""
        if self._loaded:
            return

        try:
            # 1. 加载节点组配置
            group_config = {}
            try:
                group_config = self._config_loader.load_config("nodes/_group.yaml") or {}
            except Exception:
                # 静默处理错误，使用空配置
                pass

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
                            node_config = self._config_loader.load_config(f"nodes/{node_file.name}") or {}
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
                        except Exception:
                            # 静默处理错误，继续加载其他配置
                            pass
            else:
                # 静默处理错误，使用空配置作为后备
                pass

            self._loaded = True

        except Exception:
            # 静默处理错误，使用空配置作为后备
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
                    node_config = group_config[node_type]
                    if isinstance(node_config, dict):
                        return node_config
            return {}
        except Exception:
            # 静默处理错误，返回空配置
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


def set_node_config_loader(config_loader: IConfigLoader) -> NodeConfigLoader:
    """设置节点配置加载器实例

    Args:
        config_loader: 配置加载器实例

    Returns:
        节点配置加载器实例
    """
    global _node_config_loader
    _node_config_loader = NodeConfigLoader(config_loader)
    return _node_config_loader


def get_node_config_loader() -> Optional[NodeConfigLoader]:
    """获取全局节点配置加载器实例

    Returns:
        节点配置加载器实例，如果未初始化则返回None
    """
    return _node_config_loader