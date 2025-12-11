"""基础配置数据模型

提供基础设施层的配置数据结构，不包含业务逻辑。
"""

from typing import Any, Dict, Optional


class ConfigData:
    """基础配置数据结构
    
    纯数据容器，不包含业务逻辑。
    用于在基础设施层和核心层之间传递配置数据。
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """初始化配置数据
        
        Args:
            data: 配置数据字典
        """
        self.data = data or {}
        self.metadata: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.data[key] = value
    
    def has(self, key: str) -> bool:
        """检查是否存在配置键
        
        Args:
            key: 配置键
            
        Returns:
            是否存在
        """
        return key in self.data
    
    def update(self, data: Dict[str, Any]) -> None:
        """更新配置数据
        
        Args:
            data: 要更新的数据
        """
        self.data.update(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            配置数据字典
        """
        return self.data.copy()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value


__all__ = [
    "ConfigData"
]