"""会话状态接口定义

定义专门用于会话管理的状态接口，继承自基础状态接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime

from .base import IState
from ..common_domain import AbstractSessionData


class ISessionState(IState, AbstractSessionData):
    """会话状态接口
    
    继承自基础状态接口，添加会话特定的功能。
    这个接口专门用于会话生命周期管理和状态持久化。
    
    职责：
    - 管理会话特定的属性和元数据
    - 跟踪会话活动状态
    - 维护会话关联的线程信息
    - 提供会话统计和摘要信息
    
    使用示例：
        ```python
        # 创建会话状态
        session_state = MySessionState()
        session_state.set_id("session_123")
        session_state.set_data("user_preferences", {...})
        
        # 检查会话活跃状态
        if session_state.is_active():
            print("Session is active")
        ```
    
    注意事项：
    - 会话状态应该定期更新最后活动时间
    - 消息和检查点计数应该自动维护
    - 会话配置变更应该被记录
    
    相关接口：
    - IState: 基础状态接口
    - ISessionStateManager: 会话状态管理器接口
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    # 会话特定属性 - 重用 AbstractSessionData 的 id 属性作为 session_id
    @property
    def session_id(self) -> str:
        """会话ID - 映射到基础 id 属性"""
        return self.id
    
    @property
    @abstractmethod
    def user_id(self) -> Optional[str]:
        """用户ID
        
        Returns:
            关联的用户ID，如果未设置则返回None
        """
        pass
    
    @property
    @abstractmethod
    def session_config(self) -> Dict[str, Any]:
        """会话配置
        
        Returns:
            会话配置字典
        """
        pass
    
    @property
    @abstractmethod
    def message_count(self) -> int:
        """消息计数
        
        Returns:
            会话中的消息总数
        """
        pass
    
    @property
    @abstractmethod
    def checkpoint_count(self) -> int:
        """检查点计数
        
        Returns:
            会话中的检查点总数
        """
        pass
    
    @property
    @abstractmethod
    def thread_ids(self) -> List[str]:
        """关联的线程ID列表
        
        Returns:
            线程ID列表
        """
        pass
    
    # 注意：created_at 和 updated_at 已经由 ITimestamped 提供
    # 这里添加会话特定的最后活动时间
    @property
    @abstractmethod
    def last_activity(self) -> datetime:
        """最后活动时间
        
        Returns:
            最后活动时间戳
        """
        pass
    
    # 会话特定方法
    @abstractmethod
    def increment_message_count(self) -> None:
        """增加消息计数
        
        Examples:
            ```python
            # 发送消息后更新计数
            session_state.increment_message_count()
            print(f"Message count: {session_state.message_count}")
            ```
        """
        pass
    
    @abstractmethod
    def increment_checkpoint_count(self) -> None:
        """增加检查点计数
        
        Examples:
            ```python
            # 创建检查点后更新计数
            session_state.increment_checkpoint_count()
            print(f"Checkpoint count: {session_state.checkpoint_count}")
            ```
        """
        pass
    
    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新会话配置
        
        Args:
            config: 新的配置字典，会与现有配置合并
            
        Examples:
            ```python
            # 更新会话配置
            new_config = {"timeout": 3600, "theme": "dark"}
            session_state.update_config(new_config)
            ```
        """
        pass
    
    @abstractmethod
    def add_thread(self, thread_id: str) -> None:
        """添加关联线程
        
        Args:
            thread_id: 要添加的线程ID
            
        Raises:
            ValueError: 当线程ID已存在时
            
        Examples:
            ```python
            # 添加新线程
            session_state.add_thread("thread_456")
            print(f"Thread count: {len(session_state.thread_ids)}")
            ```
        """
        pass
    
    @abstractmethod
    def remove_thread(self, thread_id: str) -> None:
        """移除关联线程
        
        Args:
            thread_id: 要移除的线程ID
            
        Examples:
            ```python
            # 移除线程
            session_state.remove_thread("thread_456")
            print(f"Thread count: {len(session_state.thread_ids)}")
            ```
        """
        pass
    
    @abstractmethod
    def update_last_activity(self) -> None:
        """更新最后活动时间
        
        Examples:
            ```python
            # 用户操作后更新活动时间
            session_state.update_last_activity()
            print(f"Last activity: {session_state.last_activity}")
            ```
        """
        pass
    
    @abstractmethod
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            是否活跃
            
        Examples:
            ```python
            # 检查会话是否在30分钟内活跃
            if session_state.is_active(30):
                print("Session is active")
            else:
                print("Session has expired")
            ```
        """
        pass
    
    @abstractmethod
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息
        
        Returns:
            会话摘要字典，包含：
            - session_id: 会话ID
            - user_id: 用户ID
            - message_count: 消息计数
            - checkpoint_count: 检查点计数
            - thread_count: 线程数量
            - last_activity: 最后活动时间
            - is_active: 是否活跃
            
        Examples:
            ```python
            summary = session_state.get_session_summary()
            print(f"Session {summary['session_id']} has {summary['message_count']} messages")
            ```
        """
        pass
    
    @abstractmethod
    def get_session_metadata(self) -> Dict[str, Any]:
        """获取会话元数据
        
        Returns:
            会话元数据字典
            
        Examples:
            ```python
            metadata = session_state.get_session_metadata()
            print(f"Session metadata: {metadata}")
            ```
        """
        pass
    
    @abstractmethod
    def set_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """设置会话元数据
        
        Args:
            metadata: 会话元数据字典
            
        Examples:
            ```python
            # 设置会话元数据
            metadata = {"source": "web", "version": "1.0"}
            session_state.set_session_metadata(metadata)
            ```
        """
        pass