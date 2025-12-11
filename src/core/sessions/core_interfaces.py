"""会话核心接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entities import Session, UserRequestEntity, UserInteractionEntity


class ISessionCore(ABC):
    """会话核心接口"""
    
    @abstractmethod
    def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'Session':
        """创建会话实体
        
        Args:
            user_id: 用户ID
            metadata: 会话元数据
            
        Returns:
            创建的会话实体
        """
        pass
    
    @abstractmethod
    def validate_session_state(self, session_data: Dict[str, Any]) -> bool:
        """验证会话状态
        
        Args:
            session_data: 会话数据
            
        Returns:
            状态是否有效
        """
        pass
    
    @abstractmethod
    def create_user_request(self, content: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'UserRequestEntity':
        """创建用户请求实体
        
        Args:
            content: 请求内容
            user_id: 用户ID
            metadata: 请求元数据
            
        Returns:
            创建的用户请求实体
        """
        pass
    
    @abstractmethod
    def create_user_interaction(self, session_id: str, interaction_type: str, content: str, thread_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> 'UserInteractionEntity':
        """创建用户交互实体
        
        Args:
            session_id: 会话ID
            interaction_type: 交互类型
            content: 交互内容
            thread_id: 线程ID
            metadata: 交互元数据
            
        Returns:
            创建的用户交互实体
        """
        pass


class ISessionValidator(ABC):
    """会话验证器接口"""
    
    @abstractmethod
    def validate_session_id(self, session_id: str) -> bool:
        """验证会话ID格式
        
        Args:
            session_id: 会话ID
            
        Returns:
            ID格式是否有效
        """
        pass
    
    @abstractmethod
    def validate_user_request(self, request: 'UserRequestEntity') -> bool:
        """验证用户请求
        
        Args:
            request: 用户请求实体
            
        Returns:
            请求是否有效
        """
        pass
    
    @abstractmethod
    def validate_user_interaction(self, interaction: 'UserInteractionEntity') -> bool:
        """验证用户交互
        
        Args:
            interaction: 用户交互实体
            
        Returns:
            交互是否有效
        """
        pass


class ISessionStateTransition(ABC):
    """会话状态转换接口"""
    
    @abstractmethod
    def can_transition(self, current_status: str, target_status: str) -> bool:
        """检查是否可以转换状态
        
        Args:
            current_status: 当前状态
            target_status: 目标状态
            
        Returns:
            是否可以转换
        """
        pass
    
    @abstractmethod
    def get_valid_transitions(self, current_status: str) -> list[str]:
        """获取有效的状态转换列表
        
        Args:
            current_status: 当前状态
            
        Returns:
            有效转换状态列表
        """
        pass