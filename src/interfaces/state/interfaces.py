"""核心状态接口定义

定义状态管理系统的基础接口，所有状态对象和管理器必须遵循此接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IState(ABC):
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
    def get_created_at(self) -> datetime:
        """获取创建时间戳
        
        Returns:
            创建时间戳
        """
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """获取最后更新时间戳
        
        Returns:
            最后更新时间戳
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
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典表示
        
        Returns:
            状态的字典表示
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IState':
        """从字典创建状态实例
        
        Args:
            data: 状态的字典表示
            
        Returns:
            新的状态实例
        """
        pass


class IStateManager(ABC):
    """状态管理器接口
    
    定义状态管理实现的契约，提供CRUD操作和生命周期管理。
    """
    
    @abstractmethod
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> IState:
        """创建新状态
        
        Args:
            state_id: 状态的唯一标识符
            initial_state: 初始状态数据
            
        Returns:
            创建的状态实例
        """
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[IState]:
        """根据ID获取状态
        
        Args:
            state_id: 状态的唯一标识符
            
        Returns:
            状态实例，如果未找到则返回None
        """
        pass
    
    @abstractmethod
    def update_state(self, state_id: str, updates: Dict[str, Any]) -> IState:
        """更新状态
        
        Args:
            state_id: 状态的唯一标识符
            updates: 要应用的更新字典
            
        Returns:
            更新后的状态实例
        """
        pass
    
    @abstractmethod
    def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态的唯一标识符
            
        Returns:
            如果状态被删除则返回True，如果未找到则返回False
        """
        pass
    
    @abstractmethod
    def list_states(self) -> List[str]:
        """列出所有状态ID
        
        Returns:
            状态ID列表
        """
        pass