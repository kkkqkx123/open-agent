"""会话状态接口定义

定义专门用于会话管理的状态接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from .interfaces import IState
from ..common_domain import AbstractSessionData


class ISessionState(IState, AbstractSessionData):
    """会话状态接口
    
    继承自基础状态接口，添加会话特定的功能。
    这个接口专门用于会话生命周期管理和状态持久化。
    """
    
    # 会话特定属性 - 重用 AbstractSessionData 的 id 属性作为 session_id
    @property
    def session_id(self) -> str:
        """会话ID - 映射到基础 id 属性"""
        return self.id
    
    @property
    @abstractmethod
    def user_id(self) -> Optional[str]:
        """用户ID"""
        pass
    
    @property
    @abstractmethod
    def session_config(self) -> Dict[str, Any]:
        """会话配置"""
        pass
    
    @property
    @abstractmethod
    def message_count(self) -> int:
        """消息计数"""
        pass
    
    @property
    @abstractmethod
    def checkpoint_count(self) -> int:
        """检查点计数"""
        pass
    
    @property
    @abstractmethod
    def thread_ids(self) -> list[str]:
        """关联的线程ID列表"""
        pass
    
    # 注意：created_at 和 updated_at 已经由 ITimestamped 提供
    # 这里添加会话特定的最后活动时间
    @property
    @abstractmethod
    def last_activity(self) -> datetime:
        """最后活动时间"""
        pass
    
    # 会话特定方法
    @abstractmethod
    def increment_message_count(self) -> None:
        """增加消息计数"""
        pass
    
    @abstractmethod
    def increment_checkpoint_count(self) -> None:
        """增加检查点计数"""
        pass
    
    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新会话配置"""
        pass
    
    @abstractmethod
    def add_thread(self, thread_id: str) -> None:
        """添加关联线程"""
        pass
    
    @abstractmethod
    def remove_thread(self, thread_id: str) -> None:
        """移除关联线程"""
        pass
    
    @abstractmethod
    def update_last_activity(self) -> None:
        """更新最后活动时间"""
        pass
    
    @abstractmethod
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            是否活跃
        """
        pass
    
    @abstractmethod
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息
        
        Returns:
            会话摘要字典
        """
        pass
    
    @abstractmethod
    def get_session_metadata(self) -> Dict[str, Any]:
        """获取会话元数据
        
        Returns:
            会话元数据字典
        """
        pass
    
    @abstractmethod
    def set_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置会话元数据
        
        Args:
            metadata: 会话元数据字典
        """
        pass


class ISessionStateManager(ABC):
    """会话状态管理器接口"""
    
    @abstractmethod
    def create_session_state(self, session_id: str, user_id: Optional[str] = None,
                           config: Optional[Dict[str, Any]] = None) -> ISessionState:
        """创建会话状态"""
        pass
    
    @abstractmethod
    def get_session_state(self, session_id: str) -> Optional[ISessionState]:
        """获取会话状态"""
        pass
    
    @abstractmethod
    def save_session_state(self, session_state: ISessionState) -> None:
        """保存会话状态"""
        pass
    
    @abstractmethod
    def delete_session_state(self, session_id: str) -> bool:
        """删除会话状态"""
        pass
    
    @abstractmethod
    def get_active_sessions(self, timeout_minutes: int = 30) -> list[ISessionState]:
        """获取活跃会话列表"""
        pass
    
    @abstractmethod
    def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """清理非活跃会话
        
        Returns:
            清理的会话数量
        """
        pass
    
    @abstractmethod
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """清空缓存"""
        pass