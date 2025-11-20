"""状态生命周期管理接口定义

定义状态生命周期管理的接口。
"""

from abc import ABC, abstractmethod
from typing import List

from .interfaces import IState


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