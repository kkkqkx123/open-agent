"""状态生命周期管理接口定义

定义状态生命周期管理的接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from .base import IState


class IStateLifecycleManager(ABC):
    """状态生命周期管理器接口
    
    定义状态生命周期管理的实现契约。
    """
    
    @abstractmethod
    def initialize_state(self, state: IState) -> None:
        """初始化状态
        
        Args:
            state: 要初始化的状态
        """
        pass
    
    @abstractmethod
    def cleanup_state(self, state: IState) -> None:
        """清理状态
        
        Args:
            state: 要清理的状态
        """
        pass
    
    @abstractmethod
    def validate_state(self, state: IState) -> List[str]:
        """验证状态
        
        Args:
            state: 要验证的状态
            
        Returns:
            验证错误列表，如果为空则表示验证通过
        """
        pass
    
    @abstractmethod
    def register_state(self, state: IState) -> None:
        """注册状态
        
        Args:
            state: 要注册的状态
        """
        pass
    
    @abstractmethod
    def unregister_state(self, state_id: str) -> None:
        """注销状态
        
        Args:
            state_id: 状态ID
        """
        pass
    
    @abstractmethod
    def on_state_saved(self, state: IState) -> None:
        """状态保存事件
        
        Args:
            state: 保存的状态
        """
        pass
    
    @abstractmethod
    def on_state_deleted(self, state_id: str) -> None:
        """状态删除事件
        
        Args:
            state_id: 删除的状态ID
        """
        pass
    
    @abstractmethod
    def on_state_error(self, state: IState, error: Exception) -> None:
        """状态错误事件
        
        Args:
            state: 发生错误的状态
            error: 错误信息
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        pass