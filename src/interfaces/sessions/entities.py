"""会话实体接口定义

定义会话管理中使用的实体接口，遵循分层架构原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..common_domain import ISerializable


class ISession(ISerializable, ABC):
    """会话接口
    
    定义会话的基本契约，用于跨层传递会话数据。
    """
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """会话ID"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """会话状态"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @property
    @abstractmethod
    def thread_ids(self) -> List[str]:
        """关联的线程ID列表"""
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        pass


class IUserRequest(ISerializable, ABC):
    """用户请求接口
    
    定义用户请求的基本契约。
    """
    
    @property
    @abstractmethod
    def request_id(self) -> str:
        """请求ID"""
        pass
    
    @property
    @abstractmethod
    def user_id(self) -> Optional[str]:
        """用户ID"""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """请求内容"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """时间戳"""
        pass


class IUserInteraction(ISerializable, ABC):
    """用户交互接口
    
    定义用户交互的基本契约。
    """
    
    @property
    @abstractmethod
    def interaction_id(self) -> str:
        """交互ID"""
        pass
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """会话ID"""
        pass
    
    @property
    @abstractmethod
    def thread_id(self) -> Optional[str]:
        """线程ID"""
        pass
    
    @property
    @abstractmethod
    def interaction_type(self) -> str:
        """交互类型"""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """交互内容"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """时间戳"""
        pass


class ISessionContext(ISerializable, ABC):
    """会话上下文接口
    
    定义会话上下文的基本契约。
    """
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """会话ID"""
        pass
    
    @property
    @abstractmethod
    def user_id(self) -> Optional[str]:
        """用户ID"""
        pass
    
    @property
    @abstractmethod
    def thread_ids(self) -> List[str]:
        """线程ID列表"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """状态"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass