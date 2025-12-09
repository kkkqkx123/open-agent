"""会话状态管理器接口定义

定义会话状态管理器的接口，提供会话生命周期管理功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .session import ISessionState


class ISessionStateManager(ABC):
    """会话状态管理器接口
    
    定义会话状态管理的契约，提供会话的创建、查询、更新和清理功能。
    
    职责：
    - 管理会话状态的生命周期
    - 提供会话的持久化和恢复
    - 维护会话的活跃状态
    - 提供会话统计和清理功能
    
    使用示例：
        ```python
        # 创建会话管理器
        manager = MySessionStateManager()
        
        # 创建新会话
        session = manager.create_session_state("session_123", "user_456")
        
        # 获取会话状态
        session = manager.get_session_state("session_123")
        ```
    
    注意事项：
    - 会话管理器应该处理并发访问
    - 应该定期清理非活跃会话
    - 需要考虑会话的持久化策略
    
    相关接口：
    - ISessionState: 会话状态接口
    - IStateManager: 通用状态管理器接口
    
    版本历史：
    - v1.0.0: 初始版本
    """
    
    @abstractmethod
    def create_session_state(self, session_id: str, user_id: Optional[str] = None,
                           config: Optional[Dict[str, Any]] = None) -> ISessionState:
        """创建会话状态
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（可选）
            config: 会话配置（可选）
            
        Returns:
            创建的会话状态实例
            
        Raises:
            ValueError: 当会话ID已存在时
            RuntimeError: 当创建失败时
            
        Examples:
            ```python
            # 创建基本会话
            session = manager.create_session_state("session_123")
            
            # 创建带用户和配置的会话
            config = {"timeout": 3600, "theme": "dark"}
            session = manager.create_session_state(
                "session_456", 
                user_id="user_789", 
                config=config
            )
            ```
        """
        pass
    
    @abstractmethod
    def get_session_state(self, session_id: str) -> Optional[ISessionState]:
        """获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态实例，如果未找到则返回None
            
        Examples:
            ```python
            session = manager.get_session_state("session_123")
            if session:
                print(f"Found session for user: {session.user_id}")
            else:
                print("Session not found")
            ```
        """
        pass
    
    @abstractmethod
    def save_session_state(self, session_state: ISessionState) -> None:
        """保存会话状态
        
        Args:
            session_state: 要保存的会话状态
            
        Raises:
            ValueError: 当会话状态无效时
            RuntimeError: 当保存失败时
            
        Examples:
            ```python
            # 修改会话后保存
            session.increment_message_count()
            manager.save_session_state(session)
            ```
        """
        pass
    
    @abstractmethod
    def delete_session_state(self, session_id: str) -> bool:
        """删除会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
            
        Examples:
            ```python
            if manager.delete_session_state("session_123"):
                print("Session deleted successfully")
            else:
                print("Session not found or deletion failed")
            ```
        """
        pass
    
    @abstractmethod
    def get_active_sessions(self, timeout_minutes: int = 30) -> List[ISessionState]:
        """获取活跃会话列表
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            活跃会话状态列表
            
        Examples:
            ```python
            # 获取30分钟内活跃的会话
            active_sessions = manager.get_active_sessions(30)
            print(f"Found {len(active_sessions)} active sessions")
            
            for session in active_sessions:
                print(f"Session {session.session_id} for user {session.user_id}")
            ```
        """
        pass
    
    @abstractmethod
    def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """清理非活跃会话
        
        Args:
            timeout_minutes: 超时时间（分钟），超过此时间的会话将被清理
            
        Returns:
            清理的会话数量
            
        Examples:
            ```python
            # 清理1小时未活动的会话
            cleaned_count = manager.cleanup_inactive_sessions(60)
            print(f"Cleaned {cleaned_count} inactive sessions")
            ```
        """
        pass
    
    @abstractmethod
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息
        
        Returns:
            统计信息字典，包含：
            - total_sessions: 总会话数
            - active_sessions: 活跃会话数
            - inactive_sessions: 非活跃会话数
            - total_messages: 总消息数
            - total_checkpoints: 总检查点数
            - average_session_duration: 平均会话时长（可选）
            
        Examples:
            ```python
            stats = manager.get_session_statistics()
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Active sessions: {stats['active_sessions']}")
            print(f"Total messages: {stats['total_messages']}")
            ```
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """清空缓存
        
        清理会话管理器的内部缓存，强制下次访问时从持久化存储重新加载。
        
        Examples:
            ```python
            # 清空缓存
            manager.clear_cache()
            print("Session manager cache cleared")
            ```
        """
        pass
    
    @abstractmethod
    def get_sessions_by_user(self, user_id: str) -> List[ISessionState]:
        """获取用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户的会话状态列表
            
        Examples:
            ```python
            # 获取特定用户的所有会话
            user_sessions = manager.get_sessions_by_user("user_123")
            print(f"User has {len(user_sessions)} sessions")
            ```
        """
        pass
    
    @abstractmethod
    def update_session_config(self, session_id: str, config: Dict[str, Any]) -> bool:
        """更新会话配置
        
        Args:
            session_id: 会话ID
            config: 新的配置字典
            
        Returns:
            是否更新成功
            
        Examples:
            ```python
            # 更新会话配置
            new_config = {"timeout": 7200, "theme": "light"}
            if manager.update_session_config("session_123", new_config):
                print("Session config updated")
            ```
        """
        pass