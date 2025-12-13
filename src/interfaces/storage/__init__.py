"""
存储接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IStorageService(ABC):
    """存储服务接口"""
    
    @abstractmethod
    def save(self, key: str, data: Any) -> None:
        """保存数据"""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """加载数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查数据是否存在"""
        pass

__all__ = ["IStorageService"]