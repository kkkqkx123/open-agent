"""会话状态实现

提供会话状态的具体实现，继承自基础状态并实现会话特定功能。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.interfaces.state.session import ISessionState
from src.interfaces.state.base import IState
from src.interfaces.common_domain import AbstractSessionStatus
from ..implementations.base_state import BaseStateImpl


logger = get_logger(__name__)


class SessionStateImpl(BaseStateImpl, ISessionState, IState):
    """会话状态实现
    
    继承自基础状态实现，添加会话特定的功能。
    """
    
    def __init__(self, session_id: str, **kwargs):
        """初始化会话状态"""
        super().__init__(**kwargs)
        
        # 会话特定字段
        self._session_id = session_id
        self._user_id = kwargs.get('user_id')
        self._session_config = kwargs.get('session_config', {})
        self._message_count = kwargs.get('message_count', 0)
        self._checkpoint_count = kwargs.get('checkpoint_count', 0)
        self._thread_ids = set(kwargs.get('thread_ids', []))
        self._last_activity = kwargs.get('last_activity', datetime.now())
        self._created_at = kwargs.get('created_at', datetime.now())
        self._session_status = kwargs.get('session_status', AbstractSessionStatus.ACTIVE)
        
        # 会话元数据
        self._session_metadata = kwargs.get('session_metadata', {})
    
    # AbstractSessionData 接口实现
    @property
    def id(self) -> str:
        """会话ID - 实现 AbstractSessionData 的 id 属性"""
        return self._session_id
    
    @property
    def status(self) -> AbstractSessionStatus:
        """会话状态 - 实现 AbstractSessionData 的 status 属性"""
        return self._session_status
    
    @property
    def created_at(self) -> datetime:
        """创建时间 - 实现 AbstractSessionData 的 created_at 属性"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """更新时间 - 实现 AbstractSessionData 的 updated_at 属性"""
        return self._updated_at
    
    # ISessionState 接口实现
    @property
    def session_id(self) -> str:
        """会话ID"""
        return self._session_id
    
    @property
    def user_id(self) -> Optional[str]:
        """用户ID"""
        return self._user_id
    
    @property
    def session_config(self) -> Dict[str, Any]:
        """会话配置"""
        return self._session_config.copy()
    
    @property
    def message_count(self) -> int:
        """消息计数"""
        return self._message_count
    
    @property
    def checkpoint_count(self) -> int:
        """检查点计数"""
        return self._checkpoint_count
    
    @property
    def thread_ids(self) -> List[str]:
        """关联的线程ID列表"""
        return list(self._thread_ids)
    
    @property
    def last_activity(self) -> datetime:
        """最后活动时间"""
        return self._last_activity
    
    def increment_message_count(self) -> None:
        """增加消息计数"""
        self._message_count += 1
        self.update_last_activity()
        logger.debug(f"会话 {self._session_id} 消息计数增加到 {self._message_count}")
    
    def increment_checkpoint_count(self) -> None:
        """增加检查点计数"""
        self._checkpoint_count += 1
        self.update_last_activity()
        logger.debug(f"会话 {self._session_id} 检查点计数增加到 {self._checkpoint_count}")
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新会话配置"""
        self._session_config.update(config)
        self.update_last_activity()
        logger.debug(f"会话 {self._session_id} 配置已更新")
    
    def add_thread(self, thread_id: str) -> None:
        """添加关联线程"""
        self._thread_ids.add(thread_id)
        self.update_last_activity()
        logger.debug(f"会话 {self._session_id} 添加线程 {thread_id}")
    
    def remove_thread(self, thread_id: str) -> None:
        """移除关联线程"""
        self._thread_ids.discard(thread_id)
        self.update_last_activity()
        logger.debug(f"会话 {self._session_id} 移除线程 {thread_id}")
    
    def update_last_activity(self) -> None:
        """更新最后活动时间"""
        self._last_activity = datetime.now()
        self._updated_at = self._last_activity
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃"""
        timeout = datetime.now() - timedelta(minutes=timeout_minutes)
        return self._last_activity >= timeout
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息"""
        return {
            "session_id": self._session_id,
            "user_id": self._user_id,
            "message_count": self._message_count,
            "checkpoint_count": self._checkpoint_count,
            "thread_count": len(self._thread_ids),
            "thread_ids": list(self._thread_ids),
            "last_activity": self._last_activity.isoformat(),
            "created_at": self._created_at.isoformat(),
            "duration_minutes": (datetime.now() - self._created_at).total_seconds() / 60,
            "is_active": self.is_active(),
            "config_keys": list(self._session_config.keys()),
            "metadata_keys": list(self._session_metadata.keys())
        }
    
    # 扩展方法
    def get_thread_count(self) -> int:
        """获取关联线程数量"""
        return len(self._thread_ids)
    
    def has_thread(self, thread_id: str) -> bool:
        """检查是否包含指定线程"""
        return thread_id in self._thread_ids
    
    def get_session_age_minutes(self) -> float:
        """获取会话年龄（分钟）"""
        return (datetime.now() - self._created_at).total_seconds() / 60
    
    def get_idle_time_minutes(self) -> float:
        """获取空闲时间（分钟）"""
        return (datetime.now() - self._last_activity).total_seconds() / 60
    
    def set_user_id(self, user_id: str) -> None:
        """设置用户ID"""
        self._user_id = user_id
        self.update_last_activity()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._session_config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._session_config[key] = value
        self.update_last_activity()
    
    def set_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置会话元数据"""
        self._session_metadata = metadata
        self.update_last_activity()
    
    def get_session_metadata(self) -> Dict[str, Any]:
        """获取会话元数据"""
        return self._session_metadata.copy()
    
    def add_metadata_value(self, key: str, value: Any) -> None:
        """添加元数据值"""
        self._session_metadata[key] = value
        self.update_last_activity()
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self._session_metadata.get(key, default)
    
    def reset_counters(self) -> None:
        """重置计数器"""
        self._message_count = 0
        self._checkpoint_count = 0
        self.update_last_activity()
        logger.debug(f"会话 {self._session_id} 计数器已重置")
    
    def archive_session(self) -> Dict[str, Any]:
        """归档会话数据
        
        Returns:
            归档数据字典
        """
        archive_data = {
            "session_id": self._session_id,
            "user_id": self._user_id,
            "created_at": self._created_at.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "message_count": self._message_count,
            "checkpoint_count": self._checkpoint_count,
            "thread_ids": list(self._thread_ids),
            "session_config": self._session_config,
            "session_metadata": self._session_metadata,
            "archived_at": datetime.now().isoformat()
        }
        
        logger.info(f"会话 {self._session_id} 已归档")
        return archive_data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'session_id': self._session_id,
            'user_id': self._user_id,
            'session_config': self._session_config,
            'message_count': self._message_count,
            'checkpoint_count': self._checkpoint_count,
            'thread_ids': list(self._thread_ids),
            'last_activity': self._last_activity.isoformat(),
            'created_at': self._created_at.isoformat(),
            'session_metadata': self._session_metadata
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionStateImpl':
        """从字典创建状态"""
        session_id = data.get('session_id')
        if not session_id:
            raise ValueError("session_id is required")
        
        instance = cls(session_id=session_id)
        instance._user_id = data.get('user_id')
        instance._session_config = data.get('session_config', {})
        instance._message_count = data.get('message_count', 0)
        instance._checkpoint_count = data.get('checkpoint_count', 0)
        instance._thread_ids = set(data.get('thread_ids', []))
        instance._session_metadata = data.get('session_metadata', {})
        
        # 处理时间
        last_activity_str = data.get('last_activity')
        if last_activity_str:
            instance._last_activity = datetime.fromisoformat(last_activity_str)
        
        created_at_str = data.get('created_at')
        if created_at_str:
            instance._created_at = datetime.fromisoformat(created_at_str)
        
        # 处理基础字段
        instance._data = data.get("data", {})
        instance._metadata = data.get("metadata", {})
        instance._id = data.get("id")
        instance._complete = data.get("complete", False)
        
        updated_at_str = data.get("updated_at")
        if updated_at_str:
            instance._updated_at = datetime.fromisoformat(updated_at_str)
        
        return instance
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SessionState(id={self._session_id}, user={self._user_id}, messages={self._message_count}, threads={len(self._thread_ids)})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"SessionStateImpl(session_id='{self._session_id}', user_id='{self._user_id}', "
                f"message_count={self._message_count}, checkpoint_count={self._checkpoint_count}, "
                f"thread_count={len(self._thread_ids)}, last_activity='{self._last_activity.isoformat()}')")