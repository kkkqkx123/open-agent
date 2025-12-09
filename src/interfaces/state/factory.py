"""状态工厂接口定义

定义状态创建的接口。
"""

from abc import ABC, abstractmethod
from typing import Any

from .base import IState
from .workflow import IWorkflowState


class IStateFactory(ABC):
    """状态工厂接口
    
    定义状态创建的实现契约。
    """
    
    @abstractmethod
    def create_workflow_state(self, **kwargs: Any) -> IWorkflowState:
        """创建工作流状态
        
        Args:
            **kwargs: 状态创建参数
            
        Returns:
            创建的工作流状态
        """
        pass
    
    @abstractmethod
    def create_state_from_type(self, state_type: str, **kwargs: Any) -> IState:
        """创建指定类型的状态
        
        Args:
            state_type: 要创建的状态类型
            **kwargs: 状态创建参数
            
        Returns:
            创建的状态
        """
        pass