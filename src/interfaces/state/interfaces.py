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
    
     
class IStateCache(ABC):
    """状态缓存接口
    
    定义状态缓存的基本契约，提供同步缓存操作接口。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional['IState']:
        """获取缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            状态实例，如果未找到或已过期则返回None
        """
        pass
    
    @abstractmethod
    def put(self, key: str, state: 'IState', ttl: Optional[int] = None) -> None:
        """设置缓存状态
        
        Args:
            key: 状态ID
            state: 状态实例
            ttl: TTL（秒），如果为None则使用默认值
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存中的状态数量
        """
        pass
    
    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """获取所有键
        
        Returns:
            所有状态ID列表
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, 'IState']:
        """批量获取缓存状态
        
        Args:
            keys: 状态ID列表
            
        Returns:
            状态字典
        """
        pass
    
    @abstractmethod
    def set_many(self, states: Dict[str, 'IState'], ttl: Optional[int] = None) -> None:
        """批量设置缓存状态
        
        Args:
            states: 状态字典
            ttl: TTL（秒）
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """清理过期缓存项
        
        Returns:
            清理的项数
        """
        pass

