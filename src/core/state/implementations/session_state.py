"""会话状态实现

提供会话状态的具体实现，继承自基础状态并实现会话特定功能。
"""

import uuid
from src.services.logger import get_logger
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from ..interfaces.sessions import ISessionState
from ..implementations.base_state import BaseStateImpl


logger = get_logger(__name__)


class SessionState(BaseStateImpl, ISessionState):
    """会话状态实现
    
    继承自基础状态实现，添加会话特定的功能。
    """
    
    def __init__(self, **kwargs):
        """初始化会话状态"""
        super().__init__(**kwargs)
        
        # 会话特定字段
        self._user_id: Optional[str] = kwargs.get('user_id')
        self._session_metadata: Dict[str, Any] = kwargs.get('session_metadata', {})
        self._is_active: bool = kwargs.get('is_active', True)
        self._last_activity: datetime = kwargs.get('last_activity', datetime.now())
        self._thread_ids: List[str] = kwargs.get('thread_ids', [])
        self._max_inactive_duration: int = kwargs.get('max_inactive_duration', 3600)  # 1小时
    
    # ISessionState 接口实现
    def get_user_id(self) -> Optional[str]:
        """获取用户ID"""
        return self._user_id
    
    def set_user_id(self, user_id: str) -> None:
        """设置用户ID"""
        self._user_id = user_id
        self._updated_at = datetime.now()
    
    def get_session_metadata(self) -> Dict[str, Any]:
        """获取会话元数据"""
        return self._session_metadata.copy()
    
    def set_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置会话元数据"""
        self._session_metadata = metadata.copy()
        self._updated_at = datetime.now()
    
    def update_session_metadata(self, updates: Dict[str, Any]) -> None:
        """更新会话元数据"""
        self._session_metadata.update(updates)
        self._updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return self._is_active
    
    def activate(self) -> None:
        """激活会话"""
        self._is_active = True
        self.update_activity()
    
    def deactivate(self) -> None:
        """停用会话"""
        self._is_active = False
        self._updated_at = datetime.now()
    
    def get_last_activity(self) -> datetime:
        """获取最后活动时间"""
        return self._last_activity
    
    def update_activity(self) -> None:
        """更新活动时间"""
        self._last_activity = datetime.now()
        self._updated_at = datetime.now()
    
    def get_thread_ids(self) -> List[str]:
        """获取关联的线程ID列表"""
        return self._thread_ids.copy()
    
    def add_thread_id(self, thread_id: str) -> None:
        """添加关联的线程ID"""
        if thread_id not in self._thread_ids:
            self._thread_ids.append(thread_id)
            self._updated_at = datetime.now()
    
    def remove_thread_id(self, thread_id: str) -> None:
        """移除关联的线程ID"""
        if thread_id in self._thread_ids:
            self._thread_ids.remove(thread_id)
            self._updated_at = datetime.now()
    
    def has_thread_id(self, thread_id: str) -> bool:
        """检查是否包含指定线程ID"""
        return thread_id in self._thread_ids
    
    def get_thread_count(self) -> int:
        """获取线程数量"""
        return len(self._thread_ids)
    
    # 会话特定方法
    def get_max_inactive_duration(self) -> int:
        """获取最大非活跃持续时间"""
        return self._max_inactive_duration
    
    def set_max_inactive_duration(self, duration: int) -> None:
        """设置最大非活跃持续时间"""
        self._max_inactive_duration = duration
        self._updated_at = datetime.now()
    
    def is_inactive(self) -> bool:
        """检查会话是否非活跃"""
        if not self._is_active:
            return True
        
        inactive_duration = (datetime.now() - self._last_activity).total_seconds()
        return inactive_duration > self._max_inactive_duration
    
    def get_inactive_duration(self) -> float:
        """获取非活跃持续时间（秒）"""
        return (datetime.now() - self._last_activity).total_seconds()
    
    def get_session_duration(self) -> float:
        """获取会话持续时间（秒）"""
        return (datetime.now() - self._created_at).total_seconds()
    
    def is_recent_activity(self, max_age_seconds: int = 300) -> bool:
        """检查是否有最近活动"""
        return self.get_inactive_duration() <= max_age_seconds
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            "id": self._id,
            "user_id": self._user_id,
            "is_active": self._is_active,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "thread_count": len(self._thread_ids),
            "session_duration": self.get_session_duration(),
            "inactive_duration": self.get_inactive_duration(),
            "is_inactive": self.is_inactive()
        }
    
    def clear_thread_ids(self) -> None:
        """清除所有线程ID"""
        self._thread_ids.clear()
        self._updated_at = datetime.now()
    
    def set_thread_ids(self, thread_ids: List[str]) -> None:
        """设置线程ID列表"""
        self._thread_ids = list(thread_ids)
        self._updated_at = datetime.now()
    
    def get_session_age(self) -> timedelta:
        """获取会话年龄"""
        return datetime.now() - self._created_at
    
    def is_long_session(self, max_duration_hours: int = 24) -> bool:
        """检查是否为长会话"""
        return self.get_session_duration() > (max_duration_hours * 3600)
    
    def extend_session(self, additional_time: int = 3600) -> None:
        """延长会话（通过更新活动时间）"""
        self._last_activity = datetime.now()
        self._max_inactive_duration += additional_time
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'user_id': self._user_id,
            'session_metadata': self._session_metadata,
            'is_active': self._is_active,
            'last_activity': self._last_activity.isoformat(),
            'thread_ids': self._thread_ids,
            'max_inactive_duration': self._max_inactive_duration
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """从字典创建状态"""
        instance = cls()
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._user_id = data.get("user_id")
        instance._session_metadata = data.get("session_metadata", {})
        instance._is_active = data.get("is_active", True)
        instance._thread_ids = data.get("thread_ids", [])
        instance._max_inactive_duration = data.get("max_inactive_duration", 3600)
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        # 处理时间
        created_at_str = data.get("created_at")
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        last_activity_str = data.get("last_activity")
        if last_activity_str:
            instance._last_activity = datetime.fromisoformat(last_activity_str)
        
        return instance
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"SessionState(id={self._id}, user_id={self._user_id}, "
                f"active={self._is_active}, threads={len(self._thread_ids)})")
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"SessionState(id={self._id}, user_id={self._user_id}, "
                f"active={self._is_active}, threads={len(self._thread_ids)}, "
                f"last_activity={self._last_activity.isoformat()})")


class UserSessionState(SessionState):
    """用户会话状态
    
    专门用于管理用户会话的状态。
    """
    
    def __init__(self, **kwargs):
        """初始化用户会话状态"""
        super().__init__(**kwargs)
        
        # 用户会话特定字段
        self._user_preferences: Dict[str, Any] = kwargs.get('user_preferences', {})
        self._user_permissions: List[str] = kwargs.get('user_permissions', [])
        self._login_time: datetime = kwargs.get('login_time', datetime.now())
        self._logout_time: Optional[datetime] = kwargs.get('logout_time')
        self._session_type: str = kwargs.get('session_type', 'user')
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好"""
        return self._user_preferences.copy()
    
    def set_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """设置用户偏好"""
        self._user_preferences = preferences.copy()
        self._updated_at = datetime.now()
    
    def update_user_preferences(self, updates: Dict[str, Any]) -> None:
        """更新用户偏好"""
        self._user_preferences.update(updates)
        self._updated_at = datetime.now()
    
    def get_user_permissions(self) -> List[str]:
        """获取用户权限"""
        return self._user_permissions.copy()
    
    def set_user_permissions(self, permissions: List[str]) -> None:
        """设置用户权限"""
        self._user_permissions = list(permissions)
        self._updated_at = datetime.now()
    
    def add_permission(self, permission: str) -> None:
        """添加权限"""
        if permission not in self._user_permissions:
            self._user_permissions.append(permission)
            self._updated_at = datetime.now()
    
    def remove_permission(self, permission: str) -> None:
        """移除权限"""
        if permission in self._user_permissions:
            self._user_permissions.remove(permission)
            self._updated_at = datetime.now()
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        return permission in self._user_permissions
    
    def get_login_time(self) -> datetime:
        """获取登录时间"""
        return self._login_time
    
    def set_login_time(self, login_time: datetime) -> None:
        """设置登录时间"""
        self._login_time = login_time
        self._updated_at = datetime.now()
    
    def get_logout_time(self) -> Optional[datetime]:
        """获取登出时间"""
        return self._logout_time
    
    def set_logout_time(self, logout_time: datetime) -> None:
        """设置登出时间"""
        self._logout_time = logout_time
        self._updated_at = datetime.now()
    
    def logout(self) -> None:
        """登出"""
        self._logout_time = datetime.now()
        self.deactivate()
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self._is_active and self._login_time is not None and self._logout_time is None
    
    def get_session_type(self) -> str:
        """获取会话类型"""
        return self._session_type
    
    def set_session_type(self, session_type: str) -> None:
        """设置会话类型"""
        self._session_type = session_type
        self._updated_at = datetime.now()
    
    def get_login_duration(self) -> Optional[float]:
        """获取登录持续时间（秒）"""
        if not self._login_time:
            return None
        
        end_time = self._logout_time or datetime.now()
        return (end_time - self._login_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'user_preferences': self._user_preferences,
            'user_permissions': self._user_permissions,
            'login_time': self._login_time.isoformat(),
            'logout_time': self._logout_time.isoformat() if self._logout_time else None,
            'session_type': self._session_type
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSessionState':
        """从字典创建状态"""
        # 首先创建父类实例，然后转换为子类类型
        session_state = SessionState.from_dict(data)
        instance: 'UserSessionState' = cls.__new__(cls)
        
        # 复制父类属性
        instance._id = session_state._id
        instance._data = session_state._data
        instance._metadata = session_state._metadata
        instance._complete = session_state._complete
        instance._created_at = session_state._created_at
        instance._updated_at = session_state._updated_at
        
        # 复制 SessionState 属性
        instance._user_id = session_state._user_id
        instance._session_metadata = session_state._session_metadata
        instance._is_active = session_state._is_active
        instance._last_activity = session_state._last_activity
        instance._thread_ids = session_state._thread_ids
        instance._max_inactive_duration = session_state._max_inactive_duration
        
        # 设置 UserSessionState 特定属性
        instance._user_preferences = data.get("user_preferences", {})
        instance._user_permissions = data.get("user_permissions", [])
        instance._session_type = data.get("session_type", "user")
        
        # 处理时间
        login_time_str = data.get("login_time")
        if login_time_str:
            instance._login_time = datetime.fromisoformat(login_time_str)
        else:
            instance._login_time = datetime.now()
        
        logout_time_str = data.get("logout_time")
        if logout_time_str:
            instance._logout_time = datetime.fromisoformat(logout_time_str)
        else:
            instance._logout_time = None
        
        return instance