"""核心状态接口定义

定义状态管理系统的基础接口，所有状态对象和管理器必须遵循此接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..common_domain import ISerializable, ITimestamped


class IState(ISerializable, ITimestamped, ABC):
    """基础状态接口
    
    定义状态对象的基本契约，所有状态实现必须遵循此接口。
    这是纯粹的状态抽象，不包含特定于任何执行引擎的功能。
    """
    
    @abstractmethod
    def get_data(self, key: str, default: Any = None) -> Any:
        """从状态中获取数据
        
        Args:
            key: 要获取数据的键
            default: 如果键不存在时返回的默认值
            
        Returns:
            与键关联的值，如果未找到则返回默认值
        """
        pass
    
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """在状态中设置数据
        
        Args:
            key: 要设置的键
            value: 要与键关联的值
        """
        pass
    
    @abstractmethod
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """从状态中获取元数据
        
        Args:
            key: 要获取元数据的键
            default: 如果键不存在时返回的默认值
            
        Returns:
            与键关联的元数据值，如果未找到则返回默认值
        """
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """在状态中设置元数据
        
        Args:
            key: 要设置的键
            value: 要与键关联的元数据值
        """
        pass
    
    @abstractmethod
    def get_id(self) -> Optional[str]:
        """获取状态ID
        
        Returns:
            状态ID，如果未设置则返回None
        """
        pass
    
    @abstractmethod
    def set_id(self, id: str) -> None:
        """设置状态ID
        
        Args:
            id: 要设置的ID
        """
        pass
    
    
    @abstractmethod
    def is_complete(self) -> bool:
        """检查状态是否完成
        
        Returns:
            如果完成则返回True，否则返回False
        """
        pass
    
    @abstractmethod
    def mark_complete(self) -> None:
        """将状态标记为完成"""
        pass
    
    