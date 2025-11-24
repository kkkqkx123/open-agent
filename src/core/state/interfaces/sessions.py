"""会话状态特化接口定义

定义专门用于会话状态管理的接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import IState


class ISessionState(IState):
    """会话状态接口
    
    继承自基础状态接口，添加会话特定的功能。
    """
    
    @abstractmethod
    def get_user_id(self) -> Optional[str]:
        """获取用户ID"""
        pass
    
    @abstractmethod
    def set_user_id(self, user_id: str) -> None:
        """设置用户ID"""
        pass
    
    @abstractmethod
    def get_session_metadata(self) -> Dict[str, Any]:
        """获取会话元数据"""
        pass
    
    @abstractmethod
    def set_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置会话元数据"""
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        pass
    
    @abstractmethod
    def activate(self) -> None:
        """激活会话"""
        pass
    
    @abstractmethod
    def deactivate(self) -> None:
        """停用会话"""
        pass
    
    @abstractmethod
    def get_last_activity(self) -> datetime:
        """获取最后活动时间"""
        pass
    
    @abstractmethod
    def update_activity(self) -> None:
        """更新活动时间"""
        pass
    
    @abstractmethod
    def get_thread_ids(self) -> List[str]:
        """获取关联的线程ID列表"""
        pass
    
    @abstractmethod
    def add_thread_id(self, thread_id: str) -> None:
        """添加关联的线程ID"""
        pass
    
    @abstractmethod
    def remove_thread_id(self, thread_id: str) -> None:
        """移除关联的线程ID"""
        pass


class ISessionStateManager(ABC):
    """会话状态管理器接口"""
    
    @abstractmethod
    def create_session(self, user_id: str, **kwargs) -> ISessionState:
        """创建会话"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ISessionState]:
        """获取会话"""
        pass
    
    @abstractmethod
    def get_user_sessions(self, user_id: str) -> List[ISessionState]:
        """获取用户的所有会话"""
        pass
    
    @abstractmethod
    def get_active_sessions(self) -> List[ISessionState]:
        """获取所有活跃会话"""
        pass
    
    @abstractmethod
    def save_session(self, session: ISessionState) -> bool:
        """保存会话"""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    def cleanup_inactive_sessions(self, max_inactive_duration: int) -> int:
        """清理非活跃会话，返回清理的数量"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass